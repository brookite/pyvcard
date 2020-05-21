def define_type(property):
    pass


class vCardType:
    @property
    def rawvalue(self):
        pass


class UnknownType(vCardType):
    pass


class Text(vCardType, str):
    pass


class NameType(vCardType):
    pass


class URI(vCardType):
    pass


class vCardTimeType(vCardType):
    pass


class Date(vCardTimeType):
    pass


class DateTime(vCardTimeType):
    pass


class Timestamp(vCardTimeType):
    pass


class UTCOffset(vCardType):
    pass


class LanguageTag(vCardType):
    pass
