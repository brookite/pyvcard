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
    'textphone',
    'main'
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
    'work',
    'cell',
    'school',
    'other',
    'customtype'
]
VALUE_TYPE = [
    "text", "uri", "date",
    "time", "date-and-or-time", "datetime",
    "timestamp", "boolean", "integer", "float",
    "utc-offset", "language-tag"
]


def validate_bool_wrapper(validator_func, *args, **kwargs):
    """
    Returns boolean value of validator function instead exception

    :param      validator_func:  The validator function
    :type       validator_func:  function
    :param      args:            The arguments of validator function
    :type       args:            list
    :param      kwargs:          The keywords arguments of validator function
    :type       kwargs:          dictionary
    """
    try:
        validator_func(*args, **kwargs)
        return True
    except Exception:
        return False


def values_count_required(property, mincount, maxcount):
    """
    Validates value count in property. Utility function

    :param      property:  The property
    :type       property:  _vCard_entry
    :param      mincount:  The mincount
    :type       mincount:  int
    :param      maxcount:  The maxcount
    :type       maxcount:  int
    """
    if len(property.values) < mincount:
        raise VCardValidationError(f"Values count must be >= {mincount}", property)
    elif len(property.values) > maxcount:
        raise VCardValidationError(f"Values count must be <= {maxcount}", property)


def params_count_required(property, mincount, maxcount):
    """
    Validates value count in property. Utility function

    :param      property:  The property
    :type       property:  _vCard_entry
    :param      mincount:  The mincount
    :type       mincount:  int
    :param      maxcount:  The maxcount
    :type       maxcount:  int
    """
    if len(property.params) < mincount:
        raise VCardValidationError(f"Values count must be >= {mincount}", property)
    elif len(property.params) > maxcount:
        raise VCardValidationError(f"Values count must be <= {maxcount}", property)


def validate_value_parameter(property, values, param_required=False, text_allowed=True):
    """
    Validates "VALUE" parameter in property

    :param      property:        The property
    :type       property:        _vCard_entry
    :param      values:          The values
    :type       values:          list
    :param      param_required:  The parameter 'VALUE' in property required
    :type       param_required:  boolean
    :param      text_allowed:    If 'text' in VALUE parameter will be allowed
    :type       text_allowed:    boolean
    """
    if "VALUE" in property.params:
        val = property.params["VALUE"].lower()
        if val not in values:
            if val != "text" and text_allowed:
                raise VCardValidationError(f"VALUE param {val} is not found", property)
    else:
        if param_required:
            raise VCardValidationError("VALUE param not found", property)


def validate_text(value, property=None):
    """
    Validates text type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if not re.match(VALID_TEXT, value):
        raise VCardValidationError("Text isn't match", property)


def validate_group(group, property=None):
    """
    Validates group in property. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if not re.match(GROUP, group):
        raise VCardValidationError("Group isn't match", property)


def validate_text_list(value, property=None):
    """
    Validates text list type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if not re.match(VALID_TEXTLIST, value):
        raise VCardValidationError("Text list isn't match", property)


def validate_datetime(value, subtype, property=None):
    """
    Validates date and time values. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      subtype:   The subtype of date or time ("datetime", "time", "date")
    :type       subtype:   str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if subtype == "datetime":
        pattern = VAILD_TIMESTAMP
    elif subtype == "time":
        pattern = VALID_TIME
    elif subtype == "date":
        pattern = VALID_DATE
    elif subtype == "date-and-or-time":
        if value.startswith("T"):
            pattern = VALID_TIME
        else:
            pattern = VALID_DATETIME
    elif subtype is None:
        if value.startswith("T"):
            pattern = VALID_TIME
        else:
            if not any(re.match(VAILD_TIMESTAMP, value), re.match(VALID_DATE, value),
                       re.match(VALID_TIME, value), re.match(VALID_DATETIME, value)
                       ):
                raise VCardValidationError("Date or time isn't match", property)
    else:
        raise ValueError("Incorrect subtype", property)
    if not re.match(pattern, value):
        raise VCardValidationError(f"{subtype} isn't match", property)


