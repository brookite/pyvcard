# pyvcard
pyvcard is a light and convenience library for interacting with vCard files. This library can parse, build, convert, perform vCard validation.  
Supports vCard 2.1, 3.0, 4.0 (RFC 2426, RFC 6350)


Advantages:

* vCard parsing
* Supported JSON (jCard), XML (xCard), CSV parsing and converting
* vCard object representation
* vCard building
* Searching in vCard object included support

__Python 3.6+ recommended. WARNING: pyvcard is in early alpha. It may be unstable__

## Tutorials:

1. Parsing simple vcf file:

```python
    cards = pyvcard.openfile("vcard.vcf", encoding="utf-8").vcards()
```

2. Parsing vcf from string

```python
    stringvcf = "BEGIN:VCARD..."
    cards = pyvcard.parse(stringvcf).vcards() #vCardSet
```

3. Building vcf

```python
    builder = pyvcard.builder()
    builder.set_version("3.0")
    builder.add_property("GEO", ["1.25", "87.5"], group="item0", params={})
    builder.set_name("John Appleseed")
    builder.set_phone("1234567890")
    vcard = builder.build()
```

4. String representation of vCard object

```python
    string = object.repr_vcard() #or 
    string = object.repr()
```

5. Indexing vCard objects for search

```python
    #example
    indexer = pyvcard.vCardIndexer(index_params=True)
    pyvcard.parse(stringvcf, indexer=indexer)
```

6. Search in vCard or in vCardSet

```python
    vcardset.find_by_name("Smith", indexsearch=True, fullmatch=True, case=True)
    vcardset.find_by_group("item0")
    vcardset.find_by_phone("1234567890")
    vcardset.find_by_phone_endswith("890")
    vcardset.find_by_phone_startswith("123")
    vcardset.find_by_property("PROFILE", "VCARD")
    vcardset.find_by_value("VCARD")
```

7. Convert vCard or vCardSet to XML, JSON, CSV

```python
    pyvcard.convert(vcardset).xml().result() #may use 'json', 'xml', 'csv', 'html'
```

8. Parse from various sources

```python
    pyvcard.parse_from(source, "csv") #may use 'json', 'xml', 'csv', 'vcf', 'html'
```

9. Difference search (for example using fuzzywuzzy)

```python
    from fuzzywuzzy import fuzz
    import pyvcard
    def wratio(str1, str2):
        return fuzz.WRatio(str1, str2)
    vset.difference_search("phone", "12345678", wratio)
```

10. Extracting main data from vCard object

```python
    print(vcard.contact_data())
    #{'name': 'John Doe', 'number': [1234567890, 123456789], 'struct_name': {'surname': 'Doe', 'given_name': 'John', 'additional_name': 'Quentin', 'prefix': 'Mr,Dr', 'suffix': 'Esq.'}}
```

11. Other features

```python
    vcard[0]
    vcard["FN"]
    pyvcard.is_vcard(vcard)
    pyvcard.is_vcard_property(vcard[0])
```
