from itertools import cycle, zip_longest, chain, product
from collections import Iterable
from pprint import pprint

iters = ([0, 1, 2], 'mn', 'mnnnknjnjn')


def f(iters):
    yield from zip_longest(map(cycle, iters))


for i in f(iters):
    print(i)
