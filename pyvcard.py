import enum
import re
import warnings
import quopri
import base64
import traceback
from pyvcard_regex import *
from pyvcard_exceptions import *
from pyvcard_validator import *

validate_vcards = True

class VERSION(enum.Enum):
    V2_1 = "2.1"
    V3 = "3.0"
    V4 = "4.0"

class _STATE(enum.Enum):
    BEGIN = 0
    END = 1


class VCardIndexer:
    def __init__(self, index_params=False):
        self._names = {}
        self._indexparams = index_params
        self._phones = {}
        self._params = {}
        self._vcards = []

    def __bool__(self):
        return True

    def setindex(self, vcard):
        if isinstance(vcard, _VCard):
            vcard._indexer = vcard
            self._vcards.append(vcard)

    def index(self, entry, vcard):
        if isinstance(entry, _vcard_entry):
            if entry.name == "FN":
                self._names[entry.values[0]] = vcard
            elif entry.name == "TEL":
                self._phones[entry.values[0]] = vcard
                self._phones[strinteger(entry.values[0])] = vcard
            elif self._indexparams:
                if entry.name in self._params:
                    self._params[entry.name] = {}
                self._params[entry.name][";".join(entry.values)] = vcard

    def __len__(self):
        return len(self._names) + len(self._phones)

    @property
    def vcards(self):
        return tuple(self._vcards)

    def get_name(self, fn):
        return self._names[fn]

    def get_phone(self, phone):
        return self._phones[phone]

    def get_param(self, param, value):
        return self._params[param][value]

    def find_by_name(self, fn, case=False, fullmatch=True):
        if fn in self._names:
            return (self._names[fn])
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
        map_function = lambda x: self._names[x]
        return tuple(set(map(map_function, filter(filter_function, self._names))))
    
    def find_by_phone(self, number, fullmatch=False, parsestr=True):
        if number in self._phones:
            return (self._phones[number])
        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            if fullmatch:
                return str(value) == str(number)
            else:
                return str(number) in str(value)
        map_function = lambda x: self._phones[x]
        return tuple(set((map(map_function, filter(filter_function, self._phones)))))

    def find_by_phone_endswith(self, number, parsestr=True):
        if number in self._phones:
            return (self._phones[number])
        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).endswith(str(number))
        map_function = lambda x: self._phones[x]
        return tuple(set(map(map_function, filter(filter_function, self._phones))))

    def find_by_phone_startswith(self, number, parsestr=True):
        if number in self._phones:
            return (self._phones[number])
        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).startswith(str(number))
        map_function = lambda x: self._phones[x]
        return tuple(set(map(map_function, filter(filter_function, self._phones))))

    def find_by_param(self, paramname, value, fullmatch=True):
        if value in self._params[paramname]:
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
        map_function = lambda x: self._params[paramname][x]
        return tuple(set(map(map_function, filter(filter_function, self._params[paramname]))))

    def find_by_paramvalue(self, value, fullmatch=True):
        result = []
        for i in self._params:
            result.append(self.find_by_param(i, value, fullmatch))
        return tuple(set(result))


def quoted_to_str(string, encoding="utf-8"):
    return quopri.decodestring(string).decode(encoding)


def str_to_quoted(string, encoding="utf-8"):
    return quopri.encodestring(string).decode(encoding)


def strinteger(string):
    n = ""
    if type(string) == int:
        return string
    for i in string:
        if i.isdigit():
            n += i
    return int(n)


def unescape(string):
    return string.decode('string_escape')


def decode_property(property):
    if "ENCODING" in property.params:
        for i in range(len(property.values)):
            if property.params["ENCODING"] == "quoted-printable":
                if property.values[i] != '':
                    property.values[i] = quoted_to_str(property.values[i])
            elif property.params["ENCODING"] in ["b", "base64"]:
                if property.values[i] != '':
                    property.values[i] = base64.decode(property.values[i])


class _vcard_entry:
    def __init__(self, name, values, params={}, group=None, version="4.0"):
        self._name = name
        self._params = params
        self._values = list(values)
        self._group = group
        if validate_vcards:
            validate_property(self, version)
        decode_property(self)
        self._values = tuple(self._values)


    def repr_vcard(self):
        string = self.name
        for i in self.params:
            string += ";"
            if self.params[i]:
                string += f"{i}={self._params[i].upper()}"
            else:
                string += i
        values = ";".join(self._values)
        string += f":{values}"
        return string

    @property
    def name(self):
        return self._name
    
    @property
    def params(self):
        return self._params

    @property
    def group(self):
        return self._group

    @property
    def values(self):
        return self._values

    def __repr__(self):
        return f"<{self._name}>"


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
        if version != "2.1":
            if m2.group(5):
                params = re.findall(PARAM, m2.group(5))
            else:
                params = []
        else:
            if m2.group(5):
                params = re.findall(PARAM_21, m2.group(5))
            else:
                params = []
        params_dict = {}
        for param in params:
            param = tuple(filter(lambda x: x != "", param))
            if len(param) == 1:
                params_dict[param[0].upper()] = None
            else:
                if param[0] in params_dict:
                    if type(params_dict[params[0]]) != list:
                        params_dict[params[0].upper()] = [params_dict[params[0].upper()]]
                    params_dict[params[0].upper()].append(params[1].lower())
                else:
                    params_dict[param[0].upper()] = param[1].lower()
        if version != "2.1":
            values = m2.group(9).split(";")
        else:
            values = m2.group(10).split(";")
        group = m2.group(1) if m2.group(1) != "" else None
        return name, values, params_dict, group
    return None


