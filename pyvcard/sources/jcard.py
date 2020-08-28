import json

import pyvcard.vobject
from pyvcard.converters import AbstractConverter, determine_type, encoding_convert
from pyvcard.parsers import AbstractParser


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
        factory = pyvcard.vobject.builder(self.indexer)
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
        return pyvcard.vobject.vCardSet(vcards)


class jCard_Converter(AbstractConverter):
    """
    This class describes a vCard object to JSON converter
    jCard (RFC 7095)
    """

    def __init__(self, obj):
        self._object = obj

    def write_vcard(self, vcard, array):
        """
        Writes a vCard. Utility method
        """
        jcard = ["vcard", []]
        properties = jcard[1]
        for prop in vcard:
            if prop.name == "VERSION" and prop.value == "4.0":
                continue
            current = []
            current.append(prop.name.lower())
            params = {}
            if prop.group is not None:
                params["group"] = prop.group
            for param in prop.params:
                if param.lower() != "value":
                    if prop.params[param] is not None:
                        if "," in prop.params[param]:
                            params[param.lower()] = prop.params[param].split(",")
                        else:
                            params[param.lower()] = prop.params[param]
                    else:
                        params[param.lower()] = None
            current.append(params)
            current.append(determine_type(prop))
            if len(prop.values) == 1:
                val = encoding_convert(prop.values[0], prop.params)
                current.append(val)
            else:
                arr = []
                for i in prop.values:
                    if isinstance(prop.values[0], bytes):
                        i = encoding_convert(prop.values[0], prop.params)
                    else:
                        if "," in i:
                            i = i.split(",")
                    arr.append(encoding_convert(i, prop.params))
                current.append(arr)
            properties.append(current)
        array.append(jcard)

    def result(self, return_obj=False, *args, **kwargs):
        """
        Returns string result of converting
        """
        vcards = []
        if isinstance(self._object, pyvcard.vobject.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, vcards)
        else:
            self.write_vcard(self._object, vcards)
        if return_obj:
            return vcards
        else:
            return json.dumps(vcards, ensure_ascii=False, *args, **kwargs)