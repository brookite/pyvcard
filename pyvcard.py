import enum
import re
import warnings
import quopri
import base64
from pyvcard_regex import *
from pyvcard_exceptions import *
from pyvcard_validator import *
from pyvcard_converters import *
from pyvcard_parsers import *

validate_vcards = True


class VERSION(enum.Enum):
    @staticmethod
    def get(version):
        if version == "2.1":
            return VERSION.V2_1
        elif version == "3.0":
            return VERSION.V3
        elif version == "4.0":
            return VERSION.V4

    V2_1 = "2.1"
    V3 = "3.0"
    V4 = "4.0"


class _STATE(enum.Enum):
    BEGIN = 0
    END = 1


class SOURCES(enum.Enum):
    XML = "xml"
    JSON = "json"
    VCF = "vcf"
    CSV = "csv"


class vCardIndexer:
    def __init__(self, index_params=False):
        self._names = {}
        self._indexparams = index_params
        self._phones = {}
        self._params = {}
        self._vcards = []
        self._groups = {}

    def __bool__(self):
        return True

    @property
    def names(self):
        return self._names

    @property
    def phones(self):
        return self._phones

    @property
    def params(self):
        return self._params

    def setindex(self, vcard):
        if isinstance(vcard, _VCard):
            vcard._indexer = vcard
            self._vcards.append(vcard)

    def index(self, entry, vcard):
        if isinstance(entry, _vCard_entry):
            if entry.group is not None:
                if entry.group not in self._groups:
                    self._groups[entry.group] = []
                self._groups[entry.group].append(vcard)
            if entry.name == "FN":
                if entry.values[0] not in self._names:
                    self._names[entry.values[0]] = []
                self._names[entry.values[0]].append(vcard)
            elif entry.name == "N":
                name = ";".join(entry.values)
                if name not in self._names:
                    self._names[name] = []
                self._names[name].append(vcard)
            elif entry.name == "TEL":
                if entry.values[0] not in self._phones:
                    self._phones[entry.values[0]] = []
                self._phones[entry.values[0]].append(vcard)
                self._phones[strinteger(entry.values[0])] = vcard
            elif self._indexparams:
                if entry.name not in self._params:
                    self._params[entry.name] = {}
                if ";".join(entry.values) not in self._params[entry.name]:
                    self._params[entry.name][";".join(entry.values)] = []
                self._params[entry.name][";".join(entry.values)].append(vcard)

    def __len__(self):
        return len(self._names) + len(self._phones)

    @property
    def vcards(self):
        return tuple(self._vcards)

    def difference_search(self, type, value, diff_func, k=85):
        def filter_function(x):
            x = str(x)
            return diff_func(x, value) >= k

        if type == "name" or type == "names":
            array = set(filter(filter_function, self._names.values()))
        elif type == "phone" or type == "phones":
            array = set(filter(filter_function, self._phones.values()))
        elif type == "param" or type == "params":
            array = []
            for param in self._params:
                for values in self._params[param]:
                    temp = set(filter(filter_function, self._params[param][values]))
                    array += temp
            array = set(array)
        return array

    def get_name(self, fn):
        return tuple(self._names[fn])

    def get_phone(self, phone):
        return tuple(self._phones[phone])

    def get_param(self, param, value):
        return tuple(self._params[param][value])

    def get_group(self, group):
        return tuple(self._groups[group])

    def find_by_group(self, group, fullmatch=True, case=False):
        if group in self._names and fullmatch:
            return tuple(self._names[fn])

        def filter_function(x):
            if not case:
                value = x.lower()
                nonlocal group
                group = group.lower()
            else:
                value = x
            if fullmatch:
                return value == group
            else:
                return group in value

        lst = filter(filter_function, self._groups.values())
        result = set()
        for i in lst:
            for j in i:
                result.add(j)
        return tuple(result)

    def find_by_name(self, fn, case=False, fullmatch=True):
        if fn in self._names and fullmatch:
            return tuple(self._names[fn])

        def filter_function(x):
            if not case:
                value = x.lower()
                nonlocal fn
                fn = fn.lower()
            else:
                value = x
            if fullmatch:
                return value == fn
            else:
                return fn in value

        lst = filter(filter_function, self._names.values())
        result = set()
        for i in lst:
            for j in i:
                result.add(j)
        return tuple(result)

    def find_by_phone(self, number, fullmatch=False, parsestr=True):
        if number in self._phones and fullmatch:
            return tuple(self._phones[number])

        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            if fullmatch:
                return str(value) == str(number)
            else:
                return str(number) in str(value)

        lst = filter(filter_function, self._phones.values())
        result = set()
        for i in lst:
            for j in i:
                result.add(j)
        return tuple(result)

    def find_by_phone_endswith(self, number, parsestr=True):
        if number in self._phones:
            return tuple(self._phones[number])

        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).endswith(str(number))

        lst = filter(filter_function, self._phones.values())
        result = set()
        for i in lst:
            for j in i:
                result.add(j)
        return tuple(result)

    def find_by_phone_startswith(self, number, parsestr=True):
        if number in self._phones:
            return tuple(self._phones[number])

        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).startswith(str(number))

        lst = filter(filter_function, self._phones.values())
        result = set()
        for i in lst:
            for j in i:
                result.add(j)
        return tuple(result)

    def find_by_param(self, paramname, value, fullmatch=True):
        if paramname in self._params:
            if value in self._params[paramname] and fullmatch:
                return (self._params[paramname][value])
        if hasattr(value, "__iter__"):
            value = ";".join(value)
        if value in self._params[paramname]:
            return self._params[paramname][value]

        def filter_function(x):
            if fullmatch:
                return x == value
            else:
                return value in x

        s = []
        lst = list(filter(filter_function, self._params[paramname].values()))
        for i in lst:
            for j in i:
                s.append(i)
        return tuple(set(s))

    def find_by_paramvalue(self, value, fullmatch=True):
        result = []
        for i in self._params:
            lst = self.find_by_param(i, value, fullmatch)
            for j in lst:
                result.append(j)
        return tuple(set(result))


