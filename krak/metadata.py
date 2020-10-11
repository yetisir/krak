from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from . import select


class DataType(ABC):
    @abstractmethod
    def get_dtype(self):
        raise NotImplementedError

    @abstractmethod
    def cast_array(self):
        raise NotImplementedError

    def get_empty_array(self, length, value):
        return np.empty(length, dtype=self.get_dtype(value))


class String(DataType):
    def get_dtype(self, value):
        return f'<U{self.length(value)}'

    def length(self, value):
        if isinstance(value, str):
            return len(value)
        else:
            return max(len(i) for i in value)

    def cast_array(self, array, value):
        if self.length(value) > array.dtype.itemsize // array.dtype.alignment:
            return np.array(array, dtype=self.get_dtype(value))
        else:
            return array


class Float(DataType):
    def get_dtype(self, value):
        return 'float'

    def cast_array(self, array, value):
        return array


class Metadata(ABC):
    def __init__(self, prefix, dtype=Float(), mesh_binding=None):
        self.bind(mesh_binding)
        self.prefix = prefix
        self.dtype = dtype

    def __repr__(self):
        return repr(self.dataframe)

    def __getitem__(self, keys):
        name, selection = self._validate_index_keys(keys)
        return self.dataframe[name][
            selection.query(self._mesh_binding(), self.component)]

    def __setitem__(self, keys, value):
        name, selection = self._validate_index_keys(keys)
        array_name = f'{self.prefix}:{name}'

        data_arrays = self.data_arrays

        if array_name in data_arrays.keys():
            array = self.dtype.cast_array(data_arrays[array_name])
        else:
            array = self.dtype.get_empty_array(self.length, value)

        array[selection.query(self._mesh_binding(), self.component)] = value
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

    @property
    def dataframe(self):
        data_arrays = self.data_arrays

        columns = [
            name for name in data_arrays.keys()
            if name.split(':')[0] == f'{self.prefix}']
        data = {
            ':'.join(column.split(':')[1:]): data_arrays[column]
            for column in columns}
        return pd.DataFrame(
            data, index=pd.RangeIndex(self.length, name='id'))


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


class CellGroups(CellMetadata):
    def __init__(self, **kwargs):
        super().__init__('slot', dtype=String(), **kwargs)


class CellFields(CellMetadata):
    def __init__(self, **kwargs):
        super().__init__('field', **kwargs)


class PointGroups(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('slot', dtype=String(), **kwargs)


class PointFields(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('field', **kwargs)


class BoundaryConditions(PointMetadata):
    def __init__(self, **kwargs):
        super().__init__('bc', **kwargs)
