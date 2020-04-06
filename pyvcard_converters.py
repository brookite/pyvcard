import xml.etree.ElementTree as et
from pyvcard import is_vcard, unescape, vCardSet
from pyvcard_validator import validate_uri
from xml.dom import minidom
from csv import DictWriter
import warnings
import io
import json


class csv_Converter:
    def __init__(self, obj):
        if is_vcard(obj) or isinstance(obj, vCardSet):
            self._object = obj
        else:
            raise ValueError("Required vCardSet or vCard type")

    @property
    def object(self):
        return self._object

    def write_vcard(self, vcard, writer):
        data = vcard.contact_data()
        row = {
            "Formatted name": data["name"],
            "Name": data["struct_name"],
            "Tel. Number": data["number"],
            "vCard": vcard.repr_vcard()
        }
        writer.writerow(row)

    def result(self):
        strio = io.StringIO()
        names = ["Formatted name", "Name", "Tel. Number", "vCard"]
        writer = DictWriter(strio, fieldnames=names)
        writer.writeheader()
        if isinstance(self._object, vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, writer)
        else:
            self.write_vcard(self._object, writer)
        val = strio.getvalue()
        strio.close()
        return val


class jCard_Converter:
    def __init__(self, obj):
        self._object = obj

    @property
    def object(self):
        return self._object

    def determine_type(self, prop):
        if "VALUE" in prop.params:
            return prop.params["VALUE"]
        else:
            if prop.name in [
                "N", "FN", "XML", "KIND", "GENDER",
                "TZ", "TITLE", "ROLE", "TEL", "EMAIL",
                "ORG", "CATEGORIES", "NOTES", "PRODID",
                "EXPERTISE", "HOBBY", "INTEREST", "ORG-DIRECTORY",
                "BIRTHPLACE", "DEATHPLACE"
            ]:
                return "text"
            elif prop.name in [
                "SOURCE", "IMPP", "GEO", "LOGO",
                "MEMBER", "RELATED", "SOUND",
                "UID", "URI", "KEY", "FBURL",
                "CALADRURI", "CALURI"
            ]:
                return "uri"
            elif prop.name in ["BDAY", "ANNIVERSARY", "DEATHDATE"]:
                return "date-and-or-time"
            elif prop.name in ["LANG"]:
                return "language-tag"
            elif prop.name in ["REV"]:
                return "timestamp"
            else:
                return "unknown"

    def write_vcard(self, vcard, array):
        vcard = ["vcard", []]
        properties = vcard[1]
        for prop in vcard:
            current = []
            current.append(prop.name.lower())
            params = {}
            if prop.group is not None:
                params["group"] = prop.group
            for param in prop.params:
                if param.lower() != "value":
                    if "," in params[param.lower()]:
                        params[param.lower()] = prop.params[param].split(",")
                    else:
                        params[param.lower()] = prop.params[param]
            current.append(params)
            current.append(self.determine_type(param))
            if len(prop.values) == 1:
                current.append(prop.values[0])
            else:
                arr = []
                for i in prop.values:
                    if "," in i:
                        i = i.split(",")
                    arr.append(i)
                current.append(arr)
            properties.append(current)
        array.append(vcard)

    def result(self, return_obj=False):
        vcards = []
        if isinstance(self._object, vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, vcards)
        else:
            self.write_vcard(self._object, vcards)
        if return_obj:
            return vcards
        else:
            return json.dumps(vcards)


class xCard_Converter:
    HEADER = "urn:ietf:params:xml:ns:vcard-4.0"

    def __init__(self, obj):
        self._object = obj

    @property
    def object(self):
        return self._object

    def _recognize_param_type(self, param, value):
        if param == "LANGUAGE":
            return "language-tag"
        elif param == "PREF":
            return "integer"
        elif param in ["MEDIATYPE", "CALSCALE", "SORT-AS", "ALTID", "VALUE"]:
            return "text"
        elif param == "GEO":
            return "uri"
        elif param in ["PID", "TYPE"]:
            if "," in value:
                return "text-list"
            else:
                return "text"
        elif param == "TZ":
            try:
                validate_uri(value)
                return "uri"
            except:
                return "text"
        else:
            return "unknown"

    def parse_vcard(self, vcardobj, root):
        vcard = et.SubElement(root, "vcard")
        for vcard_attr in vcardobj:
            value_param = "unknown"
            if vcard_attr.group is not None:
                group = et.SubElement(vcard, "group", name=vcard_attr.group)
            else:
                group = vcard
            if vcard_attr.name == "XML":
                element = et.parsestring(vcard_attr.values[0])
                et.SubElement(vcard, element)
            else:
                attr = et.SubElement(vcard, vcard_attr.name.lower())
                if len(vcard_attr.params) > 0:
                    parameters = et.SubElement(attr, "parameters")
                    for param in vcard_attr.params:
                        if param == "VALUE":
                            value_param = vcard_attr.params[param]
                        else:
                            param_node = et.SubElement(parameters, param.lower())
                            param_type = self._recognize_param_type(param, vcard_attr.params[param])
                            if param_type == "text-list":
                                txtlst = attr.params[param].split(",")
                                for txt in txtlst:
                                    pvalue_node = et.SubElement(param_node, "text")
                                    pvalue_node.text = txt
                            else:
                                pvalue_node = et.SubElement(param_node, param_type)
                                param_node = unescape(vcard_attr.params[param])
            if vcard_attr.name == "N":
                value_node = et.SubElement(group, "surname")
                value_node.text = vcard_attr.values[0]
                value_node = et.SubElement(group, "given")
                value_node.text = vcard_attr.values[1]
                value_node = et.SubElement(group, "additional")
                value_node.text = vcard_attr.values[2]
                value_node = et.SubElement(group, "prefix")
                value_node.text = vcard_attr.values[3]
                value_node = et.SubElement(group, "suffix")
                value_node.text = vcard_attr.values[4]
            else:
                value = et.SubElement(group, value_param)
                if len(vcard_attr) > 1:
                    value.text = unescape(";".join(vcard_attr.values))
                elif len(vcard_attr) == 1:
                    value.text = unescape(vcard_attr.values[0])
        return vcard

    def result(self):
        root = et.Element("vcards", xmlns=self.HEADER)
        if hasattr(self.object, "__iter__"):
            for vcardobj in self.object:
                if vcardobj.version != "4.0":
                    warnings.warn("vCard version below 4.0 may not conform to the standard xCard")
                self.parse_vcard(vcardobj, root)
        else:
            if self.object.version != "4.0":
                warnings.warn("vCard version below 4.0 may not conform to the standard xCard")
            self.parse_vcard(self.object, root)
        header = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        rough_string = et.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return header + reparsed.toprettyxml(indent='t')
