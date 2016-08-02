#http://showmedo.com/videotutorials/video?fromSeriesID=151&name=1510250
"""
database.py

class to interface with a sqlite database

for python 2.4 or earlier download pysqlite from http://pysqlite.org/

"""

import os
import sqlite3
import csv
from datetime import datetime
from fieldobjects import FieldObject, FieldObjectContainer


class MileageDatabase(object):
    """ class to handle all python communication with a sqlite database file """

    displayFields = ['Date', 'Town', 'Odometer', 'Miles', 'Gallons', 'Price',
                     'Cost', 'MPG', 'fillup']
    saveFields = displayFields
    editableFields = ['Date', 'Town', 'Odometer', 'Gallons', 'Price', 'fillup']

    def __init__(self, db_file=':memory:', overwrite=False, setup=True):
        database_already_exists = os.path.exists(db_file)
        self.db_file = db_file
        self.db = sqlite3.connect(db_file)
        if (overwrite or not database_already_exists) and setup:
            self.setupDefaultData()

        # Set up the field object container
        self._fieldobjs = FieldObjectContainer()
        for field in self.displayFields:
            displayed = field in self.displayFields
            editable = field in self.editableFields
            self.fieldobjs.append(FieldObject(field, displayed, editable))

        # Field settings
        self.fieldobjs['Gallons'].editor = FieldObject.DoubleSpinBoxEditor
        self.fieldobjs['fillup'].editor = FieldObject.CheckBoxEditor

    def __len__(self):
        return self.select('SELECT count() FROM entries')[0][0]

    def __getitem__(self, key):
        cur = self.cursor()
        cur.row_factory = sqlite3.Row
        if isinstance(key, int):
            cur.execute('SELECT * from entries WHERE eid=(?)', (key,))
            row = cur.fetchone()
            out = row
        elif isinstance(key, tuple):
            idx = key[0]
            col = key[1].lower()
            if hasattr(self, col):
                method = getattr(self, col)
                out = method(idx)
            else:
                cur.execute('SELECT * from entries WHERE eid=(?)', (idx,))
                row = cur.fetchone()
                out = row[col]
        cur.close()
        return out

    def __setitem__(self, key, value):
        idx = key[0]
        col = key[1]
        if not col in self.editableFields:
            raise KeyError('{} is not an editable field'.format(col))
        sql = 'UPDATE entries SET {}=? WHERE eid=?'.format(col)
        self.execute(sql, (value, idx))

    @property
    def isInMemory(self):
        return self.db_file == ':memory:'

    @property
    def fields(self):
        return [k.name for k in self._fieldobjs]

    @property
    def fieldobjs(self):
        return self._fieldobjs

    # Database  Interaction #

    def select(self, sql, param=tuple()):
        """ select records from the database """
        cursor = self.cursor()
        cursor.execute(sql, param)
        records = cursor.fetchall()
        cursor.close()
        return records

    def insert(self, sql, params=tuple()):
        """ insert a new record to database and return the new primary key """
        print sql
        cursor = self.cursor()
        cursor.execute(sql, params)
        newID = cursor.lastrowid
        self.db.commit()
        cursor.close()
        return newID

    def execute(self, sql, params=tuple()):
        """ execute any SQL statement but no return value given """
        cursor = self.cursor()
        cursor.execute(sql, params)
        self.db.commit()
        cursor.close()

    def executemany(self, sql, params):
        """Execute the SQL command against all parameter sequences"""
        if not isinstance(params, list):
            raise TypeError('params must be list of tuples')
        cursor = self.cursor()
        cursor.executemany(sql, params)
        self.db.commit()
        cursor.close()

    def executescript(self, sql):
        """ execute any SQL script but no return value given """
        cursor = self.cursor()
        cursor.executescript(sql)
        self.db.commit()
        cursor.close()

    def cursor(self):
        cur = self.db.cursor()
