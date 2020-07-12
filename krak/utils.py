import sys
import functools


def cli_args(function):

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        if 'args' not in kwargs:
            return function(*args, **kwargs)

        if kwargs['args'] is None:
            kwargs['args'] = sys.argv[1:]
            return function(*args, **kwargs)

    return wrapper


def assign_parent(function):

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        result.parents.append(args[0])
        return result

    return wrapper
