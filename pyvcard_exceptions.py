class VCardFormatError(Exception):
    def __init__(self, msg, object=None):
        super().__init__(msg)
        self.object = object


class VCardValidationError(Exception):
    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property
