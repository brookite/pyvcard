GROUP = r"(\d|\w|-)+"
NAME = r"([\d\w-]+)"
CR = r"\r"
LF = r"\n"
CRLF = r"{}{}".format(CR, LF)
VCARD_BORDERS = r"^({}\.)?(BEGIN|END)\:(VCARD)".format(GROUP)
DIGIT = r"0-9"
DQUOTE = r"\""
HTAB = r"\t"
SP = r" "
VCHAR=r"\x21-\x7E"
WSP = r"{}{}".format(SP, HTAB)
QSAFE_CHAR = r"[{}!\x23-x7E\w]".format(WSP)
SAFE_CHAR = r"[{}!\x23-\x39\x3C-\x7E\w]".format(WSP)
VALUE_CHAR = r"[{}{}\w]".format(WSP, VCHAR)
PARAM_VALUE="({}+|\"{}+\")".format(SAFE_CHAR, QSAFE_CHAR)
PARAM_NAME = NAME
VALUE = r"({}*)".format(VALUE_CHAR)
PARAM = r"{}\={}*\,*{}*".format(PARAM_NAME, PARAM_VALUE, PARAM_VALUE)
PARAM_21 = r"{}\=?({}*\,{})*".format(PARAM_NAME, PARAM_VALUE, PARAM_VALUE)
PARAM_GROUP = r"((\;{})*)".format(PARAM)
PARAM_GROUP_21 = r"((\;{})*)".format(PARAM_21)
CONTENTLINE = r"^({}\.)?{}{}\:{}".format(GROUP, NAME, PARAM_GROUP, VALUE)
CONTENTLINE_21 = r"^({}\.)?{}{}\:{}".format(GROUP, NAME, PARAM_GROUP_21, VALUE)
