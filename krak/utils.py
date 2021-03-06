import sys
import functools

import pandas as pd

from . import units


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


def parse_quantity(value, default_units=None):
    if isinstance(value, pd.Series):
        array = value.values
        try:
            value = array.quantity
        except TypeError:
            value = units.registry.Quantity(array, '')

    if isinstance(value, units.registry.Unit):
        value = 1 * value
    elif not isinstance(value, units.registry.Quantity):
        value = units.registry.Quantity(value, '')

    if default_units is None:
        return value

    if not isinstance(default_units, units.registry.Unit):
        raise ValueError(f'Invalid default unit "{default_units}" provided')

    if value.dimensionless:
        value = value * default_units

    if value.dimensionality != default_units.dimensionality:
        raise ValueError(f'Invalid unit "{value.units}" provided')

    return value


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
