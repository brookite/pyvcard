import re

from pyvcard.datatypes import define_type
from pyvcard.enums import _STATE, VERSION, SOURCES
from pyvcard.exceptions import vCardFormatError, vCardValidationError
from pyvcard.indexer import vCardIndexer
from pyvcard.regex import VCARD_BORDERS, CONTENTLINE, PARAM, PARAM_21, CONTENTLINE_21
from pyvcard.utils import split_noescape, unescape, quoted_to_str, base64_decode, _unfold_lines, strinteger, \
    base64_encode, str_to_quoted, escape, _fold_line
from pyvcard.validator import validate_property

import pyvcard.sources.jcard
import pyvcard.sources.xcard
import pyvcard.sources.csv_source
import pyvcard.sources.hcard

validate_vcards = True


class vCard_entry:
    """
    This class describes a vCard property
    """

    def __init__(self, name, values, params={}, group=None, version="4.0", encoded=True):
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
        self._values = tuple(self._values)
        self._version = version

    def __bool__(self):
        return True

    def __eq__(self, other):
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

    def repr_vcard(self, encode=True):
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


def _parse_line(string, version):
    """
    Utility method. Don't recommend for use in outer code
    Parses a unfolded line and returns a array for parser
    """
    m1 = re.match(VCARD_BORDERS, string)
    if m1:
        return _STATE.BEGIN if m1.group(3) == "BEGIN" else _STATE.END
    if version == "4.0":
        m2 = re.match(CONTENTLINE, string)
    else:
        m2 = re.match(CONTENTLINE_21, string)
    if m2:
        name = m2.group(3).upper()
        if name in ["BEGIN", "END"]:
            return None
        if version == "4.0":
            if m2.group(4):
                params = re.findall(PARAM, m2.group(4))
            else:
                params = []
        else:
            if m2.group(4):
                params = re.findall(PARAM_21, m2.group(4))
            else:
                params = []
        params_dict = {}
        for param in params:
            param = tuple(filter(lambda x: x != "", param))
            if len(param) == 1:
                params_dict[param[0].upper()] = None
            else:
                if param[0] in params_dict:
                    params_dict[param[0].upper()] += "," + param[1].lower()
                else:
                    params_dict[param[0].upper()] = param[1].lower().replace('"', '')
        if version == "4.0":
            values = split_noescape(m2.group(9), ";")
        else:
            values = split_noescape(m2.group(11), ";")
        for i in range(len(values)):
            values[i] = unescape(values[i])
        group = m2.group(1) if m2.group(1) != "" else None
        return name, values, params_dict, group
    else:
        if string.strip() != "":
            raise vCardFormatError(f"An parsing error occurred with string '{string}'")
    return None


def parse_property(string):
    """
    Parses a property

    :param      string:  The string
    :type       string:  str
    """
    c = _parse_line(string)
    if c is None:
        return None
    else:
        return vCard_entry(*c)


def _parse_lines(strings, indexer=None):
    """
    Utility method. Don't recommend for use
    Parses lines in list, indexer is supported
    """
    version = "4.0"
    vcard = vCard()
    args = []
    card_opened = False
    is_version = False
    buf = []
    i = 1
    for string in strings:
        parsed = _parse_line(string.rstrip(), version)
        if parsed == _STATE.BEGIN:
            vcard = vCard()
            if card_opened:
                raise vCardFormatError(f"vCard didn't closed at line {i}")
            card_opened = True
            buf = []
        elif parsed == _STATE.END:
            vcard._attrs = buf
            if not card_opened:
                raise vCardFormatError(f"Double closing or missing begin at line {i}")
            if not is_version:
                raise vCardFormatError("Missing VERSION property")
            card_opened = False
            is_version = False
            args.append(vcard)
        elif parsed:
            if parsed[0] == "VERSION":
                is_version = True
                version = "".join(parsed[1])
                vcard._set_version(version)
            entry = vCard_entry(*parsed, version=version)
            if indexer is not None:
                indexer.setindex(vcard)
                indexer.index(entry, vcard)
            buf.append(entry)
        i += 1
    if card_opened:
        raise vCardFormatError(f"vCard didn't closed at line {i}")
    return args


def decode_property(property):
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


