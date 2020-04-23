import xml.etree.ElementTree as et
import pyvcard
from pyvcard_validator import validate_uri
from xml.dom import minidom
from csv import DictWriter
import warnings
import io
import json
import base64


def encoding_convert(source, params):
    if "ENCODING" in params:
        enc = params["ENCODING"].upper()
    else:
        enc = None
    if type(source) in [tuple, list]:
        for i in range(len(source)):
            source[i] = encoding_convert(source[i], params)
    else:
        if enc == "QUOTED-PRINTABLE":
            return pyvcard.str_to_quoted(source)
        elif enc in ["BASE64", "B"]:
            return base64.b64encode(source).decode("utf-8")
        else:
            return source


class csv_Converter:
    def __init__(self, obj):
        if pyvcard.is_vcard(obj) or isinstance(obj, pyvcard.vCardSet):
            self._object = obj
        else:
            raise ValueError("Required vCardSet or vCard type")

    @property
    def object(self):
        return self._object

    def write_vcard(self, vcard, writer, permanent=False):
        data = vcard.contact_data()
        row = {
            "Formatted name": data["name"],
            "Name": data["struct_name"],
            "Tel. Number": data["number"],
        }
        if not permanent:
            row["vCard"] = vcard.repr_vcard()
        writer.writerow(row)

    def result(self):
        strio = io.StringIO()
        names = ["Formatted name", "Name", "Tel. Number", "vCard"]
        writer = DictWriter(strio, fieldnames=names)
        writer.writeheader()
        if isinstance(self._object, pyvcard.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, writer)
        else:
            self.write_vcard(self._object, writer)
        val = strio.getvalue()
        strio.close()
        return val

    def permanent_result(self):
        strio = io.StringIO()
        names = ["Formatted name", "Name", "Tel. Number"]
        writer = DictWriter(strio, fieldnames=names)
        writer.writeheader()
        if isinstance(self._object, pyvcard.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, writer, True)
        else:
            self.write_vcard(self._object, writer, True)
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
                "BIRTHPLACE", "DEATHPLACE", "VERSION"
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
        jcard = ["vcard", []]
        properties = jcard[1]
        for prop in vcard:
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
            current.append(self.determine_type(prop))
            if len(prop.values) == 1:
                val = encoding_convert(prop.values[0], prop.params)
                current.append(val)
            else:
                arr = []
                for i in prop.values:
                    if type(prop.values[0]) == bytes:
                        i = encoding_convert(prop.values[0], prop.params)
                    else:
                        if "," in i:
                            i = i.split(",")
                    arr.append(encoding_convert(i, prop.params))
                current.append(arr)
            properties.append(current)
        array.append(jcard)

    def result(self, return_obj=False):
        vcards = []
        if isinstance(self._object, pyvcard.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, vcards)
        else:
            self.write_vcard(self._object, vcards)
        if return_obj:
            return vcards
        else:
            return json.dumps(vcards, ensure_ascii=False)


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
            except Exception:
                return "text"
        else:
            return "unknown"

    def parse_vcard(self, vcardobj, root):
        vcard = et.SubElement(root, "vcard")
        group_name = None
        for vcard_attr in vcardobj:
            value_param = "unknown"
            """
            TASK: Fix conversion bugs:
            1. Empty parameters
            2. Value ';' and other values bug
            3. Strange encoding bug
            """
            if vcard_attr.group is not None:
                if group_name != vcard_attr.group:
                    group = et.SubElement(vcard, "group", name=vcard_attr.group)
                    group_name = vcard_attr.group
                else:
                    group = group
            else:
                group = vcard
            if vcard_attr.name == "XML":
                element = et.fromstring(vcard_attr.values[0])
                et.SubElement(vcard, element)
            else:
                attr = et.SubElement(group, vcard_attr.name.lower())
                if len(vcard_attr.params) > 0:
                    parameters = et.SubElement(attr, "parameters")
                    for param in vcard_attr.params:
                        if param == "VALUE":
                            value_param = vcard_attr.params[param]
                        else:
                            param_node = et.SubElement(parameters, param.lower())
                            param_type = self._recognize_param_type(param, vcard_attr.params[param])
                            if param_type == "text-list":
                                txtlst = vcard_attr.params[param].split(",")
                                for txt in txtlst:
                                    pvalue_node = et.SubElement(param_node, "text")
                                    pvalue_node.text = txt
                            else:
                                pvalue_node = et.SubElement(param_node, param_type)
                                param_node = pyvcard.unescape(vcard_attr.params[param])
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
                value = et.SubElement(attr, value_param)
                if len(vcard_attr.values) > 1:
                    value.text = encoding_convert(pyvcard.unescape(";".join(vcard_attr.values)), vcard_attr.params)
                elif len(vcard_attr.values) == 1:
                    value.text = encoding_convert(pyvcard.unescape(vcard_attr.values[0]), vcard_attr.params)
        return vcard

    def result(self):
        root = et.Element("vcards", xmlns=self.HEADER)
        if hasattr(self.object, "__iter__"):
            for vcardobj in self.object:
                self.parse_vcard(vcardobj, root)
        else:
            self.parse_vcard(self.object, root)
        rough_string = et.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml()
