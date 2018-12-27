from typing import Mapping

from pyecsca.ec.formula import ScalingFormula
from .coordinates import CoordinateModel
from .mod import Mod


class Point(object):
    coordinate_model: CoordinateModel
    coords: Mapping[str, Mod]

    def __init__(self, model: CoordinateModel, **coords: Mod):
        if not set(model.variables) == set(coords.keys()):
            raise ValueError
        self.coordinate_model = model
        self.coords = coords

    def __eq__(self, other):
        # TODO: Somehow compare projective points. Via a map to an affinepoint?
        if type(other) is not Point:
            return False
        if  self.coordinate_model != other.coordinate_model:
            return False
        self_scaling = list(filter(lambda x: isinstance(x, ScalingFormula), self.coordinate_model.formulas.items()))
        other_scaling = list(filter(lambda x: isinstance(x, ScalingFormula), other.coordinate_model.formulas.items()))
        return self.coords == other.coords

    def __str__(self):
        args = ", ".join([f"{key}={val}" for key, val in self.coords.items()])
        return f"[{args}]"

    def __repr__(self):
        return f"Point([{str(self)}] in {self.coordinate_model})"