#         cur.execute('PRAGMA foreign_keys=on')
        return cur

    def setupDefaultData(self):
        """ create the database tables and default values if it doesn't exist already """
        sql = """
            BEGIN TRANSACTION;
            DROP TABLE IF EXISTS Entries;
            CREATE TABLE IF NOT EXISTS Entries(
                eid INTEGER PRIMARY KEY,
                Date DATE,
                Town TEXT,
                Odometer REAL,
                Gallons REAL,
                Price REAL,
                Fillup BOOL,
                Linkback BOOL);
            COMMIT;
            """
        self.executescript(sql)

    def readcsv(self, csvfile):
        """Read a csv file into the database"""
        self.setupDefaultData()
        with open(csvfile, 'rb') as f:
            reader = csv.reader(f)
            header = reader.next()
            data = [row for row in reader]
        lhead = [x.lower() for x in header]

        sql_params = []
        for k, d in enumerate(data):
            linkback = False
            date = datetime.strptime(d[lhead.index('date')], '%m/%d/%y').date()
            town = d[lhead.index('town')]
            gallons = d[lhead.index('gallons')]
            if k > 0 and gallons:
                gallons = float(gallons)
                linkback = True

            odometer = d[lhead.index('odometer')]
            if odometer:
                odometer = float(odometer)
            price = d[lhead.index('price')]
            if price:
                price = float(price.replace('$', ''))
            fillup = d[lhead.index('fillup')].lower() == 'true'
            sql_params.append((date, town, odometer, gallons, price, fillup,
                               linkback))

        sql = 'INSERT INTO Entries (Date, Town, Odometer, Gallons,' + \
                            'Price, Fillup, Linkback) VALUES (?,?,?,?,?,?,?)'
        self.executemany(sql, sql_params)

    # Basic Queries #

    def get_value(self, valname, idx):
        sql = 'SELECT {} FROM entries WHERE entries.eid=(?)'.format(valname)
        return self.select(sql, (idx,))[0][0]

    def date(self, idx):
        return self.get_value('date', idx)

    def town(self, idx):
        return self.get_value('town', idx)

    def towns(self):
        """Returns a list of all towns"""
        sql = 'SELECT town FROM entries'
        return [k[0] for k in self.select(sql)]

    def odometer(self, idx):
        odo = self.get_value('odometer', idx)
#         try:
#             odo = float(self.get_value('odometer', idx))
#         except ValueError:
#             odo = None
        return odo

    def price(self, idx):
        return self.get_value('price', idx)

    def gallons(self, idx):
        return self.get_value('gallons', idx)

    def fillup(self, idx):
        return self.get_value('fillup', idx)

    def linkback(self, idx):
        return self.get_value('linkback', idx)

    # Advance Queries #

    # def basedex(self, idx):
        # """Returns the base index for calculating the mileage for
        # the given row. Returns None if a valid base doesn't exist"""
        # bdex = idx
        # while True:
            # if not self.linkback(bdex):
                # return None
            # bdex -= 1
            # if self.fillup(bdex):
                # return bdex

    def basedex(self, idx):
        sql = """SELECT MAX(e1.eid)
                    FROM entries e1
                    WHERE e1.eid < ?
                      AND e1.fillup
                      AND NOT EXISTS
                        (SELECT *
                         FROM entries e2
                         WHERE e2.eid < ?
                           AND e2.eid > e1.eid
                           AND NOT e2.linkback)"""

        bdex = self.select(sql, (idx, idx))
        if len(bdex) > 1:
            raise Exception('Too many solutions found: {}'.format(bdex))
        return bdex[0][0]

#     def sum_gallons(self, thisdex):
#         """Returns the total gallons of fuel from this entry and all previous
#         non-fillup entries.
#
#         If this entry cannot be linked to a previous entry that was a fillup,
#         it returns None, meaning that it can't be determined how many gallons
#         were used.
#         """
#         idx = thisdex
#         value = self.gallons(thisdex)
#         while True:
#             if not self.linkback(idx):
#                 print 'linkback return'
#                 return None
#             lastdex = idx - 1
#             if self.fillup(lastdex):
#                 break
#             else:
#                 igal = self.gallons(lastdex)
#                 value += igal
#                 idx -= 1
#         return value

    def sum_gallons(self, idx):
        """Returns the total gallons of fuel from this entry and all previous
        non-fillup entries.

        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning that it can't be determined how many gallons
        were used.
        """
        sql = """SELECT SUM(gallons)
                 FROM entries
                 WHERE eid <= ?
                     AND eid > ?"""
        return self.select(sql, (idx, self.basedex(idx)))[0][0]

