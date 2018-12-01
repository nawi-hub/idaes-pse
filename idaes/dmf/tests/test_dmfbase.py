##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes".
##############################################################################
"""
Tests for idaes.dmf.dmf module
"""
import json
import logging
import os
import tempfile
# third-party
import pytest
# package
from idaes.dmf import resource
from idaes.dmf import errors
from idaes.dmf.dmfbase import DMFConfig, DMF
from .util import init_logging, tmp_dmf

__author__ = 'Dan Gunter <dkgunter@lbl.gov>'

init_logging()
_log = logging.getLogger(__name__)

prop_json = [
    {
        "meta": {
            "datatype": "MEA",
            "info": "J. Chem. Eng. Data, 2009, Vol 54, pg. 3096-30100",
            "notes": "r is MEA weight fraction in aqueous soln.",
            "authors": "Amundsen, T.G., Lars, E.O., Eimer, D.A.",
            "title": "Density and Viscosity of Monoethanolamine + .etc.",
            "date": "2009"
        },
        "data": [
            {"name": "Viscosity Value",
             "units": "mPa-s",
             "values": [2.6, 6.2],
             "error_type": "absolute",
             "errors": [0.06, 0.004],
             "type": "property"},
            {"name": "r",
             "units": "",
             "values": [0.2, 1000],
             "type": "state"
             }
        ]
    }
]


@pytest.fixture(scope='function')
def tmp_propdata_file(request):
    sdir = getattr(request.module, 'scratchdir', '/tmp')
    prop = tmp_propdata()
    tmpf = open(os.path.join(sdir, 'resource.json'), 'w')
    json.dump(prop, tmpf)
    tmpf.close()
    return tmpf


def tmp_propdata():
    return prop_json[0]


def add_resources(dmf_obj, num=3, **attrs):
    ids = []
    for i in range(num):
        r = resource.Resource(value=attrs, type_='test')
        r.data = {'i': i}
        dmf_obj.add(r)
        ids.append(r.id)
    return ids


# Tests


def test_add_property_data(tmp_dmf, tmp_propdata_file):
    tmpf, prop = tmp_propdata_file, tmp_propdata()
    # Add the resource
    r = resource.Resource(type_='property_data')
    r.set_id()
    r.v['creator'] = {'name': 'Dan Gunter'}
    m = prop['meta']
    work = '{authors}, "{title}". {info}, {date}'.format(**m)
    r.v['sources'].append({'source': work, 'date': m['date']})
    r.data = {'notes': m['notes']}
    r.v['tags'].append('MEA')
    r.v['datafiles'].append({'path': tmpf.name})
    rid = tmp_dmf.add(r)
    assert rid is not None
    # Retrieve the resource
    r2 = tmp_dmf.fetch_one(rid)
    # Validate the resource
    assert r2.type == 'property_data'
    assert 'MEA' in r2.v['tags']
    # Remove the resource
    tmp_dmf.remove(identifier=rid)


def test_property_data_file(tmp_dmf, tmp_propdata_file):
    tmpf, prop = tmp_propdata_file, tmp_propdata()
    # Add the resource
    r = resource.Resource(type_='property_data')
    r.v['datafiles'].append({'path': tmpf.name})
    rid = tmp_dmf.add(r)
    assert rid is not None
    r2 = tmp_dmf.fetch_one(rid)
    path = r2.v['datafiles'][0]['path']
    f2 = open(path, 'r')
    j2 = json.load(f2)
    assert j2 == prop


def test_find_propertydata(tmp_dmf):
    # populate DMF with some property data resources
    pj = prop_json[0]
    n = 10
    for i in range(n):
        pd = resource.Resource(value={'data': pj}, type_=resource.TY_PROPERTY)
        tmp_dmf.add(pd)
    # get them back again
    filter_ = {'type': resource.TY_PROPERTY}
    pdata = list(tmp_dmf.find(filter_dict=filter_))
    assert len(pdata) == n


def test_dmf_init_minimal():
    pytest.raises(errors.DMFError, DMF)


def test_dmf_add(tmp_dmf):
    r = resource.Resource(value={'desc': 'test resource'})
    r.do_copy = True  # copy by default
    # (1) Copy, and don't remove {default behavior}
    tmpf1 = tempfile.NamedTemporaryFile(delete=False)
    tmpf1.close()
    r.v['datafiles'].append({'path': tmpf1.name})
    # (2) Copy, and remove original
    tmpf2 = tempfile.NamedTemporaryFile(delete=False)
    tmpf2.close()
    r.v['datafiles'].append({'path': tmpf2.name, 'is_tmp': True})
    # (3) Do not copy (or remove)
    tmpf3 = tempfile.NamedTemporaryFile()
    r.v['datafiles'].append({'path': tmpf3.name, 'do_copy': False})

    tmp_dmf.add(r)

    os.unlink(tmpf1.name)
    try:
        os.unlink(tmpf2.name)
        assert False, "Expected error"
    except Exception as err:
        pass

    os.unlink(tmpf3.name)
    # This is ignored. It makes no sense to ask the file
    # to be removed, but not copied (just a file delete?!)
    r = resource.Resource(value={'desc': 'test resource'})
    r.v['datafiles'].append({'path': 'foo',
                             'do_copy': False,
                             'is_tmp': True})
    tmp_dmf.add(r)


