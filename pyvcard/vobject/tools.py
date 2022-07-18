import pyvcard.vobject.structures as structures
import pyvcard.vobject.containers as containers

import pyvcard.sources.jcard
import pyvcard.sources.xcard
import pyvcard.sources.csv_source
import pyvcard.sources.hcard

class vCard_Converter:
    """
    This class describes a vCard converter to various sources.
    """

    def __init__(self, source):
        """
        Constructs a new instance.

        :param      source:  The source
        :type       source:  _VCard or vCardSet
        """
        if isinstance(source, structures.vCard) or isinstance(source, containers.vCardSet):
            self.source = source
            self._value = source.repr_vcard()
        else:
            raise TypeError(f"Required vCard or vCardSet type, not {type(source)}")

    def file(self, filename, encoding="utf-8"):
        """
        Creates a file using filename and encoding

        :param      filename:  The filename
        :type       filename:  str
        :param      encoding:  The encoding
        :type       encoding:  string
        """
        with open(filename, "w", encoding=encoding) as f:
            f.write(self._value)

    def string(self):
        """
        Returns a vCard string representation
        """
        return self._value

    def bytes(self):
        """
        Returns a vCard string representation in bytes
        """
        return bytes(self._value)

    def html(self):
        """
        Return a vCard converter object to HTML (hCard)
        """
        return pyvcard.sources.hcard.hCard_Converter(self.source)

    def csv(self):
        """
        Return a vCard converter object to CSV
        """
        return pyvcard.sources.csv_source.csv_Converter(self.source)

    def json(self):
        """
        Return a vCard converter object to JSON (jCard)
        """
        return pyvcard.sources.jcard.jCard_Converter(self.source)

    def xml(self):
        """
        Return a vCard converter object to XML (xCard)
        """
        return pyvcard.sources.xcard.xCard_Converter(self.source)


class _vCard_Builder:
    """
    Front-end to create vCard objects step by step.
    """

    def __init__(self, version="4.0", indexer=None):
        self.indexer = indexer
        self._properties = []
        self._version = version
        self.set_version(version)

    def add_property(self, name, value, params={}, group=None, encoding_raw=False):
        """
        Adds a property. Low-level function

        :param      name:          The name
        :type       name:          str
        :param      value:         The value
        :type       value:         list or str
        :param      params:        The parameters
        :type       params:        dict
        :param      group:         The group
        :type       group:         str or None
        :param      encoding_raw:  If property is encoded
        :type       encoding_raw:  boolean
        """
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, bytes):
            value = [value]
        elif hasattr(value, "__iter__") and not isinstance(value, str):

            def func(x):
                if not isinstance(x, bytes):
                    return str(x)
                else:
                    return x

            value = list(map(func, value))
        else:
            value = [str(value)]
        entry = structures.vCard_entry(name.upper(), value, params, group, version=self._version, encoded=encoding_raw)
        self._properties.append(entry)

    def set_phone(self, number):
        """
        Sets the phone.

        :param      number:  The number
        :type       number:  str or int
        """
        tel = structures.vCard_entry("TEL", [str(number)])
        self._properties.append(tel)

    def set_name(self, name):
        """
        Sets the full name and structured name.

        :param      name:  The full name
        :type       name:  str
        """
        for i in self._properties:
            if i.name == "N" or i.name == "FN":
                raise KeyError("Key 'N' and 'FN' already exists")
        if isinstance(name, str):
            fname = name
            name = name.split(" ")
            while len(name) < 5:
                name.append("")
        elif hasattr(name, "__iter__") and not isinstance(name, str):
            name = list(map(str, name))
            fname = "".join(name)
        else:
            raise ValueError(f"Invalid argument: {name}")
        entry1 = structures.vCard_entry("FN", [fname])
        self._properties.append(entry1)
        entry2 = structures.vCard_entry("N", name)
        self._properties.append(entry2)

    def set_version(self, version):
        """
        Sets the version.

        :param      version:  The version
        :type       version:  str or VERSIOn enum
        """
        if version in ["2.1", "3.0", "4.0"]:
            self._version = version
            for prop in self._properties:
                if prop.name == "VERSION":
                    self._properties.remove(prop)
                    break
            self.add_property("VERSION", version)

    def build(self):
        """
        Returns vCard object
        """
        if len(self._properties) != 0:
            vcard = structures.vCard(args=self._properties, version=self._version)
            if self.indexer is not None:
                for entry in vcard:
                    self.indexer.index(entry, vcard)
            return vcard
        else:
            raise ValueError("Empty vCard")

    def clear(self):
        """
        Clears all properties.
        """
        self._properties = []