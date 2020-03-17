class VCardFormatError(Exception):
    pass


class VCardValidatorError(Exception):
    def __init__(self, msg, property):
        super().__init__(msg)
        self.property = property