def quoted_to_str(string, encoding="utf-8"):
    return quopri.decodestring(string).decode(encoding)


def str_to_quoted(string, encoding="utf-8"):
    string = string.encode(encoding)
    qp = ""
    for i in string:
        i = hex(i)[2:]
        qp += "=" + str(i)
    return qp.upper()


def strinteger(string):
    n = ""
    if type(string) == int:
        return string
    for i in string:
        if i.isdigit():
            n += i
    return int(n)


def escape(string):
    return re.escape(string)


def unescape(string):
    if string is None or isinstance(string, bytes):
        return string
    return re.sub(r'\\(.)', r'\1', string)


def decode_property(property):
    if "ENCODING" in property._params:
        for i in range(len(property._values)):
            if property._params["ENCODING"] == "QUOTED-PRINTABLE":
                if property._values[i] != '':
                    property._values[i] = quoted_to_str(property._values[i])
            elif property._params["ENCODING"] in ["B", "BASE64"]:
                if property._values[i] != '':
                    property._values[i] = base64.b64decode(property._values[i].encode("utf-8"))


class _vCard_entry:
    def __init__(self, name, values, params={}, group=None, version="4.0"):
        self._name = name
        self._params = params
        self._values = list(values)
        self._group = group
        if self._group is not None:
            if self._group.endswith("."):
                self._group = group[:-1]
        if validate_vcards:
            validate_property(self, version)
        decode_property(self)
        self._values = tuple(self._values)
        self._version = version

    def __bool__(self):
        return True

    def repr_vcard(self, encode=True):
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
        if "ENCODING" in self._params:
            if self._params["ENCODING"].upper() == "QUOTED-PRINTABLE" and encode:
                expect_quopri = True
                for i in range(len(values)):
                    if values[i] != "":
                        charset = "utf-8"
                        if "CHARSET" in self._params:
                            charset = self._params["CHARSET"]
                        values[i] = str_to_quoted(values[i], charset)
            elif self._params["ENCODING"] in ["B", "BASE64"]:
                for i in range(len(values)):
                    values[i] = base64.b64encode(values[i]).decode("utf-8")
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
    def values(self):
        return tuple(self._values)

    @property
    def value(self):
        return self._values[0]

    def __repr__(self):
        return f"<{self._name} property>"


