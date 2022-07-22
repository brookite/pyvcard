from .utils import str_to_quoted
from .validator import validate_uri

import base64


def encoding_convert(source, params: str) -> str:
    """
    Encodes the property

    :param      source:  The source
    :type       source:  str
    :param      params:  The parameters
    :type       params:  str
    """
    if "ENCODING" in params:
        enc = params["ENCODING"].upper()
    else:
        enc = None
    if isinstance(source, list) or isinstance(source, tuple):
        for i in range(len(source)):
            source[i] = encoding_convert(source[i], params)
    else:
        if enc == "QUOTED-PRINTABLE":
            return str_to_quoted(source)
        elif enc in ["BASE64", "B"]:
            if isinstance(source, str):
                source = source.encode("utf-8")
            return base64.b64encode(source).decode("utf-8")
        else:
            return source


def determine_type(prop) -> str:
    """
    Determines the type by property.

    :param      prop:  The property
    :type       prop:  _vCard property
    """
    if "VALUE" in prop.params:
        return prop.params["VALUE"]
    else:
        if prop.name in [
            "N", "FN", "XML", "KIND", "GENDER",
            "TZ", "TITLE", "ROLE", "TEL", "EMAIL",
            "ORG", "CATEGORIES", "NOTES", "PRODID",
            "EXPERTISE", "HOBBY", "UID", "INTEREST", "ORG-DIRECTORY",
            "BIRTHPLACE", "DEATHPLACE", "VERSION", "ADR", "NICKNAME", "NOTE"
        ]:
            return "text"
        elif prop.name in [
            "SOURCE", "IMPP", "GEO", "LOGO",
            "MEMBER", "RELATED", "SOUND",
            "URI", "FBURL", "CALADRURI", "CALURI", "URL"
        ]:
            return "uri"
        elif prop.name in ["BDAY", "ANNIVERSARY", "DEATHDATE"]:
            return "date-and-or-time"
        elif prop.name in ["LANG"]:
            return "language-tag"
        elif prop.name in ["REV"]:
            return "timestamp"
        else:
            return "unknown"


def recognize_param_type(param: str, value: str) -> str:
    """
    Recognize parameter type by name (uses RFC6350)

    :param      param:  The parameter name
    :type       param:  str
    :param      value:  The value
    :type       value:  str
    """
    if param == "LANGUAGE":
        return "language-tag"
    elif param == "PREF":
        return "integer"
    elif param in ["MEDIATYPE", "CALSCALE", "SORT-AS", "ALTID", "VALUE"]:
        return "text"
    elif param == "GEO":
        return "uri"
    elif param in ["PID", "TYPE"]:
        if "," in value:
            return "text-list"
        else:
            return "text"
    elif param == "TZ":
        try:
            validate_uri(value)
            return "uri"
        except Exception:
            return "text"
    elif param in ["CHARSET", "ENCODING"]:
        return "text"
    else:
        return "unknown"


class AbstractConverter:
    def result(self):
        pass

    @property
    def object(self):
        return self._object