def _parse_lines(strings, indexer=None):
    version = "4.0"
    vcard = _VCard()
    args = []
    buf = []
    for string in strings:
        parsed = _parse_line(string, version)
        if parsed == _STATE.BEGIN:
            vcard = _VCard()
            buf = []
        elif parsed == _STATE.END:
            vcard._attrs = buf
            args.append(vcard)
        elif parsed:
            if parsed[0] == "VERSION":
                version = "".join(parsed[1])
            entry = _vcard_entry(*parsed, version=version)
            if indexer:
                indexer.index(entry, vcard)
            buf.append(entry)
    return args


class _VCard_Parser:
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
                if not source.closed():
                    source = source.readlines()
                    source = _unfold_lines(source)
                    self.__args = _parse_lines(source, self.indexer)
                else:
                    raise IOError("File is closed")
            else:
                raise IOError("Source is not file")

    def vcard(self):
        return VCardSet(self.__args, self.indexer)


class _VCard:
    def __init__(self, args=[]):
        self._attrs = args
        self._indexer = None

    def repr_vcard(self):
        string = "BEGIN:VCARD"
        for i in self:
            string += "\n"
            string += i.repr_vcard()
        string += "\nEND:VCARD"
        return string

    def __len__(self):
        return len(self._attrs)

    def __getitem__(self, key):
        if type(key) == int:
            return self._attrs[key]
        else:
            for i in self._attrs:
                if i.name == key:
                    return i

    def __iter__(self):
        return iter(self._attrs)

    @property
    def properties(self):
        return tuple(self._attrs)

    def find_by_name(self, fn, case=False, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_name(fn, case, fullmatch)
        else:
            for i in self._attrs:
                name = i.name
                if not case:
                    name = i.name.lower()
                    fn = fn.lower()
                if name == "FN":
                    if i.values[0] == fn and fullmatch:
                        return [self]
                    elif i.values[0] in fn and not fullmatch:
                        return [self]

    
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
                    elif ";".join(i.values) in value and not fullmatch:
                        return [self]

    def find_by_paramvalue(self, value, fullmatch=True, indexsearch=False):
        if self._indexer and indexsearch:
            self._indexer.find_by_paramvalue(value, fullmatch)
        else:
            if hasattr(value, "__iter__"):
                value = ";".join(value)
            for i in self._attrs:
                if ";".join(i.values) == value and fullmatch:
                    return [self]
                elif ";".join(i.values) in value and not fullmatch:
                    return [self]

class VCardSet:
    def __init__(self, iter, indexer=None):
        self._container = set(iter)
        self._indexer = indexer

    def __iter__(self):
        return iter(self._container)

    def add(self, vcard):
        if isinstance(vcard, _VCard):
            self._container.add(vcard)

    def remove(self, vcard):
        self._container.remove(vcard)

    def __contains__(self, key):
        return key in self._container

    def find_by_name(self, fn, case=False, fullmatch=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_name(fn, case, fullmatch)
        else:
            result = []
            for i in self:
                val = i.find_by_name(fn, case, fullmatch, indexsearch)
                if val:
                    for value in val:
                        result.append(value)
            return tuple(set(result))
    
    def find_by_phone(self, number, fullmatch=False, parsestr=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone(number, fullmatch, parsestr)
        else:
            result = []
            for i in self:
                val = i.find_by_phone(number, fullmatch, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.append(value)
            return tuple(set(result))

    def find_by_phone_endswith(self, number, parsestr=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_endswith(number, parsestr)
        else:
            result = []
            for i in self:
                val = i.find_by_phone_endswith(number,parsestr, indexsearch)
                if val:
                    for value in val:
                        result.append(value)            
            return tuple(set(result))

    def find_by_phone_startswith(self, number, parsestr=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_startswith(number, parsestr)
        else:
            result = []
            for i in self:
                val = i.find_by_phone_startswith(number, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.append(value)
            return tuple(set(result))

    def find_by_param(self, paramname, value, fullmatch=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_param(paramname, value, fullmatch)
        else:
            result = []
            for i in self:
                val = i.find_by_param(paramname, value, fullmatch)
                if val:
                    for value in val:
                        result.append(value)
            return tuple(set(result))

    def find_by_paramvalue(self, value, fullmatch=True, indexsearch=True):
        if indexsearch and self._indexer:
            return self._indexer.find_by_param(value, fullmatch)
        else:
            result = []
            for i in self:
                for paramname in i:
                    val = i.find_by_param(paramname, value, fullmatch)
                    if val:
                        for value in val:
                            result.append(value)
            return tuple(set(result))


def parse(source, indexer=None):
    return _VCard_Parser(source, indexer)


pth1 = "D:\\Мои файлы\\Рабочий стол\\vcards\\contacts.vcf"
f = open(pth1, "r", encoding="utf-8").read()
try:
    indexer = VCardIndexer()
    parser = parse(f, indexer)
    s = parser.vcard()
    print(s._indexer)
    for vcard in s.find_by_phone(0000, indexsearch=False):
        print(vcard.repr_vcard())
    print("DONE")
    # fix replacing contains
except VCardValidationError as e:
    traceback.print_exc()
    print(e.property.values)