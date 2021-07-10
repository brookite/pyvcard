def get_string(obj) -> str:
    """
    Gets the string from file or str. Utility method
    """
    if isinstance(obj, str):
        return obj
    elif hasattr(obj, "close"):
        if not obj.closed():
            s = obj.read()
            obj.close()
            obj = s
            return obj
        else:
            raise ValueError("File is closed")
    else:
        raise ValueError("Required specific object string or file descriptor")


class AbstractParser:
    def vcards(self):
        pass




