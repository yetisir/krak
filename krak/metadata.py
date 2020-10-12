from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
import pint

from . import select, utils, units, config


class DataType(ABC):
    @abstractmethod
    def get_dtype(self, value):
        raise NotImplementedError

    @abstractmethod
    def cast_array(self, array, value):
        raise NotImplementedError

    @abstractmethod
    def parse_value(self, value):
        raise NotImplementedError

    @property
    @abstractmethod
    def units(self):
        raise NotImplementedError

    def get_empty_array(self, length, value):
        return np.empty(length, dtype=self.get_dtype(value.magnitude))


class String(DataType):
    units = False

    def get_dtype(self, value):
        return f'<U{self.length(value)}'

    def length(self, value):
        if isinstance(value, pint.Quantity):
            value = value.magnitude

        if isinstance(value, str):
            return len(value)
        else:
            try:
                return max(len(i) for i in value)
            except TypeError:
                return 8

    def cast_array(self, array, value):
        if self.length(value) > array.dtype.itemsize // array.dtype.alignment:
            try:
                return np.array(array, dtype=self.get_dtype(value))
            except TypeError:
                raise TypeError('Unsupported type for metadata')
        else:
            return array

    def parse_value(self, value):
        return pint.Quantity(value, '')


class Float(DataType):
    units = True

    def get_dtype(self, value):
        return 'float'

    def cast_array(self, array, value):
        return array

    def parse_value(self, value):
        value = utils.parse_quantity(value)
        return units.SI().convert(value)

    def get_empty_array(self, length, value):
        array = super().get_empty_array(length, value)
        array[:] = np.nan
        return array


class Metadata(ABC):
    def __init__(self, prefix, dtype=Float(), mesh_binding=None):
        self.bind(mesh_binding)
        self.prefix = prefix
        self.dtype = dtype

        self._array_units = {}

    def __repr__(self):
        return repr(self.data())

    def __getitem__(self, keys):
        name, selection = self._validate_index_keys(keys)

        return self.data(name)[
            selection.query(self._mesh_binding(), self.component)]

    def __setitem__(self, keys, value):
        value = self.dtype.parse_value(value)

        name, selection = self._validate_index_keys(keys)

        array_name = f'{self.prefix}:{name}'

        if array_name in self.data_arrays.keys():
            self._update_array(array_name, value, selection)
        else:
            self._create_array(array_name, value, selection)

    def _create_array(self, array_name, value, selection):
        array = self.dtype.get_empty_array(self.length, value)
        array[selection.query(
            self._mesh_binding(), self.component)] = value.magnitude
        self.data_arrays[array_name] = array
        self._array_units[array_name] = value.units

    def _update_array(self, array_name, value, selection):
        data_arrays = self.data_arrays

        if isinstance(selection, select.All):
            self._array_units[array_name] = value.units

        if value.units != self._array_units[array_name]:
            raise ValueError(f'Incompatible units for "{value}"')

        array = self.dtype.cast_array(data_arrays[array_name], value)
        array[selection.query(
            self._mesh_binding(), self.component)] = value.magnitude
        data_arrays[array_name] = array

    @property
    @abstractmethod
    def component(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def data_arrays(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def length(self):
        raise NotImplementedError

    def _validate_index_keys(self, keys):
        if not isinstance(keys, tuple):
            keys = (keys, select.All())
        if len(keys) == 1:
            keys = (keys, select.All())
        elif len(keys) == 0 or len(keys) > 2:
            raise ValueError('Invalid number of metadata indices')

        if not isinstance(keys[0], str):
            raise TypeError('First metadata index must be a string')
        if not isinstance(keys[1], select.BaseRange):
            raise TypeError('Second metadata index must be a Range object')

        return keys

    def bind(self, mesh_binding):
        self._mesh_binding = mesh_binding

    def data(self, name=None):
        data_arrays = self.data_arrays

        data = {}
        for column in data_arrays.keys():
            prefix, *column_name = column.split(':')
            if prefix != f'{self.prefix}':
                continue
            column_name = ':'.join(column_name)

            if not self.dtype.units:
                data[f'{column_name}'] = data_arrays[column]
                continue

            array = config.settings.units.convert(
                data_arrays[column] * self._array_units[column])
            units = f'{array.units:~}'
            index = f'{column_name} [{units}]'
            data[index] = array.magnitude
            if name == column_name:
                break

        dataframe = pd.DataFrame(
            data, index=pd.RangeIndex(self.length, name='id'))
        if name is None:
            return dataframe
        else:
            return dataframe[index]


class CellMetadata(Metadata):
    component = 'cells'

    @property
    def data_arrays(self):
        return self._mesh_binding().pyvista.cell_arrays

    @property
    def length(self):
        return len(self._mesh_binding().cells)


class PointMetadata(Metadata):
    component = 'points'

    @property
    def data_arrays(self):
        return self._mesh_binding().pyvista.point_arrays

    @property
    def length(self):
        return len(self._mesh_binding().points)


class Properties(CellMetadata):
    def __init__(self, **kwargs):
        super().__init__('property', **kwargs)


class CellSets(CellMetadata):
    def __init__(self, **kwargs):
        super().__init__('set', dtype=String(), **kwargs)


class CellFields(CellMetadata):
    def __init__(self, **kwargs):
        super().__init__('field', **kwargs)


class PointSets(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('set', dtype=String(), **kwargs)


class PointFields(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('field', **kwargs)


class BoundaryConditions(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('bc', **kwargs)
