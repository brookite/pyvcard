import enum
import re
import warnings
from pyvcard_regex import *
from pyvcard_exceptions import *


class VERSION(enum.Enum):
    V2_1 = "2.1"
    V3 = "3.0"
    V4 = "4.0"

class _STATE(enum.Enum):
    BEGIN = 0
    END = 1

class _vcard_entry:
    def __init__(self, name, values, params={}):
        self._name = name
        self._params = params
        self._values = values

    def repr_vcard(self):
        string = self.name
        c = 0
        for i in self.params:
            if c > 0:
                string += ';'
            if self.params[i]:
                string += f"{i}={self._params[i]}"
            else:
                string += i
            c += 1
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
    def values(self):
        return self._values

    def __repr__(self):
        return f"<{self._name}>"


def _unfold_lines(strings):
    lines = []
    for string in strings:
        if len(string) > 75:
            warnings.warn("Long line found in current VCard (length > 75)")
        if string.startswith(" ") or string.startswith("\t"):
            if len(lines) == 0:
                raise VCardFormatError("Illegal whitespace at string 1")
            lines[-1] += string[1:]
        elif string.startswith("="):
            lines[-1] += string
        else:
            lines.append(string)
    return lines


def _parse_line(string, version):
    m1 = re.match(VCARD_BORDERS, string)
    if m1:
        return _STATE.BEGIN if m1.group(3) == "BEGIN" else _STATE.END
    m2 = re.match(CONTENTLINE, string)
    if m2:
        name = m2.group(3)
        if version == "2.1":
            params = re.findall(PARAM_21, m2.group(4))
            params_dict = {}
            for param in params:
                params_dict[param[0]] = param[1]
        else:
            params = re.findall(PARAM, m2.group(4))
            params_dict = {}
            for param in params:
                if len(param) == 1:
                    params_dict[param[0]] = None
                else:
                    params_dict[param[0]] = param[1]
        values = m2.group(9).split(";")
        return name, values, params_dict
    return None


def _parse_lines(strings):
    version = "4.0"
    args = []
    buf = []
    for string in strings:
        parsed = _parse_line(string, version)
        if parsed == _STATE.BEGIN:
            buf = []
        elif parsed == _STATE.END:
            args.append(buf)
        elif parsed:
            if parsed[0] == "VERSION":
                version = "".join(parsed[1])
            buf.append(_vcard_entry(*parsed))
    return args


class _vcard_Parser:
    def __init__(self, source):
        source = source.splitlines(False)
        source = _unfold_lines(source)
        self.__args = _parse_lines(source)

    def vcard(self):
        arr = []
        for rawvcard in self.__args:
            arr.append(_VCard(rawvcard))
        return arr


class _VCard:
    def __init__(self, args):
        self._attrs = args


pth1 = "D:\\Мои файлы\\Папки по годам\\2019\\contacts.vcf"
f = open(pth1, "r", encoding="utf-8").read()
parser = _vcard_Parser(f)
for i in parser.vcard()[0]._attrs:
    print(i.repr_vcard())