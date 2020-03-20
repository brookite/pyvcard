from pyvcard_exceptions import *
from urllib.parse import urlparse
import re
import warnings


def values_count_required(property, mincount, maxcount):
    if len(property.values) < mincount:
        raise VCardValidationError(property, f"Values count must be >= {mincount}", property)
    elif len(property.values) > maxcount:
        raise VCardValidationError(property, f"Values count must be <= {maxcount}", property)


def params_count_required(property, mincount, maxcount):
    if len(property.params) < mincount:
        raise VCardValidationError(property, f"Values count must be >= {mincount}", property)
    elif len(property.params) > maxcount:
        raise VCardValidationError(property, f"Values count must be <= {maxcount}", property)


def validate_value_parameter(property, values, param_required=False, text_allowed=True):
    if "VALUE" in property.params:
        val = property.params["VALUE"].lower()
        if property.params["VALUE"].lower() in values or \
            (property.params["VALUE"] == "text" & text_allowed):
            raise VCardValidationError(f"VALUE param {val} not found", property)
    else:
        return not param_required


def validate_text(value, property=None):
    pass


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


def params_names_required(property, names, values={}, property=None):
    for i in property.params:
        if len(values) != 0:
            for value in values:
                if i in values:
                    if value.lower() not in values[i]:
                        raise VCardValidationError("Value is unknown", property)
        if i.lower() not in names:
            raise VCardValidationError("Param name is unknown")


def validate_parameter(property):
    pass


def validate_property(property, version):
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
        validate_text(property.values[0])
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
        validate_text(property.values[0], property)
    elif property.name in ["PHOTO", "LOGO"]:
        if verison == "4.0":
            validate_value_parameter(property, ["uri"], text_allowed=False)
            values_count_required(property, 1, 1)
        else:
            values_count_required(property, 1, 1)
            if "ENCODING" not in property.params:
                raise VCardValidationError("Encoding not found in params", property)
            else:
                if property.params["ENCODING"] != "b":
                    raise VCardValidationError("Encoding must be 'b'", property)
    elif property.name == "BDAY":
        validate_value_parameter(property, ["date-and-or-time"])
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None)
    elif property.name == "ANNIVERSARY":
        validate_value_parameter(property, ["date-and-or-time"])
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None)
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
                    if subvalue in [
                        'dom',
                        'intl',
                        'postal',
                        'parcel',
                        'home',
                        'work',
                        'pref'
                    ]:
                        raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "LABEL":
        values_count_required(property, 7, 7)
        if version == "4.0":
            warnings.warn("LABEL property is not defined in VCard 4.0")
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            for subvalue in subvalues:
                if subvalue in [
                    'dom',
                    'intl',
                    'postal',
                    'parcel',
                    'home',
                    'work',
                    'pref'
                ]:
                    raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "TEL":
        validate_value_parameter(property, ["uri"])
        if "TYPE" in property.params:
            subvalues = property.params["TYPE"].split(",")
            length = len(subvalues)
            for subvalue in subvalues:
                if subvalue in [
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
                ]:
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
                if subvalue in [
                    'internet',
                    'x400',
                    'pref',
                    'dom',
                    'intl',
                    'postal',
                    'parcel',
                    'home',
                    'work'
                ]:
                    raise VCardValidationError(f"ADR type {subvalue} is unknown")
    elif property.name == "IMPP":
        validate_value_parameter(property, ["uri"])
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])
    elif property.name == "MAILER":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "LANG":
        values_count_required(property, 1, 1)
        validate_value_parameter(property, ["language-tag"], text_allowed=False)
        validate_language_tag(property.values[0])
    elif property.name == "TZ":
        if version == "4.0":
            validate_value_parameter(property, ["utc-offset", "uri"])
            values_count_required(property, 1, 1)
            if property.params["VALUE"] == "text":
                validate_text(property.values[0])
            elif property.params["VALUE"] == "utc-offset":
                validate_utc_offset(property.values[0])
            elif property.params["VALUE"] == "uri":
                validate_uri(property.values[0])
        else:
            values_count_required(property, 1, 1)
            validate_utc_offset(property.values[0])
    elif property.name == "GEO":
        if version == "4.0":
            validate_value_parameter(property, ["uri"], text_allowed=False)
            values_count_required(property, 1, 1)
            validate_uri(property.values[0])
        else:
            values_count_required(property, 2, 2)
            for i in property.values:
                validate_float(i)                 
    elif property.name == "TITLE":
        validate_value_parameter(property, ["text"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])    
    elif property.name == "ROLE":
        validate_value_parameter(property, [])
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "ORG":
        validate_value_parameter(property, [])
        values_count_required(property, 2, 2)
        validate_text(property.values[0])
    elif property.name == "MEMBER":
        validate_value_parameter(property, ["uri"], text_allowed=False)
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])
    elif property.name == "RELATED":
        if version != "4.0":
            warnings.warn("Related property allowed only in version 4.0")
        validate_value_parameter(property, ["uri"], param_required=True)
        values_count_required(property, 1, 1)
        if property.params["VALUE"] == "uri":
            validate_uri(property.values[0])
        else:
            validate_text(property.values[0])
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

