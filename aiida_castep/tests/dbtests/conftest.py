"""
conftest that prepares fixtures with tests involving orm of aiida
"""
from __future__ import absolute_import
import tempfile
import shutil
import pytest
import os

from aiida.manage.fixtures import fixture_manager


def get_backend_str():
    """ Return database backend string.

    Reads from 'TEST_AIIDA_BACKEND' environment variable.
    Defaults to django backend.
    """
    from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
    backend_env = os.environ.get('TEST_AIIDA_BACKEND')
    if not backend_env:
        return BACKEND_DJANGO
    elif  backend_env in (BACKEND_DJANGO, BACKEND_SQLA):
        return backend_env

    raise ValueError("Unknown backend '{}' read from TEST_AIIDA_BACKEND environment variable".format(backend_env))


@pytest.fixture(scope='session')
def aiida_profile():
    """setup a test profile for the duration of the tests
    If the environmental variable AIIDA_TEST_PROFILE is present
    will use an alternative fixture_manager that uses the test profile"""
    import os
    test_profile = os.environ.get('AIIDA_TEST_PROFILE', None)
    if test_profile is not None:
        from fixture import fixture_manager

    with fixture_manager() as fixture_mgr:
        yield fixture_mgr


@pytest.fixture(scope='function')
def new_database(aiida_profile):
    """clear the database after each test"""
    yield aiida_profile
    aiida_profile.reset_db()


@pytest.fixture(scope="module")
def otfgdata():
    from aiida.plugins import DataFactory
    return DataFactory("castep.otfgdata")


@pytest.fixture(scope="module")
def otfg():
    import aiida_castep.data.otfg as otfg
    return otfg


@pytest.fixture(scope="module")
def imps(aiida_profile):

    class Imports:

        def __init__(self):
            from aiida.plugins import CalculationFactory
            from aiida.plugins import DataFactory
            import aiida_castep.data.otfg as otfg
            Dict = DataFactory("dict")
            for k, v in locals().items():
                setattr(self, k, v)

    return Imports()



@pytest.fixture
def localhost(aiida_profile, tmpdir):
    """Fixture for a local computer called localhost"""
    # Check whether Aiida uses the new backend interface to create collections.
    from aiida.manage.fixtures import _GLOBAL_FIXTURE_MANAGER
    from aiida.common import exceptions
    from aiida.orm import Computer
    aiida_profile = _GLOBAL_FIXTURE_MANAGER
    ldir = str(tmpdir)
    try:
        computer = Computer.objects.get("localhost")

    except exceptions.NotExistent:
        computer = Computer()
        computer.set_name("localhost")
        computer.set_description("localhost")
        computer.set_workdir(ldir)
        computer.set_hostname("localhost")
        computer.set_scheduler_type("direct")
        computer.set_transport_type("local")
        computer.store()
    return computer


@pytest.fixture()
def code_echo(localhost):
    """Fixture of a code that just echos"""
    from aiida.orm import Code
    code = Code()
    code.set_remote_computer_exec(
        (localhost, "/bin/echo"))
    code.set_input_plugin_name("castep.castep")
    code.store()
    return code


@pytest.fixture()
def remotedata(localhost, tmpdir):
    """Create an remote data"""
    from aiida.orm import RemoteData

    rmd = RemoteData()
    rmd.set_computer(localhost)
    rmd.set_remote_path(str(tmpdir))
    return rmd


@pytest.fixture
def kpoints_data(aiida_profile):
    """
    Return a factory for kpoints
    """
    from aiida.plugins import DataFactory
    return DataFactory("array.kpoints")()


@pytest.fixture
def kpoints_mesh(kpoints_data):
    """Factory for kpoints with mesh"""
    def _kpoints_mesh(mesh, *args, **kwargs):
        kpoints_data.set_kpoints_mesh(mesh)
        return kpoints_data
    return _kpoints_mesh


@pytest.fixture
def kpoints_list(kpoints_data):
    """Factory for kpoints with mesh"""
    def _kpoints_list(klist, *args, **kwargs):
        kpoints_data.set_kpoints(klist, *args, **kwargs)
        return kpoints_data
    return _kpoints_list


@pytest.fixture
def OTFG_family_factory(aiida_profile):
    """Return a factory for upload OTFGS"""
    from aiida_castep.data.otfg import upload_otfg_family

    def _factory(otfg_entries, name, desc="TEST", **kwargs):
        upload_otfg_family(otfg_entries, name, desc, **kwargs)
        return

    return _factory


@pytest.fixture
def STO_calculation(aiida_profile, STO_structure,
                    OTFG_family_factory,
                    code_echo, imps,
                    localhost, kpoints_mesh):


    c = imps.CalculationFactory("castep.castep")()
    pdict = {"PARAM": {
        "task": "singlepoint"
    },
             "CELL": {
                 "symmetry_generate": True
             }}
    # pdict["CELL"].pop("block species_pot")
    param = imps.Dict(dict=pdict)
    c.use_structure(STO_structure)
    OTFG_family_factory(["C9"], "C9", stop_if_existing=False)
    c.use_pseudos_from_family("C9")
    c.use_kpoints(kpoints_mesh((3, 3, 3)))
    c.use_code(code_echo)
    c.set_computer(localhost)
    c.set_resources({"num_machines": 1, "num_mpiprocs_per_machine": 2})
    c.use_parameters(param)

    return c


def test_sto_calc(STO_calculation):
    STO_calculation.store_all()
    assert STO_calculation.pk

@pytest.fixture
def STO_structure(aiida_profile, imps):
    """Return a STO structure"""
    StructureData = imps.DataFactory("structure")
    a = 3.905

    cell = ((a, 0., 0.), (0., a, 0.), (0., 0., a))
    s = StructureData(cell=cell)
    s.append_atom(position=(0., 0., 0.), symbols=["Sr"])
    s.append_atom(position=(a / 2, a / 2, a / 2), symbols=["Ti"])
    s.append_atom(position=(a / 2, a / 2, 0.), symbols=["O"])
    s.append_atom(position=(a / 2, 0., a / 2), symbols=["O"])
    s.append_atom(position=(0., a / 2, a / 2), symbols=["O"])
    s.label = "STO"
    return s


def test_localhost_fixture(localhost):
    """
    Test the localhost fixture
    """
    localhost.name == "localhost"
    assert localhost.pk is not None


def test_code_fixture(code_echo):
    """
    Test the localhost fixture
    """
    assert code_echo.pk is not None
    code_echo.get_remote_exec_path()


def test_remotedata_fixture(remotedata):
    assert remotedata.get_remote_path()
