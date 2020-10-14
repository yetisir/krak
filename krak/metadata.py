from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
import pint_pandas

from . import select, utils, units, config, materials


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

    def get_empty_array(self, length, value):
        return np.empty(length, dtype=self.get_dtype(value.magnitude))


class String(DataType):
    def get_dtype(self, value):
        return f'<U{self.length(value)}'

    def length(self, value):
        if isinstance(value, units.registry.Quantity):
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
        if isinstance(value, pd.Series):
            value = value.values
        return units.registry.Quantity(value, '')


class Float(DataType):
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
        dataframe = self.dataframe
        columns = []
        for column in dataframe.columns:
            values = dataframe[column].values
            if isinstance(values, pint_pandas.pint_array.PintArray):
                units = dataframe[column].values.units
                columns.append((column, f'[{units:~}]'))
            else:
                columns.append((column, ''))

        dataframe.columns = pd.MultiIndex.from_tuples(
            columns, names=('name', 'unit'))
        return repr(dataframe)

    def __getitem__(self, keys):
        name, selection = self._validate_index_keys(keys)

        return self.dataframe[name][
            selection.query(self._mesh_binding(), self.component)]

    def __setitem__(self, keys, value):
        value = self.dtype.parse_value(value)

        name, selection = self._validate_index_keys(keys)

        array_name = f'{self.prefix}:{name}'

        if array_name in self.data_arrays.keys():
            self._update_array(array_name, value, selection)
        else:
            self._create_array(array_name, value, selection)

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

    @property
    def dataframe(self):
        data_arrays = self.data_arrays

        data = {}
        for column, array_units in self._array_units.items():
            prefix, *column_name = column.split(':')
            if prefix != f'{self.prefix}':
                continue
            column_name = ':'.join(column_name)

            if array_units.dimensionless:
                data[column_name] = pd.Series(
                    data_arrays[column])
                continue

            array = config.settings.units.convert(
                data_arrays[column] * array_units)
            units = f'{array.units:~}'
            data[column_name] = pd.Series(
                array.magnitude, dtype=f'pint[{units}]')

        return pd.DataFrame(data, index=pd.RangeIndex(self.length, name='id'))

    def bind(self, mesh_binding):
        self._mesh_binding = mesh_binding

    def _create_array(self, array_name, value, selection):
        array = self.dtype.get_empty_array(self.length, value)
        selection_mask = selection.query(self._mesh_binding(), self.component)
        array[selection_mask] = value.magnitude
        self.data_arrays[array_name] = array
        self._array_units[array_name] = value.units

    def _update_array(self, array_name, value, selection):
        data_arrays = self.data_arrays

        if isinstance(selection, select.All):
            self._array_units[array_name] = value.units

        if value.units != self._array_units[array_name]:
            raise ValueError(f'Incompatible units for "{value}"')

        array = self.dtype.cast_array(data_arrays[array_name], value)
        selection_mask = selection.query(self._mesh_binding(), self.component)
        array[selection_mask] = value.magnitude
        data_arrays[array_name] = array

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
        self.models = CellMetadata('property', dtype=String())
        self.models.bind(self._mesh_binding)

    def __setitem__(self, keys, value):
        name, selection = self._validate_index_keys(keys)
        array_name = f'{self.prefix}:{name}'

        all_materials = self._available_materials()
        if name == 'model':
            if value not in all_materials.keys():
                raise ValueError(f'Model name {value} not recognized')
            self.models[name, selection] = value
            self._array_units[array_name] = units.Unit('')
            return

        properties = self._available_properties()
        if name in properties.keys():
            value = properties[name](value).quantity
            super().__setitem__(keys, value)
        else:
            raise ValueError(f'Property name {name} not recognized')

    def _available_materials(self):
        all_materials = utils.get_all_subclasses(materials.BaseMaterial)
        return {material.name: material for material in all_materials}

    def _available_properties(self):
        properties = {}
        for material in self._available_materials().values():
            properties.update(material.property_types)

        return properties


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
