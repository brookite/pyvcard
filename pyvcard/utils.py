import base64
import quopri
import re
import warnings

from .exceptions import vCardFormatError

quopri_warning = True
line_warning = True


def escape(string, characters=[";", ",", "\n", "\r", ":"]):
    """
    Escapes listed characters with a character \\

    :param      string:            The string
    :type       string:            str
    :param      characters:        The characters
    :type       characters:        Array
    """
    if not isinstance(string, str):
        return string
    for char in characters:
        if char in ["\t", "\r", "\n"]:
            if char == "\n":
                string = string.replace(char, "\\n")
            elif char == "\t":
                string = string.replace(char, "\\t")
            elif char == "\r":
                string = string.replace(char, "\\r")
        else:
            string = string.replace(char, "\\" + char)
    return string


def unescape(string, only_double=False):
    """
    Unescapes all escaped characters

    :param      string:       The string
    :type       string:       str
    :param      only_double:  If need unescape only double '\\' characters
    :type       only_double:  boolean
    """
    if string is None or isinstance(string, bytes):
        return string
    if only_double:
        r = re.sub(r'\\\\n', r'\\n', string)
        r = re.sub(r'\\\\r', r'\\r', r)
    else:
        r = re.sub(r'\\r', r'\r', string)
        r = re.sub(r'\\n', r'\n', r)
        r = re.sub(r'\\t', r'\t', r)
        r = re.sub(r'\\(.)', r'\1', r)
    return r


def quoted_to_str(string, encoding="utf-8", property=None):
    """
    Decodes Quoted-Printable text to string with encoding

    :param      string:    The target string
    :type       string:    str
    :param      encoding:  The encoding, default is UTF-8
    :type       encoding:  str
    """
    try:
        return quopri.decodestring(unescape(string)).decode(encoding)
    except Exception as e:
        if quopri_warning:
            warnings.warn("Quoted-Printable string wasn't decoded: %s" % str(e))
        if property is not None:
            property._encoding_flag = False
        return string


def str_to_quoted(string, encoding="utf-8"):
    """
    Encoded string to Quoted-Printable text with encoding

    :param      string:    The target string
    :type       string:    str
    :param      encoding:  The encoding, default is UTF-8
    :type       encoding:  str
    """
    try:
        string = quopri.encodestring(string.encode("utf-8")).decode("ascii")
        return string.replace("\r", "=0D").replace("\n", "=0A").replace("==", "=")
    except Exception as e:
        if quopri_warning:
            warnings.warn("String wasn't encoded to Quoted-Printable: %s" % str(e))
        return string


def strinteger(string):
    """
    Clears a string from non-numeric characters
    :param      string:  The string
    :type       string:  str

    Returns a int or a float (if '.' was in string)
    """
    n = ""
    if isinstance(string, int) or string == "":
        return string
    for i in string:
        if i.isdigit() or i == ".":
            n += i
    if string[0] == "-":
        n = "-" + n
    try:
        return int(n) if "." not in n else float(n)
    except Exception:
        return 0


def base64_encode(value):
    """
    Encodes bytes to base64 encoding

    :param      value:  The value
    :type       value:  bytes

    Retutns base64 encoded string
    """
    return base64.b64encode(value).decode("utf-8")


def base64_decode(value, property=None):
    """
    Decodes base64 to bytes

    :param      value:  The value
    :type       value:  bytes

    Retutns base64 decoded bytes
    """
    try:
        return base64.b64decode(value)
    except Exception as e:
        warnings.warn("Bytes wasn't decoded from Base64: %s" % str(e))
        if property is not None:
            property._encoding_flag = False
        return bytes(value)


def _unfold_lines(strings):
    """
    Utility method. Don't recommend for use in outer code
    Unfolds the lines in list
    """
    lines = []
    for string in strings:
        string.replace("\n", "")
        if string == "":
            continue
        if len(string) > 75 and line_warning:
            warnings.warn("Long line found in current VCard (length > 75)")
        if string.startswith(" ") or string.startswith("\t"):
            if len(lines) == 0:
                raise vCardFormatError("Illegal whitespace at string 1")
            lines[-1] += string[1:].lstrip()
        elif string.startswith("="):
            if len(lines) == 0:
                raise vCardFormatError("Illegal whitespace at string 1")
            lines[-1] += string[1:]
        elif string.startswith(";"):
            if len(lines) == 0:
                raise vCardFormatError("Illegal whitespace at string 1")
            lines[-1] += string
        elif len(lines) > 0:
            if lines[-1].endswith("=0D=0A="):
                lines[-1] += string
            else:
                lines.append(string)
        else:
            lines.append(string)
    return lines


def split_noescape(str, sep):
    """
    Splits with no escape.
    Similar to str.split but does not consider escaped characters

    :param      str:  The string
    :type       str:  str
    :param      sep:  The separator
    :type       sep:  str

    :returns:   splitted string
    :rtype:     list
    """
    return re.split(r'(?<!\\)' + sep, str)


def _fold_line(string, expect_quopri=False):
    """
    Utility method. Don't recommend for use in outer code
    Folds the line, may expect quoted-printable
    """
    if len(string) > 75:
        cuts = len(string) // 75
        strings = []
        begin = 0
        length = 75
        add_char = ''
        for i in range(cuts):
            if i == 1:
                length = 74
            end = begin + length
            tmp = string[begin:end]
            if i > 0:
                tmp = add_char + tmp
            if expect_quopri:
                while tmp[-1] != "=":
                    end -= 1
                    tmp = add_char + string[begin:end]
                add_char = '='
            else:
                add_char = ' '
            strings.append(tmp)
            begin = end
        if len(string[begin:]) > 0:
            tmp = add_char + string[begin:]
            strings.append(tmp)
        return "\n".join(strings)
    else:
        return string
