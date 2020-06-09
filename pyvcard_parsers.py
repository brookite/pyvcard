import xml.etree.ElementTree as et
import pyvcard
from csv import DictReader
import io
import re
import json


def get_string(obj):
    """
    Gets the string from file or str. Utility method
    """
    if isinstance(obj, str):
        return obj
    elif hasattr(obj, "close"):
        if not obj.closed():
            s = obj.read()
            obj.close()
            obj = s
            return obj
        else:
            raise ValueError("File is closed")
    else:
        raise ValueError("Required specific object string or file descriptor")


class AbstractParser:
    def vcards(self):
        pass


class xCard_Parser(AbstractParser):
    """
    This class describes a XML to vCard object parser
    xCard (RFC 6351)
    """

    def __init__(self, xcard, indexer=None):
        self.xcard = xcard
        self.indexer = indexer

    def _is_supported_tag(self, name):
        return name.lower() in [
            "language-tag", "uri", "text", "integer",
            "unknown", "vcards", "vcard", "parameters",
            "date", "time", "date-time", "date-and-or-time",
            "timestamp", "boolean", "float", "utc-offset", "sex"
        ]

    def _tag_name(self, tag):
        return re.sub(r"{.+}", "", tag.tag)

    def vcards(self):
        """
        Returns result of parsing

        :returns:   vCard objects
        :rtype:     vCardSet
        """
        vcards = []
        root = et.fromstring(get_string(self.xcard))
        for node in root:
            if self._tag_name(node) == "vcard":
                factory = pyvcard.builder(self.indexer)
                if self._tag_name(node[0]) == "group":
                    group = node[0].attrib["name"]
                    node = node[0]
                else:
                    group = None
                for vcard_data in node:
                    params = {}
                    value = None
                    name = self._tag_name(vcard_data).upper()
                    name_array = None
                    for attr in vcard_data:
                        if self._tag_name(attr) == "parameters":
                            for param in attr:
                                if len(param) == 1:
                                    if param[0].text == "":
                                        params[self._tag_name(param).upper()] = None
                                    else:
                                        params[self._tag_name(param).upper()] = param[0].text
                                else:
                                    s = []
                                    for subvalues in param:
                                        s.append(subvalues.text)
                                    s = ",".join(s)
                                    params[self._tag_name(param).upper()] = s
                        else:
                            if name == "N":
                                if name_array is None:
                                    name_array = ['' for i in range(5)]
                                if self._tag_name(attr) == "surname":
                                    name_array[0] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "given":
                                    name_array[1] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "additional":
                                    name_array[2] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "prefix":
                                    name_array[3] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "suffix":
                                    name_array[4] = attr.text if attr.text is not None else ""
                                value = name_array
                            elif name == "ADR":
                                if name_array is None:
                                    name_array = ['' for i in range(7)]
                                if self._tag_name(attr) == "pobox":
                                    name_array[0] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "ext":
                                    name_array[1] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "street":
                                    name_array[2] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "locality":
                                    name_array[3] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "region":
                                    name_array[4] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "code":
                                    name_array[5] = attr.text if attr.text is not None else ""
                                if self._tag_name(attr) == "country":
                                    name_array[6] = attr.text if attr.text is not None else ""
                                value = name_array
                            elif self._is_supported_tag(self._tag_name(attr)):
                                if value is None:
                                    value_type = self._tag_name(attr)
                                    if value_type != "unknown":
                                        params["VALUE"] = value_type
                                    value = [attr.text]
                                else:
                                    value.append(attr.text)
                            else:
                                value = [et.tostring(attr, 'utf-8').decode("utf-8")]
                    if name == "VERSION":
                        factory.set_version(value[0])
                    else:
                        factory.add_property(name, value, group=group, params=params, encoding_raw=True)
                vcards.append(factory.build())
        return pyvcard.vCardSet(vcards)


class csv_Parser(AbstractParser):
    """
    This class describes a CSV to vCard object parser
    """

    def __init__(self, csv, indexer=None):
        self.csv = csv
        self.indexer = indexer

    def vcards(self):
        """
        Returns result of parsing

        :returns:   vCard objects
        :rtype:     vCardSet
        """
        strio = io.StringIO(get_string(self.csv))
        reader = DictReader(strio, delimiter=",")
        raw = list(reader)
        s = ''
        for data in raw:
            s += data["vCard"] + "\n"
        return pyvcard.parse(s, self.indexer).vcards()


class jCard_Parser(AbstractParser):
    """
    This class describes a JSON to vCard object parser
    jCard (RFC 7095)
    """
    class jCard_ValidationError(Exception):
        pass

    def __init__(self, source, indexer=None):
        self.indexer = indexer
        if isinstance(source, str):
            self.source = json.loads(source)
        else:
            self.source = source

    def parse_vcard(self, vcard):
        """
        Utility method
        """
        factory = pyvcard.builder(self.indexer)
        if vcard[0] != "vcard":
            raise self.jCard_ValidationError("jCard isn't match to standard")
        for data in vcard[1:][0]:
            name = data[0].upper()
            if name == "VERSION":
                factory.set_version(data[3])
                continue
            params = data[1]
            newparams = {}
            group = None
            for param in params:
                if "group" in params:
                    group = params["group"]
                else:
                    if isinstance(params[param], str):
                        newparams[param.upper()] = params[param].lower()
                    elif params[param] is not None:
                        newparams[param.upper()] = ",".join(params[param]).lower()
            if data[2] != "unknown":
                newparams["VALUE"] = data[2].lower()
            if len(data[3:]) == 1:
                if hasattr(data[3:][0], "__iter__") and not isinstance(data[3:][0], str):
                    value = data[3:][0]
                else:
                    value = data[3:]
            factory.add_property(name, value, newparams, group, encoding_raw=True)
        return factory.build()

    def vcards(self):
        """
        Returns result of parsing

        :returns:   vCard objects
        :rtype:     vCardSet
        """
        vcards = []
        if self.source[0] == "vcard":
            vcards.append(self.parse_vcard(self.source))
        else:
            for vcard in self.source:
                vcards.append(self.parse_vcard(vcard))
        return pyvcard.vCardSet(vcards)
