import re
from typing import Union

from .vobject import is_vcard
from .enums import VERSION
from .utils import base64_encode, base64_decode
from .vobject import vCard_entry, vCard


class _VersionMigrator:
    """
    This class describes a vCard version migrator.
    """

    def __init__(self, source):
        """
        Constructs a new instance.

        :param      source:  The source
        :type       source:  vCard object
        """
        self._source = source
        if not is_vcard(self._source):
            raise TypeError("vCard required, not vCardSet")

    def _version_conv(self, version: VERSION) -> str:
        if version == VERSION.V2_1:
            version = "2.1"
        elif version == VERSION.V3:
            version = "3.0"
        elif version == VERSION.V4:
            version = "4.0"
        return version

    def migrate(self, version: Union[str, VERSION]):
        """
        Migrates vCard to specified version

        :param      version:  The version
        :type       version:  str or VERSION
        """
        version = self._version_conv(version)
        if self._source.version.value == "2.1" and version == "3.0":
            return self._2to3()
        elif self._source.version.value == "3.0" and version == "4.0":
            return self._3to4()
        elif self._source.version.value == "2.1" and version == "4.0":
            return self._3to4(self._2to3())
        elif self._source.version.value == "3.0" and version == "2.1":
            return self._3to2()
        elif self._source.version.value == "4.0" and version == "3.0":
            return self._4to3()
        elif self._source.version.value == "4.0" and version == "2.1":
            return self._3to2(self._4to3())
        else:
            return self._source

    def _2to3(self, source=None):
        if source is None:
            source = self._source
        args = []
        args.append(vCard_entry("VERSION", "3.0"))
        for prop in source:
            if prop.name == "VERSION":
                continue
            params = {}
            for param in prop.params:
                if param == "ENCODING":
                    if prop.params["ENCODING"].upper() == "QUOTED-PRINTABLE":
                        continue
                if prop.params[param] is None:
                    if "TYPE" not in params:
                        params["TYPE"] = param.lower()
                    else:
                        params["TYPE"] += "," + param.lower()
                    continue
                params[param] = prop.params[param]
            args.append(vCard_entry(prop.name, prop.values, params, prop.group, version="3.0", encoded=False))
        return vCard(args, "3.0")

    def _3to4(self, source=None):
        if source is None:
            source = self._source
        args = []
        args.append(vCard_entry("VERSION", "4.0"))
        for prop in source:
            if prop.name in ["VERSION", "AGENT", "LABEL", "NAME", "MAILER", "CLASS"]:
                continue
            values = prop.values
            params = prop.params
            for param in prop.params:
                if param == "ENCODING":
                    if prop.name in ["LOGO", "PHOTO"]:
                        vtype = "data:image/{};base64,"
                        replace = "jpeg"
                    elif prop.name == "SOUND":
                        vtype = "data:audio/{};base64,"
                        replace = "basic"
                    elif prop.name == "KEY":
                        vtype = "application/{};base64,"
                        replace = "pgp-keys"
                    if "TYPE" in prop.params:
                        replace = prop.params["TYPE"]
                    param = prop.params
                    params.pop("ENCODING")
                    vtype = vtype.format(replace)
                    if isinstance(prop.value, bytes):
                        val = base64_encode(prop.value)
                    else:
                        val = prop.value
                    values = [vtype + val]
                elif param == "TYPE":
                    params["TYPE"] = params["TYPE"].split(",")
                    if "intl" in params["TYPE"]:
                        params["TYPE"].pop("intl")
                    elif "dom" in params["TYPE"]:
                        params["TYPE"].pop("dom")
                    elif "postal" in params["TYPE"]:
                        params["TYPE"].pop("postal")
                    if "parcel" in params["TYPE"]:
                        params["TYPE"].pop("parcel")
                    params["TYPE"] = ",".join(params["TYPE"])
                elif prop.params[param] is None:
                    params.pop(param)
                    if "TYPE" not in params:
                        params["TYPE"] = param.lower()
                    else:
                        params["TYPE"] += "," + param.lower()
            if prop.name == "GEO":
                values = ["geo:" + ",".join(prop.values)]
            args.append(vCard_entry(prop.name, values, params, prop.group, version="4.0", encoded=False))
        return vCard(args, version="4.0")

    def _3to2(self, source=None):
        if source is None:
            source = self._source
        args = []
        args.append(vCard_entry("VERSION", "2.0"))
        for prop in source:
            if prop.name in [
                "VERSION", "CATEGORIES", "CLASS", "NICKNAME",
                "PRODID", "SORT-STRING", "SOURCE", "NAME", "PROFILE"
            ]:
                continue
            params = {}
            for value in prop.values:
                if not value.isascii():
                    params["ENCODING"] = "quoted-printable"
                    break
            for param in prop.params:
                if param == "TYPE":
                    types = prop.params[param].split(",")
                    for t in types:
                        params[t] = None
                    continue
                params[param] = prop.params[param]
            args.append(vCard_entry(prop.name, prop.values, params, prop.group, version="2.0", encoded=False))
        return vCard(args, "2.0")

    def _4to3(self, source=None):
        if source is None:
            source = self._source
        args = []
        args.append(vCard_entry("VERSION", "3.0"))
        for prop in source:
            if prop.name in [
                "VERSION", "RELATED", "KIND", "GENDER",
                "LANG", "ANNIVERSARY", "XML", "CLIENTPIDMAP",
                "FBURL", "CALADRURI", "CAPURI", "CALURI", "IMPP"
            ]:
                continue
            values = []
            params = prop.params
            regex = r"data:{}\/(\w+);base64,"
            for value in prop.values:
                if prop.name in ["LOGO", "PHOTO"]:
                    regex = regex.format("image")
                    m = re.match(regex, value)
                elif prop.name == "SOUND":
                    regex = regex.format("audio")
                    m = re.match(regex, value)
                elif prop.name == "KEY":
                    regex = regex.format("application")
                    m = re.match(regex, value)
                elif prop.name == "GEO":
                    values = prop.value.replace("geo:", "").split(",")
                    break
                else:
                    m = None
                if m:
                    value = base64_decode(re.sub(regex, value))
                    params["ENCODING"] = "b"
                    params["TYPE"] = m.group(1)
                values.append(value)
            args.append(vCard_entry(prop.name, values, params, prop.group, version="3.0", encoded=False))
        return vCard(args, version="3.0")