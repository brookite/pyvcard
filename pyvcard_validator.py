from pyvcard_exceptions import *
from pyvcard_regex import *
from urllib.parse import urlparse
import re
import warnings

TYPE_TEL = [
    'home',
    'msg',
    'work',
    'pref',
    'voice',
    'fax',
    'cell',
    'video',
    'pager',
    'bbs',
    'modem',
    'car',
    'isdn',
    'pcs',
    'textphone'
]
LABEL_TEL = [
    'dom',
    'intl',
    'postal',
    'parcel',
    'home',
    'work',
    'pref'
]
TYPE_EMAIL = [
    'internet',
    'x400',
    'pref',
    'dom',
    'intl',
    'postal',
    'parcel',
    'home',
    'work'
]
VALUE_TYPE = [
    "text", "uri", "date",
    "time", "date-and-or-time", "datetime",
    "timestamp", "boolean", "integer", "float",
    "utc-offset", "language-tag"
]


def validate_bool_wrapper(validator_func):
    try:
        validator_func()
        return True
    except Exception:
        return False


def values_count_required(property, mincount, maxcount):
    if len(property.values) < mincount:
        raise VCardValidationError(f"Values count must be >= {mincount}", property)
    elif len(property.values) > maxcount:
        raise VCardValidationError(f"Values count must be <= {maxcount}", property)


def params_count_required(property, mincount, maxcount):
    if len(property.params) < mincount:
        raise VCardValidationError(f"Values count must be >= {mincount}", property)
    elif len(property.params) > maxcount:
        raise VCardValidationError(f"Values count must be <= {maxcount}", property)


def validate_value_parameter(property, values, param_required=False, text_allowed=True):
    if "VALUE" in property.params:
        val = property.params["VALUE"].lower()
        if property.params["VALUE"].lower() in values or \
                (property.params["VALUE"] == "text" & text_allowed):
            raise VCardValidationError(f"VALUE param {val} not found", property)
    else:
        if param_required:
            raise VCardValidationError("VALUE param not found", property)


def validate_text(value, property=None):
    if not re.match(VALID_TEXT, value):
        raise VCardValidationError("Text isn't match", property)


def validate_group(group, property=None):
    if not re.match(GROUP, group):
        raise VCardValidationError("Group isn't match", property)


def validate_text_list(value, property=None):
    if not re.match(VALID_TEXTLIST, value):
        raise VCardValidationError("Text list isn't match", property)


def validate_datetime(value, subtype, property=None):
    if subtype == "datetime":
        pattern = VAILD_TIMESTAMP
    elif subtype == "time":
        pattern = VALID_TIME
    elif subtype == "date":
        pattern = VALID_DATE
    elif subtype is None:
        if not any(re.match(VAILD_TIMESTAMP, value), re.match(VALID_DATE, value),
                   re.match(VALID_TIME, value)
                   ):
            raise VCardValidationError("Date or time isn't match", property)
    else:
        raise ValueError("Incorrect subtype", property)
    if not re.match(pattern, value):
        raise VCardValidationError(f"{subtype} isn't match", property)


def validate_float(value, property=None):
    if re.match(VALID_FLOAT, value) is not None:
        raise VCardValidationError("Float isn't match", property)


def validate_integer(value, property=None):
    if re.match(VALID_INTEGER, value) is not None:
        raise VCardValidationError("Integer isn't match", property)


def validate_utc_offset(value, property=None):
    if re.match(VALID_INTEGER, value) is not None:
        raise VCardValidationError("UTC offset isn't match", property)


def validate_language_tag(value, property=None):
    if re.match(LANG_TAG, value) is not None:
        raise VCardValidationError("Language Tag isn't match", property)


def validate_boolean(value, property=None):
    if not (value.upper() == "TRUE" or value.upper() == "FALSE"):
        raise VCardValidationError("Boolean must be true or false", property)


def validate_uri(value, property=None):
    parsed = urlparse(value)
    if parsed[0] == '' or (parsed[1] == '' and parsed[2] == ''):
        raise VCardValidationError("URI is incorrect", property)


def params_names_required(property, names, values={}):
    for i in property.params:
        if len(values) != 0:
            for value in values:
                if i in values:
                    if value.lower() not in values[i]:
                        raise VCardValidationError("Value is unknown", property)
        if i.lower() not in names:
            raise VCardValidationError("Param name is unknown")


def validate_parameter(property):
    for param in property.params:
        if param == "LANGUAGE":
            validate_language_tag(property.params[param], property)
        elif param == "PREF":
            i = int(property.params[param])
            if i > 100 or i < 1:
                raise VCardValidationError("PREF param has invalid parameter", property)
        elif param == "PID":
            if not re.match(r"(\d+)(.(\d+))*(,(\d+)(.(\d+)))*", property.params[param]):
                raise VCardValidationError("PID param has invalid parameter", property)
        elif param == "SORT-AS":
            if not re.match(r"\"(\w+)(,(\w+))*\"", property.params[param]):
                raise VCardValidationError("SORT-AS param has invalid parameter", property)
        elif param == "LEVEL":
            values = [
                "beginner", "average", "expert",
                "high", "medium", "low"
            ]
            if property.params[param] not in values:
                raise VCardValidationError("Incorrect LEVEL parameter value", property)
        elif param == "INDEX":
            if not re.match(VALID_INTEGER, property.params[param]):
                raise VCardValidationError("SORT-AS param has invalid parameter", property)


