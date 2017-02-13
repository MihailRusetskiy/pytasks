from functools import partial
from pprint import pprint
import functools


#def add_factory(x):
#    return partial(sum, [5])(x)


#add_factory = lambda y : sum([5, y])


def added5(y):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            return y + 5
        return inner
    return decorator

@added5(y=10)
def add_factory():
    return 5


add5 = add_factory(10)
pprint(add5)
