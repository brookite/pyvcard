from pyvcard_exceptions import LibraryNotFoundError
import pyvcard_parsers
import pyvcard_converters
import pyvcard

try:
    from bs4 import BeautifulSoup as bs
    _lib_imported = True
except Exception:
    _lib_imported = False


def _check_lib():
    if not _lib_imported:
        raise LibraryNotFoundError("BeautifulSoup4")


SUPPORTED_TAGS = set([
    "n", "fn", "url", "email", "tel",
    "adr", "geo", "photo", "sound", "logo",
    "bday", "title", "role", "org", "category", "note",
    "class", "key", "mailer", "uid", "rev", "tz", "nickname",
    "sort-string", "label", "uri", "agent"
])


class hCard_Parser(pyvcard_parsers.AbstractParser):
    def __init__(self, html, indexer):
        _check_lib()
        self._parser = bs(html, "html.parser")
        self.indexer = indexer

    def _is_type_and_value(self, tag):
        value = []
        for subtag in tag:
            if isinstance(subtag, str):
                value.append(subtag)
            elif "value" in subtag["class"]:
                value.append(subtag.string)
        return value

    def _struct_types_parse(self, prop, childs):
        if prop["class"] == "n":
            n_arr = ["" for i in range(5)]
            for child in childs:
                if child["class"] == "family-name":
                    n_arr[0] += child.string
                if child["class"] == "given-name":
                    n_arr[1] += child.string
                if child["class"] == "additional-name":
                    n_arr[2] += child.string
                if child["class"] == "honorific-prefix":
                    n_arr[3] += child.string
                if child["class"] == "honorific-suffix":
                    n_arr[4] += child.string
            return n_arr
        elif prop["class"] == "adr":
            adr_arr = ["" for i in range(7)]
            for child in childs:
                if child["class"] == "post-office-box":
                    adr_arr[0] += child.string
                if child["class"] == "extended-address":
                    adr_arr[1] += child.string
                if child["class"] == "street-address":
                    adr_arr[2] += child.string
                if child["class"] == "locality":
                    adr_arr[3] += child.string
                if child["class"] == "region":
                    adr_arr[4] += child.string
                if child["class"] == "postal-code":
                    adr_arr[5] += child.string
                if child["class"] == "country-name":
                    adr_arr[6] += child.string
            return adr_arr
        elif prop["class"] == "geo":
            geo_arr = ["" for i in range(2)]
            for child in childs:
                if child["class"] == "latitude":
                    geo_arr[0] += child.string
                if child["class"] == "longitude":
                    geo_arr[1] += child.string
            return geo_arr
        else:
            arr = []
            for child in childs:
                arr.append(child.string)
            return arr

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
                            values = [childs[0].string]
                    elif childs[0].name == "data":
                        if "value" in childs[0].attrs:
                            values = [childs[0]["value"]]
                        else:
                            values = [childs[0].string]
                    elif childs[0].name == "time":
                        if "datetime" in childs[0].attrs:
                            values = [childs[0]["datetime"]]
                        else:
                            values = [childs[0].string]
                    elif childs[0].name == "img":
                        values = childs[0]["src"]
                    elif childs[0].name == "object":
                        values = childs[0]["data"]
                    else:
                        values = pyvcard.split_noescape(childs[0].string, ";")
            elif len(self._is_type_and_value(childs)) > 0:
                values = self._is_type_and_value(childs)
            else:
                if prop["class"] in ["adr", "n", "geo"]:
                    values = self._struct_types_parse(prop, childs)
            self.builder.add_property(tagname, values, params)

    def vcards(self):
        self.vcards = []
        self.builder = pyvcard.builder(indexer=self.indexer)
        self._hcards = self._parser.select(".vcard")
        for hcard in self._hcards:
            for tag in SUPPORTED_TAGS:
                self._preprocess_tag(tag, hcard)
            self.vcards.append(self.builder.build())
            self.builder = pyvcard.builder(indexer=self.indexer)
        return pyvcard.vCardSet(self.vcards)


