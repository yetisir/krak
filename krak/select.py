from abc import ABC, abstractmethod


class BaseRange(ABC):
    def __add__(self, other):
        return Union(self, other)

    def __sub__(self, other):
        return Intersection(self, Invert(other))

    def __neg__(self):
        return Invert(self)


class Union(BaseRange):
    pass

class Intersection(BaseRange):
    pass

class Invert(BaseRange):
    pass

class All(BaseRange):
    def query(self, mesh):
        pass

class Nothing(BaseRange):
    def query(self, mesh):
        pass

class CoordinateRange(BaseRange):
    def query(self, mesh):
        pass

class XRange(BaseRange):
    def query(self, mesh):
        pass
