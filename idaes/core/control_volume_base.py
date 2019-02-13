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
Base class for control volumes
"""

from __future__ import division

# Import Python libraries
import logging

# Import Pyomo libraries
from pyomo.common.config import ConfigBlock, ConfigValue, In
from pyutilib.enum import Enum

# Import IDAES cores
from idaes.core import ProcessBlockData, useDefault, declare_process_block_class
from idaes.core.util.config import (is_physical_parameter_block,
                                    is_reaction_parameter_block)
from idaes.core.util.exceptions import (ConfigurationError,
                                        DynamicError)
from idaes.core.util.misc import add_object_reference

__author__ = "Andrew Lee"

# Set up logger
_log = logging.getLogger(__name__)


# Enumerate options for material balances
MaterialBalanceType = Enum(
    'none',
    'componentPhase',
    'componentTotal',
    'elementTotal',
    'total')

# Enumerate options for energy balances
EnergyBalanceType = Enum(
    'none',
    'enthalpyPhase',
    'enthalpyTotal',
    'energyPhase',
    'energyTotal')

# Enumerate options for momentum balances
MomentumBalanceType = Enum(
    'none',
    'pressureTotal',
    'pressurePhase',
    'momentumTotal',
    'momentumPhase')

# Enumerate options for flow direction
FlowDirection = Enum(
    'forward',
    'backward')

# Enumerate options for material flow basis
MaterialFlowBasis = Enum(
    'molar',
    'mass',
    'other')

# Set up example ConfigBlock that will work with ControlVolume autobuild method
CONFIG_Template = ProcessBlockData.CONFIG()
CONFIG_Template.declare("dynamic", ConfigValue(
    default=useDefault,
    domain=In([useDefault, True, False]),
    description="Dynamic model flag",
    doc="""Indicates whether this model will be dynamic,
**default** - useDefault.
**Valid values:** {
**useDefault** - get flag from parent,
**True** - set as a dynamic model,
**False** - set as a steady-state model}"""))
CONFIG_Template.declare("has_holdup", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Holdup construction flag",
    doc="""Indicates whether holdup terms should be constructed or not.
Must be True if dynamic = True,
**default** - False.
**Valid values:** {
**True** - construct holdup terms,
**False** - do not construct holdup terms}"""))
CONFIG_Template.declare("material_balance_type", ConfigValue(
    default=MaterialBalanceType.componentPhase,
    domain=In(MaterialBalanceType),
    description="Material balance construction flag",
    doc="""Indicates what type of mass balance should be constructed,
**default** - MaterialBalanceType.componentPhase.
**Valid values:** {
**MaterialBalanceType.none** - exclude material balances,
**MaterialBalanceType.componentPhase** - use phase component balances,
**MaterialBalanceType.componentTotal** - use total component balances,
**MaterialBalanceType.elementTotal** - use total element balances,
**MaterialBalanceType.total** - use total material balance.}"""))
CONFIG_Template.declare("energy_balance_type", ConfigValue(
    default=EnergyBalanceType.enthalpyTotal,
    domain=In(EnergyBalanceType),
    description="Energy balance construction flag",
    doc="""Indicates what type of energy balance should be constructed,
**default** - EnergyBalanceType.enthalpyTotal.
**Valid values:** {
**EnergyBalanceType.none** - exclude energy balances,
**EnergyBalanceType.enthalpyTotal** - single ethalpy balance for material,
**EnergyBalanceType.enthalpyPhase** - ethalpy balances for each phase,
**EnergyBalanceType.energyTotal** - single energy balance for material,
**EnergyBalanceType.energyPhase** - energy balances for each phase.}"""))
CONFIG_Template.declare("momentum_balance_type", ConfigValue(
    default=MomentumBalanceType.pressureTotal,
    domain=In(MomentumBalanceType),
    description="Momentum balance construction flag",
    doc="""Indicates what type of momentum balance should be constructed,
**default** - MomentumBalanceType.pressureTotal.
**Valid values:** {
**MomentumBalanceType.none** - exclude momentum balances,
**MomentumBalanceType.pressureTotal** - single pressure balance for material,
**MomentumBalanceType.pressurePhase** - pressure balances for each phase,
**MomentumBalanceType.momentumTotal** - single momentum balance for material,
**MomentumBalanceType.momentumPhase** - momentum balances for each phase.}"""))
CONFIG_Template.declare("has_rate_reactions", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Rate reaction construction flag",
    doc="""Indicates whether terms for rate controlled reactions should be
