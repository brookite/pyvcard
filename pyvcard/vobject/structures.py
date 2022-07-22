from typing import Dict, Union, List, Collection

from pyvcard.enums import VERSION
from pyvcard.validator import validate_property
from pyvcard.datatypes import define_type
from pyvcard.utils import quoted_to_str, base64_decode, strinteger, \
    base64_encode, str_to_quoted, escape, _fold_line

validate_vcards = True


def decode_property(property: "vCard_entry"):
    """
    Utility method. Don't recommend for use in outer code
    Decodes a property.

    :param      property:  The property
    :type       property:  vCard property
    """
    charset = "utf-8"
    if "CHARSET" in property._params:
        charset = property._params["CHARSET"].lower()
    if "ENCODING" in property._params:
        for i in range(len(property._values)):
            if property._params["ENCODING"].upper() == "QUOTED-PRINTABLE":
                if property._values[i] != '':
                    property._values[i] = quoted_to_str(property._values[i], charset, property)
            elif property._params["ENCODING"].upper() in ["B", "BASE64"]:
                if property._values[i] != '':
                    property._values[i] = base64_decode(property._values[i].encode(charset), property)


class vCard_entry:
    """
    This class describes a vCard property
    """

    def __init__(self, name: str, values: List[str],
                 params: Dict[str, str] = {},
                 group=None,
                 version: str = "4.0",
                 encoded: bool = True):
        """
        Constructs a new instance of property.

        :param      name:     The name
        :type       name:     str
        :param      values:   The values
        :type       values:   list
        :param      params:   The parameters
        :type       params:   dict
        :param      group:    The group
        :type       group:    str or None
        :param      version:  The version, default is 4.0
        :type       version:  string
        :param      encoded:  If decoding wasn't complete
        :type       encoded:  boolean
        """
        self._name = name
        self._params = params
        self._encoding_flag = True
        self._escaping_flag = True
        if isinstance(values, str):
            self._values = [values]
        else:
            self._values = list(values)
        self._group = group
        if self._group is not None:
            if self._group.endswith("."):
                self._group = group[:-1]
        if validate_vcards:
            validate_property(self, version)
        if encoded is True:
            decode_property(self)
        self._version = version

    def __bool__(self):
        return True

    def __eq__(self, other: "vCard_entry"):
        if id(self) == id(other):
            return True
        if type(self) != type(other):
            return False
        if self._name != other._name:
            return False
        if self._params != other._params:
            return False
        if self._group != other._group:
            return False
        if self._values != other._values:
            return False
        if self._version != other._version:
            return False
        return True

    def __hash__(self):
        hashcode = 0
        hashcode += hash(self._name)
        for key in self._params:
            hashcode += hash(self._params[key])
        for i in self._values:
            hashcode += hash(i)
        hashcode += hash(self._group)
        hashcode += hash(self._version)
        return hashcode

    def repr_vcard(self, encode: bool = True):
        """
        Returns a string representation of entry

        :param      encode:  encode property (like bytes, or quoted-printable)
        :type       encode:  boolean
        """
        if self.group is not None:
            string = f"{self.group}."
        else:
            string = ""
        string += self.name
        for i in self._params:
            string += ";"
            if self._params[i]:
                string += f"{i}={self._params[i].upper()}"
            else:
                string += i
        values = list(self._values)
        expect_quopri = False
        if not self._encoding_flag:
            encode = False
        if "ENCODING" in self._params:
            if self._params["ENCODING"].upper() == "QUOTED-PRINTABLE" and encode:
                expect_quopri = True
                for i in range(len(values)):
                    if values[i] != "":
                        charset = "utf-8"
                        if "CHARSET" in self._params:
                            charset = self._params["CHARSET"]
                        values[i] = str_to_quoted(values[i], charset)
            elif self._params["ENCODING"].upper() in ["B", "BASE64"]:
                for i in range(len(values)):
                    if self._encoding_flag:
                        values[i] = base64_encode(values[i])
                    else:
                        values[i] = str(values[i])
        else:
            for i in range(len(values)):
                if self._escaping_flag:
                    values[i] = escape(values[i])
        values = ";".join(values)
        string += f":{values}"
        return _fold_line(string, expect_quopri)

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return dict(self._params)

    @property
    def group(self):
        return self._group

    @property
    def typedvalue(self):
        return define_type(self)

    @property
    def values(self):
        return tuple(self._values)

    @property
    def value(self):
        return self._values[0]

    def __repr__(self):
        reprval = ";".join(self.values)
        return f"<{self._name} property: {reprval}>"


