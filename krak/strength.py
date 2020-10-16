from abc import ABC, abstractmethod

import numpy as np
from scipy import optimize

from . import utils, spatial, properties


class Base(ABC):
    def normal_stress(self, sigma_3):
        sigma_1 = self.sigma_1_strength(sigma_3)
        derivative = self.derivative(sigma_3)
        term_1 = ((sigma_1 + sigma_3) / 2.0) - ((sigma_1 - sigma_3) / 2.0)
        term_2 = ((derivative - 1) / (derivative + 1))

        return term_1 * term_2

    def shear_strength(self, sigma_3):
        sigma_1 = self.sigma_1_strength(sigma_3)
        derivative = self.derivative(sigma_3)

        return (sigma_1 - sigma_3) * (np.sqrt(derivative) / (derivative + 1))

    @abstractmethod
    def sigma_1_strength(self, sigma_3):
        raise NotImplementedError

    @abstractmethod
    def derivative(self, sigma_3):
        raise NotImplementedError


class MohrCoulomb(Base):
    def __init__(self, c, phi, sigma_t=None, **kwargs):
        super().__init__(**kwargs)
        self.c = c
        self.phi = phi
        self.sigma_t = sigma_t

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c):
        self._c = properties.CohesiveStrength(c).quantity

    @property
    def sigma_t(self):
        if self._sigma_t is None:
            return -(self.c / np.tan(self._phi))
        else:
            return self._sigma_t

    @sigma_t.setter
    def sigma_t(self, sigma_t):
        if sigma_t is None:
            self._sigma_t = None
        else:
            self._sigma_t = properties.TensileStrength(sigma_t).quantity

    @property
    def phi(self):
        return self._phi.to('degrees')

    @phi.setter
    def phi(self, phi):
        self._phi = properties.FrictionAngle(phi).quantity

    def sigma_1_strength(self, sigma_3):
        term_1 = (2 * self.c * np.cos(self._phi)) / (1 - np.sin(self._phi))
        term_2 = ((1 + np.sin(self._phi)) / (1 - np.sin(self._phi))) * sigma_3
        return term_1 + term_2

    def derivative(self, sigma_3):
        return (1 + np.sin(self._phi)) / (1 - np.sin(self._phi))


