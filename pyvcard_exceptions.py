class VCardFormatError(Exception):
    """
    This class describes a vCard exception that will be raised if
    string format were violated

    Has 'property' attribute in instance
    """

    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property


class VCardValidationError(Exception):
    """
    This class describes a vCard exception that
    will be raised if vCard definition rules were violated

    Has 'property' attribute in instance
    """

    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property
