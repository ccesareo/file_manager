from collections import defaultdict


def fm_groupby(iterable, key):
    result = defaultdict(list)
    for item in iterable:
        result[key(item)].append(item)
    return result