def test_dmf_update(tmp_dmf):
    ids = add_resources(tmp_dmf, 2)
    r1 = tmp_dmf.fetch_one(ids[0])
    r1.v[r1.TYPE_FIELD] = 'test'
    r1.v['desc'] = 'Updated description'
    tmp_dmf.update(r1)
    r1b = tmp_dmf.fetch_one(ids[0])
    assert r1b.v['desc'] == 'Updated description'
    r2 = tmp_dmf.fetch_one(ids[1])
    assert r2.v['desc'] != 'Updated description'


def test_dmf_update_newtype(tmp_dmf):
    ids = add_resources(tmp_dmf, 1)
    r1 = tmp_dmf.fetch_one(ids[0])
    r1.v[r1.TYPE_FIELD] = 'this type is different'
    try:
        tmp_dmf.update(r1)
    except errors.DMFError:
        pass
    else:
        assert False, 'DMFError expected for update() with new type'


def test_dmf_delete(tmp_dmf):
    n = 10
    ids = add_resources(tmp_dmf, num=n)
    assert tmp_dmf.count() == n
    while n > 0:
        n = n - 1
        tmp_dmf.remove(ids[n])
        assert tmp_dmf.count() == n


def test_dmf_find(tmp_dmf):
    # populate with batches of records
    # they all have the tag 'all', each batch has 'batch<N>' as well
    # All resources in a batch are given version 1.0.<N>
    # Individual resources will have data of {i: 0..<batchsz-1>}
    batchsz, numbatches = 10, 9
    all_ids = []
    for i in range(numbatches):
        n = batchsz
        batch = 'batch{:d}'.format(i + 1)
        version = resource.version_list([1, 0, i + 1])
        ids = add_resources(tmp_dmf, num=n, tags=['all', batch],
                            version_info={'version': version})
        all_ids.extend(ids)
    if _log.isEnabledFor(logging.DEBUG):
        r = tmp_dmf.fetch_one(all_ids[0])
        _log.debug("First resource:\n{}".format(r))
    # Find all records, 2 ways
    total_num = batchsz * numbatches
    result = list(tmp_dmf.find())
    assert len(result) == total_num
    result = list(tmp_dmf.find({'tags': ['all']}))
    assert len(result) == total_num
    # Find with 'all'
    result = list(tmp_dmf.find({'tags!': ['all', 'batch1']}))
    assert len(result) == batchsz

#########################
# DMFConfig             #
#########################

@pytest.fixture
def dmfconfig_tmp():
    """Default file is in user's home directory.
       We don't want to actually modify this with a test.
       So switch it out and switch it back when the fixture
       is done.
    """
    default_filename = DMFConfig.filename
    tmpfile = tempfile.NamedTemporaryFile()
    DMFConfig.filename = tmpfile.name
    yield tmpfile
    tmpfile.close()
    DMFConfig.filename = default_filename


@pytest.fixture
def dmfconfig_none():
    """Default file is in user's home directory.
    Replace it with a nonexistent file.
    """
    default_filename = DMFConfig.filename
    DMFConfig.filename = os.path.join(os.path.sep, 'idaes',
                                      *map(str, range(20)))
    yield True
    DMFConfig.filename = default_filename


def test_dmfconfig_init_defaults_nofile(dmfconfig_none):
    config = DMFConfig()
    assert config.c == DMFConfig.DEFAULTS


def test_dmfconfig_init_defaults_emptyfile(dmfconfig_tmp):
    config = DMFConfig()
    assert config.c == DMFConfig.DEFAULTS


def test_dmfconfig_init_defaults2(dmfconfig_tmp):
    config = DMFConfig(defaults={'look': 'here'})
    assert config.c['look'] == 'here'


def test_dmfconfig_bad_file(dmfconfig_tmp):
    dmfconfig_tmp.write(b'{[\n')
    dmfconfig_tmp.file.flush()
    pytest.raises(ValueError, DMFConfig)


def test_dmfconfig_somefile(dmfconfig_tmp):
    dmfconfig_tmp.write(b'workspace: foobar\n')
    dmfconfig_tmp.file.flush()
    config = DMFConfig()


def test_dmfconfig_save(dmfconfig_tmp):
    config = DMFConfig()
    config.save()


def test_dmfconfig_save_nofile(dmfconfig_none):
    config = DMFConfig()
    pytest.raises(IOError, config.save)


def test_dmfconfig_attrs(dmfconfig_tmp):
    config = DMFConfig()
    assert config.workspace is not None