constructed,
**default** - False.
**Valid values:** {
**True** - include kinetic reaction terms,
**False** - exclude kinetic reaction terms.}"""))
CONFIG_Template.declare("has_equilibrium_reactions", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Equilibrium reaction construction flag",
    doc="""Indicates whether terms for equilibrium controlled reactions
should be constructed,
**default** - False.
**Valid values:** {
**True** - include equilibrium reaction terms,
**False** - exclude equilibrium reaction terms.}"""))
CONFIG_Template.declare("has_phase_equilibrium", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Phase equilibrium construction flag",
    doc="""Indicates whether terms for phase equilibrium should be
constructed,
**default** = False.
**Valid values:** {
**True** - include phase equilibrium terms
**False** - exclude phase equilibrium terms.}"""))
CONFIG_Template.declare("has_mass_transfer", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Mass transfer term construction flag",
    doc="""Indicates whether terms for mass transfer should be constructed,
**default** - False.
**Valid values:** {
**True** - include mass transfer terms,
**False** - exclude mass transfer terms.}"""))
CONFIG_Template.declare("has_heat_of_reaction", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Heat of reaction term construction flag",
    doc="""Indicates whether terms for heat of reaction should be constructed,
**default** - False.
**Valid values** {
**True** - include heat of reaction terms,
**False** - exclude heat of reaction terms.}"""))
CONFIG_Template.declare("has_heat_transfer", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Heat transfer term construction flag",
    doc="""Indicates whether terms for heat transfer should be constructed,
**default** - False.
**Valid values:** {
**True** - include heat transfer terms,
**False** - exclude heat transfer terms.}"""))
CONFIG_Template.declare("has_work_transfer", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Work transfer term construction flag",
    doc="""Indicates whether terms for work transfer should be constructed,
**default** - False.
**Valid values** {
**True** - include work transfer terms,
**False** - exclude work transfer terms.}"""))
CONFIG_Template.declare("has_pressure_change", ConfigValue(
    default=False,
    domain=In([True, False]),
    description="Pressure change term construction flag",
    doc="""Indicates whether terms for pressure change should be
constructed,
**default** - False.
**Valid values:** {
**True** - include pressure change terms,
**False** - exclude pressure change terms.}"""))
CONFIG_Template.declare("property_package", ConfigValue(
    default=useDefault,
    domain=is_physical_parameter_block,
    description="Property package to use for control volume",
    doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PropertyParameterObject** - a PropertyParameterBlock object.}"""))
CONFIG_Template.declare("property_package_args", ConfigBlock(
    implicit=True,
    description="Arguments to use for constructing property packages",
    doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see property package for documentation.}"""))
CONFIG_Template.declare("reaction_package", ConfigValue(
    default=None,
    domain=is_reaction_parameter_block,
    description="Reaction package to use for control volume",
    doc="""Reaction parameter object used to define reaction calculations,
**default** - None.
**Valid values:** {
**None** - no reaction package,
**ReactionParameterBlock** - a ReactionParameterBlock object.}"""))
CONFIG_Template.declare("reaction_package_args", ConfigBlock(
    implicit=True,
    description="Arguments to use for constructing reaction packages",
    doc="""A ConfigBlock with arguments to be passed to a reaction block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see reaction package for documentation.}"""))

@declare_process_block_class("ControlVolume", doc="This class is not usually "
    "used directly. Use ControlVolume0DBlock or ControlVolume1DBlock instead.")
class ControlVolumeBlockData(ProcessBlockData):
    """
    The ControlVolumeBlockData Class forms the base class for all IDAES
    ControlVolume models. The purpose of this class is to automate the tasks
    common to all control volume blockss and ensure that the necessary
    attributes of a control volume block are present.

    The most signfiicant role of the ControlVolumeBlockData class is to set up the
    bconstruction arguments for the control volume block, automatically link to
    the time domain of the parent block, and to get the information about the
    property and reaction packages.
    """

    CONFIG = ProcessBlockData.CONFIG()
    CONFIG.declare("dynamic", ConfigValue(
        domain=In([useDefault, True, False]),
        default=useDefault,
        description="Dynamic model flag",
        doc="""Indicates whether this model will be dynamic,
