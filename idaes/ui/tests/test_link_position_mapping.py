##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
import pytest

from idaes.ui.icons import UnitModelIcon


inputs = (
    (
        "default",
        "{'groups': {'in': {'position': {'name': 'left', 'args': {'x': 2, 'y': 0, 'dx': 1, 'dy': 1}}, "
        "'attrs': {'rect': {'stroke': '#000000', 'stroke-width': 0, 'width': 0, 'height': 0}}, 'markup': "
        "'<g><rect/></g>'}, 'out': {'position': {'name': 'left', 'args': {'x': 48, 'y': 50, 'dx': 1, 'dy': 1}}, "
        "'attrs': {'rect': {'stroke': '#000000', 'stroke-width': 0, 'width': 0, 'height': 0}}, 'markup': "
        "'<g><rect/></g>'}}, 'items':[{'group': 'in', 'id': 'in'}, {'group': 'out', 'id': 'out'}]}"
    ),
    (
        "cstr",
        "{'groups': {'in': {'position': {'name': 'left', 'args': {'x': 15, 'y': 0, 'dx': 1, 'dy': 1}}, 'attrs': "
        "{'rect': {'stroke': '#000000', 'stroke-width': 0, 'width': 0, 'height': 0}}, 'markup': '<g><rect/></g>'}, "
        "'out': {'position': {'name': 'left', 'args': {'x': 48, 'y': 45, 'dx': 1, 'dy': 1}}, 'attrs': {'rect': "
        "{'stroke': '#000000', 'stroke-width': 0, 'width': 0, 'height': 0}}, 'markup': '<g><rect/></g>'}}, 'items': "
        "[{'group': 'in', 'id': 'in'}, {'group': 'out', 'id': 'out'}]}"
    ),
)


@pytest.mark.unit
def test_link_position_mapping():
    for unit_name, expected in inputs:
        expected_dict = eval(expected)
        positions = UnitModelIcon(unit_name).link_positions
        assert positions == expected_dict
