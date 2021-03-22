import io
from csv import DictWriter, DictReader

import pyvcard.vobject
from pyvcard.converters import AbstractConverter
from pyvcard.parsers import AbstractParser, get_string

import pyvcard

class csv_Converter(AbstractConverter):
    """
    This class describes a vCard object to CSV converter.
    """

    def __init__(self, obj):
        if pyvcard.vobject.is_vcard(obj) or isinstance(obj, pyvcard.vobject.vCardSet):
            self._object = obj
        else:
            raise ValueError("Required vCardSet or vCard type")

    def write_vcard(self, vcard, writer, permanent=False):
        """
        Writes a vCard. Utility method
        """
        data = vcard.contact_data()
        if not permanent:
            row = {
                "Formatted name": data["name"],
                "Name": data["struct_name"],
                "Tel. Number": str(data["number"]),
                "vCard": vcard.repr_vcard()
            }
        else:
            row = {
                "Formatted name": data["name"]
            }
            if data["struct_name"] is not None:
                row["Name"] = " ".join(list(data["struct_name"].values()))
            else:
                row["Name"] = ""
            if data["number"] is not None:
                row["Tel. Number"] = ";".join(list(map(str, data["number"])))
            else:
                row["Tel. Number"] = ""
        writer.writerow(row)

    def result(self):
        """
        Returns string machine-readable result of converting
        """
        strio = io.StringIO()
        names = ["Formatted name", "Name", "Tel. Number", "vCard"]
        writer = DictWriter(strio, delimiter=',', lineterminator='\n', fieldnames=names)
        writer.writeheader()
        if isinstance(self._object, pyvcard.vobject.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, writer)
        else:
            self.write_vcard(self._object, writer)
        val = strio.getvalue()
        strio.close()
        return val

    def permanent_result(self):
        """
        Returns string result of converting.
        This operation is irreversible. Parsing this csv will be impossible
        """
        strio = io.StringIO()
        names = ["Formatted name", "Name", "Tel. Number"]
        writer = DictWriter(strio, delimiter=',', lineterminator='\n', fieldnames=names)
        writer.writeheader()
        if isinstance(self._object, pyvcard.vobject.vCardSet):
            for vcard in self._object:
                self.write_vcard(vcard, writer, True)
        else:
            self.write_vcard(self._object, writer, True)
        val = strio.getvalue()
        strio.close()
        return val


class csv_Parser(AbstractParser):
    """
    This class describes a CSV to vCard object parser
    """

    def __init__(self, csv, indexer=None):
        self.csv = csv
        self.indexer = indexer

    def vcards(self):
        """
        Returns result of parsing

        :returns:   vCard objects
        :rtype:     vCardSet
        """
        strio = io.StringIO(get_string(self.csv))
        reader = DictReader(strio, delimiter=",")
        raw = list(reader)
        s = ''
        for data in raw:
            s += data["vCard"] + "\n"
        return pyvcard.parse(s, self.indexer).vcards()