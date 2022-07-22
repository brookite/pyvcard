from typing import Collection, Optional, Union, List

import pyvcard.vobject.structures
from pyvcard.indexer import vCardIndexer
from pyvcard.utils import base64_encode


class _vCardContainerMixin:
    """
    This class describes a set with vCard objects
    """

    def __init__(self, iterable: Collection = []):
        for obj in iterable:
            if not pyvcard.vobject.structures.is_vcard(obj):
                raise TypeError("vCardSet requires only vCard objects")
        self._indexer: vCardIndexer = None

    def add(self, vcard: "vCard"):
        """
        Adds the specified vCard.

        :param      vcard:  The vCard
        :type       vcard:  vCard
        """
        if pyvcard.vobject.structures.is_vcard(vcard):
            super().add(vcard)

    def setindex(self, indexer: vCardIndexer):
        """
        Sets indexer for this object

        :param      indexer:  The indexer
        :type       indexer:  instance of vCardIndexer
        """
        if isinstance(indexer, vCardIndexer):
            self._indexer = indexer
        else:
            raise TypeError(f"Required vCardIndexer instance, not {type(indexer)}")

    def repr_vcard(self, encode: bool = True):
        """
        Returns a string representation of vCard

        :param      encode:  encode property (like bytes, or quoted-printable)
        :type       encode:  boolean
        """
        s = ""
        for vcard in self:
            s += vcard.repr_vcard(encode)
            s += "\n"
        return s

    def difference_search(self, type: str, value: str,
                          diff_func, k: int = 85,
                          use_param: Optional[str] = None,
                          indexsearch: bool = True):
        """
        Searches for specific parameters using a third-party function that returns an integer value similarity coefficient
        (example: fuzzywuzzy module methods)

        :param      type:       The type (name, phone, param)
        :type       type:       str
        :param      value:      The value that need find
        :type       value:      str
        :param      diff_func:  The difference function, returns integer value coefficient
        :type       diff_func:  function or any callable object
        :param      k:          the minimum value of the difference function at which it will be
                                considered that the value is found
        :type       k:          int
        :param      use_param:  if not None and type is "param" finds only by property name
        :type       use_param:  str or None
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.difference_search(type, value, diff_func, k=k)

        if type == "name" or type == "names":
            attr = "name"
        elif type == "phone" or type == "phones":
            attr = "phone"
        elif type == "param" or type == "params":
            attr = "param"

        def type_convert(x):
            if isinstance(x, bytes):
                return base64_encode(x)
            else:
                return str(x)

        def filter_function(x):
            if attr == "name":
                x = x.contact_name()
                return diff_func(x, value) >= k
            elif attr == "phone":
                x = x.contact_number()
                for i in x:
                    return diff_func(str(i), value) >= k
                return False
            elif attr == "param":
                lst = []
                for param in x:
                    if (use_param is not None and param.name == use_param) or use_param is None:
                        ivalue = ";".join(list(map(type_convert, param.values)))
                        lst.append(diff_func(ivalue, value))
                m = max(lst)
                if m > 0:
                    return m >= k
                else:
                    return False
        array = tuple(set(filter(filter_function, self)))
        return array

    def find_by_group(self, group: str,
                      case: bool = False,
                      fullmatch: bool = True,
                      indexsearch: bool = True):
        """
        Finds a by group.

        :param      group:        The group
        :type       group:        str
        :param      case:         case sensitivity
        :type       case:         boolean
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_group(group, case=case, fullmatch=fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_group(group, case, fullmatch, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_name(self, fn: str,
                     case: bool = False, fullmatch: bool = True,
                     indexsearch: bool = True):
        """
        Finds a by name.

        :param      fn:           The full name or structured name joined by ";"
        :type       fn:           str
        :param      case:         case sensitivity
        :type       case:         boolean
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_name(fn, case, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_name(fn, case, fullmatch, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone(self, number: Union[str, int],
                      fullmatch: bool = False,
                      parsestr: bool = True, indexsearch: bool = True):
        """
        Finds a by phone number.

        :param      number:       The number
        :type       number:       str or int
        :param      fullmatch:    The fullmatch
        :type       fullmatch:    boolean
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone(number, fullmatch, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone(number, fullmatch, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone_endswith(self, number: Union[str, int],
                               parsestr: bool = True,
                               indexsearch: bool = True):
        """
        Finds a by phone number ending.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_endswith(number, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone_endswith(number, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_phone_startswith(self, number: Union[str, int],
                                 parsestr: bool = True,
                                 indexsearch: bool = True):
        """
        Finds a by starts of a phone.

        :param      number:       The number
        :type       number:       str or int
        :param      parsestr:     remove all non-digit symbols(default: True)
        :type       parsestr:     boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_phone_startswith(number, parsestr)
        else:
            result = set()
            for i in self:
                val = i.find_by_phone_startswith(number, parsestr, indexsearch)
                if val:
                    for value in val:
                        result.add(value)
            return tuple(result)

    def find_by_property(self, paramname: str, value: Union[str, List[str]],
                         fullmatch: bool = True,
                         indexsearch: bool = True):
        """
        Finds a by property name and value.

        :param      paramname:    The property name
        :type       paramname:    str
        :param      value:        The value
        :type       value:        str or list
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_property(paramname, value, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_property(paramname, value, fullmatch)
                if val:
                    for e in val:
                        result.add(e)
            return tuple(result)

    def find_by_value(self, value: str,
                      fullmatch: bool = True,
                      indexsearch: bool = True):
        """
        Finds a by property value.

        :param      value:        The property value
        :type       value:        str
        :param      fullmatch:    finds by a full match
        :type       fullmatch:    boolean
        :param      indexsearch:  use indexer in search if defined (default is True)
        :type       indexsearch:  boolean
        """
        if indexsearch and self._indexer:
            return self._indexer.find_by_value(value, fullmatch)
        else:
            result = set()
            for i in self:
                val = i.find_by_value(value, fullmatch)
                if val:
                    for e in val:
                        result.add(e)
            return tuple(result)


class vCardList(list, _vCardContainerMixin):
    def __init__(self, iterable=[], indexer=None):
        super(vCardList, self).__init__(iterable)
        self._indexer = indexer


class vCardSet(set, _vCardContainerMixin):
    def __init__(self, iterable=[], indexer=None):
        super(vCardSet, self).__init__(iterable)
        self._indexer = indexer