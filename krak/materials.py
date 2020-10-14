from abc import ABC, abstractmethod

import pandas as pd

from . import strength, properties


class BaseMaterial(ABC):

    def __repr__(self):
        return repr(pd.Series(self.properties))

    @property
    def properties(self):
        properties = {}
        for cls in self.__class__.__mro__:
            if hasattr(cls, 'property_types') and cls != BaseMaterial:
                properties.update(cls.property_types)
        properties = {
            name: getattr(self, name) for name in properties.keys()}
        return properties

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def property_types(self):
        raise NotImplementedError


class Null(BaseMaterial):
    name = 'null'
    property_types = {}


class RigidBody(BaseMaterial):
    name = 'rigid'
    property_types = {
        'density': properties.Density,
    }

    def __init__(self, density, **kwargs):
        super().__init__(**kwargs)
        self.density = density

    @property
    def density(self):
        return self._density

    @density.setter
    def density(self, density):
        self._density = properties.Density(density).quantity


class Elastic(RigidBody):
    name = 'elastic'
    property_types = {
        'bulk': properties.BulkModulus,
        'shear': properties.ShearModulus,
    }

    def __init__(
            self, bulk=None, shear=None, poisson=None, young=None,
            **kwargs):
        super().__init__(**kwargs)
        bulk, shear = self._get_elastic_parameters(
            bulk=bulk, shear=shear, poisson=poisson, young=young)
        self._bulk = bulk
        self._shear = shear

    @property
    def bulk(self):
        return self._bulk

    @bulk.setter
    def bulk(self, bulk):
        self._bulk = properties.BulkModulus(bulk).quantity

    @property
    def shear(self):
        return self._shear

    @shear.setter
    def shear(self, shear):
        self._shear = properties.ShearModulus(shear).quantity

    @property
    @staticmethod
    def property_names(self):
        return

    @property
    def poisson(self):
        return (
            (3 * self.bulk - 2 * self.shear) /
            (2 * (3 * self.bulk + self.shear))
        )

    @poisson.setter
    def poisson(self, poisson):
        bulk, shear = self._get_elastic_parameters(
            poisson=poisson, young=self.young)
        self.bulk = bulk
        self.shear = shear

    @property
    def young(self):
        return (9 * self.shear * self.bulk) / (3 * self.bulk + self.shear)

    @young.setter
    def young(self, young):
        bulk, shear = self._get_elastic_parameters(
            poisson=self.poisson, young=young)
        self.bulk = bulk
        self.shear = shear

    @classmethod
    def _get_elastic_parameters(
            cls, bulk=None, shear=None, poisson=None, young=None):
        shear = shear if shear is None else properties.ShearModulus(
            shear).quantity
        bulk = bulk if bulk is None else properties.BulkModulus(bulk).quantity

        poisson = poisson if poisson is None else properties.PoissonsRatio(
            poisson).quantity
        young = young if young is None else properties.YoungsModulus(
            young).quantity

        if shear is None:
            try:
                shear = cls._shear(young, poisson, bulk)
            except TypeError:
                raise TypeError(
                    'Insufficient information to calculate shear modulus')
        if bulk is None:
            try:
                bulk = cls._bulk(young, poisson, shear)
            except TypeError:
                raise TypeError(
                    'Insufficient information to calculate bulk modulus')
        return bulk, shear

    @staticmethod
    def _shear(young, poisson, bulk):
        if young is not None and poisson is not None:
            return young / (2.0 * (1.0 + poisson))
        if young is not None and bulk is not None:
            return (3 * bulk * young) / (9 * bulk - young)
        if poisson is not None and bulk is not None:
            return (3 * bulk * (1 - 2 * poisson)) / (2 * (1 + poisson))

    @staticmethod
    def _bulk(young, poisson, shear):
        if young is not None and poisson is not None:
            return young / (3.0 * (1.0 - 2 * poisson))
        if young is not None and shear is not None:
            return (young * shear) / (3 * (3 * shear - young))
        if poisson is not None and shear is not None:
            return (2 * shear * (1 + poisson)) / (3 * (1 - 2 * poisson))


class MohrCoulomb(Elastic, strength.MohrCoulomb):
    name = 'mohr-coulomb'
    property_types = {
        'friction': properties.FrictionAngle,
        'cohesion': properties.CohesiveStrength,
        'tension': properties.TensileStrength,
        'dilation': properties.DilationAngle,
    }

    def __init__(
            self, friction, cohesion, tension=None, dilation=None,
            **kwargs):
        super().__init__(
            phi=friction, c=cohesion, sigma_t=tension, **kwargs)
        self.psi = dilation

    @property
    def friction(self):
        return self.phi

    @friction.setter
    def friction(self, friction):
        self.phi = properties.FrictionAngle(friction).quantity

    @property
    def dilation(self):
        if self.psi is None:
            return self.phi
        else:
            return self.psi

    @dilation.setter
    def dilation(self, dilation):
        self.psi = properties.DilationAngle(dilation).quantity

    @property
    def cohesion(self):
        return self.c

    @cohesion.setter
    def cohesion(self, cohesion):
        self.c = properties.CohesiveStrength(cohesion).quantity

    @property
    def tension(self):
        return self.sigma_t

    @tension.setter
    def tension(self, tension):
        self.sigma_t = properties.TensileStrength(tension).quantity


# class HoekBrown(strength.HoekBrown, Elastic):
#     name = 'hoek-brown'

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
