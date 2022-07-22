import os

from pyvcard.migrator import _VersionMigrator
from pyvcard.vobject import parse

"""
Used official vCard standards
RFC 2426 - vCard 3.0
RFC 6350 - vCard 4.0
RFC 6351 - xCard
RFC 7095 - jCard
http://microformats.org/wiki/hcard -  hCard
"""


def openfile(file: os.PathLike, mode="r", encoding=None, buffering=-1,
             errors=None, newline=None, opener=None, indexer=None):
    """
    Opens a file for parsing vCard files (vcf). Returns a parser

    The arguments are similar to the standard function 'open'.
    :param      indexer:    The indexer
    :type       indexer:    instance of vCardIndexer or None
    """
    f = open(file, mode, encoding=encoding, buffering=buffering,
             errors=errors, newline=newline, opener=opener)
    return parse(f, indexer=indexer)


def migrate_vcard(vcard: "vCard"):
    """
    Migrates vCard objects to various vCard standard version

    :param      vcard:  The vcard
    :type       vcard:  vCard object
    """
    return _VersionMigrator(vcard)



