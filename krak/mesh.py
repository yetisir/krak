from abc import ABC, abstractmethod

import pandas
import pymesh
import pyvista
import tetgen
from tqdm import tqdm
import vtk

from . import spatial, tools, remesh


class Mesh(ABC):

    def __init__(self, mesh):
        super().__init__()

        self.pv_mesh = mesh.cast_to_unstructured_grid()
        self._remove_invalid_cells()

    def __add__(self, other):
        return self.merge(other)

    def __sub__(self, other):
        pass

    @classmethod
    def from_file(cls, file_name, file_type=None):
        return cls(pyvista.read_meshio(file_name, file_type))

    @classmethod
    def from_pyvista(cls, mesh):
        return cls(mesh)

    @classmethod
    def from_vtk(cls, mesh):
        return cls(pyvista.wrap(mesh))  # untested

    @classmethod
    def from_meshio(cls, mesh):
        return cls(pyvista.from_meshio(mesh))

    @property
    @abstractmethod
    def dimension(self):
        raise NotImplementedError

    def plot(self, *args, **kwargs):
        self.pv_mesh.plot(*args, **kwargs)

    @property
    def cells(self):
        # TODO: use meshios maps instead of iterating through vtk
        cell_list_connectivity = []
        start_index = 1

        cell_iterator = self.pv_mesh.NewCellIterator()
        cell_connectivity = self.pv_mesh.cells
        for i in range(self.pv_mesh.n_cells):
            end_index = start_index + cell_iterator.GetNumberOfPoints()
            cell_list_connectivity.append(
                cell_connectivity[start_index:end_index])
            start_index = end_index + 1

        return pandas.DataFrame(cell_list_connectivity).add_prefix('point_')

    @property
    def points(self):
        return pandas.DataFrame(self.pv_mesh.points, columns=['x', 'y', 'z'])

    def _remove_invalid_cells(self):
        invalid_cell_indices = [
            i for i, cell_type in enumerate(self.pv_mesh.celltypes)
            if cell_type not in self.supported_cell_types]
        self.pv_mesh.remove_cells(invalid_cell_indices)

    @property
    def supported_cell_types(self):
        return [
            cell_type for cell_type, dimension
            in Map.cell_dimensions.items()
            if dimension == self.dimension]

    @property
    def bounds(self):
        return self.pv_mesh.bounds

    def translate(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)

        copy = self.pv_mesh.copy(deep=True)
        copy.translate(direction)

        return self.__class__(copy)

    def rotate(self, axis, angle):
        pass

    def scale(self, reference, ratio):
        pass

    def clip(self, surface, direction):
        pass

    def cell_to_point(self):
        pass

    def point_to_cell(self):
        pass

    def flatten(self, plane=None):
        if plane is None:
            plane = spatial.Plane(origin=(0, 0, 0), normal=(0, 0, 1))

        flattened_mesh = self.pv_mesh.extract_surface().project_points_to_plane(
            origin=plane.origin, normal=plane.orientation)

        return self.__class__(flattened_mesh)

    def merge(self, *meshes):
        pv_mesh = self.pv_mesh
        for mesh in meshes:
            pv_mesh = pv_mesh.merge(mesh.pv_mesh)

        return self.__class__(pv_mesh)


class PointMesh(Mesh):
    dimension = 0

    def extrude(self, direction, distance):
        pass


class LineMesh(Mesh):
    dimension = 1

    def _clean_line(self):
        return self.pv_mesh.extract_surface().clean()

    def extrude(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)

        line = self._clean_line()
        extruded_surface = line.extrude(direction).triangulate()
        return SurfaceMesh(extruded_surface)

    def extend(self, direction, distance=None):
        pass

    def split(self, angle=90):
        flattened_mesh = self.flatten()._clean_line()



