import re

from pyvcard.regex import VCARD_BORDERS, CONTENTLINE, PARAM, PARAM_21, CONTENTLINE_21
from pyvcard.utils import split_noescape, unescape, _unfold_lines, remove_junk_symbols
from pyvcard.enums import _STATE
from pyvcard.exceptions import vCardFormatError, vCardValidationError

import pyvcard.vobject.containers
import pyvcard.vobject.structures

def _parse_line(string, version):
    """
    Utility method. Don't recommend for use in outer code
    Parses a unfolded line and returns a array for parser
    """
    string = remove_junk_symbols(string)
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
        return pyvcard.vobject.structures.vCard_entry(*c)


def _parse_lines(strings, indexer=None):
    """
    Utility method. Don't recommend for use
    Parses lines in list, indexer is supported
    """
    version = "4.0"
    vcard = pyvcard.vobject.structures.vCard()
    args = []
    card_opened = False
    is_version = False
    buf = []
    i = 1
    for string in strings:
        parsed = _parse_line(string, version)
        if parsed == _STATE.BEGIN:
            vcard = pyvcard.vobject.structures.vCard()
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
            entry = pyvcard.vobject.structures.vCard_entry(*parsed, version=version)
            if indexer is not None:
                indexer.setindex(vcard)
                indexer.index(entry, vcard)
            buf.append(entry)
        i += 1
    if card_opened:
        raise vCardFormatError(f"vCard didn't closed at line {i}")
    return args


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
        return pyvcard.vobject.containers.vCardSet(self.__args, indexer=self.indexer)

    def vcard_list(self):
        """
        :returns:   ordered result of parsing
        :rtype:     vCardList
        """
        return pyvcard.vobject.containers.vCardList(self.__args, indexer=self.indexer)



