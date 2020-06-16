from pyvcard_exceptions import LibraryNotFoundError
import pyvcard_parsers
import pyvcard_converters
import pyvcard

try:
    from bs4 import BeautifulSoup as bs
    from bs4.element import Tag
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


def _get_string(tag):
    string = tag.string
    if string is None:
        string = ""
    return string


def _has_class(tag, *tags, target=None):
    if not isinstance(tag, Tag):
        return False
    if "class" not in tag.attrs:
        return False
    if len(tag["class"]) == 0:
        return False
    else:
        lst = list(tag["class"])
        if target is not None:
            return target in lst and target in tags
        if len(lst) > 0:
            for t in lst:
                if t in tags:
                    return True
            return False
        else:
            return False


class hCard_Parser(pyvcard_parsers.AbstractParser):
    """
    This class describes a HTML to vCard object parser (hCard)
    """

    def __init__(self, html, indexer):
        _check_lib()
        self._parser = bs(html, "html.parser")
        self.indexer = indexer

    def _is_type_and_value(self, tag):
        value = []
        classes = []
        for subtag in tag:
            if isinstance(subtag, Tag):
                classes.extend(subtag["class"])
        if "type" in classes and "value" in classes:
            for subtag in tag:
                if isinstance(subtag, str):
                    value.append(subtag)
                elif "value" in subtag["class"]:
                    value.append(_get_string(subtag))
        return value

    def _struct_types_parse(self, prop, childs, target=None):
        if _has_class(prop, "fn", target=target):
            s = ""
            for child in childs:
                s += _get_string(child)
            return [s]
        elif _has_class(prop, "n", target=target):
            n_arr = ["" for i in range(5)]
            for child in childs:
                if _has_class(child, "family-name"):
                    n_arr[0] += _get_string(child)
                elif _has_class(child, "given-name"):
                    n_arr[1] += _get_string(child)
                elif _has_class(child, "additional-name"):
                    n_arr[2] += _get_string(child)
                elif _has_class(child, "honorific-prefix"):
                    n_arr[3] += _get_string(child)
                elif _has_class(child, "honorific-suffix"):
                    n_arr[4] += _get_string(child)
            return n_arr
        elif _has_class(prop, "adr", target=target):
            adr_arr = ["" for i in range(7)]
            for child in childs:
                if _has_class(child, "post-office-box"):
                    adr_arr[0] += _get_string(child)
                elif _has_class(child, "extended-address"):
                    adr_arr[1] += _get_string(child)
                elif _has_class(child, "street-address"):
                    adr_arr[2] += _get_string(child)
                elif _has_class(child, "locality"):
                    adr_arr[3] += _get_string(child)
                elif _has_class(child, "region"):
                    adr_arr[4] += _get_string(child)
                elif _has_class(child, "postal-code"):
                    adr_arr[5] += _get_string(child)
                elif _has_class(child, "country-name"):
                    adr_arr[6] += _get_string(child)
            return adr_arr
        elif _has_class(prop, "geo", target=target):
            geo_arr = ["" for i in range(2)]
            for child in childs:
                if _has_class(child, "latitude"):
                    geo_arr[0] += _get_string(child)
                elif _has_class(child, "longitude"):
                    geo_arr[1] += _get_string(child)
            return geo_arr
        else:
            arr = []
            for child in childs:
                arr.append(_get_string(child))
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
                            values = [_get_string(childs[0])]
                    elif childs[0].name == "data":
                        if "value" in childs[0].attrs:
                            values = childs[0]["value"].split(";")
                        else:
                            values = [_get_string(childs[0])]
                    elif childs[0].name == "time":
                        if "datetime" in childs[0].attrs:
                            values = [childs[0]["datetime"]]
                        else:
                            values = [_get_string(childs[0])]
                    elif childs[0].name == "img":
                        if "src" in childs[0].attrs:
                            values = childs[0]["src"]
                        elif "data" in childs[0].attrs:
                            values = childs[0]["data"]
                    elif childs[0].name == "object":
                        values = childs[0]["data"]
                    else:
                        values = pyvcard.split_noescape(_get_string(childs[0]), ";")
            elif len(childs) == 0:
                if prop.name == "abbr":
                    if "title" in prop.attrs:
                        values = [prop["title"]]
                    else:
                        values = [_get_string(prop)]
                elif prop.name == "data":
                    if "value" in prop.attrs:
                        values = prop["value"].split(";")
                    else:
                        values = [_get_string(prop)]
                elif prop.name == "time":
                    if "datetime" in prop.attrs:
                        values = [prop["datetime"]]
                    else:
                        values = [_get_string(prop)]
                elif prop.name == "img":
                    if "src" in prop.attrs:
                        values = prop["src"]
                    elif "data" in prop.attrs:
                        values = prop["data"]
                    else:
                        continue
                elif prop.name == "object":
                    values = prop["data"]
                else:
                    continue
            elif len(self._is_type_and_value(childs)) > 0:
                values = self._is_type_and_value(childs)
            else:
                values = self._struct_types_parse(prop, childs, tagname)
                if len(values) == 0:
                    continue
            self.builder.add_property(tagname, values, params)

    def vcards(self):
        """
        Returns result of parsing

        :returns:   vCard objects
        :rtype:     vCardSet
        """
        self.vcards = []
        self.builder = pyvcard.builder(indexer=self.indexer, version="3.0")
        self._hcards = self._parser.select(".vcard")
        for hcard in self._hcards:
            for tag in SUPPORTED_TAGS:
                self._preprocess_tag(tag, hcard)
            self.vcards.append(self.builder.build())
            self.builder = pyvcard.builder(indexer=self.indexer, version="3.0")
        return pyvcard.vCardSet(self.vcards)


