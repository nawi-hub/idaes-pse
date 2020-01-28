import numpy as np
from math import sqrt
from copy import deepcopy

from ..geometry import Cube, Cuboctahedron
from ..transform_func import ScaleFunc, RotateFunc, ReflectFunc
from .unit_cell_lattice import UnitCell, UnitCellLattice
from ..tiling import CubicTiling


class FCCLattice(UnitCellLattice):
    RefIAD = sqrt(2) / 2

    # === STANDARD CONSTRUCTOR
    def __init__(self, IAD):
        RefUnitCellShape = Cube(1, BotBackLeftCorner=np.array([0, 0, 0], dtype=float))
        RefUnitCellTiling = CubicTiling(RefUnitCellShape)
        RefFracPositions = [np.array([0.0, 0.0, 0.0]),
                            np.array([0.5, 0.5, 0.0]),
                            np.array([0.0, 0.5, 0.5]),
                            np.array([0.5, 0.0, 0.5])]
        RefUnitCell = UnitCell(RefUnitCellTiling, RefFracPositions)
        UnitCellLattice.__init__(self, RefUnitCell)
        self._IAD = FCCLattice.RefIAD  # IAD is set correctly after calling applyTransF
        self._RefNeighborsPattern = [np.array([0.0, -0.5, 0.5]),
                                     np.array([-0.5, -0.5, 0.0]),
                                     np.array([-0.5, 0.0, 0.5]),
                                     np.array([0.5, -0.5, 0.0]),
                                     np.array([0.0, -0.5, -0.5]),
                                     np.array([-0.5, 0.0, -0.5]),
                                     np.array([-0.5, 0.5, 0.0]),
                                     np.array([0.0, 0.5, 0.5]),
                                     np.array([0.5, 0.0, 0.5]),
                                     np.array([0.5, 0.0, -0.5]),
                                     np.array([0.0, 0.5, -0.5]),
                                     np.array([0.5, 0.5, 0.0])]
        self.applyTransF(ScaleFunc(IAD / FCCLattice.RefIAD))
        assert (self.isConsistentWithDesign())

    # === CONSTRUCTOR - Aligned with FCC {100}
    @classmethod
    def alignedWith100(cls, IAD):
        return cls(IAD)  # Default implementation

    # === CONSTRUCTOR - Aligned with FCC {110}
    @classmethod
    def alignedWith110(cls, IAD):
        result = cls(IAD)
        raise NotImplementedError('TODO')
        return result

    # === CONSTRUCTOR - Aligned with FCC {111}
    @classmethod
    def alignedWith111(cls, IAD, blnTrianglesAlignedWithX=True):
        result = cls(IAD)
        thetaX = -np.pi * 0.25
        thetaY = -np.arctan2(-sqrt(2), 2)
        thetaZ = (np.pi * 0.5 if blnTrianglesAlignedWithX else 0)
        result.applyTransF(RotateFunc.fromXYZAngles(thetaX, thetaY, thetaZ))
        return result

    # === ASSERTION OF CLASS DESIGN
    def isConsistentWithDesign(self):
        # TODO: Put some real checks here
        return UnitCellLattice.isConsistentWithDesign(self)

    # === MANIPULATION METHODS
    def applyTransF(self, TransF):
        if (isinstance(TransF, ScaleFunc)):
            if (TransF.isIsometric):
                self._IAD *= TransF.Scale[0]
            else:
                raise ValueError('FCCLattice applyTransF: Can only scale isometrically')
        UnitCellLattice.applyTransF(self, TransF)

    # === PROPERTY EVALUATION METHODS
    # NOTE: inherited from UnitCellLattice
    # def isOnLattice(self,P):

    def areNeighbors(self, P1, P2):
        return np.linalg.norm(P2 - P1) <= self.IAD

    def getNeighbors(self, P):
        RefP = self._getConvertToReference(P)
        result = deepcopy(self._RefNeighborsPattern)
        for NeighP in result:
            NeighP += RefP
            self._convertFromReference(NeighP)
        return result

    # === BASIC QUERY METHODS
    @property
    def IAD(self):
        return self._IAD

    @property
    def FCC111LayerSpacing(self):
        return self.IAD * sqrt(2) / sqrt(3)

    @property
    def FCC100LayerSpacing(self):
        return self.IAD * 0.5

    @property
    def FCC110LayerSpacing(self):
        return self.IAD * sqrt(2) / 2