def _unfold_lines(strings):
    lines = []
    for string in strings:
        string.replace("\n", "")
        if len(string) > 75:
            warnings.warn("Long line found in current VCard (length > 75)")
        if string.startswith(" ") or string.startswith("\t"):
            if len(lines) == 0:
                raise VCardFormatError("Illegal whitespace at string 1")
            lines[-1] += string[1:]
        elif string.startswith("="):
            lines[-1] += string[1:]
        elif string.startswith(";"):
            lines[-1] += string
        else:
            lines.append(string)
    return lines


def _fold_line(string, expect_quopri=False):
    if len(string) > 75:
        cuts = len(string) // 75
        strings = []
        begin = 0
        length = 75
        for i in range(cuts):
            if i == 1:
                length = 74
            end = begin + length
            tmp = string[begin:end]
            if expect_quopri:
                while tmp[-1] != "=":
                    end -= 1
                    tmp = string[begin:end]
            strings.append(tmp)
            begin = end
        if len(string[begin:]) > 0:
            strings.append(string[begin:])
        return "\n ".join(strings)
    else:
        return string


def _parse_line(string, version):
    m1 = re.match(VCARD_BORDERS, string)
    if m1:
        return _STATE.BEGIN if m1.group(3) == "BEGIN" else _STATE.END
    if version != "2.1":
        m2 = re.match(CONTENTLINE, string)
    else:
        m2 = re.match(CONTENTLINE_21, string)
    if m2:
        name = m2.group(3)
        if name in ["BEGIN", "END"]:
            return None
        if version != "2.1":
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
                    params_dict[param[0].upper()] += "," + param[1].upper()
                else:
                    params_dict[param[0].upper()] = param[1].upper()
        if version != "2.1":
            values = m2.group(9).split(";")
        else:
            values = m2.group(11).split(";")
        group = m2.group(1) if m2.group(1) != "" else None
        return name, values, params_dict, group
    else:
        if string.strip() != "":
            raise VCardFormatError(f"An parsing error occurred with string '{string}'")
    return None


def parse_property(string):
    c = _parse_line(string)
    if c is None:
        return None
    else:
        return _vCard_entry(*c)


def _parse_lines(strings, indexer=None):
    version = "4.0"
    vcard = _vCard()
    args = []
    card_opened = False
    is_version = False
    buf = []
    for string in strings:
        parsed = _parse_line(string, version)
        if parsed == _STATE.BEGIN:
            vcard = _vCard()
            if card_opened:
                raise VCardFormatError(f"vCard didn't closed at line {i}")
            card_opened = True
            buf = []
        elif parsed == _STATE.END:
            vcard._attrs = buf
            if not card_opened:
                raise VCardFormatError(f"Double closing or missing begin at line {i}")
            if not is_version:
                raise VCardFormatError("Missing VERSION property")
            card_opened = False
            is_version = False
            args.append(vcard)
        elif parsed:
            if parsed[0] == "VERSION":
                is_version = True
                version = "".join(parsed[1])
                vcard._set_version(version)
            entry = _vCard_entry(*parsed, version=version)
            if indexer is not None:
                indexer.index(entry, vcard)
            buf.append(entry)
    if card_opened:
        raise VCardFormatError(f"vCard didn't closed at line {i}")
    return args


class _vCard_Parser:
    def __init__(self, source, indexer=None):
        self.indexer = indexer
        if type(source) == str:
            if source.strip() == "":
                raise VCardValidationError("Empty file")
            source = source.splitlines(False)
            source = _unfold_lines(source)
            self.__args = _parse_lines(source, self.indexer)
        else:
            if hasattr(source, "fileno"):
                if not source.closed:
                    source = source.read().split("\n")
                    source = _unfold_lines(source)
                    self.__args = _parse_lines(source, self.indexer)
                else:
                    raise IOError("File is closed")
            else:
                raise IOError("Source is not file")

    def vcards(self):
        return vCardSet(self.__args, self.indexer)