class vCard_Parser:
    """
    Parses a vCard files (VCF) or any vCard string
    """

    def __init__(self, source, indexer=None):
        self.indexer = indexer
        if isinstance(source, str):
            if source.strip() == "":
                raise vCardValidationError("Empty file")
            source = source.splitlines(False)
            source = _unfold_lines(source)
            self.__args = _parse_lines(source, self.indexer)
        else:
            if hasattr(source, "fileno"):
                if not source.closed:
                    fsource = source.read().split("\n")
                    source.close()
                    fsource = _unfold_lines(fsource)
                    self.__args = _parse_lines(fsource, self.indexer)
                else:
                    raise IOError("File is closed")
            else:
                raise IOError(f"Source is not file, type is {type(source)}")

    def vcards(self):
        """
        :returns:   result of parsing
        :rtype:     vCardSet
        """
        return vCardSet(self.__args, indexer=self.indexer)


class vCard:
    """
    This class describes a vCard object representation.
    """

    def __init__(self, args=[], version=None):
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
        If one of value is not defined - they equals None
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

    def _set_version(self, version):
        self._version = version

    def __repr__(self):
        if self._version is not None:
            return f"<VCard {self._version} object at {hex(id(self))}>"
        else:
            return f"<VCard object at {hex(id(self))}>"

    def __bytes__(self):
        return self.repr_vcard().encode("utf-8")

    def repr_vcard(self, encode=True):
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

    def __getitem__(self, key):
        """
        Gets property in vCard

        :param      key:  The key, if number - returns by a index, if name - returns by a first occurence of name
        :type       key:  int or str

        :returns:   vCard entry object (array or single element)
        """
        if isinstance(key, int):
            return self._attrs[key]
        else:
            return self.get(key, False)

    def get(self, key: str, prefer_array=False):
        """
        Gets property in vCard

        :param      key:  The key, if number - returns by a index, if name - returns by a first occurence of name
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

    def __contains__(self, key):
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

    def find_by_group(self, group, case=False, fullmatch=True, indexsearch=True):
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

    def find_by_name(self, fn, case=False, fullmatch=True, indexsearch=True):
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

    def find_by_phone(self, number, fullmatch=True, parsestr=True, indexsearch=True):
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

    def find_by_phone_endswith(self, number, parsestr=True, indexsearch=True):
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

    def find_by_phone_startswith(self, number, parsestr=True, indexsearch=True):
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

    def find_by_property(self, paramname, value, fullmatch=True, indexsearch=True):
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

    def find_by_value(self, value, fullmatch=True, indexsearch=True):
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
                for i in lst:
                    result.append(i)
            return result


class vCardSet(set):
    """
    This class describes a set with vCard objects
    """

    def __init__(self, iter=[], indexer=None):
        super().__init__(iter)
        for object in iter:
            if not is_vcard(object):
                raise TypeError("vCardSet requires only vCard objects")
        self._indexer = indexer

    def add(self, vcard):
        """
        Adds the specified vCard.

        :param      vcard:  The vCard
        :type       vcard:  vCard
        """
        if is_vcard(vcard):
            super().add(vcard)

    def setindex(self, indexer):
        """
        Sets indexer for this object

        :param      indexer:  The indexer
        :type       indexer:  instance of vCardIndexer
        """
        if isinstance(indexer, vCardIndexer):
            self._indexer = indexer
        else:
            raise TypeError(f"Required vCardIndexer instance, not {type(indexer)}")

    def repr_vcard(self, encode=True):
        """
        Returns a string representation of vCard

        :param      encode:  encode property (like bytes, or quoted-printable)
        :type       encode:  boolean
        """
        s = ""
        for vcard in self:
            s += vcard.repr_vcard(encode)
            s += "\n"
        return s

    def difference_search(self, type, value, diff_func, k=85, use_param=None, indexsearch=True):
        """
        Searches for specific parameters using a third-party function that returns an integer value similarity coefficient
        (example: fuzzywuzzy module methods)

        :param      type:       The type (name, phone, param)
        :type       type:       str
        :param      value:      The value that need find
        :type       value:      str
        :param      diff_func:  The difference function, returns integer value coefficient
        :type       diff_func:  function or any callable object
        :param      k:          the minimum value of the difference function at which it will be
                                considered that the value is found
        :type       k:          int
        :param      use_param:  if not None and type is "param" finds only by property name
        :type       use_param:  str or None
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.difference_search(type, value, diff_func, k=k)

        if type == "name" or type == "names":
            attr = "name"
        elif type == "phone" or type == "phones":
            attr = "phone"
        elif type == "param" or type == "params":
            attr = "param"

        def type_convert(x):
            if isinstance(x, bytes):
                return base64_encode(x)
            else:
                return str(x)

        def filter_function(x):
            if attr == "name":
                x = x.contact_name()
                return diff_func(x, value) >= k
            elif attr == "phone":
                x = x.contact_number()
                for i in x:
                    return diff_func(str(i), value) >= k
                return False
            elif attr == "param":
                lst = []
                for param in x:
                    if (use_param is not None and param.name == use_param) or use_param is None:
                        ivalue = ";".join(list(map(type_convert, param.values)))
                        lst.append(diff_func(ivalue, value))
                m = max(lst)
                if m > 0:
                    return m >= k
                else:
                    return False
        array = tuple(set(filter(filter_function, self)))
        return array

    def find_by_group(self, group, case=False, fullmatch=True, indexsearch=True):
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
        if indexsearch and self._indexer:
            return self._indexer.find_by_group(group, case=case, fullmatch=fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_group(group, case, fullmatch, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_name(self, fn, case=False, fullmatch=True, indexsearch=True):
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
        if indexsearch and self._indexer:
            return self._indexer.find_by_name(fn, case, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_name(fn, case, fullmatch, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone(self, number, fullmatch=False, parsestr=True, indexsearch=True):
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
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone(number, fullmatch, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone(number, fullmatch, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone_endswith(self, number, parsestr=True, indexsearch=True):
        """
        Finds a by phone number ending.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_endswith(number, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone_endswith(number, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone_startswith(self, number, parsestr=True, indexsearch=True):
        """
        Finds a by starts of a phone.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_startswith(number, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone_startswith(number, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_property(self, paramname, value, fullmatch=True, indexsearch=True):
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
        if indexsearch and self._indexer:
            return self._indexer.find_by_property(paramname, value, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_property(paramname, value, fullmatch)
                if val:
                    for e in val:
                        result.add(e)
            return tuple(result)

    def find_by_value(self, value, fullmatch=True, indexsearch=True):
        """
        Finds a by property value.

        :param      value:        The property value
        :type       value:        str
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_value(value, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_value(value, fullmatch)
                if val:
                    for e in val:
                        result.add(e)
            return tuple(result)


def is_vcard(object):
    """
    Determines whether the specified object is vCard object.

    :param      object:  The object
    :type       object:  any type
    """
    return isinstance(object, vCard)


def is_vcard_property(object):
    """
    Determines whether the specified object is vCard property object.

    :param      object:  The object
    :type       object:  any type
    """
    return isinstance(object, vCard_entry)


class vCard_Converter:
    """
    This class describes a vCard converter to various sources.
    """

    def __init__(self, source):
        """
        Constructs a new instance.

        :param      source:  The source
        :type       source:  _VCard or vCardSet
        """
        if isinstance(source, vCard) or isinstance(source, vCardSet):
            self.source = source
            self._value = source.repr_vcard()
        else:
            raise TypeError(f"Required vCard or vCardSet type, not {type(source)}")

    def file(self, filename, encoding="utf-8"):
        """
        Creates a file using filename and encoding

        :param      filename:  The filename
        :type       filename:  str
        :param      encoding:  The encoding
        :type       encoding:  string
        """
        with open(filename, "w", encoding=encoding) as f:
            f.write(self._value)

    def string(self):
        """
        Returns a vCard string representation
        """
        return self._value

    def bytes(self):
        """
        Returns a vCard string representation in bytes
        """
        return bytes(self._value)

    def html(self):
        """
        Return a vCard converter object to HTML (hCard)
        """
        return pyvcard.sources.hcard.hCard_Converter(self.source)

    def csv(self):
        """
        Return a vCard converter object to CSV
        """
        return pyvcard.sources.csv_source.csv_Converter(self.source)

    def json(self):
        """
        Return a vCard converter object to JSON (jCard)
        """
        return pyvcard.sources.jcard.jCard_Converter(self.source)

    def xml(self):
        """
        Return a vCard converter object to XML (xCard)
        """
        return pyvcard.sources.xcard.xCard_Converter(self.source)


class _vCard_Builder:
    """
    Front-end to create vCard objects step by step.
    """

    def __init__(self, version="4.0", indexer=None):
        self.indexer = indexer
        self._properties = []
        self._version = version
        self.set_version(version)

    def add_property(self, name, value, params={}, group=None, encoding_raw=False):
        """
        Adds a property. Low-level function

        :param      name:          The name
        :type       name:          str
        :param      value:         The value
        :type       value:         list or str
        :param      params:        The parameters
        :type       params:        dict
        :param      group:         The group
        :type       group:         str or None
        :param      encoding_raw:  If property is encoded
        :type       encoding_raw:  boolean
        """
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, bytes):
            value = [value]
        elif hasattr(value, "__iter__") and not isinstance(value, str):

            def func(x):
                if not isinstance(x, bytes):
                    return str(x)
                else:
                    return x

            value = list(map(func, value))
        else:
            value = [str(value)]
        entry = vCard_entry(name.upper(), value, params, group, version=self._version, encoded=encoding_raw)
        self._properties.append(entry)

    def set_phone(self, number):
        """
        Sets the phone.

        :param      number:  The number
        :type       number:  str or int
        """
        tel = vCard_entry("TEL", [str(number)])
        self._properties.append(tel)

    def set_name(self, name):
        """
        Sets the full name and structured name.

        :param      name:  The full name
        :type       name:  str
        """
        for i in self._properties:
            if i.name == "N" or i.name == "FN":
                raise KeyError("Key 'N' and 'FN' already exists")
        if isinstance(name, str):
            fname = name
            name = name.split(" ")
            while len(name) < 5:
                name.append("")
        elif hasattr(name, "__iter__") and not isinstance(name, str):
            name = list(map(str, name))
            fname = "".join(name)
        else:
            raise ValueError(f"Invalid argument: {name}")
        entry1 = vCard_entry("FN", [fname])
        self._properties.append(entry1)
        entry2 = vCard_entry("N", name)
        self._properties.append(entry2)

    def set_version(self, version):
        """
        Sets the version.

        :param      version:  The version
        :type       version:  str or VERSIOn enum
        """
        if version in ["2.1", "3.0", "4.0"]:
            self._version = version
            self.add_property("VERSION", version)

    def build(self):
        """
        Returns vCard object
        """
        if len(self._properties) != 0:
            vcard = vCard(args=self._properties, version=self._version)
            if self.indexer is not None:
                for entry in vcard:
                    self.indexer.index(entry, vcard)
            return vcard
        else:
            raise ValueError("Empty vCard")

    def clear(self):
        """
        Clears all properties.
        """
        self._properties = []


def parse(source, indexer=None):
    """
    Returns a vCard parser object

    :param      source:   The source
    :type       source:   file descriptor or str
    :param      indexer:  The indexer that will be set
    :type       indexer:  instance of vCardIndexer or None
    """
    return vCard_Parser(source, indexer=indexer)


def convert(source):
    """
    Returns a vCard converter object

    :param      source:  The source
    :type       source: vCard or vCardSet
    """
    return vCard_Converter(source)


def parse_from(source, type, indexer=None):
    """
    Parses vCard from various sources (see SOURCES enum)

    :param      source:   The source
    :type       source:   str
    :param      type:     The type
    :type       type:     str or SOURCES enum
    :param      indexer:  The indexer
    :type       indexer:  instance of vCardIndexer or None
    """
    if type == SOURCES.XML or type == "xml":
        return pyvcard.sources.xcard.xCard_Parser(source, indexer)
    elif type == SOURCES.JSON or type == "json":
        return pyvcard.sources.jcard.jCard_Parser(source, indexer)
    elif type == SOURCES.CSV or type == "csv":
        return pyvcard.sources.csv_source.csv_Parser(source, indexer)
    elif type == SOURCES.HTML or type == "html":
        return pyvcard.sources.hcard.hCard_Parser(source, indexer)
    elif type == SOURCES.VCF:
        return parse(source, indexer)
    else:
        raise TypeError(f"Type {type} isn't found")


def parse_name_property(prop):
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


def builder(indexer=None, version="4.0"):
    """
    Returns a vCard object builder

    :param      indexer:  The indexer
    :type       indexer: instance of vCardIndexer or None
    :param      version:  The version
    :type       version:  string
    """
    return _vCard_Builder(indexer=indexer, version=version)