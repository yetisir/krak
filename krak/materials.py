from abc import ABC, abstractmethod

from . import strength, utils


class Base(ABC):
    properties = {
        'density': properties.Density,
    }

    def __init__(self, density):
        self.density = density

    @property
    @abstractmethod
    def name(self):
        raise NotImplementedError


class Null(Base):
    name = 'null'
    properties = {}


class Elastic():
    name = 'elastic'
    properties = {
        'bulk': properties.Bulk,
        'shear': properties.ShearModulus
    }

    def __init__(self, bulk=None, shear=None, poisson=None, young=None):
        bulk, shear = self._get_elastic_parameters(
            bulk=bulk, shear=shear, poisson=poisson, young=young)
        self.bulk = bulk
        self.shear = shear

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
        shear = utils.validate_positive(shear, 'shear')
        bulk = utils.validate_positive(bulk, 'bulk')

        poisson = utils.validate_positive(poisson, 'poisson')
        young = utils.validate_positive(young, 'young')

        if shear is None:
            shear = cls._shear(young, poisson)
        if bulk is None:
            bulk = cls._bulk(young, poisson)

        return bulk, shear

    @staticmethod
    def _shear(young, poisson):
        return young / (2.0 * (1.0 + poisson))

    @staticmethod
    def _bulk(young, poisson):
        return young / (3.0 * (1.0 - 2 * poisson))


class MohrCoulomb(strength.MohrCoulomb, Elastic):
    name = 'mohr-coulomb'

    def __init__(self, friction, cohesion, tension=None, dilation=None):
        super().__init__(
            phi=friction, c=cohesion, sigma_t=tension)
        self.dilation = dilation


class HoekBrown(strength.HoekBrown, Elastic):
    name = 'hoek-brown'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