def validate_float(value, property=None):
    """
    Validates text type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry
    """
    if re.match(VALID_FLOAT, value) is None:
        raise VCardValidationError("Float isn't match", property)


def validate_integer(value, property=None):
    """
    Validates integer type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if re.match(VALID_INTEGER, value) is None:
        raise VCardValidationError("Integer isn't match", property)


def validate_utc_offset(value, property=None):
    """
    Validates text type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if re.match(VALID_TZ, value) is None:
        raise VCardValidationError("UTC offset isn't match", property)


def validate_language_tag(value, property=None):
    """
    Validates language tag type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if re.match(LANG_TAG, value) is None:
        raise VCardValidationError("Language Tag isn't match", property)


def validate_boolean(value, property=None):
    """
    Validates boolean type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if not (value.upper() == "TRUE" or value.upper() == "FALSE"):
        raise VCardValidationError("Boolean must be true or false", property)


def validate_uri(value, property=None):
    """
    Validates uri type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    parsed = urlparse(value)
    if parsed[0] == '' or (parsed[1] == '' and parsed[2] == ''):
        raise VCardValidationError("URI is incorrect", property)


def validate_parameter(property):
    """
    Validates parameters in property

    :param      property:  The property
    :type       property:  _vCard_entry
    """
    for param in property.params:
        if param == "LANGUAGE":
            validate_language_tag(property.params[param], property)
        elif param == "PREF" and property.params[param] is not None:
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
    """
    Validates the property (values and parameters)

    :param      property:  The property
    :type       property:  _vCard_entry
    :param      version:   The version
    :type       version:   str
    """
    validate_parameter(property)
    if property.name == "PROFILE":
        if property.values[0].lower() != "vcard":
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
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        if "ENCODING" in property.params:
            if property.params["ENCODING"].lower() not in ["b", "base64"]:
                raise VCardValidationError("Encoding must be 'b' or 'base64' ", property)
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
                    if subvalue.lower() not in LABEL_TEL and not subvalue.lower().startswith("x-"):
                        raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "LABEL":
        values_count_required(property, 1, 1)
        if version == "4.0":
            warnings.warn("LABEL property is not defined in VCard 4.0")
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in LABEL_TEL and not subvalue.lower().startswith("x-"):
                    raise VCardValidationError(f"LABEL type {subvalue} is unknown")
    elif property.name == "TEL":
        validate_value_parameter(property, ["uri"])
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in TYPE_TEL and not subvalue.lower().startswith("x-"):
                    raise VCardValidationError(f"TEL type {subvalue} is unknown")
    elif property.name == "EMAIL":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in TYPE_EMAIL and not subvalue.lower().startswith("x-"):
                    raise VCardValidationError(f"EMAIL type {subvalue} is unknown")
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
            if property.params["VALUE"].lower() == "text":
                validate_text(property.values[0], property)
            elif property.params["VALUE"].lower() == "utc-offset":
                validate_utc_offset(property.values[0], property)
            elif property.params["VALUE"].lower() == "uri":
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
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "ROLE":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0], property)
    elif property.name == "ORG":
        validate_value_parameter(property, [])
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
        if property.params["VALUE"].lower() == "uri":
            validate_uri(property.values[0], property)
        else:
            validate_text(property.values[0], property)
        if "TYPE" in property.params:
            if property.params["TYPE"].lower() not in [
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
            if property.params["VALUE"].lower() == "uri":
                validate_uri(property.values[0])
    elif property.name in ["UID", "KEY"]:
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"].lower() == "uri":
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
            if property.params["VALUE"].lower() == "uri":
                validate_uri(property.values[0])
            else:
                property.values[0] = property.values[0].decode('string_escape')
    elif property.name in ["BIRTHDATE", "DEATHPLACE"]:
        values_count_required(property, 1, 1)
        validate_value_parameter(property, ["uri"])
        if "VALUE" in property.params:
            if property.params["VALUE"].lower() == "uri":
                validate_uri(property.values[0])
            else:
                validate_text(property.values[0])
    elif property.name in ["HOBBY", "EXPERTISE", "INTEREST", "ORG-DIRECTORY"]:
        values_count_required(property, 1, 1)
        validate_value_parameter(property, [])