def validate_property(property, version):
    validate_parameter(property)
    if property.name == "PROFILE":
        if property.value.lower() != "vcard":
            raise VCardValidationError(property, "Profile must be with VALUE=VCARD")
    elif property.name == "SOURCE":
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0], property)
    elif property.name == "KIND":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "XML":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "FN":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "N":
        validate_value_parameter(property, [])
        values_count_required(property, 5, 5)
    elif property.name == "NICKNAME":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text_list(property.values[0], property)
    elif property.name in ["PHOTO", "LOGO"]:
        if version == "4.0":
            validate_value_parameter(property, ["uri"], text_allowed=False)
            values_count_required(property, 1, 1)
        else:
            values_count_required(property, 1, 1)
            if "ENCODING" not in property.params:
                raise VCardValidationError("Encoding not found in params", property)
            else:
                if property.params["ENCODING"] != "b":
                    raise VCardValidationError("Encoding must be 'b'", property)
    elif property.name in ["BDAY", "ANNIVERSARY", "DEATHDATE"]:
        validate_value_parameter(property, ["date-and-or-time"])
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None, property)
    elif property.name == "GENDER":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 2)
        if len(property.values[0]) != 1:
            raise VCardValidationError("Incorrect gender tag")
    elif property.name == "ADR":
        validate_value_parameter(property, [])
        values_count_required(property, 7, 7)
        if version == "3.0":
            if "TYPE" in property.params:
                subvalues = property.params["TYPE"].split(",")
                for subvalue in subvalues:
                    subvalue = subvalue.lower()
                    if subvalue not in LABEL_TEL:
                        raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "LABEL":
        values_count_required(property, 7, 7)
        if version == "4.0":
            warnings.warn("LABEL property is not defined in VCard 4.0")
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue not in TYPE_LABEL:
                    raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "TEL":
        validate_value_parameter(property, ["uri"])
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            length = len(subvalues)
            for subvalue in subvalues:
                if subvalue not in TYPE_TEL:
                    raise VCardValidationError(f"ADR type {subvalue} is unknown")
        if version != "4.0":
            length = 1
        values_count_required(property, length, length)
    elif property.name == "EMAIL":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            length = len(subvalues)
            for subvalue in subvalues:
                if subvalue not in TYPE_EMAIL:
                    raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "IMPP":
        validate_value_parameter(property, ["uri"])
        values_count_required(property, 1, 1)
        validate_uri(property.values[0], property)
    elif property.name == "MAILER":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "LANG":
        values_count_required(property, 1, 1)
        validate_value_parameter(property, ["language-tag"], text_allowed=False)
        validate_language_tag(property.values[0], property)
    elif property.name == "TZ":
        if version == "4.0":
            validate_value_parameter(property, ["utc-offset", "uri"])
            values_count_required(property, 1, 1)
            if property.params["VALUE"] == "text":
                validate_text(property.values[0], property)
            elif property.params["VALUE"] == "utc-offset":
                validate_utc_offset(property.values[0], property)
            elif property.params["VALUE"] == "uri":
                validate_uri(property.values[0], property)
        else:
            values_count_required(property, 1, 1)
            validate_utc_offset(property.values[0], property)
    elif property.name == "GEO":
        if version == "4.0":
            validate_value_parameter(property, ["uri"], text_allowed=False)
            values_count_required(property, 1, 1)
            validate_uri(property.values[0], property)
        else:
            values_count_required(property, 2, 2)
            for i in property.values:
                validate_float(i)
    elif property.name == "TITLE":
        validate_value_parameter(property, ["text"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0], property)
    elif property.name == "ROLE":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "ORG":
        validate_value_parameter(property, [])
        values_count_required(property, 2, 2)
        validate_text(property.values[0], property)
    elif property.name == "MEMBER":
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0], property)
    elif property.name == "RELATED":
        if version != "4.0":
            warnings.warn("Related property allowed only in version 4.0")
        validate_value_parameter(property, ["uri"], text_allowed=True)
        values_count_required(property, 1, 1)
        if property.params["VALUE"] == "uri":
            validate_uri(property.values[0], property)
        else:
            validate_text(property.values[0], property)
        if "TYPE" in property.params:
            if property.params["TYPE"] not in [
                "contact", "acquaintance", "friend", "met",
                "co-worker", "colleague", "co-resident",
                "neighbor", "child", "parent",
                "sibling", "spouse", "kin", "muse",
                "crush", "date", "sweetheart", "me",
                "agent", "emergency"
            ]:
                raise VCardValidationError("TYPE is incorrect", property)
            else:
                raise VCardValidationError("TYPE not found", property)
    elif property.name in ["CATEGORIES", "NOTE", "PRODID"]:
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text_list(property.values[0], property)
    elif property.name == "REV":
        if version == "4.0":
            validate_value_parameter(property, ["timestamp"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_datetime(property.values[0], None, property)
    elif property.name == ["SORT-STRING", "CLASS"]:
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "SOUND":
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] == "uri":
                validate_uri(property.values[0])
    elif property.name in ["UID", "KEY"]:
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] == "uri":
                validate_uri(property.values[0])
            else:
                validate_text(property.values[0])
    elif property.name == ["FBURL", "CALADRURI", "CALURI", "URL"]:
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])
    elif property.name == "CLIENTPIDMAP":
        values_count_required(property, 2, 2)
        validate_integer(property.values[0])
        validate_uri(property.values[1])
    elif property.name == "AGENT":
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] == "uri":
                validate_uri(property.values[0])
            else:
                property.values[0] = property.values[0].decode('string_escape')
    elif property.name in ["BIRTHDATE", "DEATHPLACE"]:
        values_count_required(property, 1, 1)
        validate_value_parameter(property, ["uri"])
        if "VALUE" in property.params:
            if property.params["VALUE"] == "uri":
                validate_uri(property.values[0])
            else:
                validate_text(property.values[0])
    elif property.name in ["HOBBY", "EXPERTISE", "INTEREST", "ORG-DIRECTORY"]:
        values_count_required(property, 1, 1)
        validate_value_parameter(property, [])