**default** - useDefault.
**Valid values:** {
**useDefault** - get flag from parent,
**True** - set as a dynamic model,
**False** - set as a steady-state model}"""))
    CONFIG.declare("has_holdup", ConfigValue(
        default=useDefault,
        domain=In([useDefault, True, False]),
        description="Holdup construction flag",
        doc="""Indicates whether holdup terms should be constructed or not.
Must be True if dynamic = True,
**default** - False.
**Valid values:** {
**True** - construct holdup terms,
**False** - do not construct holdup terms}"""))
    CONFIG.declare("property_package", ConfigValue(
        default=useDefault,
        domain=is_physical_parameter_block,
        description="Property package to use for control volume",
        doc="""Property parameter object used to define property calculations,
**default** - useDefault.
**Valid values:** {
**useDefault** - use default package from parent model or flowsheet,
**PropertyParameterObject** - a PropertyParameterBlock object.}"""))
    CONFIG.declare("property_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing property packages",
        doc="""A ConfigBlock with arguments to be passed to a property block(s)
and used when constructing these, **default** - None. **Valid values:** {
see property package for documentation.}"""))
    CONFIG.declare("reaction_package", ConfigValue(
        default=None,
        domain=is_reaction_parameter_block,
        description="Reaction package to use for control volume",
        doc="""Reaction parameter object used to define reaction calculations,
**default** - None.
**Valid values:** {
**None** - no reaction package,
**ReactionParameterBlock** - a ReactionParameterBlock object.}"""))
    CONFIG.declare("reaction_package_args", ConfigBlock(
        implicit=True,
        description="Arguments to use for constructing reaction packages",
        doc="""A ConfigBlock with arguments to be passed to a reaction block(s)
and used when constructing these,
**default** - None.
**Valid values:** {
see reaction package for documentation.}"""))
    CONFIG.declare("auto_construct", ConfigValue(
        default=False,
        domain=In([True, False]),
        description="Argument indicating whether ControlVolume should "
                    "automatically construct balance equations",
        doc="""If set to True, this argument will trigger the auto_construct
