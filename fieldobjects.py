#!/usr/bin/python
# Original Author: Christopher Nyland
# Original Creation Date: 2012/08/08

import types
import exceptions
from collections import MutableSequence


class FieldObject(object):

    LineEditEditor = None
    ComboBoxEditor = 1
    CheckBoxEditor = 2
    DateEditEditor = 3
    SpinBoxEditor = 4
    DoubleSpinBoxEditor = 5

    def __init__(self, name, displayed=True, editable=True):
        self._name = name
        self._original_name = name
        self.name_editable = True
        self.required = False
        self._editor = None
        self._editable = editable
        self._displayed = displayed

    def __eq__(self, other):
        """ Magic function defining equality

        For the FieldObject class there are two forms of equality to be matched
        by one is standard python matching of hash values. The other match is
        matching the name of the field with a string. The function matches both
        and then returns an or of the results.

        """
        # First compare the hash and then the name and return an or of the
        # result
        hash_same = hash(self) == hash(other)
        name_same = self.name == other
        return (hash_same or name_same)

    def __ne__(self, other):
        """ Magic function defining inequality

        For the FieldObject class there are two forms of equality to be matched
        by one is standard python matching of hash values. The other match is
        matching the name of the field with a string. The function matches both
        and then returns an or of the results.

        """

        # First compare the hash and then the name and return and or of the
        # result
        hash_different = hash(self) != hash(other)
        name_different = self.name != other
        if hash_different:
            return name_different
        else:
            return hash_different
        return (hash_different or name_different)

    @property
    def editable(self):
        return self._editable

    @editable.setter
    def editable(self, value):
        self._editable = value

    @property
    def editor(self):
        return self._editor

    @editor.setter
    def editor(self, value):
        self._editor = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self.name_editable:
            self._name = value
        else:
            exceptions.ValueError("The name of this object cannot be set")

    @property
    def displayed(self):
        return self._displayed

    @displayed.setter
    def displayed(self, value):
        self._displayed = value

    @property
    def original_name(self):
        return self._original_name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class FieldObjectCopy(FieldObject):

    def __init__(self, name, copyof=None, required=False):
        super(FieldObjectCopy, self).__init__(name, required)
        self._copyof = copyof

    def setCopyOf(self, copyof):
        self._copyof = copyof

    def __hash__(self):
        return hash(self._copyof)

    @property
    def copyof(self):
        return self._copyof

    @property
    def editor(self):
        return self._copyof.editor

    @property
    def editable(self):
        return self._copyof.editable


class FieldObjectContainer(MutableSequence):

    def __init__(self, fieldobjs=None):
        if fieldobjs is None:
            self._fieldobjs = []
            return
        all_objs = [isinstance(k, FieldValue) for k in fieldobjs]
        all_str = [isinstance(k, str) for k in fieldobjs]
        if all(all_str):
            self._fieldobjs = [FieldObject(k) for k in fieldobjs]
        elif all(all_objs):
            self._fieldobjs = fieldobjs
        else:
            raise TypeError('Input fields must all be either '
                                      'FieldObject instances or strings')

    def __getitem__(self, key):
        if isinstance(key, FieldObject):
            key = key.name
        if isinstance(key, str) or isinstance(key, unicode):
            for k in self._fieldobjs:
                if k.name == key:
                    return k
        else:
            return self._fieldobjs[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        if isinstance(value, FieldObject):
            self._fieldobjs[key] = value
        else:
            self._fieldobjs[key] = FieldObject(str(value))

    def __delitem__(self, key):
        del self._fieldobjs[key]

    def __len__(self):
        return len(self._fieldobjs)

    def insert(self, index, value):
        if isinstance(value, FieldObject):
            self._fieldobjs.insert(index, value)
        else:
            self._fieldobjs.insert(index, FieldObject(str(value)))

    def append(self, value):
        if isinstance(value, FieldObject):
            self._fieldobjs.append(value)
        else:
            self._fieldobjs.append(FieldObject(str(value)))

    def index(self, value):
        if isinstance(value, str):
            names = [k.name for k in self._fieldobjs]
            return names.index(value)
        else:
            return self._fieldobjs.index(value)


class FieldValue(object):
    """

    This class exist so that I can hold on the to original data type that
    was input. It will always return that type. If the type is set as None then
    the type really isn't stored and the this class will act like any normal
    variable

    """

    _SENTINEL = object()

    def __init__(self, value=None, vtype=_SENTINEL):
        self._NUMTYPES = [types.IntType, types.FloatType, types.LongType,
                          types.ComplexType]
        self._value = value
        if vtype is self._SENTINEL:
            self._vtype = type(value)
        else:
            self._vtype = vtype

    @property
    def value(self):
        if self.type is types.NoneType:
            return self._value
        elif ((self.type in self._NUMTYPES) and
              (type(self._value) is types.StringType)):
            return sum(map(ord, self._value))
        else:
            return self.type(self._value)

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def type(self):
        return self._vtype

    @type.setter
    def type(self, value):
        if isinstance(value, types.TypeType):
            self._vtype = value
        else:
            raise exceptions.TypeError('NotAValidTypeError')