class HoekBrown(Base):

    def __init__(
            self, sigma_ci, gsi=None, d=None, mi=None, mb=None, s=None,
            a=None, sigma_t=None):

        self.sigma_ci = utils.validate_positive(sigma_ci, 'sigma_ci')
        self.mi = utils.validate_positive(mi, 'mi')
        self.gsi = utils.validate_positive(gsi, 'gsi')
        self.d = utils.validate_positive(d, 'd')
        self.sigma_t = utils.validate_positive(sigma_t, 'sigma_t')

        mb = utils.validate_positive(mb, 'mb')
        s = utils.validate_positive(s, 's')
        a = utils.validate_positive(a, 'a')

        if self.mi is None:
            self.mb = mb

        if self.gsi is None:
            self.a = a if a is not None else 0.5

        if self.d is None:
            self.s = s if s is not None else 1.0

        if self.sigma_t is None:
            self.sigma_t = -(self.s * self.sigma_ci) / self.mb

    @property
    def mb(self):
        return self.mi * np.exp((self.gsi - 100.0)/(28.0 - (14.0 * self.d)))

    @mb.setter
    def mb(self, mb):
        self.mi = mb / np.exp((self.gsi - 100.0)/(28.0 - (14.0 * self.d)))

    @property
    def s(self):
        return np.exp((self.gsi - 100.0)/(9.0 - (3.0 * self.d)))

    @s.setter
    def s(self, s):
        self.d = (9.0 - (self.gsi - 100.0) / np.log(s)) * (1.0 / 3.0)

    @property
    def a(self):
        return (0.5 + (
            np.exp((np.negative(self.gsi)) / 15.0) -
            np.exp(-20.0 / 3.0)) / 6.0)

    @a.setter
    def a(self, a):
        self.gsi = -15.0 * np.log((a - 0.5) * 6 + np.exp(-20.0 / 3.0))

    @property
    def sigma_cm(self):
        numerator1 = (self.mb + 4 * self.s - self.a * (self.mb - 8 * self.s))
        numerator2 = np.power(self.mb / 4 + self.s, self.a - 1)
        denominator = 2 * (1 + self.a) * (2 + self.a)

        return self.sigma_ci * numerator1 * numerator2 / denominator

    def sigma_1_strength(self, sigma_3):
        base = (self.mb * (sigma_3 / self.sigma_ci) + self.s)
        if base < 0:
            return 0

        return sigma_3 + (self.sigma_ci * np.power(base, self.a))

    def derivative(self, sigma_3):
        base = (self.mb * (sigma_3 / self.sigma_ci) + self.s)
        if base < 0:
            return 0
        return 1 + self.a * self.mb * np.power(base, self.a - 1)

    def equivalent_mc_average(
            self, sigma_3_max=None, H=None, gamma=None, excavation='slope'):

        if sigma_3_max is None:
            if excavation == 'slope':
                sigma_3_max = self._calculate_sigma_3_max(
                    H, gamma, 0.72, -0.91)
            elif excavation == 'tunnel':
                sigma_3_max = self._calculate_sigma_3_max(
                    H, gamma, 0.47, -0.94)

        phi = self._calculate_average_phi(sigma_3_max)
        c = self._calculate_average_c(sigma_3_max)

        return MohrCoulomb(c=c, phi=phi)

    def _calculate_sigma_3_max(self, H, gamma, coefficient, exponent):
        return coefficient * np.power(
            (self.sigma_cm / (H * gamma)), exponent) * self.sigma_cm

    def _calculate_average_phi(self, sigma_3_max):
        sigma_3_n = sigma_3_max / self.sigma_ci

        numerator = 6 * self.a * self.mb * np.power(
            self.s + self.mb * sigma_3_n, self.a - 1)
        denominator = 2 * (1 + self.a) * (2 + self.a) + numerator

        return np.rad2deg(np.arcsin(numerator / denominator))

    def _calculate_average_c(self, sigma_3_max):
        sigma_3_n = sigma_3_max / self.sigma_ci

        x1 = np.power(self.s + self.mb * sigma_3_n, self.a - 1)
        x2 = (1 + self.a) * (2 + self.a)
        numerator = (self.sigma_ci * (
            (1 + 2 * self.a) * self.s + (1 - self.a) *
            self.mb * sigma_3_n) * x1)
        denominator = x2 * np.sqrt(1 + 6 * self.a * self.mb * x1 / x2)

        return numerator / denominator

    def equivalent_mc_exact(
            self, sigma_3, sigma_1=None, correction='vertical'):

        if sigma_1 is None:
            sigma_1 = self.sigma_1_strength(sigma_3)

        if correction == 'vertical':
            sigma_3 = sigma_3
        elif correction == 'closest':
            sigma_3 = self._find_closest(sigma_3, sigma_1)
        elif correction == 'hybrid':
            if sigma_1 > self.sigma_1_strength(sigma_3):
                sigma_3 = self._find_closest(sigma_3, sigma_1)
        else:
            raise ValueError('Unrecognized correction type')

        derivative = self.derivative(sigma_3)
        sigma_1 = self.sigma_1_strength(sigma_3)

        phi = np.rad2deg(
            np.arctan((derivative - 1) / (2 * np.sqrt(derivative))))
        c = (sigma_1 - (sigma_3 * derivative)) / (2 * np.sqrt(derivative))

        return MohrCoulomb(c=c, phi=phi)

    def _find_closest(self, sigma_3, sigma_1):

        def closest_point(trial_sigma_3, sigma_3, sigma_1):
            """[summary]

            Args:
                trial_sigma_3 (float): [description]
                sigma_3 (float): [description]
                sigma_1 (float): [description]

            Returns:
                float: Dot product of envelope tangent and vector from point
            """
            reference_point = spatial.Vector([sigma_3, sigma_1, 0])
            envelope_point = spatial.Vector(
                [trial_sigma_3, self.sigma_1_strength(trial_sigma_3), 0])

            envelope_tangent = spatial.Vector(
                [1, self.derivative(trial_sigma_3), 0])

            if envelope_point[1] >= 0:
                closest_direction = reference_point - envelope_point

                return closest_direction.unit * envelope_tangent.unit
            else:
                # negative strength - so return max possiblie dot product of
                # parallel unit vectors
                return 1

        closest_sigma_3 = optimize.fmin(
            closest_point, x0=sigma_3, args=(sigma_3, sigma_1), ftol=0.1,
            disp=False)
        return closest_sigma_3[0]
