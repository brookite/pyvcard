from pyvcard_exceptions import LibraryNotFoundError
from pyvcard_converters import AbstractConverter
from pyvcard_parsers import AbstractParser
import pyvcard

try:
    from bs4 import BeautifulSoup as bs
    _lib_imported = True
except Exception:
    _lib_imported = False


def _check_lib():
    if not _lib_imported:
        raise LibraryNotFoundError("BeautifulSoup4")


SUPPORTED_TAGS = [
    "n", "fn", "url", "email", "tel",
    "adr", "geo", "photo", "sound", "logo",
    "bday", "title", "role", "org", "category", "note",
    "class", "key", "mailer", "uid", "rev", "tz", "nickname",
    "sort-string", "label"
]


class hCardParser(AbstractParser):
    def __init__(self, html):
        _check_lib()
        self.attribs = []
        self.builder = pyvcard.build()
        self._parser = bs(html, "html.parser")
        self._hcard = parser.select(".vcard")
        for tag in SUPPORTED_TAGS:
            self._preprocess_tag(tag)

    def _is_type_and_value(self, tag):
        value = []
        for subtag in tag:
            if isinstance(subtag, str):
                value.append(subtag)
            elif "value" in subtag["class"]:
                value.append(subtag.text)
        return value


    def _preprocess_tag(self, tagname):
        selected = self._hcard.select("." + tagname)
        for prop in selected:
            params = {}
            if "type" in prop.attrs:
                params["type"] = prop.attrs["type"]
            childs = list(prop.children)
            if len(childs) == 1:
                if isinstance(childs[0], str):
                    values = [childs[0]]
                else:
                    if childs[0].name == "a":
                        values = [childs[0]["href"]]
                    else:
                        values = childs[0].text.split(";")
            elif len(self._is_type_and_value(childs)) > 0:
                values = self._is_type_and_value(childs)
            else:
                if prop["class"] in ["adr", "n", "geo"]:
                    pass
            self.builder.add_property(tagname, values, params)


    def vcards(self):
        pass
