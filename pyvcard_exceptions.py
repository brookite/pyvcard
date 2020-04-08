class VCardFormatError(Exception):
    pass


class VCardValidationError(Exception):
    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property
