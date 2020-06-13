import unittest
import pyvcard
from traceback import print_exc
import os
from fuzzywuzzy import fuzz

vcard_dir = "./vcards/"
test_path = "./tests/"

bundle = pyvcard.vCardSet()
indexer = pyvcard.vCardIndexer(index_params=True)
for i in os.listdir(vcard_dir):
    if i.endswith(".vcf"):
        pth = os.path.join(vcard_dir, i)
        try:
            vcard = pyvcard.openfile(pth, encoding="utf-8", indexer=indexer).vcards()
            bundle.update(vcard)
        except pyvcard.VCardValidationError as e:
            print(pth, str(e))
        except Exception as e:
            print_exc()
            print(pth, str(e))
bundle.setindex(indexer)


def wratio(str1, str2):
    return fuzz.WRatio(str1, str2)


class vcardtest(unittest.TestCase):

    def test_parsing_errors(self):
        c = 0
        for i in os.listdir(os.path.join(vcard_dir, "errors")):
            try:
                if i.endswith(".vcf"):
                    pth = os.path.join(vcard_dir, i)
                    pyvcard.openfile(pth, encoding="utf-8").vcards()
                c += 1
            except Exception:
                pass
        self.assertEqual(c, 0)

    def test_building_vcf(self):
        factory = pyvcard.builder()
        factory.set_version("4.0")
        factory.set_phone(12345678910)
        factory.set_name("Test App")
        txt = factory.build().repr_vcard()
        f = open(os.path.join(test_path, "factory.xml"), "w", encoding="utf-8")
        f.write(txt)
        f.close()

    def test_converting_vcf(self):
        txt = bundle.repr_vcard()
        f = open(os.path.join(test_path, "test.vcf"), "w", encoding="utf-8")
        f.write(txt)
        f.close()
        vcardfd = pyvcard.openfile(os.path.join(test_path, "test.vcf"), "r", encoding="utf-8")
        txt = vcardfd.vcards().repr_vcard()
        f = open(os.path.join(test_path, "test2.vcf"), "w", encoding="utf-8")
        f.write(txt)
        f.close()

    def test_csv(self):
        txt = pyvcard.convert(bundle).csv().result()
        f = open(os.path.join(test_path, "test.csv"), "w", encoding="utf-8")
        f.write(txt)
        f.close()
        pyvcard.parse_from(txt, "csv").vcards()

    def test_csv_permanent(self):
        txt = pyvcard.convert(bundle).csv().permanent_result()
        f = open(os.path.join(test_path, "test2.csv"), "w", encoding="utf-8")
        f.write(txt)
        f.close()

    def test_json(self):
        txt = pyvcard.convert(bundle).json().result()
        f = open(os.path.join(test_path, "test.json"), "w", encoding="utf-8")
        f.write(txt)
        f.close()
        pyvcard.parse_from(txt, "json").vcards()

    def test_jsoncsv_examples(self):
        f = open(os.path.join(test_path, "xmltest.xml"), "r", encoding="utf-8")
        txt = f.read()
        f.close()
        pyvcard.parse_from(txt, "xml").vcards()
        f = open(os.path.join(test_path, "jtest.json"), "r", encoding="utf-8")
        txt = f.read()
        f.close()
        pyvcard.parse_from(txt, "json").vcards()

    def test_xml(self):
        txt = pyvcard.convert(bundle).xml().result()
        f = open(os.path.join(test_path, "test.xml"), "w", encoding="utf-8")
        f.write(txt)
        f.close()
        pyvcard.parse_from(txt, "xml").vcards()

    def test_search(self):
        self.file = open(os.path.join(test_path, "log.txt"), "w", encoding="utf-8")
        r = [None for i in range(17)]
        r[0] = bundle.find_by_name("Андрей", fullmatch=False, case=False, indexsearch=False)
        r[1] = bundle.find_by_name("Андрей", fullmatch=True, case=True, indexsearch=False)
        r[2] = bundle.find_by_name("Дима", fullmatch=True, case=True, indexsearch=False)
        r[3] = bundle.find_by_phone_endswith("185", indexsearch=False)
        r[4] = bundle.find_by_phone_endswith(185, indexsearch=False)
        r[5] = bundle.find_by_phone_startswith(7937, indexsearch=False)
        r[6] = bundle.find_by_phone_startswith("7937", indexsearch=False)
        r[7] = bundle.find_by_phone("1234567890", indexsearch=False)
        r[8] = bundle.find_by_phone(1234567890, indexsearch=False)
        r[9] = bundle.find_by_group("item0", indexsearch=False)
        r[10] = bundle.find_by_group("Item0", case=True, indexsearch=False)
        r[11] = bundle.find_by_value("VCARD", fullmatch=True, indexsearch=False)
        r[11] = bundle.find_by_value("VCARD", indexsearch=False)
        r[12] = bundle.find_by_property("PROFILE", "VCARD", indexsearch=False)
        r[13] = bundle.find_by_phone_endswith("890", indexsearch=False)
        r[14] = bundle.find_by_phone_endswith(89, indexsearch=False)
        r[15] = bundle.find_by_phone("1234567890", fullmatch=False, indexsearch=False)
        r[16] = bundle.find_by_phone(1234567890, fullmatch=False, indexsearch=False)
        for i in range(len(r)):
            self.file.write(str(i) + "=" * 10 + "\n")
            for vcard in r[i]:
                self.file.write(str(vcard.contact_data()) + "\n")
        self.file.close()

    def test_indexer(self):
        self.file = open(os.path.join(test_path, "log2.txt"), "w", encoding="utf-8")
        r = [None for i in range(17)]
        r[0] = bundle.find_by_name("Андрей", fullmatch=False, case=False)
        r[1] = bundle.find_by_name("Андрей", fullmatch=True, case=True)
        r[2] = bundle.find_by_name("Дима", fullmatch=True, case=True)
        r[3] = bundle.find_by_phone_endswith("185")
        r[4] = bundle.find_by_phone_endswith(185)
        r[5] = bundle.find_by_phone_startswith(7937)
        r[6] = bundle.find_by_phone_startswith("7937")
        r[7] = bundle.find_by_phone("1234567890")
        r[8] = bundle.find_by_phone(1234567890)
        r[9] = bundle.find_by_group("item0")
        r[10] = bundle.find_by_group("Item0", case=True)
        r[11] = bundle.find_by_value("VCARD", fullmatch=True)
        r[11] = bundle.find_by_value("VCARD")
        r[12] = bundle.find_by_property("PROFILE", "VCARD")
        r[13] = bundle.find_by_phone_endswith("890")
        r[14] = bundle.find_by_phone_endswith(89)
        r[15] = bundle.find_by_phone("1234567890", fullmatch=False)
        r[16] = bundle.find_by_phone(1234567890, fullmatch=False)
        for i in range(len(r)):
            self.file.write(str(i) + "=" * 10 + "\n")
            for vcard in r[i]:
                self.file.write(str(vcard.contact_data()) + "\n")
        self.file.close()

    def test_difference_search(self):
        self.file = open(os.path.join(test_path, "log3.txt"), "w", encoding="utf-8")
        r = [None for i in range(12)]
        r[0] = bundle.difference_search("phone", "12345678", wratio)
        r[1] = bundle.difference_search("phone", "1234567", wratio)
        r[2] = bundle.difference_search("name", "Дима", wratio)
        r[3] = bundle.difference_search("name", "Андрей", wratio)
        r[4] = bundle.difference_search("param", "VCARD", wratio)
        r[5] = bundle.difference_search("param", "VCARD", wratio)
        r[6] = bundle.difference_search("phone", "12345678", wratio, indexsearch=False)
        r[7] = bundle.difference_search("phone", "1234567", wratio, indexsearch=False)
        r[8] = bundle.difference_search("name", "Дима", wratio, indexsearch=False)
        r[9] = bundle.difference_search("name", "Андрей", wratio, indexsearch=False)
        r[10] = bundle.difference_search("param", "VCARD", wratio, indexsearch=False)
        r[11] = bundle.difference_search("param", "VCARD", wratio, indexsearch=False)
        for i in range(len(r)):
            self.file.write(str(i) + "=" * 10 + "\n")
            for vcard in r[i]:
                self.file.write(str(vcard.contact_data()) + "\n")
        self.file.close()

    def test_util(self):
        self.assertEqual(pyvcard.is_vcard(list(bundle)[0]), True)
        self.assertEqual(pyvcard.is_vcard_property(list(bundle)[0][0]), True)
        self.assertEqual(pyvcard.is_vcard([]), False)
        self.assertEqual(pyvcard.is_vcard_property(list(bundle)[0]), False)
        self.assertEqual(pyvcard.strinteger("12345-122345"), 12345122345)

    def test_html(self):
        conv = pyvcard.convert(bundle)
        txt = conv.html().strresult()
        f = open(os.path.join(test_path, "test.html"), "w", encoding="utf-8")
        f.write(txt)
        f.close()
        parsed = pyvcard.parse_from(txt, "html").vcards()
        f = open(os.path.join(test_path, "parsed.vcf"), "w", encoding="utf-8")
        f.write(parsed.repr_vcard())
        f.close()

    def test_type(self):
        for vcard in bundle:
            for prop in vcard:
                prop.typedvalue

    def test_migrate(self):
        pass


if __name__ == "__main__":
    unittest.main()
