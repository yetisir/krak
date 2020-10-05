from pyvista import examples

from . import mesh


def random_hills():
    return mesh.load_mesh(examples.load_random_hills())


def lidar():
    return mesh.load_mesh(examples.download_lidar())


def crater_topo():
    return mesh.load_mesh(examples.download_crater_topo)

# def

# examples.download_damavand_volcano

# examples.download_faults

# examples.download_saddle_surface

# examples.download_tetra_dc_mesh

# examples.load_channels()

# examples.download_honolulu

# examples.download_sky_box_nz

# examples.download_structured_grid
# examples.download_structured_grid_two

# examples.download_unstructured_grid

# examples.download_topo_global

# examples.download_topo_land

# examples.download_usa
