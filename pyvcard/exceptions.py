class vCardFormatError(Exception):
    """
    This class describes a vCard exception that will be raised if
    string format were violated

    Has 'property' attribute in instance
    """

    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property


class vCardValidationError(Exception):
    """
    This class describes a vCard exception that
    will be raised if vCard definition rules were violated

    Has 'property' attribute in instance
    """

    def __init__(self, msg, property=None):
        super().__init__(msg)
        self.property = property


class LibraryNotFoundError(Exception):
    """
    This class describes a exception what may be occure when pyvcard couldn't find required libraries

    Libraries argument contains all required libraries
    """

    def __init__(self, *libraries):
        lib = ", ".join(libraries)
        super().__init__(f"One or more libraries wasn't found ({lib}). Please install this")
        self.libraries = libraries
