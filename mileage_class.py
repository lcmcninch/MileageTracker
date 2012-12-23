#import QtCore, QtGui

class mileageList(list):
    pass
    

class mileageEntry(object):
    def __init__(self, date, location, odometer, gallons, price, fillup,
                 previous=None):
        self._date = date
        self._location = location
        self._odometer = odometer
        self._gallons = gallons
        self._price = price
        self.fillup = fillup
        self.previous = previous
    
    def __getitem__(self, key):
        return self.__getattribute__(key.lower())
    
    @property
    def date(self):
        return self._date
    
    @property
    def town(self):
        return self._location
    
    @property
    def odometer(self):
        return self._odometer
    
    @property
    def price(self):
        return self._price
    
    @property
    def gallons(self):
        """Returns the gallons of fuel from this entry and all previous
        non-fillup entries.
        
        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning that it can't be determined how many gallons
        were used.
        """
        return addPrevious(self, self._gallons, 'gallons')
    
    @property
    def miles(self):
        """Returns the miles driven since the last fillup
        
        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning there is no basis for mpg calculations.
        """
        if not self.previous:
            return None
        m = self.odometer - self.previous.odometer
        return addPrevious(self, m, 'miles')
    
    @property
    def mpg(self):
        if not self.fillup or self.miles is None or self.gallons is None:
            return None
        return self.miles/float(self.gallons)


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
    m = mileageEntry((2011, 12, 21), 'Stevensville', 19321, 13.4, 3.23, True)
    m1 = mileageEntry((2011, 12, 22), 'Stevensville', 19621, 12.1, 3.43, False,
                      m)
    m2 = mileageEntry((2011, 12, 23), 'Stevensville', 19921, 11.4, 3.13, True,
                      m1)
    print m2.gallons
    print m2.miles
    print m1.mpg, m2.mpg
    print m2['mpg']