class SurfaceMesh(Mesh):
    dimension = 2
    # TODO: add watertight attribute

    def _clean_surface(self):
        return self.pv_mesh.extract_surface().clean()

    def _to_pymesh(self):
        return pymesh.form_mesh(self.points.values, self.cells.values)

    def tetrahedral_mesh(self, **kwargs):
        # TODO: check if watertight
        # TODO: replace with CGAL to avoid AGPL
        tetrahedralizer = tetgen.TetGen(self._clean_surface())
        tetrahedralizer.make_manifold()
        tetrahedralizer.tetrahedralize(**kwargs)
        return VolumeMesh(tetrahedralizer.grid)

    def voxel_mesh(self, **kwargs):
        # TODO: check if watertight
        voxelized_mesh = pyvista.voxelize(self._clean_surface(), **kwargs)
        return VolumeMesh(voxelized_mesh)

    def boundary(self):
        boundary = self._clean_surface().extract_feature_edges(
            manifold_edges=False, feature_edges=False)
        return LineMesh(boundary)

    def extrude(self, direction, distance=None):
        direction = spatial.Direction(direction).scale(distance)
        boundary = self.boundary()

        extruded_surface = boundary.extrude(direction)
        translated_surface = self.translate(direction)


        return self.merge(extruded_surface, translated_surface)

    def extend(self, direction, distance=None):
        pass

    def clip_closed(self, plane=None, **kwargs):
        if plane is None:
            plane = spatial.Plane(**kwargs)

        vtk_plane = vtk.vtkPlane()
        vtk_plane.SetOrigin(*plane.origin)
        vtk_plane.SetNormal(*plane.orientation)

        plane_collection = vtk.vtkPlaneCollection()
        plane_collection.AddItem(vtk_plane)

        clipper = vtk.vtkClipClosedSurface()
        clipper.SetClippingPlanes(plane_collection)
        clipper.SetInputData(self._clean_surface())
        clipper.Update()
        return SurfaceMesh.from_vtk(clipper.GetOutput())

    def _split_long_edges(self, max_length):
        mesh = pymesh.form_mesh(self.points.values, self.cells.values)
        split_mesh, _ = pymesh.split_long_edges(mesh, max_length)
        return tools.create_mesh(split_mesh.vertices, split_mesh.faces)

    def _collapse_short_edges(self, min_length):
        mesh = pymesh.form_mesh(self.points.values, self.cells.values)
        collapsed_mesh, _ = pymesh.collapse_short_edges(mesh, min_length, preserve_feature=True)
        return tools.create_mesh(collapsed_mesh.vertices, collapsed_mesh.faces)

    def _to_pymesh(self):
        return pymesh.form_mesh(self.points.values, self.cells.values)


    def remesh(self, detail='low', algorithm='general'):
        # TODO: rewrite
        #if size is None:
        #    cell_sizes = self.pv_mesh.compute_cell_sizes()
        #    size = average_cell_size = cell_sizes.cell_arrays['Area'].mean()

        algorithm_map = {
            'general': remesh.gen_remesh,
            'greedy': remesh.gre_remesh,
            'incremental': remesh.inc_remesh,
        }

        return tools.load_mesh(algorithm_map[algorithm](self._to_pymesh(), detail=detail))

class VolumeMesh(Mesh):
    dimension = 3

    def surface_mesh(self):
        return SurfaceMesh(self.pv_mesh.extract_surface().clean())


class Map:

    cell_dimensions = {
        0: None,  # empty
        1: 0,  # vertex
        2: 0,  # poly_vertex
        3: 1,  # line
        4: 1,  # poly_line
        5: 2,  # triangle
        6: 2,  # triangle_strip
        7: 2,  # polygon
        8: 2,  # pixel
        9: 2,  # quad
        10: 3,  # tetra
        11: 3,  # voxel
        12: 3,  # hexahedron
        13: 3,  # wedge
        14: 3,  # pyramid
        15: 3,  # penta_prism
        16: 3,  # hexa_prism
        21: 1,  # line3
        22: 2,  # triangle6
        23: 2,  # quad8
        24: 3,  # tetra10
        25: 3,  # hexahedron20
        26: 3,  # wedge15
        27: 3,  # pyramid13
        28: 2,  # quad9
        29: 3,  # hexahedron27
        30: 2,  # quad6
        31: 3,  # wedge12
        32: 3,  # wedge18
        33: 3,  # hexahedron24
        34: 2,  # triangle7
        35: 1,  # line4
        42: 3,  # polyhedron
    }

    dimension_classes = {
            0: PointMesh,
            1: LineMesh,
            2: SurfaceMesh,
            3: VolumeMesh,
        }


def dimension_class(dimension):
    return Map.dimension_classes[dimension]


def cell_dimension(cell_type):
    return Map.cell_dimensions[cell_type]
