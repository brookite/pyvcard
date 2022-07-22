from typing import List, Optional

from .exceptions import *
from .regex import *
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
    'text',
    'isdn',
    'pcs',
    'textphone',
    'main',
    'other'
]
LABEL_TEL = [
    'dom',
    'intl',
    'postal',
    'parcel',
    'home',
    'work',
    'pref',
    'other',
    'customtype'
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


def values_count_required(property: "vCard_entry", mincount: int, maxcount: int) -> None:
    """
    Validates value count in property. Utility function

    :param      property:  The property
    :type       property:  vCard_entry
    :param      mincount:  The mincount
    :type       mincount:  int
    :param      maxcount:  The maxcount
    :type       maxcount:  int
    """
    if len(property.values) < mincount:
        raise vCardValidationError(f"Values of property {property.name} count must be in [{mincount}, {maxcount}]", property)
    elif len(property.values) > maxcount:
        raise vCardValidationError(f"Values of property {property.name} count must be in [{mincount}, {maxcount}]", property)


def params_count_required(property: "vCard_entry", mincount: int, maxcount: int) -> None:
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
        raise vCardValidationError(f"Values of property {property.name} count must be in [{mincount}, {maxcount}]", property)
    elif len(property.params) > maxcount:
        raise vCardValidationError(f"Values of property {property.name}  count must be in [{mincount}, {maxcount}]", property)


def validate_value_parameter(property: "vCard_entry",
                             values: List[str],
                             param_required: bool = False,
                             text_allowed: bool = True) -> None:
    """
    Validates "VALUE" parameter in property

    :param      property:        The property
    :type       property:        vCard_entry
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
                raise vCardValidationError(f"VALUE param {val} is not found", property)
    else:
        if param_required:
            raise vCardValidationError("VALUE param not found", property)


def validate_group(group: str,
                   property: Optional["vCard_entry"] = None) -> None:
    """
    Validates group in property. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  vCard_entry or None
    """
    if not re.match(GROUP, group):
        raise vCardValidationError("Group isn't match", property)


def validate_datetime(value: str, subtype: str,
                      property: Optional["vCard_entry"] = None) -> None:
    """
    Validates date and time values. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      subtype:   The subtype of date or time ("datetime", "time", "date")
    :type       subtype:   str
    :param      property:  The property
    :type       property:  vCard_entry or None
    """
    if subtype == "datetime" or subtype == "date-time":
        pattern = VALID_DATETIME
    elif subtype == "timestamp":
        pattern = VALID_TIMESTAMP
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
            if not any([
                re.match(VALID_TIMESTAMP, value), re.match(VALID_DATE, value),
                re.match(VALID_TIME, value), re.match(VALID_DATETIME, value)
            ]):
                raise vCardValidationError("Date or time isn't match", property)
    else:
        raise ValueError("Incorrect subtype", property)
    if not re.match(pattern, value):
        raise vCardValidationError(f"{subtype} isn't match", property)


def validate_float(value: str, property: Optional["vCard_entry"] = None) -> None:
    """
    Validates text type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  vCard_entry or None
    """
    if re.match(VALID_FLOAT, value) is None:
        raise vCardValidationError("Float isn't match", property)


def validate_integer(value, property=None):
    """
    Validates integer type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  vCard_entry or None
    """
    if re.match(VALID_INTEGER, value) is None:
        raise vCardValidationError("Integer isn't match", property)


def validate_utc_offset(value: str, property: Optional["vCard_entry"] = None):
    """
    Validates text type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if re.match(VALID_TZ, value) is None:
        raise vCardValidationError("UTC offset isn't match", property)


def validate_language_tag(value: str, property: Optional["vCard_entry"] = None):
    """
    Validates language tag type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if re.match(LANG_TAG, value) is None:
        raise vCardValidationError("Language Tag isn't match", property)


def validate_boolean(value: str, property: Optional["vCard_entry"] = None) -> None:
    """
    Validates boolean type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    if not (value.upper() == "TRUE" or value.upper() == "FALSE"):
        raise vCardValidationError("Boolean must be true or false", property)


def validate_uri(value, property: Optional["vCard_entry"] = None) -> None:
    """
    Validates uri type value. Property if not None will be saved in exception

    :param      value:     The value
    :type       value:     str
    :param      property:  The property
    :type       property:  _vCard_entry or None
    """
    parsed = urlparse(value)
    if parsed[0] == '' or (parsed[1] == '' and parsed[2] == ''):
        raise vCardValidationError("URI is incorrect", property)


def validate_parameter(property: "vCard_entry"):
    """
    Validates parameters in property

    :param      property:  The property
    :type       property:  vCard_entry
    """
    for param in property.params:
        if param == "LANGUAGE":
            validate_language_tag(property.params[param], property)
        elif param == "PREF" and property.params[param] is not None:
            i = int(property.params[param])
            if i > 100 or i < 1:
                raise vCardValidationError("PREF param has invalid parameter", property)
        elif param == "PID":
            if not re.match(r"(\d+)(.(\d+))*(,(\d+)(.(\d+)))*", property.params[param]):
                raise vCardValidationError("PID param has invalid parameter", property)
        elif param == "SORT-AS":
            if not re.match(r"\"(\w+)(,(\w+))*\"", property.params[param]):
                raise vCardValidationError("SORT-AS param has invalid parameter", property)
        elif param == "LEVEL":
            values = [
                "beginner", "average", "expert",
                "high", "medium", "low"
            ]
            if property.params[param] not in values:
                raise vCardValidationError("Incorrect LEVEL parameter value", property)
        elif param == "INDEX":
            if not re.match(VALID_INTEGER, property.params[param]):
                raise vCardValidationError("SORT-AS param has invalid parameter", property)


def validate_property(property: "vCard_entry", version: str):
    """
    Validates the property (values and parameters)

    :param      property:  The property
    :type       property:  vCard_entry
    :param      version:   The version
    :type       version:   str
    """
    validate_parameter(property)
    if property.name == "PROFILE":
        if property.values[0].lower() != "vcard":
            raise vCardValidationError(property, "Profile must be with VALUE=VCARD")
    elif property.name == "SOURCE":
        if version == "4.0":
            validate_value_parameter(property, ["uri"], text_allowed=False)
            validate_uri(property.values[0], property)
        values_count_required(property, 1, 1)
    elif property.name == "KIND":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "XML":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "FN":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "N":
        validate_value_parameter(property, [])
        values_count_required(property, 5, 5)
    elif property.name == "NICKNAME":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name in ["PHOTO", "LOGO"]:
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        if "ENCODING" in property.params:
            if property.params["ENCODING"].lower() not in ["b", "base64"]:
                raise vCardValidationError("Encoding must be 'b' or 'base64' ", property)
    elif property.name in ["BDAY", "ANNIVERSARY", "DEATHDATE"]:
        validate_value_parameter(property, ["date-and-or-time", "date", "date-time"])
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], "datetime", property)
    elif property.name == "GENDER":
        values_count_required(property, 1, 2)
        if len(property.values[0]) != 1:
            raise vCardValidationError("Incorrect gender tag")
    elif property.name == "ADR":
        validate_value_parameter(property, [])
        values_count_required(property, 7, 7)
        if version == "3.0":
            if "TYPE" in property.params:
                subvalues = property.params["TYPE"].split(",")
                for subvalue in subvalues:
                    subvalue = subvalue.lower()
                    if subvalue.lower() not in LABEL_TEL and not subvalue.lower().startswith("x-"):
                        raise vCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "LABEL":
        values_count_required(property, 1, 1)
        if version == "4.0":
            warnings.warn("LABEL property is not defined in VCard 4.0")
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in LABEL_TEL and not subvalue.lower().startswith("x-"):
                    raise vCardValidationError(f"LABEL type {subvalue} is unknown")
    elif property.name == "TEL":
        validate_value_parameter(property, ["uri"])
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in TYPE_TEL and not subvalue.lower().startswith("x-"):
                    raise vCardValidationError(f"TEL type {subvalue} is unknown")
    elif property.name == "EMAIL":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue.lower() not in TYPE_EMAIL and not subvalue.lower().startswith("x-"):
                    raise vCardValidationError(f"EMAIL type {subvalue} is unknown")
    elif property.name == "IMPP":
        validate_value_parameter(property, ["uri"])
        values_count_required(property, 1, 1)
        validate_uri(property.values[0], property)
    elif property.name == "MAILER":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "LANG":
        values_count_required(property, 1, 1)
        validate_value_parameter(property, ["language-tag"], text_allowed=False)
        validate_language_tag(property.values[0], property)
    elif property.name == "TZ":
        if version == "4.0":
            validate_value_parameter(property, ["utc-offset", "uri"])
            values_count_required(property, 1, 1)
            if "VALUE" in property.params:
                if property.params["VALUE"].lower() == "utc-offset":
                    validate_utc_offset(property.values[0], property)
                elif property.params["VALUE"].lower() == "uri":
                    validate_uri(property.values[0], property)
            else:
                validate_utc_offset(property.values[0], property)
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
                validate_float(i, property)
    elif property.name == "TITLE":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "ROLE":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name == "ORG":
        validate_value_parameter(property, [])
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
        if "TYPE" in property.params:
            if property.params["TYPE"].lower() not in [
                "contact", "acquaintance", "friend", "met",
                "co-worker", "colleague", "co-resident",
                "neighbor", "child", "parent",
                "sibling", "spouse", "kin", "muse",
                "crush", "date", "sweetheart", "me",
                "agent", "emergency"
            ]:
                raise vCardValidationError("TYPE is incorrect", property)
            else:
                raise vCardValidationError("TYPE not found", property)
    elif property.name == "CATEGORIES":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
    elif property.name in ["NOTE", "PRODID"]:
        validate_value_parameter(property, [])
        if len(property.values) > 1 and version == "2.1":
            value = ";".join(property.values)
            property._values = [value]
        else:
            values_count_required(property, 0, 1)
    elif property.name == "REV":
        if version == "4.0":
            validate_value_parameter(property, ["timestamp"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_datetime(property.values[0], "timestamp", property)
    elif property.name == ["SORT-STRING", "CLASS"]:
        values_count_required(property, 1, 1)
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
    elif property.name in ["HOBBY", "EXPERTISE", "INTEREST", "ORG-DIRECTORY"]:
        values_count_required(property, 1, 1)
        validate_value_parameter(property, [])
