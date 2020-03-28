import re 

GROUP = re.compile(r"(\d|\w|-)+")
NAME = re.compile(r"([\d\w-]+)")
CR = re.compile(r"\r")
LF = re.compile(r"\n")
CRLF = re.compile(r"{}{}".format(CR.pattern, LF.pattern))
VCARD_BORDERS = re.compile(r"^({}\.)?(BEGIN|END)\:(VCARD)".format(GROUP.pattern))
DIGIT = re.compile(r"0-9")
DQUOTE = re.compile(r"\"")
HTAB = re.compile(r"\t")
SP = re.compile(r" ")
VCHAR= re.compile(r"\x21-\x7E")
WSP = re.compile(r"{}{}".format(SP.pattern, HTAB.pattern))
QSAFE_CHAR = re.compile(r"[{}!\x23-x7E\w]".format(WSP.pattern))
SAFE_CHAR = re.compile(r"[{}!\x23-\x39\x3C-\x7E\w]".format(WSP.pattern))
VALUE_CHAR = re.compile(r"[{}{}\w]".format(WSP.pattern, VCHAR.pattern))
PARAM_VALUE= re.compile(r"({}+|\"{}+\")".format(SAFE_CHAR.pattern, QSAFE_CHAR.pattern))
PARAM_NAME = NAME
VALUE = re.compile(r"({}*)".format(VALUE_CHAR.pattern))
PARAM = re.compile(r"{}\={}*\,*{}*".format(PARAM_NAME.pattern, PARAM_VALUE.pattern, PARAM_VALUE.pattern))
PARAM_21 = re.compile(r"{}\=?({}*\,?{}?)*".format(PARAM_NAME.pattern, PARAM_VALUE.pattern, PARAM_VALUE.pattern))
PARAM_GROUP = re.compile(r"(\;?({})*)".format(PARAM.pattern))
PARAM_GROUP_21 = re.compile(r"(\;({}))*".format(PARAM_21.pattern))
CONTENTLINE = re.compile(r"^({}\.)?{}{}\:{}$".format(GROUP.pattern, NAME.pattern, PARAM_GROUP.pattern, VALUE.pattern))
CONTENTLINE_21 = re.compile(r"^({}\.)?{}{}\:{}$".format(GROUP.pattern, NAME.pattern, PARAM_GROUP_21.pattern, VALUE.pattern))
ESCAPED = re.escape("\\;,nN")

VALID_FLOAT = re.compile(r"^[+-]?\d+(\.\d+)?$")
VALID_INTEGER = re.compile(r"^([+-]?\d+,?)+$")
LANG_TAG = re.compile(r"([a-z]{1,8})(-[a-z]{1,8})*")
VALID_TZ = re.compile(r"(Z|[+-]\d{2}:?\d{2})")
QOUTED_STRING = re.compile(r"{0}({1}*){0}".format(DQUOTE.pattern, QSAFE_CHAR.pattern))
VALID_DATE = re.compile(r"(\d{4}|-)-?(\d{2}|-)-?(\d{2})?")
ZONE = re.compile(r"(Z|{})".format(VALID_TZ.pattern))
VALID_TIME = re.compile(r"(\d{2}|-)?:?(\d{2}|-)?:?(\d{2}|-)?" + rf"{ZONE.pattern}?")
VAILD_TIMESTAMP = re.compile(r"^{}T{}$".format(VALID_DATE.pattern, VALID_TIME.pattern))
VALID_TEXT = re.compile(r"^(({}|:|\")*|(\\\\({})*))*$".format(SAFE_CHAR.pattern, ESCAPED))
VALID_TEXTLIST = re.compile(r"^(({})+,?)+$".format(VALID_TEXT.pattern[1:-1]))
