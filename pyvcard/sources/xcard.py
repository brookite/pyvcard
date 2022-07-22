import re
import pyvcard.vobject

from pyvcard.converters import AbstractConverter, determine_type, recognize_param_type, encoding_convert
import xml.etree.ElementTree as et
from xml.dom import minidom

from pyvcard.parsers import AbstractParser, get_string
from pyvcard.utils import unescape


class xCard_Converter(AbstractConverter):
    """
    This class describes a vCard object to XML converter
    xCard (RFC 6351)
    """
    HEADER = "urn:ietf:params:xml:ns:vcard-4.0"

    def __init__(self, obj):
        self._object = obj

    def parse_vcard(self, vcardobj, root):
        """
        Writes a vCard. Utility method
        """
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
                                    pvalue_node.text = unescape(vcard_attr.params[param])
            self.value_struct(attr, vcard_attr, value_param)
        return vcard

    def value_struct(self, attr, vcard_attr, value_param):
        """
        Utility method. Don't recommend for use in outer code!
        Converts value to node
        """
        if vcard_attr.name == "N":
            value_node = et.SubElement(attr, "surname")
            value_node.text = encoding_convert(unescape(vcard_attr.values[0]), vcard_attr.params)
            value_node = et.SubElement(attr, "given")
            value_node.text = encoding_convert(unescape(vcard_attr.values[1]), vcard_attr.params)
            value_node = et.SubElement(attr, "additional")
            value_node.text = encoding_convert(unescape(vcard_attr.values[2]), vcard_attr.params)
            value_node = et.SubElement(attr, "prefix")
            value_node.text = encoding_convert(unescape(vcard_attr.values[3]), vcard_attr.params)
            value_node = et.SubElement(attr, "suffix")
            value_node.text = encoding_convert(unescape(vcard_attr.values[4]), vcard_attr.params)
        elif vcard_attr.name == "ADR":
            value_node = et.SubElement(attr, "pobox")
            value_node.text = encoding_convert(unescape(vcard_attr.values[0]), vcard_attr.params)
            value_node = et.SubElement(attr, "ext")
            value_node.text = encoding_convert(unescape(vcard_attr.values[1]), vcard_attr.params)
            value_node = et.SubElement(attr, "street")
            value_node.text = encoding_convert(unescape(vcard_attr.values[2]), vcard_attr.params)
            value_node = et.SubElement(attr, "locality")
            value_node.text = encoding_convert(unescape(vcard_attr.values[3]), vcard_attr.params)
            value_node = et.SubElement(attr, "region")
            value_node.text = encoding_convert(unescape(vcard_attr.values[4]), vcard_attr.params)
            value_node = et.SubElement(attr, "code")
            value_node.text = encoding_convert(unescape(vcard_attr.values[5]), vcard_attr.params)
            value_node = et.SubElement(attr, "country")
            value_node.text = encoding_convert(unescape(vcard_attr.values[6]), vcard_attr.params)
        else:
            if len(vcard_attr.values) > 1:
                for val in vcard_attr.values:
                    v = et.SubElement(attr, value_param)
                    if val != "":
                        v.text = encoding_convert(unescape(val), vcard_attr.params)
            elif len(vcard_attr.values) == 1:
                value = et.SubElement(attr, value_param)
                value.text = encoding_convert(unescape(vcard_attr.values[0]), vcard_attr.params)

    def result(self):
        """
        Returns string result of converting
        """
        root = et.Element("vcards", xmlns=self.HEADER)
        if hasattr(self.object, "__iter__"):
            for vcardobj in self.object:
                self.parse_vcard(vcardobj, root)
        else:
            self.parse_vcard(self.object, root)
        rough_string = et.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml()


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
                factory = pyvcard.vobject.builder(self.indexer)
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
        return pyvcard.vobject.vCardSet(vcards)