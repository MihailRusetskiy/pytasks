import re
from datetime import date, datetime


class NameField:
    def __init__(self):
        self.prop = None

    def __get__(self, instance, owner):
        return instance.__dict__['_name'] if '_name' in instance.__dict__ else None

    def __set__(self, instance, value):
        if isinstance(value, str):
            instance.__dict__['_name'] = value
        else:
            raise TypeError('incorrect name format')

    def __delete__(self, instance):
        del instance.__dict__['_name']


class BirthdayField:
    def __init__(self):
        self.prop = None

    def __get__(self, instance, owner):
        return instance.__dict__['_bd'] if '_bd' in instance.__dict__ else None

    def __set__(self, instance, value):
        if isinstance(value, datetime) or isinstance(value, date):
            instance.__dict__['_bd'] = value
        else:
            raise TypeError('incorrect birthday format')

    def __delete__(self, instance):
        del instance.__dict__['_bd']


class PhoneField:
    def __init__(self):
        self.prop = None

    def __get__(self, instance, owner):
        return instance.__dict__['_phone'] if '_phone' in instance.__dict__ else None

    def __set__(self, instance, value):
        phonePattern = re.compile(r'^(\d{3}) (\d{2}) (\d{7})$')
        if phonePattern.search(value):
            instance.__dict__['_phone'] = value
        else:
            raise ValueError('incorrect phone number')

    def __delete__(self, instance):
        del instance.__dict__['_phone']
