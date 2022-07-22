from typing import Union

from pyvcard.parsers import AbstractParser
from pyvcard.vobject.tools import vCard_Converter, _vCard_Builder
from pyvcard.vobject.parsing import vCard_Parser
from pyvcard.vobject.structures import vCard, vCard_entry, is_vcard, is_vcard_property, \
    parse_name_property, validate_vcards
from pyvcard.vobject.containers import vCardSet, vCardList
from pyvcard.enums import SOURCES

import pyvcard.sources.jcard
import pyvcard.sources.xcard
import pyvcard.sources.csv_source
import pyvcard.sources.hcard


def parse(source, indexer: "vCardIndexer" = None) -> vCard_Parser:
    """
    Returns a vCard parser

    :param      source:   Source to find .vcf file
    :type       source:   File descriptor or str
    :param      indexer:  The indexer that will be set
    :type       indexer:  vCardIndexer or None
    """
    return vCard_Parser(source, indexer=indexer)


def convert(source: str) -> vCard_Converter:
    """
    Returns a vCard converter object

    :param      source:  Source to find .vcf file
    :type       source: vCard or vCardSet
    """
    return vCard_Converter(source)


def parse_from(source: str, type: str, indexer: "vCardIndexer" = None) -> Union[AbstractParser, vCard_Parser]:
    """
    Parses vCard from various sources (see SOURCES enum)

    :param      source:   Source to find .vcf file
    :type       source:   str
    :param      type:     The type
    :type       type:     str or SOURCES enum
    :param      indexer:  The indexer
    :type       indexer:  instance of vCardIndexer or None
    """
    if type == SOURCES.XML or type == "xml":
        return pyvcard.sources.xcard.xCard_Parser(source, indexer)
    elif type == SOURCES.JSON or type == "json":
        return pyvcard.sources.jcard.jCard_Parser(source, indexer)
    elif type == SOURCES.CSV or type == "csv":
        return pyvcard.sources.csv_source.csv_Parser(source, indexer)
    elif type == SOURCES.HTML or type == "html":
        return pyvcard.sources.hcard.hCard_Parser(source, indexer)
    elif type == SOURCES.VCF:
        return parse(source, indexer)
    else:
        raise TypeError(f"Type {type} isn't found")


def builder(indexer: "vCardIndexer" = None, version="4.0") -> _vCard_Builder:
    """
    Returns a vCard object builder

    :param      indexer:  The indexer
    :type       indexer: instance of vCardIndexer or None
    :param      version:  The version
    :type       version:  string
    """
    return _vCard_Builder(indexer=indexer, version=version)
