import xml.etree.ElementTree as et
import pyvcard
from pyvcard_validator import validate_uri
from xml.dom import minidom
from csv import DictWriter
import io
import json
import base64


def encoding_convert(source, params):
    if "ENCODING" in params:
        enc = params["ENCODING"].upper()
    else:
        enc = None
    if isinstance(source, list) or isinstance(source, tuple):
        for i in range(len(source)):
            source[i] = encoding_convert(source[i], params)
    else:
        if enc == "QUOTED-PRINTABLE":
            return pyvcard.str_to_quoted(source)
        elif enc in ["BASE64", "B"]:
            return base64.b64encode(source).decode("utf-8")
        else:
            return source


def determine_type(prop):
    if "VALUE" in prop.params:
        return prop.params["VALUE"]
    else:
        if prop.name in [
            "N", "FN", "XML", "KIND", "GENDER",
            "TZ", "TITLE", "ROLE", "TEL", "EMAIL",
            "ORG", "CATEGORIES", "NOTES", "PRODID",
            "EXPERTISE", "HOBBY", "INTEREST", "ORG-DIRECTORY",
            "BIRTHPLACE", "DEATHPLACE", "VERSION", "ADR"
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


def recognize_param_type(param, value):
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
    elif param in ["CHARSET", "ENCODING"]:
        return "text"
    else:
        return "unknown"


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
            "Tel. Number": str(data["number"]),
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

    def write_vcard(self, vcard, array):
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
        vcards = []
        if isinstance(self._object, pyvcard.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, vcards)
        else:
            self.write_vcard(self._object, vcards)
        if return_obj:
            return vcards
        else:
            return json.dumps(vcards, ensure_ascii=False, *args, **kwargs)


class xCard_Converter:
    HEADER = "urn:ietf:params:xml:ns:vcard-4.0"

    def __init__(self, obj):
        self._object = obj

    @property
    def object(self):
        return self._object

    def parse_vcard(self, vcardobj, root):
        vcard = et.SubElement(root, "vcard")
        group_name = None
        for vcard_attr in vcardobj:
            if vcard_attr.name == "VERSION" and vcard_attr.value == "4.0":
                continue
            value_param = "unknown"
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
                            value_param = determine_type(vcard_attr)
                            param_node = et.SubElement(parameters, param.lower())
                            param_type = recognize_param_type(param, vcard_attr.params[param])
                            if param_type == "text-list":
                                txtlst = vcard_attr.params[param].split(",")
                                for txt in txtlst:
                                    pvalue_node = et.SubElement(param_node, "text")
                                    pvalue_node.text = txt
                            else:
                                pvalue_node = et.SubElement(param_node, param_type)
                                if vcard_attr.params[param] is not None:
                                    pvalue_node.text = pyvcard.unescape(vcard_attr.params[param])
            self.value_struct(attr, vcard_attr, value_param)
        return vcard

    def value_struct(self, attr, vcard_attr, value_param):
        if vcard_attr.name == "N":
            value_node = et.SubElement(attr, "surname")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[0]), vcard_attr.params)
            value_node = et.SubElement(attr, "given")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[1]), vcard_attr.params)
            value_node = et.SubElement(attr, "additional")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[2]), vcard_attr.params)
            value_node = et.SubElement(attr, "prefix")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[3]), vcard_attr.params)
            value_node = et.SubElement(attr, "suffix")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[4]), vcard_attr.params)
        elif vcard_attr.name == "ADR":
            value_node = et.SubElement(attr, "pobox")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[0]), vcard_attr.params)
            value_node = et.SubElement(attr, "ext")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[1]), vcard_attr.params)
            value_node = et.SubElement(attr, "street")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[2]), vcard_attr.params)
            value_node = et.SubElement(attr, "locality")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[3]), vcard_attr.params)
            value_node = et.SubElement(attr, "region")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[4]), vcard_attr.params)
            value_node = et.SubElement(attr, "code")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[5]), vcard_attr.params)
            value_node = et.SubElement(attr, "country")
            value_node.text = encoding_convert(pyvcard.unescape(vcard_attr.values[6]), vcard_attr.params)
        else:
            if len(vcard_attr.values) > 1:
                for val in vcard_attr.values:
                    v = et.SubElement(attr, value_param)
                    if val != "":
                        v.text = encoding_convert(pyvcard.unescape(val), vcard_attr.params)
            elif len(vcard_attr.values) == 1:
                value = et.SubElement(attr, value_param)
                value.text = encoding_convert(pyvcard.unescape(vcard_attr.values[0]), vcard_attr.params)

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
