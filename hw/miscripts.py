class DocAPI:
    def __init__(self, x):
        self.x = x

    def __get__(self, instance, owner):
        return instance.__dict__['_name'] if '_name' in instance.__dict__ else None

    def __set__(self, instance, value):
        if isinstance(value, str):
            instance.__dict__['_name'] = value
        else:
            raise TypeError('incorrect name format')

    def __delete__(self, instance):
        del instance.__dict__['_name']
