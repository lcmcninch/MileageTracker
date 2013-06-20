# $Rev$
# $LastChangedDate$
# $URL$
__version__ = '$Id$'.replace('$', '')

from os import linesep


class mileageList(list):

    def __init__(self, entries=[]):
        super(mileageList, self).__init__()
        self.extend(entries)
        self.displayFields = mileageEntry.displayFields
        self.saveFields = mileageEntry.saveFields
        self.editableFields = mileageEntry.editableFields

    def write(self, fid, ftype='csv', delimiter=','):
        itemString = lambda x: '' if x is None else str(x)
        if ftype == 'csv':
            header = self.saveFields
            fid.write(delimiter.join(header))
            fid.write(linesep)
            for x in self:
                out = [itemString(x[k]) for k in header]
                fid.write(delimiter.join(out))
                fid.write(linesep)


class mileageEntry(object):

    displayFields = ['Date', 'Town', 'Odometer', 'Miles', 'Gallons', 'Price',
                     'Cost', 'MPG']
    saveFields = displayFields + ['fillup']
    editableFields = ['Date', 'Town', 'Odometer', 'Gallons', 'Price']

    def __init__(self, date, location, odometer, gallons, price, fillup,
                 previous=None):
        self._date = date
        self._location = location
        self._odometer = float(odometer) if odometer else None
        self._gallons = float(gallons) if gallons else None
        self._price = float(price) if price else None
        self.fillup = (False if (isinstance(fillup, str) and
                                fillup.lower() in ['false', 'f', '0']) else
                                bool(fillup))
        self.previous = previous

    def __getitem__(self, key):
        return self.__getattribute__(key.lower())

    def __setitem__(self, key, value):
        self.__setattr__(key.lower(), value)

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
        self._odometer = float(value)

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = float(value.replace('$', ''))

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
        return addPrevious(self, self.gallons, 'gallons')

    @property
    def miles(self):
        """Returns the miles driven since the last fillup

        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning there is no basis for mpg calculations.
        """
        if not self.odometer:
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
        return self.miles/float(self.sum_gallons)

    @property
    def cost(self):
        if self._price and self._gallons:
            return round(self._price * self._gallons, 2)


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
    m = mileageEntry('2011/12/21', 'Stevensville', 19321, 13.4, 3.23, False)
    m1 = mileageEntry('2011/12/22', 'Stevensville', 19621, 12.1, 3.43, False,
                      m)
    m2 = mileageEntry('2011/12/23', 'Stevensville', 19921, 11.4, 3.13, True,
                      m1)
#    print m2.sum_gallons
    print m2.miles
#    print m1.mpg, m2.mpg
#    print m2['mpg']