class vCard:
    """
    This class describes a vCard object representation.
    """

    def __init__(self, args: Collection[vCard_entry] = [],
                 version: str = None):
        self._attrs = args
        self._indexer = None
        self._version = version

    def __bool__(self):
        return True

    @property
    def indexer(self):
        return self._indexer

    @property
    def version(self):
        return VERSION.get(self._version)

    def __eq__(self, other):
        if id(self) == id(other):
            return True
        if type(self) != type(other):
            return False
        if self.contact_data() != other.contact_data():
            return False
        if len(self) != len(other):
            return False
        for i in range(len(self)):
            if self[i] != other[i]:
                return False
        if self.indexer != other.indexer:
            return False
        if self.version != other.version:
            return False
        return True

    def __hash__(self):
        hashcode = 0
        if self._indexer is None:
            hashcode += 0
        else:
            hashcode += hash(self._indexer)
        if self._version is None:
            hashcode += 0
        else:
            hashcode += hash(self._indexer)
        for i in self:
            hashcode += hash(i)
        contact = self.contact_data()
        for i in contact:
            if isinstance(contact[i], list) or isinstance(contact[i], tuple):
                for k in contact[i]:
                    hashcode += hash(k)
            elif isinstance(contact[i], dict):
                for k in contact[i]:
                    hashcode += hash(contact[i][k])
            else:
                hashcode += hash(contact[i])
        return hashcode

    def contact_data(self):
        """
        Returns main data of vCard:
        1. Full Name
        2. Struct Name - dict
        3. Phone Number - list
        If one of value is not defined - they equal None
        Returns a dict with keys "name", "number", "struct_name"
        """
        obj = dict.fromkeys(["name", "number", "struct_name"], None)
        obj["number"] = []
        for i in self:
            if i.name == "FN":
                obj["name"] = i.values[0]
            elif i.name == "TEL":
                obj["number"].append(strinteger(i.values[0]))
            elif i.name == "N":
                obj["struct_name"] = parse_name_property(i.values)
        return obj

    def contact_name(self):
        """
        Returns full name in vCard or None
        """
        name = None
        for i in self:
            if i.name == "FN":
                name = i.values[0]
        return name

    def contact_structname(self):
        """
        Returns dict with structured name or None
        """
        name = None
        for i in self:
            if i.name == "N":
                name = parse_name_property(i.values)
        return name

    def contact_number(self):
        """
        Returns a list with phone numbers in vCard
        """
        name = []
        for i in self:
            if i.name == "TEL":
                name.append(strinteger(i.values[0]))
        return name

    def _set_version(self, version: str):
        self._version = version

    def __repr__(self):
        if self._version is not None:
            return f"<VCard {self._version} object at {hex(id(self))}>"
        else:
            return f"<VCard object at {hex(id(self))}>"

    def __bytes__(self):
        return self.repr_vcard().encode("utf-8")

    def repr_vcard(self, encode: bool = True):
        """
        Returns a string representation of vCard

        :param      encode:  encode property (like bytes, or quoted-printable)
        :type       encode:  boolean
        """
        string = "BEGIN:VCARD"
        for i in self:
            string += "\n"
            string += i.repr_vcard(encode)
        string += "\nEND:VCARD"
        return string

    def __len__(self):
        return len(self._attrs)

    def __getitem__(self, key: Union[str, int]):
        """
        Gets property in vCard

        :param      key:  The key, if number - returns by an index, if name - returns by a first occurrence of name
        :type       key:  int or str

        :returns:   vCard entry object (array or single element)
        """
        if isinstance(key, int):
            return self._attrs[key]
        else:
            return self.get(key, False)

    def get(self, key: str, prefer_array: bool = False):
        """
        Gets property in vCard

        :param      key:  The key, if number - returns by an index, if name - returns by a first occurrence of name
        :type       key:  str

        :param      prefer_array: Return results only as list or tuple
        :type       prefer_array: boolean

        :returns:   vCard entry object (array or single element (if not prefer_array))
        """
        arr = []
        for i in self._attrs:
            if i.name == key:
                arr.append(i)
        if len(arr) == 1 and not prefer_array:
            return arr[0]
        else:
            return tuple(arr)

    def __contains__(self, key: str):
        if not is_vcard_property(key):
            for i in self._attrs:
                if i.name == key:
                    return True
            return False
        else:
            return key in self._attrs

    def __iter__(self):
        return iter(self._attrs)

    @property
    def properties(self):
        return tuple(self._attrs)

    def find_by_group(self, group: str,
                      case: bool = False,
                      fullmatch: bool = True,
                      indexsearch: bool = True):
        """
        Finds a by group.

        :param      group:        The group
        :type       group:        str
        :param      case:         case sensitivity
        :type       case:         boolean
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_group(group, case=case, fullmatch=fullmatch)
        else:
            if not case and group is not None:
                group = group.lower()
            for i in self._attrs:
                if not case and i.group is not None:
                    value = i.group.lower()
                else:
                    value = i.group
                if value == group and fullmatch:
                    return [self]
                elif value is not None:
                    if group in value and not fullmatch:
                        return [self]
                else:
                    if value == group:
                        return [self]
            return []

    def find_by_name(self, fn: str,
                     case: bool = False,
                     fullmatch: bool = True,
                     indexsearch: bool = True):
        """
        Finds a by name.

        :param      fn:           The full name or structured name joined by ";"
        :type       fn:           str
        :param      case:         case sensitivity
        :type       case:         boolean
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_name(fn, case, fullmatch)
        else:
            if not case:
                fn = fn.lower()
            for i in self._attrs:
                if i.name == "FN":
                    if not case:
                        value = i.values[0].lower()
                    else:
                        value = i.values[0]
                    if value == fn and fullmatch:
                        return [self]
                    elif fn in value and not fullmatch:
                        return [self]
            return []

    def find_by_phone(self, number: Union[str, int],
                      fullmatch: bool = False,
                      parsestr: bool = True, indexsearch: bool = True):
        """
        Finds a by phone number.

        :param      number:       The number
        :type       number:       str or int
        :param      fullmatch:    The fullmatch
        :type       fullmatch:    boolean
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_phone(number, fullmatch, parsestr)
        else:
            r = []
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value) == str(number) and fullmatch:
                        r.append(self)
                    elif str(number) in str(value) and not fullmatch:
                        r.append(self)
            return r

    def find_by_phone_endswith(self, number: Union[str, int],
                               parsestr: bool = True,
                               indexsearch: bool = True):
        """
        Finds a by phone number ending.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_phone_endswith(number, parsestr)
        else:
            r = []
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value).endswith(str(number)):
                        r.append(self)
            return r

    def repr(self):
        """
        Returns a string representation of vCard
        """
        return self.repr_vcard()

    def find_by_phone_startswith(self, number: Union[str, int],
                                 parsestr: bool = True,
                                 indexsearch: bool = True):
        """
        Finds a by starts of a phone.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_phone_startswith(number, parsestr)
        else:
            r = []
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value).startswith(str(number)):
                        r.append(self)
            return r

    def find_by_property(self, paramname: str, value: Union[str, List[str]],
                         fullmatch: bool = True,
                         indexsearch: bool = True):
        """
        Finds a by property name and value.

        :param      paramname:    The property name
        :type       paramname:    str
        :param      value:        The value
        :type       value:        str or list
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_property(paramname, value, fullmatch)
        else:
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = ";".join(value)
            for i in self._attrs:
                if i.name == paramname:

                    def type_convert(x):
                        if isinstance(x, bytes):
                            return base64_encode(x)
                        else:
                            return str(x)
                    ivalues = list(map(type_convert, i.values))
                    if ";".join(ivalues) == value and fullmatch:
                        return [self]
                    elif value in ";".join(ivalues) and not fullmatch:
                        return [self]
            return []

    def find_by_value(self, value: str,
                      fullmatch: bool = True,
                      indexsearch: bool = True):
        """
        Finds a by property value.

        :param      value:        The property value
        :type       value:        str
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if self._indexer and indexsearch:
            return self._indexer.find_by_value(value, fullmatch)
        else:
            result = []
            for i in self._attrs:
                lst = self.find_by_property(i.name, value, fullmatch, indexsearch)
                for j in lst:
                    result.append(j)
            return result


def is_vcard(object) -> bool:
    """
    Determines whether the specified object is vCard object.

    :param      object:  The object
    :type       object:  any type
    """
    return isinstance(object, vCard)


def is_vcard_property(object) -> bool:
    """
    Determines whether the specified object is vCard property object.

    :param      object:  The object
    :type       object:  any type
    """
    return isinstance(object, vCard_entry)


def parse_name_property(prop) -> Dict:
    """
    Parses name property list to dict with keys: surname, given_name, additional_name,
    prefix, suffix

    :param      prop:  vCard property or array
    :type       prop:  _vCard_entry or array
    """
    result = None
    if is_vcard_property(prop):
        if prop.name == "N":
            result = {}
            result["surname"] = prop.values[0]
            result["given_name"] = prop.values[1]
            result["additional_name"] = prop.values[2]
            result["prefix"] = prop.values[3]
            result["suffix"] = prop.values[4]
    else:
        result = {}
        result["surname"] = prop[0]
        result["given_name"] = prop[1]
        result["additional_name"] = prop[2]
        result["prefix"] = prop[3]
        result["suffix"] = prop[4]
    return result