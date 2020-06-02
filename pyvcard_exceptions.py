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


class LibraryNotFoundError(Exception):
    def __init__(self, *libraries):
        lib = ", ".join(libraries)
        super().__init__(f"One or more libraries wasn't found ({lib}). Please install this")
        self.property = property
