import xml.etree.ElementTree as et
from pyvcard import builder, parse
from csv import DictReader
import io


def get_string(self, obj):
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
        raise ValueError("Required xcard object string or file descriptor")


class xCard_Parser:
    def __init__(self, xcard):
        self.xcard = xcard

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
                factory = builder()
                factory.set_version("4.0")
                params = {}
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
                    factory.add_property(name, value, params=params)
                vcards.append(factory.build())
        return vcards


class csv_Parser:
    def __init__(self, csv):
        self.csv = csv

    def vcards(self):
        strio = io.StringIO(get_string(self.csv))
        reader = DictReader(strio, delimiter=",")
        raw = list(reader)
        s = ''
        for data in raw:
            s += data["vCard"]
        return parse(s).vcards()
