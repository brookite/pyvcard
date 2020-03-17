from pyvcard_exceptions import *
from urlparse import urlparse
import re
import warnings


def values_count_required(property, mincount, maxcount):
    if len(property.values) < mincount:
        raise VCardValidationError(property, f"Values count must be >= {mincount}")
    elif len(property.values) > maxcount:
        raise VCardValidationError(property, f"Values count must be <= {maxcount}")


def params_count_required(property, mincount, maxcount):
    if len(property.params) < mincount:
        raise VCardValidationError(property, f"Values count must be >= {mincount}")
    elif len(property.params) > maxcount:
        raise VCardValidationError(property, f"Values count must be <= {maxcount}")


def validate_text(value):
    pass


def validate_datetime(value, subtype):
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
            raise VCardValidationError("Date or time isn't match")
    else:
        raise ValueError("Incorrect subtype")
    if not re.match(pattern, value):
        raise VCardValidationError(f"{subtype} isn't match")


def validate_float(value):
    if re.match(VALID_FLOAT, value) is not None:
        raise VCardValidationError("Float isn't match")


def validate_integer(value):
    if re.match(VALID_INTEGER, value) is not None:
        raise VCardValidationError("Integer isn't match")


def validate_utc_offset(value):
   if re.match(VALID_INTEGER, value) is not None:
        raise VCardValidationError("UTC offset isn't match")


def validate_language_tag(value):
   if re.match(LANG_TAG, value) is not None:
        raise VCardValidationError("Language Tag isn't match")


def validate_boolean(value):
    return value.upper() == "TRUE" or value.upper() == "FALSE"


def validate_uri(value):
    parsed = urlparse(value)
    if parsed[0] == '' or (parsed[1] == '' and parsed[2] == ''):
        raise VCardValidationError("URI is incorrect")


def params_names_required(property, names, values={}):
    for i in property.params:
        if len(values) != 0:
            for value in values:
                if i in values:
                    if value.lower() not in values[i]:
                        raise VCardValidationError("Value is unknown")
        if i.lower() not in names:
            raise VCardValidationError("Param name is unknown")


def validate_parameter(property):
    pass


def validate_property(property, version):
    if property.name == "PROFILE":
        if property.value.lower() != "vcard":
            raise VCardValidationError(property, "Profile must be with VALUE=VCARD")
    elif property.name == "SOURCE":
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])
    elif property.name == "KIND":
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "XML":
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "FN":
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "N":
        values_count_required(property, 5, 5)
    elif property.name == "NICKNAME":
        values_count_required(property, 1, 1)
    elif property.name in "PHOTO":
        values_count_required(property, 1, 1)
    elif property.name == "BDAY":
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None)
    elif property.name == "ANNIVERSARY":
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None)
    elif property.name == "BDAY":
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            if property.params["VALUE"] != "text":
                validate_datetime(property.values[0], None)
    elif property.name == "GENDER":
        values_count_required(property, 1, 2)
        if len(property.values[0]) != 1:
            raise VCardValidationError("Incorrect gender tag")
    elif property.name == "ADR":
        values_count_required(property, 7, 7)
        if version == "3.0":
            if "TYPE" in property.params:
                subvalues = property.params["TYPE"].split(",")
                for subvalue.lower() in subvalues:
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
        values_count_required(property, 1, 1)
        validate_uri(property.values[0])
    elif property.name == "MAILER":
        values_count_required(property, 1, 1)
        validate_text(property.values[0])
    elif property.name == "LANG":
        values_count_required(property, 1, 1)
        if "VALUE" in property.params:
            validate_language_tag(property.params["VALUE"])
        validate_language_tag(property.values[0])















