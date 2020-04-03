class _xCard_Parser:
    def __init__(self, xcard):
        pass
    
    def _is_supported_tag(self, name):
        return name.lower() in [
            "language-tag", "uri", "text", "integer",
            "unknown", "vcards", "vcard", "parameters"
        ]    
    
    def vcard(self):
        pass