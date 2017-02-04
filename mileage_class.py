from os import linesep
from fieldobjects import FieldObject, FieldObjectContainer


class mileageList(list):

    def __init__(self, entries=[]):
        super(mileageList, self).__init__()
        self.extend(entries)
        self.displayFields = mileageEntry.displayFields
        self.saveFields = mileageEntry.saveFields

        # Set up the field object container
        self._fieldobjs = FieldObjectContainer()
        for field in self.displayFields:
            displayed = field in self.displayFields
            editable = field in self.editableFields
            self.fieldobjs.append(FieldObject(field, displayed, editable))

        # Field settings
        self.fieldobjs['Gallons'].editor = FieldObject.DoubleSpinBoxEditor
        self.fieldobjs['fillup'].editor = FieldObject.CheckBoxEditor
        self.fieldobjs['Date'].editor = FieldObject.DateEditEditor

    def removeEntry(self, index):
        """ Removes and returns the given index """
        return self.pop(index)

    def append(self, value):
        value.container = self
        list.append(self, value)

    def write(self, fid, ftype='csv', delimiter=','):
        def itemString(x):
            return '' if x is None else str(x)
        if ftype == 'csv':
            header = self.saveFields
            fid.write(delimiter.join(header))
            fid.write(linesep)
            for x in self:
                out = [itemString(x[k]) for k in header]
                fid.write(delimiter.join(out))
                fid.write(linesep)
        elif ftype == 'mtf':
            sql_params = [(x.date, x.town, x.odometer, x.gallons, x.price,
                           x.compareprice, x.fillup, x.previous is not None)
                          for x in self]
            sql = """INSERT INTO Entries (Date, Town, Odometer, Gallons,
                     Price, ComparePrice, Fillup, Linkback) VALUES (?,?,?,?,?,?,?,?)"""
            fid.executemany(sql, sql_params)

    def getFieldByName(self, value):
        for fieldobj in self.fieldobjs:
            if fieldobj == value:
                return fieldobj

    @property
    def fields(self):
        return [k.name for k in self._fieldobjs]

    @property
    def fieldobjs(self):
        return self._fieldobjs

    @property
    def editableFields(self):
        return mileageEntry.editableFields


class mileageEntry(object):

    displayFields = ['Date', 'Town', 'Odometer', 'Miles', 'Gallons', 'Price',
                     'Cost', 'MPG', 'fillup', 'ComparePrice', 'Savings', 'PreviousDex']
    saveFields = displayFields
    editableFields = ['Date', 'Town', 'Odometer', 'Gallons', 'Price', 'fillup',
                      'ComparePrice']
    compareMPG = 31.5

    def __init__(self, date, location, odometer, gallons, price, fillup,
                 previous=None, compareprice=None):
        self._date = date
        self._location = location
        self._odometer = float(odometer) if odometer else None
        self._gallons = float(gallons) if gallons else None
        self._price = float(price) if price else None
        self.fillup = (False if (isinstance(fillup, str) and
                                 fillup.lower() in ['false', 'f', '0']) else
                       bool(fillup))
        self.previous = previous
        self._compareprice = float(compareprice) if compareprice else None

    def __getitem__(self, key):
        return self.__getattribute__(str(key).lower())

    def __setitem__(self, key, value):
        self.__setattr__(key.lower(), value)

    @property
    def previousdex(self):
        if self.previous:
            return self.container.index(self.previous)

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        self._date = str(value)

    @property
    def town(self):
        return self._location

    @town.setter
    def town(self, value):
        self._location = str(value)

    @property
    def odometer(self):
        return self._odometer

    @odometer.setter
    def odometer(self, value):
        try:
            self._odometer = float(value)
        except ValueError:
            self._odometer = None

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        try:
            value = value.replace('$', '')
        except:
            pass
        finally:
            self._price = float(value)

    @property
    def gallons(self):
        """Returns the gallons of fuel from this entry only. """
        return self._gallons

    @gallons.setter
    def gallons(self, value):
        self._gallons = float(value)

    @property
    def sum_gallons(self):
        """Returns the total gallons of fuel from this entry and all previous
        non-fillup entries.

        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning that it can't be determined how many gallons
        were used.
        """
        return addPrevious(self, self.gallons, 'sum_gallons')

    @property
    def miles(self):
        """Returns the miles driven since the last fillup

        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning there is no basis for mpg calculations.
        """
        if not self.odometer or not self.fillup:
            return None
        prev_obj = self.previous
        while True:
            if not prev_obj:
                return None
            p = prev_obj.odometer
            if prev_obj.fillup and p:
                break
            prev_obj = prev_obj.previous
        return self.odometer - p

    @property
    def mpg(self):
        if not self.fillup or self.miles is None or self.gallons is None:
            return None
        return self.miles / float(self.sum_gallons)

    @property
    def cost(self):
        if self._price and self._gallons:
            return round(self._price * self._gallons, 2)

    @property
    def compareprice(self):
        return self._compareprice

    @compareprice.setter
    def compareprice(self, value):
        try:
            value = value.replace('$', '')
        except:
            pass
        finally:
            self._compareprice = float(value)

    @property
    def savings(self):
        if self.compareprice:
            return self.miles/self.compareMPG*self.compareprice - self.cost


def addPrevious(obj, value, field):
    """
    Recursively adds the value of previous non-fillup entries.
    If the given object has no previous reference, returns False
    """
    if not obj.previous:
        return None
    if not obj.previous.fillup:
        p = getattr(obj.previous, field)
        if p is None:
            return None
        value += p
    return value

if __name__ == "__main__":
    container = mileageList()
    m = mileageEntry('2011/12/21', 'Stevensville', 19321, 13.4, 3.23, False)
    m1 = mileageEntry('2011/12/22', 'Stevensville', 19621, 12.1, 3.43, False,
                      m)
    m2 = mileageEntry('2011/12/23', 'Stevensville', 19921, 11.4, 3.13, True,
                      m1, compareprice=1.25)
    container.append(m)
    container.append(m1)
    container.append(m2)
#    print m2.sum_gallons
    print m2.miles
    print m2.compareprice
#    print m1.mpg, m2.mpg
#    print m2['mpg']
