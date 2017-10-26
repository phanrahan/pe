from random import randint
from itertools import product

__all__ = ['random', 'complete']

def random(func, n, width):
    max = 1 << width
    tests = []
    for i in range(n):
        x = randint(0,max)
        y = randint(0,max)
        test = [x, y]
        result = func(*test)
        test.append(result[0])
        tests.append(test)
    return tests

def complete(func, n, width):
    max = 1 << width
    tests = []
    for i in range(n):
        for j in range(n):
            test = [i, j]
            result = func(*test)
            test.append(result[0])
            tests.append(test)
    return tests
