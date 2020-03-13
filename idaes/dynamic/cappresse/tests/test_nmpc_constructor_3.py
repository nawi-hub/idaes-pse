##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2019, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Test for Cappresse's module for NMPC.
"""

import pytest
from pyomo.environ import (Block, ConcreteModel,  Constraint, Expression,
                           Set, SolverFactory, Var, value, 
                           TransformationFactory, TerminationCondition)
from pyomo.network import Arc
from pyomo.kernel import ComponentSet

from idaes.core import (FlowsheetBlock, MaterialBalanceType, EnergyBalanceType,
        MomentumBalanceType)
from idaes.core.util.model_statistics import (degrees_of_freedom, 
        activated_equalities_generator)
from idaes.core.util.initialization import initialize_by_time_element
from idaes.core.util.exceptions import ConfigurationError
from idaes.generic_models.unit_models import CSTR, Mixer, MomentumMixingType
from idaes.dynamic.cappresse import nmpc
from idaes.dynamic.cappresse.nmpc import *
import idaes.logger as idaeslog
from cstr_for_testing import make_model

__author__ = "Robert Parker"


# See if ipopt is available and set up solver
if SolverFactory('ipopt').available():
    solver = SolverFactory('ipopt')
    solver.options = {'tol': 1e-6,
                      'mu_init': 1e-8,
                      'bound_push': 1e-8}
else:
    solver = None


def test_constructor_3():
    m_plant = make_model(horizon=6, ntfe=60, ntcp=2)
    m_controller = make_model(horizon=3, ntfe=30, ntcp=2)
    sample_time = 0.5
    # Six samples per horizon, five elements per sample

    initial_plant_inputs = [m_plant.fs.mixer.S_inlet.flow_rate[0],
                            m_plant.fs.mixer.E_inlet.flow_rate[0]]

    # energy_holdup should now be a fixed variable 
    # (only in plant model...)
    m_plant.fs.cstr.control_volume.energy_holdup.fix(300)
    m_plant.fs.cstr.control_volume.energy_accumulation_disc_eq.deactivate()

    nmpc = NMPCSim(m_plant.fs, m_controller.fs, initial_plant_inputs,
            solver=solver, outlvl=idaeslog.DEBUG, 
            sample_time=sample_time)

    # Check that variables have been categorized properly
    ##################
    # In plant model #
    ##################
    p_mod = nmpc.p_mod
    assert p_mod is m_plant.fs
    init_input_set = ComponentSet(initial_plant_inputs)

    init_deriv_list = []
    init_diff_list = []
    init_fixed_list = [p_mod.cstr.control_volume.volume[0],
                       p_mod.mixer.E_inlet.temperature[0],
                       p_mod.mixer.S_inlet.temperature[0],
                       p_mod.cstr.control_volume.energy_holdup[0, 'aq']]

    init_ic_list = []

    init_alg_list = [
        p_mod.cstr.outlet.flow_rate[0],
        p_mod.cstr.outlet.temperature[0],
        p_mod.cstr.inlet.flow_rate[0],
        p_mod.cstr.inlet.temperature[0],
        p_mod.mixer.outlet.flow_rate[0],
        p_mod.mixer.outlet.temperature[0],
        p_mod.cstr.control_volume.energy_accumulation[0, 'aq']
        ]

    for j in p_mod.properties.component_list:
        init_deriv_list.append(
                p_mod.cstr.control_volume.material_accumulation[0, 'aq', j])
        init_diff_list.append(
                p_mod.cstr.control_volume.material_holdup[0, 'aq', j])

        init_ic_list.append(
                p_mod.cstr.control_volume.material_holdup[0, 'aq', j])
        
        init_fixed_list.append(p_mod.mixer.E_inlet.conc_mol[0, j])
        init_fixed_list.append(p_mod.mixer.S_inlet.conc_mol[0, j])

        init_alg_list.extend([
            p_mod.cstr.outlet.conc_mol[0, j],
            p_mod.cstr.outlet.flow_mol_comp[0, j],
            p_mod.cstr.inlet.conc_mol[0, j],
            p_mod.cstr.inlet.flow_mol_comp[0, j],
            p_mod.cstr.control_volume.rate_reaction_generation[0, 'aq', j],
            p_mod.mixer.outlet.conc_mol[0, j],
            p_mod.mixer.outlet.flow_mol_comp[0, j],
            p_mod.mixer.E_inlet.flow_mol_comp[0, j],
            p_mod.mixer.S_inlet.flow_mol_comp[0, j]
            ])

    for r in p_mod.reactions.rate_reaction_idx:
        init_alg_list.extend([
            p_mod.cstr.control_volume.reactions[0].reaction_coef[r],
            p_mod.cstr.control_volume.reactions[0].reaction_rate[r],
            p_mod.cstr.control_volume.rate_reaction_extent[0, r]
            ])

    init_deriv_set = ComponentSet(init_deriv_list)
    init_diff_set = ComponentSet(init_diff_list)
    init_fixed_set = ComponentSet(init_fixed_list)
    init_alg_set = ComponentSet(init_alg_list)
    init_ic_set = ComponentSet(init_ic_list)

    assert len(p_mod.input_vars) == len(init_input_set)
    for v in p_mod.input_vars:
        assert v[0] in init_input_set

    assert len(p_mod.deriv_vars) == len(init_deriv_set)
    for v in p_mod.deriv_vars:
        assert v[0] in init_deriv_set

    assert len(p_mod.diff_vars) == len(init_deriv_set)
    for v in p_mod.diff_vars:
        assert v[0] in init_diff_set

    assert len(p_mod.fixed_vars) == len(init_fixed_set)
    for v in p_mod.fixed_vars:
        assert v[0] in init_fixed_set

    assert len(p_mod.alg_vars) == len(init_alg_set)
    for v in p_mod.alg_vars:
        assert v[0] in init_alg_set

    assert len(p_mod.ic_vars) == len(init_ic_set)
    for v in p_mod.ic_vars:
        assert v[0] in init_ic_set

    assert len(p_mod.scalar_vars) == 0

    for var in p_mod.deriv_vars:
        assert len(var) == len(p_mod.time)
        assert var.index_set() is p_mod.time
    for var in p_mod.alg_vars:
        assert len(var) == len(p_mod.time)
        assert var.index_set() is p_mod.time


if __name__ == '__main__':
    test_constructor_3()