class hCard_Converter(pyvcard_converters.AbstractConverter):
    def __init__(self, vcard):
        _check_lib()
        self._vcard = vcard

    def _add_span_tag(self, prop):
        tag = self.soup.new_tag("span", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _setvalue(self, property, tag):
        if "TYPE" in property.params:
            typetag = self.soup.new_tag("span", attrs={"class": "type"})
            if property.name.lower() == "tel":
                valuetag = self.soup.new_tag("a", attrs={"class": "value"})
                valuetag["href"] = "tel:" + property.value
            else:
                valuetag = self.soup.new_tag("span", attrs={"class": "value"})
            typetag.string = property.params["TYPE"]
            valuetag.string = ";".join(property.values)
            tag.append(typetag)
            tag.append(valuetag)
        if tag.name == "img":
            if "ENCODING" in property.params:
                tag["data"] = property.value
            else:
                tag["src"] = property.value
        elif tag.name == "a":
            tag["href"] = property.value if property.name.lower() != "email" else "mailto:" + property.value
            tag.string = property.value
        elif tag.name in ["adr", "n", "geo"]:
            self._setvalue_struct_type(property, tag)
        else:
            tag.string = property.value

    def _setvalue_struct_type(self, property, tag):
        if tag.name == "adr":
            postoffice = self.soup.new_tag("span", attrs={"class": "post-office-box"})
            postoffice.string = property.values[0]
            ea = self.soup.new_tag("span", attrs={"class": "extended-address"})
            ea.string = property.values[1]
            sa = self.soup.new_tag("span", attrs={"class": "street-address"})
            sa.string = property.values[2]
            loc = self.soup.new_tag("span", attrs={"class": "locality"})
            loc.string = property.values[3]
            reg = self.soup.new_tag("span", attrs={"class": "region"})
            reg.string = property.values[4]
            postal = self.soup.new_tag("span", attrs={"class": "postal-code"})
            postal.string = property.values[5]
            country = self.soup.new_tag("span", attrs={"class": "country-name"})
            country.string = property.values[6]
            tag.append(postoffice)
            tag.append(ea)
            tag.append(sa)
            tag.append(loc)
            tag.append(reg)
            tag.append(postal)
            tag.append(country)
        elif tag.name == "n":
            fn = self.soup.new_tag("span", attrs={"class": "family-name"})
            fn.string = property.values[0]
            gn = self.soup.new_tag("span", attrs={"class": "given-name"})
            gn.string = property.values[1]
            an = self.soup.new_tag("span", attrs={"class": "additional-name"})
            an.string = property.values[2]
            hp = self.soup.new_tag("span", attrs={"class": "honorific-prefix"})
            hp.string = property.values[3]
            hs = self.soup.new_tag("span", attrs={"class": "honorific-suffix"})
            hs.string = property.values[4]
            tag.append(fn)
            tag.append(gn)
            tag.append(an)
            tag.append(hp)
            tag.append(hs)
        elif tag.name == "geo":
            tag["title"] = ";".join(property.values)

    def _add_link_tag(self, prop):
        tag = self.soup.new_tag("a", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_img_tag(self, prop):
        tag = self.soup.new_tag("img", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_abbr_tag(self, prop):
        tag = self.soup.new_tag("abbr", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_div_tag(self, prop):
        tag = self.soup.new_tag("div", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_time_tag(self, prop):
        tag = self.soup.new_tag("time", attrs={"class": property.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def result(self):
        self.soup = bs()
        self.root = self.soup.new_tag("div", attrs={"class": "vcard"})
        for prop in self._vcard:
            if prop.name in SUPPORTED_TAGS:
                if prop.name in ["bday"]:
                    self._add_time_tag(prop)
                elif prop.name in ["logo", "photo"]:
                    self._add_img_tag(prop)
                elif prop.name in ["n", "adr"]:
                    self._add_span_tag(prop)
                elif prop.name in ["uri", "url", "email"]:
                    self._add_link_tag(prop)
                elif prop.name in ["geo"]:
                    self._add_abbr_tag(prop)
                else:
                    self._add_div_tag(prop)

        self.soup.append(self.root)
        return self.root

    def strresult(self):
        return str(self.result())

    def include_to_html(self, htmlpath):
        with open(htmlpath, "r") as fd:
            html = fd.read()
            htmlsoup = bs(html, "html.parser")
            body = htmlsoup.select("body")[0]
            body.append(self.result())
            text = str(htmlsoup)
        with open(htmlpath, "w") as fd:
            fd.write(text)
        return text
