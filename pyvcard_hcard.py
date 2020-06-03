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
    "sort-string", "label", "uri"
]


class hCardParser(AbstractParser):
    def __init__(self, html):
        _check_lib()
        self.vcards = []
        self.builder = pyvcard.build()
        self._parser = bs(html, "html.parser")
        self._hcards = self._parser.select(".vcard")
        for hcard in self._hcards:
            for tag in SUPPORTED_TAGS:
                self._preprocess_tag(tag, hcard)
            self.vcard.append(self.builder.build())
            self.builder = pyvcard.build()

    def _is_type_and_value(self, tag):
        value = []
        for subtag in tag:
            if isinstance(subtag, str):
                value.append(subtag)
            elif "value" in subtag["class"]:
                value.append(subtag.text)
        return value

    def _struct_types_parse(self, prop):
        pass

    def _preprocess_tag(self, tagname, hcard):
        selected = hcard.select("." + tagname)
        for prop in selected:
            params = {}
            if "type" in prop.attrs:
                params["type"] = prop.attrs["type"]
            childs = list(prop.children)
            if len(childs) == 1:
                if isinstance(childs[0], str):
                    values = [childs[0]]
                else:
                    if childs[0].name in ["a", "area"] and tagname in ["url", "uid", "uri"]:
                        value = childs[0]["href"].replace("tel:", "").replace("mailto:", "")
                        values = [value]
                    elif childs[0].name in ["img", "area"] and tagname not in ["url", "uid", "uri"]:
                        value = childs[0]["alt"]
                        values = [value]
                    elif childs[0].name == "abbr":
                        if "title" in childs[0].attrs:
                            values = [childs[0]["title"]]
                        else:
                            values = [childs[0].text]
                    elif childs[0].name == "data":
                        if "value" in childs[0].attrs:
                            values = [childs[0]["value"]]
                        else:
                            values = [childs[0].text]
                    elif childs[0].name == "time":
                        if "datetime" in childs[0].attrs:
                            values = [childs[0]["datetime"]]
                        else:
                            values = [childs[0].text]
                    elif childs[0].name == "img":
                        values = childs[0]["src"]
                    elif childs[0].name == "object":
                        values = childs[0]["data"]
                    else:
                        values = childs[0].text.split(";")
            elif len(self._is_type_and_value(childs)) > 0:
                values = self._is_type_and_value(childs)
            else:
                if prop["class"] in ["adr", "n", "geo"]:
                    values = self._struct_types_parse(prop)
            self.builder.add_property(tagname, values, params)

    def vcards(self):
        return pyvcard.vCardSet(self.vcards)