class _vCard:
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

    def contact_data(self):
        obj = dict.fromkeys(["name", "number", "struct_name"], None)
        for i in self:
            if i.name == "FN":
                obj["name"] = i.values[0]
            elif i.name == "TEL":
                obj["number"] = strinteger(i.values[0])
            elif i.name == "N":
                obj["struct_name"] = ";".join(i.values)
        return obj

    def contact_name(self):
        name = None
        for i in self:
            if i.name == "FN":
                name = i.values[0]
        return name

    def contact_structname(self):
        name = None
        for i in self:
            if i.name == "TEL":
                obj["struct_name"] = ";".join(i.values)
        return name

    def contact_number(self):
        name = None
        for i in self:
            if i.name == "TEL":
                name = strinteger(i.values[0])
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
        string = "BEGIN:VCARD"
        for i in self:
            string += "\n"
            string += i.repr_vcard(encode)
        string += "\nEND:VCARD"
        return string

    def __len__(self):
        return len(self._attrs)

    def __getitem__(self, key):
        if type(key) == int:
            return self._attrs[key]
        else:
            arr = []
            for i in self._attrs:
                if i.name == key:
                    arr.append(i)
            if len(arr) == 1:
                return arr[0]
            else:
                return arr

    def __contains__(self, key):
        for i in self._attrs:
            if i.name == key:
                return True
        return False

    def __iter__(self):
        return iter(self._attrs)

    @property
    def properties(self):
        return tuple(self._attrs)

    def find_by_group(self, group, case=False, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_group(group, case=case, fullmatch=fullmatch)
        else:
            for i in self._attrs:
                if not case:
                    group = group.lower()
                if i.name == "FN":
                    if not case:
                        value = i.values[0].lower()
                    else:
                        value = i.values[0]
                    if value == group and fullmatch:
                        return [self]
                    elif value in group and not fullmatch:
                        return [self]
            return []

    def find_by_name(self, fn, case=False, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_name(fn, case, fullmatch)
        else:
            for i in self._attrs:
                if not case:
                    fn = fn.lower()
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

    def find_by_phone(self, number, fullmatch=False, parsestr=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_phone(number, fullmatch, parsestr)
        else:
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value) == str(number) and fullmatch:
                        return [self]
                    elif str(number) in str(value) and not fullmatch:
                        return [self]
            return []

    def find_by_phone_endswith(self, number, parsestr=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_phone_endswith(number, parsestr)
        else:
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value).endswith(str(number)):
                        return [self]
            return []

    def find_by_phone_startswith(self, number, parsestr=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_phone_startswith(number, parsestr)
        else:
            for i in self._attrs:
                if i.name == "TEL":
                    if parsestr:
                        value = strinteger(i.values[0])
                    else:
                        value = i.values[0]
                    if str(value).startswith(str(number)):
                        return(self)
            return []

    def find_by_param(self, paramname, value, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_param(paramname, value, fullmatch)
        else:
            if hasattr(value, "__iter__"):
                value = ";".join(value)
            for i in self._attrs:
                if i.name == paramname:
                    if ";".join(i.values) == value and fullmatch:
                        return [self]
                    elif value in ";".join(i.values) and not fullmatch:
                        return [self]
            return []

    def find_by_paramvalue(self, value, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_paramvalue(value, fullmatch)
        else:
            if hasattr(value, "__iter__"):
                value = ";".join(value)
            for i in self._attrs:
                if ";".join(i.values) == value and fullmatch:
                    return [self]
                elif value in ";".join(i.values) and not fullmatch:
                    return [self]
            return []


class vCardSet(set):
    def __init__(self, iter=[], indexer=None):
        super().__init__(iter)
        for object in iter:
            if not is_vcard(object):
                raise TypeError("VCardSet requires VCard objects")
        self._indexer = indexer

    def add(self, vcard):
        if isinstance(vcard, _VCard):
            super().add(vcard)

    def repr_vcard(self, encode=True):
        s = ""
        for vcard in self:
            s += vcard.repr_vcard(encode)
            s += "\n"
        return s

    def find_by_group(self, group, case=False, fullmatch=True, indexsearch=True):
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

    def find_by_param(self, paramname, value, fullmatch=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_param(paramname, value, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_param(paramname, value, fullmatch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_paramvalue(self, value, fullmatch=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_paramvalue(value, fullmatch)
        else:
            result = set()
            for i in self:
                for paramname in i:
                    val = i.find_by_paramvalue(paramname, value, fullmatch)
                    if val:
                        for value in val:
                            result.add(value)
            return tuple(result)


class _vCard_Converter:
    def __init__(self, source):
        if isinstance(source, _vCard) or isinstance(source, vCardSet):
            self.source = source
            self._value = source.repr_vcard()
        else:
            raise TypeError("Required VCard type")

    def file(self, filename, encoding="utf-8"):
        with open(filename, "w", encoding=encoding) as f:
            f.write(self._value)

    def string(self):
        return self._value

    def bytes(self):
        return bytes(self._value)

    def csv(self):
        return csv_Converter(self.source)

    def json(self):
        return jCard_Converter(self.source)

    def xml(self):
        return xCard_Converter(self.source)


class _vCard_Builder:
    def __init__(self, version="4.0", indexer=None):
        self.indexer = indexer
        self._properties = []
        self._version = version

    def add_property(self, name, value, params={}, group=None):
        if isinstance(value, str):
            value = value.split(";")
        elif hasattr(value, "__iter__") and not isinstance(value, str):
            value = list(map(str, value))
        elif isinstance(value, bytes):
            value = [value]
        else:
            value = [str(value)]
        entry = _vCard_entry(name, value, params, group, version=self._version)
        self._properties.append(entry)

    def set_phone(self, number):
        for i in self._properties:
            if i.name == "TEL":
                raise KeyError("Key already exists")
        tel = _vCard_entry("TEL", [str(number)])
        self._properties.append(tel)

    def set_name(self, name):
        for i in self._properties:
            if i.name == "N" or i.name == "FN":
                raise KeyError("Key already exists")
        if isinstance(name, str):
            fname = name
            name = name.split(" ")
        elif hasattr(name, "__iter__"):
            name = list(map(str, name))
            fname = "".join(name)
        else:
            raise ValueError(f"Invalid argument: {name}")
        entry1 = _vCard_entry("FN", [fname])
        self._properties.append(entry1)
        entry2 = _vCard_entry("N", name)
        self._properties.append(entry2)

    def set_version(self, version):
        if version in ["2.1", "3.0", "4.0"]:
            self._version = version
            self.add_property("VERSION", version)

    def build(self):
        if len(self._properties) != 0:
            vcard = _vCard(args=self._properties, version=self._version)
            if self.indexer is not None:
                for entry in vcard:
                    self.indexer.index(entry, vcard)
            return vcard
        else:
            raise ValueError("Empty vCard")

    def clear(self):
        self._properties = []


def parse(source, indexer=None):
    return _vCard_Parser(source, indexer)


def convert(source):
    return _vCard_Converter(source)


def parse_from(source, type, indexer=None):
    if type == SOURCES.XML or type == "xml":
        return xCard_Parser(source, indexer)
    elif type == SOURCES.JSON or type == "json":
        return jCard_Parser(source, indexer)
    elif type == SOURCES.CSV or type == "csv":
        return csv_Parser(source, indexer)
    elif type == SOURCES.VCF:
        return parse(source, indexer)
    else:
        raise TypeError("Type isn't found")


def builder(indexer=None, version="4.0"):
    return _vCard_Builder(indexer=indexer, version=version)


def openfile(file, mode="r", encoding=None, buffering=-1,
             errors=None, newline=None, opener=None, indexer=None):
    f = open(file, mode, encoding=encoding, buffering=buffering,
             errors=errors, newline=newline, opener=opener)
    return parse(f, indexer)


def is_vcard(object):
    return isinstance(object, _vCard)


def parse_name_property(prop):
    result = None
    if prop.name == "N":
        result = {}
        result["surname"] = prop.values[0]
        result["given_name"] = prop.values[1]
        result["additional_name"] = prop.values[2]
        result["prefix"] = prop.values[3]
        result["suffix"] = prop.values[4]
    return result


# Remove semicolon struct conversion xml
# Parser fixes
# Documentation
