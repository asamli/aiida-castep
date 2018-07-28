"""
Tests for utils module
"""

import pytest
import ase
from ..utils import *

@pytest.fixture
def unsorted_atoms():
    atoms = ase.Atoms("TiO2",
                      cell=[5, 5, 5],
                      positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    return atoms


@pytest.fixture
def sorted_atoms():
    atoms = ase.Atoms(numbers=[8, 8, 22],
                      cell=[5, 5, 5],
                      positions=[[1, 0, 0], [0, 1, 0], [0, 0, 0]])
    return atoms


def test_ase_to_castep_index(unsorted_atoms):
    res = ase_to_castep_index(unsorted_atoms, [0, 2, 1])
    assert res[0] == ["Ti", 1]
    assert res[1] == ["O", 2]
    assert res[2] == ["O", 1]


def test_sort_atoms(unsorted_atoms, sorted_atoms):
    unsorted_atoms = sort_atoms_castep(unsorted_atoms, copy=True)
    assert np.all(unsorted_atoms.numbers == sorted_atoms.numbers)


def test_check_sorted(unsorted_atoms, sorted_atoms):
    assert is_castep_sorted(unsorted_atoms) == False
    assert is_castep_sorted(sorted_atoms) == True
