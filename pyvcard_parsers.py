import xml.etree.ElementTree as et
import pyvcard
from csv import DictReader
import io
import json


def get_string(obj):
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


class xCard_Parser:
    def __init__(self, xcard, indexer=None):
        self.xcard = xcard
        self.indexer = indexer

    def _is_supported_tag(self, name):
        return name.lower() in [
            "language-tag", "uri", "text", "integer",
            "unknown", "vcards", "vcard", "parameters",
            "date", "time", "date-time", "date-and-or-time",
            "timestamp", "boolean", "float", "utc-offset"
        ]

    def vcards(self):
        vcards = []
        tree = et.parsestring(get_string(self._object))
        root = tree.getroot()
        for node in root:
            if node.name == "vcard":
                factory = pyvcard.builder(self.indexer)
                factory.set_version("4.0")
                params = {}
                if node[0].name == "group":
                    group = node[0]["name"]
                    node = node[0]
                for vcard_data in node:
                    name = vcard_data.name.upper()
                    for attr in vcard_data:
                        if attr.name == "parameters":
                            for param in attr:
                                if len(param) == 1:
                                    params[param.name.upper()] = param[0].text
                                else:
                                    s = []
                                    for subvalues in param:
                                        s.append(subvalues.text)
                                    s = "".join(s)
                                    params[param.name.upper()] = s
                        else:
                            if name == "N":
                                name_array = ['' for i in range(5)]
                                for tag in vcard_data:
                                    if tag.name == "surname":
                                        name_array[0] = tag.text
                                    if tag.name == "given":
                                        name_array[1] = tag.text
                                    if tag.name == "additional":
                                        name_array[2] = tag.text
                                    if tag.name == "prefix":
                                        name_array[3] = tag.text
                                    if tag.name == "suffix":
                                        name_array[4] = tag.text
                                value = name_array
                            elif self._is_supported_tag(name):
                                value_type = attr.name
                                if value_type != "unknown":
                                    params["VALUE"] = value_type
                                value = attr.text.split(";")
                            else:
                                value = [et.tostring(attr, 'utf-8')]
                    factory.add_property(name, value, group=group, params=params)
                vcards.append(factory.build())
        return vcards


class csv_Parser:
    def __init__(self, csv, indexer=None):
        self.csv = csv
        self.indexer = indexer

    def vcards(self):
        strio = io.StringIO(get_string(self.csv))
        reader = DictReader(strio, delimiter=",")
        raw = list(reader)
        s = ''
        for data in raw:
            s += data["vCard"] + "\n"
        return pyvcard.parse(s, self.indexer).vcards()


class jCard_Parser:
    class jCard_ValidationError(Exception):
        pass

    def __init__(self, source, indexer=None):
        self.indexer = indexer
        if isinstance(source, str):
            self.source = json.loads(source)
        else:
            self.source = source

    def parse_vcard(self, vcard):
        factory = pyvcard.builder(self.indexer)
        factory.set_version("4.0")
        if vcard[0] != "vcard":
            raise self.jCard_ValidationError("jCard isn't match to standard")
        for data in vcard[1:][0]:
            name = data[0].upper()
            params = data[1]
            newparams = {}
            group = None
            for param in params:
                if "group" in params:
                    group = params["group"]
                else:
                    newparams[param.upper()] = params[param]
            if data[2] != "unknown":
                newparams["VALUE"] = data[2]
            if len(data[3:]) == 1:
                if hasattr(data[3:][0], "__iter__") and not isinstance(data[3:][0], str):
                    value = data[3:][0]
                else:
                    value = data[3:]
            factory.add_property(name, value, newparams, group)
        return factory.build()

    def vcards(self):
        vcards = []
        if self.source[0] == "vcard":
            vcards.append(self.parse_vcard(self.source))
        else:
            for vcard in self.source:
                vcards.append(self.parse_vcard(vcard))
        return vcards
