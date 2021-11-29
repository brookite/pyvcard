import pyvcard.vobject
from pyvcard.utils import strinteger, base64_encode


class vCardIndexer:
    """
    This class is used to create indexes for vСard, speeding up the search
    This class does not guarantee a quick search, creators of third-party solutions
    can inherit this class for their implementations
    """

    def __init__(self, index_params=False):
        """
        Constructs a new instance.

        :param      index_params:  Indexes all properties (not only phone and name)
        :type       index_params:  boolean
        """
        self._names = {}
        self._indexparams = index_params
        self._phones = {}
        self._params = {}
        self._vcards = []
        self._groups = {}

    def __bool__(self):
        return True

    @property
    def names(self):
        return self._names

    @property
    def phones(self):
        return self._phones

    @property
    def params(self):
        return self._params

    def setindex(self, vcard):
        """
        Sets indexer as main for vCard

        :param      vcard:  The target vCard
        :type       vcard:  _vCard
        """
        if pyvcard.vobject.is_vcard(vcard):
            vcard._indexer = self
            self._vcards.append(vcard)

    def index(self, entry, vcard):
        """
        Indexes property in vcard. Don't recommend for use in outer code
        This method is used in vCard parsers

        :param      entry:  vCard property
        :type       entry:  _vCard_entry
        :param      vcard:  The target vCard
        :type       vcard:  _vCard
        """
        if isinstance(entry, pyvcard.vobject.vCard_entry):
            if entry.group is not None:
                if entry.group not in self._groups:
                    self._groups[entry.group] = []
                self._groups[entry.group].append(vcard)
            if entry.name == "FN":
                if entry.values[0] not in self._names:
                    self._names[entry.values[0]] = []
                self._names[entry.values[0]].append(vcard)
            elif entry.name == "N":
                name = ";".join(entry.values)
                if name not in self._names:
                    self._names[name] = []
                self._names[name].append(vcard)
            elif entry.name == "TEL":
                if entry.values[0] not in self._phones:
                    self._phones[entry.values[0]] = []
                self._phones[entry.values[0]].append(vcard)
                if strinteger(entry.values[0]) not in self._phones:
                    self._phones[strinteger(entry.values[0])] = []
                self._phones[strinteger(entry.values[0])].append(vcard)
            elif self._indexparams:
                if entry.name not in self._params:
                    self._params[entry.name] = {}

                def type_convert(x):
                    if isinstance(x, bytes):
                        return base64_encode(x)
                    else:
                        return str(x)
                ivalues = list(map(type_convert, entry.values))
                if ";".join(ivalues) not in self._params[entry.name]:
                    self._params[entry.name][";".join(ivalues)] = []
                self._params[entry.name][";".join(ivalues)].append(vcard)

    def __len__(self):
        return len(self._names) + len(self._phones)

    @property
    def vcards(self):
        return tuple(self._vcards)

    def difference_search(self, type, value, diff_func, k=85, use_param=None):
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
        """
        def filter_function(x):
            x = str(x)
            return diff_func(x, value) >= k

        if type == "name" or type == "names":
            array = list(filter(filter_function, self._names.keys()))
            array2 = []
            for i in array:
                for k in self._names[i]:
                    array2.append(k)
            array = set(array2)
        elif type == "phone" or type == "phones":
            array = list(filter(filter_function, self._phones.keys()))
            array2 = []
            for i in array:
                for k in self._phones[i]:
                    array2.append(k)
            array = set(array2)
        elif type == "param" or type == "params":
            array = set()
            if use_param is None:
                for param in self._params:
                    temp = set(filter(filter_function, self._params[param]))
                    for i in temp:
                        for j in self._params[param][i]:
                            array.add(j)
            else:
                temp = set(filter(filter_function, self._params[use_param]))
                array.update(temp)
                for i in temp:
                    for j in self._params[use_param][i]:
                        array.add(j)
        return tuple(array)

    def get_name(self, fn):
        """
        Gets the name in indexer.

        :param      fn:   Full name
        :type       fn:   str
        """
        return tuple(self._names[fn])

    def get_phone(self, phone):
        """
        Gets the phone in indexer.

        :param      phone:  The phone
        :type       phone:  str or int
        """
        return tuple(self._phones[phone])

    def get_param(self, param, value):
        """
        Gets the property values in indexer.

        :param      param:  The parameter
        :type       param:  str
        :param      value:  The value
        :type       value:  str
        """
        return tuple(self._params[param][value])

    def get_group(self, group):
        """
        Gets the group in indexer.

        :param      group:  The group
        :type       group:  str
        """
        return tuple(self._groups[group])

    def find_by_group(self, group, fullmatch=True, case=False):
        """
        Finds a by group in all indexed vcards.

        :param      group:      The group
        :type       group:      str
        :param      fullmatch:  find by full match
        :type       fullmatch:  boolean
        :param      case:       case sensitivity
        :type       case:       boolean
        """
        if group in self._groups and fullmatch:
            return tuple(self._groups[group])
        elif not fullmatch:
            def filter_function(x):
                if not case:
                    value = x.lower()
                    nonlocal group
                    group = group.lower()
                else:
                    value = x
                if fullmatch:
                    return value == group
                else:
                    return group in value

            lst = filter(filter_function, self._groups.keys())
            result = set()
            for i in lst:
                for j in self._groups[i]:
                    result.add(j)
            return tuple(result)
        else:
            return tuple()

    def find_by_name(self, fn, case=False, fullmatch=True):
        """
        Finds a by name in all indexed vcards.

        :param      fn:      The name (list will be joined by ';')
        :type       fn:      str
        :param      fullmatch:  find by full match
        :type       fullmatch:  boolean
        :param      case:       case sensitivity
        :type       case:       boolean
        """
        if fn in self._names and fullmatch:
            return tuple(self._names[fn])
        elif not fullmatch:
            def filter_function(x):
                if not case:
                    if isinstance(x, str):
                        value = x.lower()
                    else:
                        value = ";".join((map(str, x)))
                    nonlocal fn
                    fn = fn.lower()
                else:
                    value = x
                if fullmatch:
                    return value == fn
                else:
                    return fn in value

            lst = filter(filter_function, self._names.keys())
            result = set()
            for i in lst:
                for j in self._names[i]:
                    result.add(j)
            return tuple(result)
        else:
            return tuple()

    def find_by_phone(self, number, fullmatch=False, parsestr=True):
        """
        Finds a by phone number in all indexed vcards.

        :param      number:      The phone number
        :type       number:      str or int
        :param      fullmatch:  find by full match
        :type       fullmatch:  boolean
        :param      parsestr:    remove all non-digit symbols(default: True)
        :type       parsestr:       boolean
        """
        if number in self._phones and fullmatch:
            return tuple(self._phones[number])
        elif not fullmatch:
            def filter_function(x):
                if parsestr:
                    value = strinteger(x)
                else:
                    value = x
                if fullmatch:
                    return str(value) == str(number)
                else:
                    return str(number) in str(value)

            lst = filter(filter_function, self._phones.keys())
            result = set()
            for i in lst:
                for j in self._phones[i]:
                    result.add(j)
            return tuple(result)
        else:
            return tuple()

    def find_by_phone_endswith(self, number, parsestr=True):
        """
        Finds a by phone number ending in all indexed vcards.

        :param      number:      The phone number ending
        :type       number:      str or int
        :param      parsestr:    remove all non-digit symbols(default: True)
        :type       parsestr:       boolean
        """
        if number in self._phones:
            return tuple(self._phones[number])

        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).endswith(str(number))

        lst = filter(filter_function, self._phones.keys())
        result = set()
        for i in lst:
            for j in self._phones[i]:
                result.add(j)
        return tuple(result)

    def find_by_phone_startswith(self, number, parsestr=True):
        """
        Finds a by start of phone number in all indexed vcards.

        :param      number:      Start of phone number
        :type       number:      str or int
        :param      parsestr:    remove all non-digit symbols(default: True)
        :type       parsestr:       boolean
        """
        if number in self._phones:
            return tuple(self._phones[number])

        def filter_function(x):
            if parsestr:
                value = strinteger(x)
            else:
                value = x
            return str(value).startswith(str(number))

        lst = filter(filter_function, self._phones.keys())
        result = set()
        for i in lst:
            for j in self._phones[i]:
                result.add(j)
        return tuple(result)

    def find_by_property(self, paramname, value, fullmatch=True):
        """
        Finds a by property name and value.

        :param      paramname:  The property name
        :type       paramname:  str
        :param      value:      The value
        :type       value:      str or list
        :param      fullmatch:  find by full match
        :type       fullmatch:  boolean
        """
        if paramname in self._params:
            if value in self._params[paramname] and fullmatch:
                return (self._params[paramname][value])
        if hasattr(value, "__iter__") and not isinstance(value, str):
            value = ";".join(value)

        def filter_function(x):
            if fullmatch:
                return x == value
            else:
                return value in x

        s = []
        if paramname in self._params:
            lst = list(filter(filter_function, self._params[paramname].keys()))
            for i in lst:
                for j in self._params[paramname][i]:
                    s.append(i)
        return tuple(set(s))

    def find_by_value(self, value, fullmatch=True):
        """
        Finds a by property value.

        :param      value:      The value
        :type       value:      str or list
        :param      fullmatch:  find by full match
        :type       fullmatch:  boolean
        """
        result = []
        for i in self._params:
            result += self.find_by_property(i, value, fullmatch)
        return tuple(set(result))

