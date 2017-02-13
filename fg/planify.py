from collections import Iterable

items = 'abc', 3, [8, ('x', 'y'), [100, [99, [98, [97]]]]]


def planify(items, ignore_types=(str, bytes)):
    planify.__dict__['called_times'] = planify.__dict__.get('called_times', 0) + 1
    flatten_items = []
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, ignore_types):
            flatten_items.extend(planify(x))
        else:
            flatten_items.append(x)
    return flatten_items


def planify2(items, ignore_types=(str, bytes)):
    for x in items:
        if isinstance(x, Iterable) and not isinstance(x, ignore_types):
            yield from planify2(x)
        else:
            yield x


print(planify(items))
print(type(planify2(items)))
print(list(planify2(items)))