class hCard_Converter(pyvcard_converters.AbstractConverter):
    """
    This class describes a vCard object to HTML converter (hCard)
    """

    def __init__(self, vcard):
        _check_lib()
        self._vcard = vcard
        if pyvcard.is_vcard(self._vcard):
            self._vcard = pyvcard.vCardSet([self._vcard])

    def _add_span_tag(self, prop):
        tag = self.soup.new_tag("span", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _setvalue(self, property, tag):
        if _has_class(tag, "adr", "n", "geo", "org"):
            self._setvalue_struct_type(property, tag)
        elif tag.name == "img":
            if "ENCODING" in property.params:
                tag["data"] = property.value
            else:
                tag["src"] = property.value
        elif tag.name == "a":
            tag["href"] = property.value if property.name.lower() != "email" else "mailto:" + property.value
            tag.string = property.value
        elif "TYPE" in property.params:
            typetag = self.soup.new_tag("span", attrs={"class": "type"})
            if property.name.lower() == "tel":
                valuetag = self.soup.new_tag("a", attrs={"class": "value"})
                valuetag["href"] = "tel:" + property.value
            else:
                valuetag = self.soup.new_tag("span", attrs={"class": "value"})
            typetag.string = property.params["TYPE"]
            values = []
            for value in property.values:
                if isinstance(value, bytes):
                    value = pyvcard.base64_encode(value)
                values.append(value)
            valuetag.string = ";".join(values)
            tag.append(typetag)
            tag.append(valuetag)
        else:
            if isinstance(property.value, bytes):
                tag.string = pyvcard.base64_encode(property.value)
            else:
                tag.string = ";".join(property.values)

    def _setvalue_struct_type(self, property, tag):
        if _has_class(tag, "adr"):
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
        elif _has_class(tag, "n"):
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
        elif _has_class(tag, "geo"):
            value = property.values
            if len(value) == 1:
                value = value[0].replace("geo:", "").split(",")
            lat = self.soup.new_tag("span", attrs={"class": "latitude"})
            lat.string = value[0]
            long = self.soup.new_tag("span", attrs={"class": "longitude"})
            long.string = value[1]
            tag.append(lat)
            tag.append(long)
        elif _has_class(tag, "org"):
            on = self.soup.new_tag("span", attrs={"class": "organization-name"})
            on.string = property.values[0]
            if len(property.values) > 1:
                ou = self.soup.new_tag("span", attrs={"class": "organization-unit"})
                ou.string = property.values[1]
            tag.append(on)
            if len(property.values) > 1:
                tag.append(ou)

    def _add_link_tag(self, prop):
        tag = self.soup.new_tag("a", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_img_tag(self, prop):
        tag = self.soup.new_tag("img", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_abbr_tag(self, prop):
        tag = self.soup.new_tag("abbr", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_div_tag(self, prop):
        tag = self.soup.new_tag("div", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def _add_time_tag(self, prop):
        tag = self.soup.new_tag("time", attrs={"class": prop.name.lower()})
        self._setvalue(prop, tag)
        self.root.append(tag)

    def result(self):
        """
        Returns result of converting as bs4.element.Tag (BeautfiulSoup4)
        """
        self.soup = bs(features="html.parser")
        for vcard in self._vcard:
            self.root = self.soup.new_tag("div", attrs={"class": "vcard"})
            for prop in vcard:
                if prop.name.lower() in SUPPORTED_TAGS:
                    if prop.name.lower() in ["bday"]:
                        self._add_time_tag(prop)
                    elif prop.name.lower() in ["logo", "photo"]:
                        self._add_img_tag(prop)
                    elif prop.name.lower() in ["n", "adr"]:
                        self._add_span_tag(prop)
                    elif prop.name.lower() in ["uri", "url", "email"]:
                        self._add_link_tag(prop)
                    else:
                        self._add_div_tag(prop)
            self.soup.append(self.root)
        return self.soup

    def strresult(self):
        """
        Returns result of converting as string (HTML)
        """
        return str(self.result())

    def include_to_html(self, htmlpath, encoding="utf-8"):
        """
        Includes hCards in body to HTML file

        :param      htmlpath:  file path
        :type       htmlpath:  str
        :param      encoding:  The encoding of file
        :type       encoding:  str
        """
        with open(htmlpath, "r", encoding=encoding) as fd:
            html = fd.read()
            htmlsoup = bs(html, "html.parser")
            body = htmlsoup.select("body")[0]
            body.append(self.result())
            text = str(htmlsoup)
        with open(htmlpath, "w", encoding=encoding) as fd:
            fd.write(text)
        return text
