import pyvcard
from pyvcard_regex import *
from pyvcard_exceptions import *
from urllib.parse import urlparse
import datetime
from pyvcard_converters import determine_type


def define_type(property):
    if property.name == "N":
        return NameType(property.values)
    else:
        type_val = determine_type(property)
        if type_val == "uri":
            return URI(property.values)
        elif type_val == "text":
            return Text(property.values)
        elif type_val == "language-tag":
            return LanguageTag(property.values)
        elif type_val == "timestamp" or type_val == "date-and-or-time":
            return DateTime(property.values)
        elif type_val == "date":
            return Date(property.values)
        elif type_val == "time":
            return Time(property.values)
        elif type_val == "utc-offset":
            return UTCOffset(property.values)
        else:
            return UnknownType(property.values)


class vCardType:
    @property
    def rawvalue(self):
        return self._value


class UnknownType(vCardType):
    def __init__(self, value):
        self._value = value


class Text(vCardType, str):
    def __init__(self, value):
        if isinstance(value, str):
            self._value = value
        str.__init__(value)


class NameType(vCardType):
    def __init__(self, value):
        if len(value) == 5:
            self._array = value
            self._dict = pyvcard.parse_name_property(self._array)

    def __getitem__(self, value):
        return self._dict[value]

    def __contains__(self, key):
        if key in self._dict:
            return self._dict[key] is not None
        return False

    @property
    def suffix(self):
        return self._suffix

    @property
    def given_name(self):
        return self._given_name

    @property
    def surname(self):
        return self._surname

    @property
    def prefix(self):
        return self._prefix

    @property
    def additional_name(self):
        return self._additional_name


class URI(vCardType):
    def __init__(self, value):
        self._value = value

    def parse(self):
        return urlparse(self._value)


class vCardTimeType(vCardType):
    pass


class Date(vCardTimeType):
    def __init__(self, value):
        self._value = value
        parsed = re.match(VALID_DATE, value[0])
        if not parsed:
            raise VCardValidationError("This value isn't date")
        if parsed.group(1) != "-" or parsed.group(1) is not None:
            self._year = int(parsed.group(1))
        else:
            self._year = None
        if parsed.group(2) != "-" or parsed.group(2) is not None:
            self._month = int(parsed.group(2))
        else:
            self._month = None
        if parsed.group(3) != "-" or parsed.group(3) is not None:
            self._day = int(parsed.group(3))
        else:
            self._day = None

    @property
    def month(self):
        return self._month

    @property
    def year(self):
        return self._year

    @property
    def day(self):
        return self._day

    @property
    def array(self):
        return [self.year, self.month, self.day]

    @property
    def date(self):
        if all(map(lambda x: x is not None, self.array)):
            return datetime.date(*self.array)
        else:
            return None


class Time(vCardTimeType):
    def __init__(self, value):
        self._value = value
        parsed = re.match(VALID_TIME, value[0])
        if not parsed:
            raise VCardValidationError("This value isn't time")
        if parsed.group(1) != "-" or parsed.group(1) is not None:
            self._h = int(parsed.group(1))
        else:
            self._h = None
        if parsed.group(2) != "-" or parsed.group(2) is not None:
            self._m = int(parsed.group(2))
        else:
            self._m = None
        if parsed.group(3) != "-" or parsed.group(3) is not None:
            self._s = int(parsed.group(3))
        else:
            self._s = None
        if parsed.group(3) != "-" or parsed.group(3) is not None:
            self._offset = parsed.group(4)
        else:
            self._offset = None

    @property
    def seconds(self):
        return self._s

    @property
    def hour(self):
        return self._h

    @property
    def minutes(self):
        return self._m

    @property
    def utc_offset(self):
        return self._offset


class DateTime(vCardTimeType):
    def __init__(self, value):
        self._value = value
        parsed = re.match(VALID_DATETIME, value[0])
        if not parsed:
            raise VCardValidationError("This value isn't datetime")
        self._year = None if parsed.group(2) == "-" or parsed.group(1) is None else int(parsed.group(2))
        self._month = None if parsed.group(3) == "-" or parsed.group(1) is None else int(parsed.group(3))
        self._day = None if parsed.group(4) == "-" or parsed.group(1) is None else int(parsed.group(4))
        self._h = 0 if parsed.group(6) == "-" or parsed.group(1) is None else int(parsed.group(6))
        self._m = 0 if parsed.group(7) == "-" or parsed.group(1) is None else int(parsed.group(7))
        self._s = 0 if parsed.group(8) == "-" or parsed.group(1) is None else int(parsed.group(8))
        self._offset = None if parsed.group(10) == "-" or parsed.group(1) is None else parsed.group(10)

    @property
    def seconds(self):
        return self._s

    @property
    def hour(self):
        return self._h

    @property
    def minutes(self):
        return self._m

    @property
    def utc_offset(self):
        return self._offset

    @property
    def month(self):
        return self._month

    @property
    def year(self):
        return self._year

    @property
    def day(self):
        return self._day

    @property
    def array(self):
        return [self.year, self.month, self.day, self.hour, self.minutes, self.seconds]

    @property
    def datetime(self):
        if all(map(lambda x: x is not None, self.array)):
            return datetime.datetime(*self.array)
        else:
            return None


class UTCOffset(vCardType):
    def __init__(self, value):
        self._value = value
        parsed = re.match(VALID_TZ, value[0])
        if not parsed:
            self._hour = 0
            self._sign = 1
            self._minutes = 0
        else:
            if parsed.group(2) is None or parsed.group(2) == "+":
                self._sign = 1
            else:
                self._sign = -1
            self._hour = 0 if parsed.group(3) is None else int(parsed.group(3))
            self._minutes = 0 if parsed.group(4) is None else int(parsed.group(4))

    @property
    def sign(self):
        return self._sign

    @property
    def hour(self):
        return self._hour

    @property
    def minutes(self):
        return self._minutes


class LanguageTag(vCardType):
    def __init__(self, value):
        self._value = value