method which will attempt to construct a set of material, energy and momentum
balance equations based on the parent unit's config block. The parent unit must
have a config block which derives from CONFIG_Base,
**default** - False.
**Valid values:** {
**True** - use automatic construction,
**False** - do not use automatic construciton.}"""))

    def build(self):
        """
        General build method for Control Volumes blocks. This method calls a
        number of sub-methods which automate the construction of expected
        attributes of all ControlVolume blocks.

        Inheriting models should call `super().build`.

        Args:
            None

        Returns:
            None
        """
        super(ControlVolumeBlockData, self).build()

        # Setup dynamics flag and time domain
        self._setup_dynamics()

        # Get property package details
        self._get_property_package()

        # Get indexing sets
        self._get_indexing_sets()

        # Get reaction package details (as necessary)
        self._get_reaction_package()

        if self.config.auto_construct is True:
            self._auto_construct()

    def add_geometry(self, *args, **kwargs):
        """
        Method for defining the geometry of the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_geometry. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_material_balances(self,
                              balance_type=MaterialBalanceType.componentPhase,
                              **kwargs):
        """
        General method for adding material balances to a control volume.
        This method makes calls to specialised sub-methods for each type of
        material balance.

        Args:
            balance_type - MaterialBalanceType Enum indicating which type of
                    material balance should be constructed.
            has_rate_reactions - whether default generation terms for rate
                    reactions should be included in material balances
            has_equilibrium_reactions - whether generation terms should for
                    chemical equilibrium reactions should be included in
                    material balances
            has_phase_equilibrium - whether generation terms should for phase
                    equilibrium behaviour should be included in material
                    balances
            has_mass_transfer - whether generic mass transfer terms should be
                    included in material balances
            custom_molar_term - a Pyomo Expression representing custom terms to
                    be included in material balances on a molar basis.
            custom_mass_term - a Pyomo Expression representing custom terms to
                    be included in material balances on a mass basis.

        Returns:
            Constraint objects constructed by sub-method
        """
        if balance_type == MaterialBalanceType.none:
            mb = None
        elif balance_type == MaterialBalanceType.componentPhase:
            mb = self.add_phase_component_balances(**kwargs)
        elif balance_type == MaterialBalanceType.componentTotal:
            mb = self.add_total_component_balances(**kwargs)
        elif balance_type == MaterialBalanceType.elementTotal:
            mb = self.add_total_element_balances(**kwargs)
        elif balance_type == MaterialBalanceType.total:
            mb = self.add_total_material_balances(**kwargs)
        else:
            raise ConfigurationError(
                    "{} invalid balance_type for add_material_balances."
                    "Please contact the unit model developer with this bug."
                    .format(self.name))

        return mb

    def add_energy_balances(self,
                            balance_type=EnergyBalanceType.enthalpyPhase,
                            **kwargs):
        """
        General method for adding energy balances to a control volume.
        This method makes calls to specialised sub-methods for each type of
        energy balance.

        Args:
            balance_type (EnergyBalanceType): Enum indicating which type of
                energy balance should be constructed.
            has_heat_of_reaction (bool): whether terms for heat of reaction
                should be included in energy balance
            has_heat_transfer (bool): whether generic heat transfer terms should
                be included in energy balances
            has_work_transfer (bool): whether generic mass transfer terms should
                be included in energy balances
            custom_term (Expression): a Pyomo Expression representing custom
                terms to be included in energy balances

        Returns:
            Constraint objects constructed by sub-method
        """
        if balance_type == EnergyBalanceType.none:
            eb = None
        elif balance_type == EnergyBalanceType.enthalpyTotal:
            eb = self.add_total_enthalpy_balances(**kwargs)
        elif balance_type == EnergyBalanceType.enthalpyPhase:
            eb = self.add_phase_enthalpy_balances(**kwargs)
        elif balance_type == EnergyBalanceType.energyTotal:
            eb = self.add_total_energy_balances(**kwargs)
        elif balance_type == EnergyBalanceType.energyPhase:
            eb = self.add_phase_energy_balances(**kwargs)
        else:
            raise ConfigurationError(
                    "{} invalid balance_type for add_energy_balances."
                    "Please contact the unit model developer with this bug."
                    .format(self.name))

        return eb

    def add_momentum_balances(self,
                              balance_type=MomentumBalanceType.pressureTotal,
                              **kwargs):
        """
        General method for adding momentum balances to a control volume.
        This method makes calls to specialised sub-methods for each type of
        momentum balance.

        Args:
            balance_type (MomentumBalanceType): Enum indicating which type of
                momentum balance should be constructed.
            has_pressure_change (bool): whether default generation terms for
                pressure change should be included in momentum balances
            custom_term (Expression): a Pyomo Expression representing custom
                terms to be included in momentum balances

        Returns:
            Constraint objects constructed by sub-method
        """
        if balance_type == MomentumBalanceType.none:
            mb = None
        elif balance_type == MomentumBalanceType.pressureTotal:
            mb = self.add_total_pressure_balances(**kwargs)
        elif balance_type == MomentumBalanceType.pressurePhase:
            mb = self.add_phase_pressure_balances(**kwargs)
        elif balance_type == MomentumBalanceType.momentumTotal:
            mb = self.add_total_momentum_balances(**kwargs)
        elif balance_type == MomentumBalanceType.momentumPhase:
            mb = self.add_phase_momentum_balances(**kwargs)
        else:
            raise ConfigurationError(
                    "{} invalid balance_type for add_momentum_balances."
                    "Please contact the unit model developer with this bug."
                    .format(self.name))

        return mb

    def _auto_construct(self):
        """
        Placeholder _auto_construct method to ensure a useful exception is
        returned if auto_build is set to True but something breaks in the
        process. Derived ControlVolume classes should overload this.

        Args:
            None

        Returns:
            None
        """
        parent = self.parent_block()

        self.add_geometry()
        self.add_state_blocks()
        self.add_reaction_blocks()

        self.add_material_balances(
            material_balance_type=parent.config.material_balance_type,
            has_rate_reactions=parent.config.has_rate_reactions,
            has_equilibrium_reactions=parent.config.has_equilibrium_reactions,
            has_phase_equilibrium=parent.config.has_phase_equilibrium,
            has_mass_transfer=parent.config.has_mass_transfer)

        self.add_energy_balances(
            energy_balance_type=parent.config.energy_balance_type,
            has_heat_of_reaction=parent.config.has_heat_of_reaction,
            has_heat_transfer=parent.config.has_heat_transfer,
            has_work_transfer=parent.config.has_work_transfer)

        self.add_momentum_balances(
            has_pressure_change=parent.config.has_pressure_change)

        try:
            self.apply_transformation()
        except AttributeError:
            pass

    def _setup_dynamics(self):
        """
        This method automates the setting of the dynamic flag and time domain
        for control volume blocks.

        If dynamic flag is 'use_parent_value', method attempts to get the value
        of the dynamic flag from the parent model, otherwise the local value is
        used. The time domain is always collected from the parent model.

        Finally, the method checks the has_holdup argument (if present), and
        ensures that has_holdup is True if dynamic is True.

        Args:
            None

        Returns:
            None
        """
        # Check the dynamic flag, and retrieve if necessary
        if self.config.dynamic == useDefault:
            # Get dynamic flag from parent
            try:
                self.config.dynamic = self.parent_block().config.dynamic
            except AttributeError:
                # If parent does not have dynamic flag, raise Exception
                raise DynamicError('{} has a parent model '
                                   'with no dynamic attribute.'
                                   .format(self.name))

        # Try to get reference to time object from parent
        try:
            # Guess that parent has a reference to time domain
            add_object_reference(self,
                                 "time_ref",
                                 self.parent_block().time_ref)
        except AttributeError:
            try:
                # Should not happen, but guess parent has actual time domain
                add_object_reference(self,
                                     "time_ref",
                                     self.parent_block().time)
            except AttributeError:
                # Can't find time domain
                raise DynamicError('{} has a parent model '
                                   'with no time domain'.format(self.name))

        # Set and validate has_holdup argument
        if self.config.has_holdup == useDefault:
            # Default to same value as dynamic flag
            self.config.has_holdup = self.config.dynamic
        elif self.config.has_holdup is False:
            if self.config.dynamic is True:
                # Dynamic model must have has_holdup = True
                raise ConfigurationError(
                            '{} inconsistent arguments for control volume. '
                            'dynamic was set to True, which requires that '
                            'has_holdup = True (was False). Please correct '
                            'your arguments to be consistent.'
                            .format(self.name))

    # Add placeholder methods for adding property and reaction packages
    def add_state_blocks(self, *args, **kwargs):
        """
        Method for adding StateBlocks to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_state_blocks. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_reaction_blocks(self, *args, **kwargs):
        """
        Method for adding ReactionBlocks to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_reaction_blocks. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    # Add placeholder methods for all types of material, energy and momentum
    # balance equations which return NotImplementedErrors
    def add_phase_component_balances(self, *args, **kwargs):
        """
        Method for adding material balances indexed by phase and component to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_phase_component_material_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_component_balances(self, *args, **kwargs):
        """
        Method for adding material balances indexed by component to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_component_material_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_element_balances(self, *args, **kwargs):
        """
        Method for adding total elemental material balances indexed to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_element_material_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_material_balances(self, *args, **kwargs):
        """
        Method for adding a total material balance to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_material_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_phase_enthalpy_balances(self, *args, **kwargs):
        """
        Method for adding enthalpy balances indexed by phase to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_phase_enthalpy_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_enthalpy_balances(self, *args, **kwargs):
        """
        Method for adding a total enthalpy balance to
        the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_enthalpy_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_phase_energy_balances(self, *args, **kwargs):
        """
        Method for adding energy balances (including kinetic energy) indexed by
        phase to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_phase_energy_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_energy_balances(self, *args, **kwargs):
        """
        Method for adding a total energy balance (including kinetic energy)
        to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_energy_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_phase_pressure_balances(self, *args, **kwargs):
        """
        Method for adding pressure balances indexed by
        phase to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_phase_pressure_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_pressure_balances(self, *args, **kwargs):
        """
        Method for adding a total pressure balance to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_pressure_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_phase_momentum_balances(self, *args, **kwargs):
        """
        Method for adding momentum balances indexed by phase to the control
        volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_phase_momentum_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))

    def add_total_momentum_balances(self, *args, **kwargs):
        """
        Method for adding a total momentum balance to the control volume.

        See specific control volume documentation for details.
        """
        raise NotImplementedError(
                "{} control volume class has not implemented a method for "
                "add_total_momentum_balances. Please contact the "
                "developer of the ControlVolume class you are using."
                .format(self.name))