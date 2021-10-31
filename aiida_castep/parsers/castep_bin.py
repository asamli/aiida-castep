"""
Parser interface for CASTEP bin file

A few quantities are only avaliable from the CASTEP bin file
"""
import numpy as np

from castepxbin import read_castep_bin
from .constants import units


class CastepBinParser:
    """
    Parser for the `castep_bin` file.

    The heavy lifting is done by the `castepxbin` package, but here we need to do unit
    conversion and reorganisation.
    """

    _supported_quantities = ('eigenvalues', 'occupations', 'kpoints', 'forces',
                             'fermi_energy', 'total_energy',
                             'scaled_positions')

    def __init__(self, fileobj=None, filename=None):
        """
        Instantiate from an file object
        """
        self.filename = filename
        if fileobj:
            self.fileobj = fileobj
        else:
            self.fileobj = open(filename, mode="rb")

        self.raw_data = read_castep_bin(fileobj=self.fileobj)
        self.data = {}

        # Close the file handle if it is opened by us
        if filename is not None:
            self.fileobj.close()

    @property
    def eigenvalues(self):
        """Return the eigenvalues array with shape (ns, nk, nb)"""
        array = self.raw_data.get('eigenvalues')
        if array is None:
            return None
        # Change from nb, nk, ns to ns, nk, nb
        array = np.swapaxes(array, 0, 2) * units['Eh']
        return array

    @property
    def total_energy(self):
        """Total energy in eV"""
        return self.raw_data['total_energy'] * units['Eh']

    @property
    def fermi_energy(self):
        """Fermi energy in eV"""
        return self.raw_data['fermi_energy'] * units['Eh']

    @property
    def occupancies(self):
        """Return the occupation array with shape (ns, nk, nb)"""
        array = self.raw_data.get('occupancies')
        if array is None:
            return None
        # Change from nb, nk, ns to ns, nk, nb
        array = np.swapaxes(array, 0, 2)
        return array

    @property
    def kpoints(self):
        """Return the kpoints array with shape (nk, 3)"""
        array = self.raw_data.get('kpoints_of_eigenvalues')
        if array is None:
            return None
        # Change from nb, nk, ns to ns, nk, nb
        array = np.swapaxes(array, 0, 1)
        return array

    @property
    def forces(self):
        """Return the force array in unit eV/A"""
        array = self.raw_data.get('forces')
        if array is None:
            return None
        forces = self._reindex3(array)
        forces = forces * (units['Eh'] / units['a0'])
        return forces

    @property
    def scaled_positions(self):
        """Return the scaled positions"""
        array = self.raw_data.get('ionic_positions')
        if array is None:
            return None
        return self._reindex3(array)

    @property
    def cell(self):
        """Cell matrix (of row vectors)"""
        array = self.raw_data.get('real_lattice')
        return array * units['a0']

    def _reindex3(self, array):
        """Reshape the array (N, i_ion, i_species) into the common (NION, N) shape"""
        nelem, _, nspecies = array.shape
        nions_in_species = self.raw_data['num_ions_in_species']
        nsites = sum(nions_in_species)
        output = np.zeros((nsites, nelem), dtype=array.dtype)

        # Reconstruct the array with shape (NIONS, N)
        i = 0
        for ispec in range(nspecies):
            for iion in range(nions_in_species[ispec]):
                output[i, :] = array[:, iion, ispec]
                i += 1

        return output

    def _reindex2(self, array):
        """Reshape the array (N, i_ion, i_species) into the common (NION, N) shape"""
        _, nspecies = array.shape
        nions_in_species = self.raw_data['num_ions_in_species']
        nsites = sum(nions_in_species)
        output = np.zeros(nsites, dtype=array.dtype)

        # Reconstruct the array with shape (NIONS, N)
        i = 0
        for ispec in range(nspecies):
            for iion in range(nions_in_species[ispec]):
                output[i] = array[iion, ispec]
                i += 1

        return output