#     def miles(self, idx):
#         """Returns the miles driven since the last fillup
#
#         If this entry cannot be linked to a previous entry that was a fillup,
#         it returns None, meaning there is no bases for mileage calculations.
#         """
#         linkback = self.linkback(idx)
#         if not linkback:
#             return None
#         curodo = self.odometer(idx)
#         pidx = idx - 1
#         while True:
#             linkback = self.linkback(pidx)
#             fillup = self.fillup(pidx)
#             # If you find a fillup, break and return miles
#             if fillup:
#                 lastodo = self.odometer(pidx)
#                 break
#             # Otherwise if you can, go back one and try again
#             elif linkback:
#                 pidx -= 1
#             # Otherwise return None (A link to a fillup can't be made)
#             else:
#                 return  None
#         return curodo - lastodo

    def miles(self, idx):
        """Returns the miles driven since the last fillup

        If this entry cannot be linked to a previous entry that was a fillup,
        it returns None, meaning there is no bases for mileage calculations.
        """
        if not self.linkback(idx):
            return
        od1 = self.odometer(self.basedex(idx))
        od2 = self.odometer(idx)
        if None not in (od1, od2):
            return od2 - od1

    def mpg(self, idx):
        """Returns the calculated MPG for a given index"""
        miles = self.miles(idx)
        gallons = self.sum_gallons(idx)
        if miles and gallons:
            return miles/float(gallons)

    def cost(self, idx):
        """Returns the calculated fuel cost for the given entry"""
        price = self.price(idx)
        gallons = self.gallons(idx)
        if price and gallons:
            return round(price * gallons, 2)

    # Model Interface #

    def addEntry(self, date, town, odometer, gallons, price, fillup,
                 linkback):
        """Add an entry to the database"""
        args = (date, town, odometer, gallons, price, fillup, linkback)
        sql = """INSERT INTO entries(date, town, odometer, gallons, price,
                                     fillup, linkback)
                 VALUES (?,?,?,?,?,?,?)"""
        eid = self.insert(sql, args)
        return eid

    def removeEntry(self, idx):
        """Remove the entry at the given index"""
        #This should be improved to make sure that if an entry is removed,
        #there are no other entries with dependencies.
        print 'Removing entry', idx
        self.execute('DELETE FROM entries WHERE eid=?', (idx,))

if __name__ == '__main__':
#     db = MileageDatabase('newdatabase2.db')
#     db.readcsv('JettaFuelRecord.csv')
    db = MileageDatabase('biggap.db')
#     db.readcsv('TestFileWithBigGaps.csv')

    #Basic odometer queries prior to implementing miles method
#     odometer, prev = db.select('SELECT odometer, previous FROM entries where eid=3')[0]
#     oldodometer = db.select('SELECT odometer FROM entries WHERE eid=(?)', (prev,))[0][0]
#     print oldodometer, odometer, odometer - oldodometer

#     #Test some calculations
#     for k in range(21, 27):
# #         print k, db.miles(k)
# #         print k, db.date(k), db.town(k), db.price(k), db.gallons(k), db.miles(k)
#         print k, db.sum_gallons(k), db.cost(k)

#     #Test linkback and fillup functionality
#     for k in range(1, 27):
#         print k, db.fillup(k), db.linkback(k)

    #Write query that will find the mileage basis entry for any given entry
    #25 basis should be 23
    #The following returns 24 just for test purposes. If the last AND is AND NOT
    #it does what we want.
#     print db.select('SELECT eid FROM entries e2 WHERE e2.eid < 25 AND \
#                     e2.eid > 23 AND e2.linkback')
#     print db.select('SELECT eid FROM entries e2 WHERE e2.eid < ? AND \
#                     e2.eid > ? AND e2.linkback', (25, 23))

#     #So use the modified version of above in a larger query to find the basis
#     entry = 25
#     print db.select('SELECT MAX(eid) FROM entries e1 WHERE eid < ? AND fillup \
#      AND NOT EXISTS (SELECT * FROM entries e2 WHERE e2.eid < ? AND \
#                     e2.eid > e1.eid AND NOT e2.linkback)', (entry, entry))
#     print db.basedex(entry)

#     #Test for sum_gallons using new basedex
#     print db.basedex(4)
#     print db.miles(4)
#     print db.select('SELECT SUM(gallons) FROM entries WHERE (eid <= ? AND eid > ?)',
#                      (4, db.basedex(4)))
#     print db.sum_gallons(4)

#     #Test creating a temporary table for further query
#     cur = db.db.cursor()
#     cur.execute('CREATE TEMP TABLE search as SELECT * FROM entries WHERE eid=5')
#     print cur.execute('SELECT * FROM search').fetchall()
#     cur.close()

#     #Test __getitem__
#     print db[1]
#     print db[1, 'date']

    #Misc Tests
    # idx = len(db)
    # db.removeEntry(idx)

    db[4, 'Town'] = 'Belmaria'
