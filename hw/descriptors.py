from datetime import datetime
from hw.fields import PhoneField, NameField, BirthdayField
from hw.miscripts import DocAPI
from hw.ormapi import Model, PhoneField, NameField, BirthdayField


class Person(object):
    name = NameField()
    birthday = BirthdayField()
    phone = PhoneField()

mihail = Person()
mihail.name = 'Mihail'
mihail.birthday = datetime.strptime("1996-05-01", "%Y-%m-%d")
mihail.phone = '375 29 3401416'

#mihail.name = None
#mihail.birthday = '1996-05-01'
#mihail.phone = '375 2 3401416'


class Foo(object):
    __doc__ = DocAPI()

    def __init__(self, x):
        self.x = x

    def meth(self, y):
        """Multiplies two values self.x and y."""
        return self.x * y

docapidesc = Foo()


class Person(Model):
    __table__ = "persons"
    name = NameField()
    birthday = BirthdayField()
    phone = PhoneField()

mihail = Person()
mihail.name = 'Mihail'
mihail.birthday = datetime.strptime("1996-05-01", "%Y-%m-%d")
mihail.phone = '375 29 3401416'
