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


def validate_positive(value, parameter):
    error = ValueError(
        f'Parameter "{parameter}" must be a positive number')
    try:
        float_value = float(value)
    except TypeError:
        return None
    except ValueError:
        raise error

    if float_value < 0:
        raise error

    return float_value


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
