from abc import ABC, abstractmethod

import numpy as np
import pymesh
import pyvista
import tetgen
from tqdm import tqdm

from . import spatial


class Filter(ABC):
    def __init__(self, mesh, **kwargs):
        if mesh.dimension not in self.dimensions:
            raise ValueError('Mesh dimension is not supported by Filter')
        self.mesh = mesh

    @abstractmethod
    def filter(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self):
        raise NotImplementedError


class Translate(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, direction=(0, 0, 1), distance=0):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        # TODO: use vtk tranform methods
        mesh = self.mesh.copy().pyvista
        mesh.translate(self.direction)
        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class Rotate(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, axis=(0, 0, 1), angle=0):
        pass

    def filter(self):
        pass


class Scale(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, reference=(0, 0, 0), ratio=1):
        pass

    def filter(self):
        pass


class Clip(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, surface, direction):
        pass

    def filter(self):
        pass

#     def clip_closed(self, plane=None, **kwargs):
#         if plane is None:
#             plane = spatial.Plane(**kwargs)
#
#         vtk_plane = vtk.vtkPlane()
#         vtk_plane.SetOrigin(*plane.origin)
#         vtk_plane.SetNormal(*plane.orientation)
#
#         plane_collection = vtk.vtkPlaneCollection()
#         plane_collection.AddItem(vtk_plane)
#
#         clipper = vtk.vtkClipClosedSurface()
#         clipper.SetClippingPlanes(plane_collection)
#         clipper.SetInputData(self._clean())
#         clipper.Update()
#         return SurfaceMesh.from_vtk(clipper.GetOutput())


class ClipClosed(Filter):
    dimensions = [2]

    def __init__(self, mesh, surface, direction):
        pass

    def filter(self):
        pass


class Flatten(Filter):
    dimensions = [0, 1, 2]

    def __init__(self, mesh, plane=None, origin=(0, 0, 0), normal=(0, 0, 1)):
        super().__init__(mesh)
        if plane is None:
            plane = spatial.Plane(origin=origin, normal=normal)
        self.plane = plane

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().project_points_to_plane(
            origin=self.plane.origin, normal=self.plane.orientation)
        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class Merge(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, *meshes):
        super().__init__(meshes[0])
        dimensions = [mesh.dimension for mesh in meshes]
        if len(set(dimensions)) > 1:
            raise ValueError(
                'Merge only possible for meshes of same dimension')

        self.meshes = meshes

    def filter(self):
        merged_mesh = self.meshes[0].pyvista
        for mesh in self.meshes[1:]:
            merged_mesh = merged_mesh.merge(mesh.pyvista)

        return self.meshes[0].mesh_class()(merged_mesh, parents=[self.meshes])


class Extrude(Filter):
    dimensions = [0, 1, 2]

    def __init__(self, mesh, direction=(0, 0, 1), distance=1):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        pass
        # TODO: proper extrusion


class ExtrudeSurface(Filter):
    dimensions = [2]

    def __init__(self, mesh, direction=(0, 0, 1), distance=0):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().extrude(self.direction)
        return self.mesh.mesh_class()(mesh, parents=[self.mesh]).clean()


class Split(Filter):
    dimensions = [1]  # ?

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        # TODO: finish splitting algorithm
        mesh = self.mesh.flatten()
        return self.mesh.mesh_class()(mesh)


class Clean(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        mesh = self.mesh.pyvista
        if self.mesh.dimension == 1:
            mesh = mesh.extract_surface()
        if self.mesh.dimension == 2:
            mesh = mesh.extract_surface()
        return self.mesh.mesh_class()(mesh.clean(), parents=[self.mesh.parents])


class Extend(Filter):
    dimensions = [1, 2]

    def __init__(self, mesh, direction=(0, 0, 1), distance=0):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        pass


class Copy(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        return self.mesh.mesh_class()(self.mesh.pyvista.copy(deep=True))


class TetrahedralMesh(Filter):
    dimensions = [2]

    def __init__(self, mesh, **kwargs):
        super().__init__(mesh)

        # TODO: specify kwargs
        self.kwargs = kwargs

    def filter(self):
        # TODO: check if watertight
        # TODO: replace with CGAL to avoid AGPL
        tetrahedralizer = tetgen.TetGen(
            self.mesh.clean().pyvista.extract_surface())
        tetrahedralizer.make_manifold()
        tetrahedralizer.tetrahedralize(**self.kwargs)
        return self.mesh.mesh_class(offset=1)(
            tetrahedralizer.grid, parents=[self.mesh])


class VoxelMesh(Filter):
    dimensions = [2]

    def __init__(self, mesh, **kwargs):
        super().__init__(mesh)

        # TODO: specify kwargs
        self.kwargs = kwargs

    def filter(self):
        voxelized_mesh = pyvista.voxelize(
            self.mesh.clean().pyvista, **self.kwargs)
        return self.mesh.mesh_class(offset=1)(voxelized_mesh, parents=[self.mesh])


class Boundary(Filter):
    dimensions = [1, 2]
    # TODO: distiguish between surface and boundary edge

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        boundary = self.mesh.pyvista.extract_feature_edges(
            manifold_edges=False, feature_edges=False)
        return self.mesh.mesh_class(dimension=1)(boundary, parents=[self.mesh])


class Surface(Filter):
    dimensions = [2, 3]

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        return self.mesh.mesh_class(dimension=2)(
            self.mesh.pyvista.extract_surface(), parents=[self.mesh])


class Remesh(Filter):
    # dimensions = [1, 2, 3]  # ?
    dimensions = [2]

    def __init__(
            self, mesh, max_length=1, max_angle=150, max_iterations=10,
            tolerance=1e-6, size_relative=1e-2, size_absolute=None):

        super().__init__(mesh)
        self.max_iterations = max_iterations
        self.max_length = max_length
        self.max_angle = max_angle
        self.tolerance = tolerance

        if size_absolute is None:
            bounds = np.array(mesh.bounds)
            bbox_min = bounds[range(0, 6, 2)]
            bbox_max = bounds[range(1, 6, 2)]
            size_absolute = np.linalg.norm(bbox_max - bbox_min) * size_relative

        self.size_absolute = size_absolute

    def filter(self):
        mesh = pymesh.form_mesh(
            self.mesh.points.values, self.mesh.cells.values)

        mesh, _ = pymesh.split_long_edges(mesh, self.size_absolute)
        num_vertices = mesh.num_vertices
        for _ in tqdm(range(self.max_iterations)):
            mesh, _ = pymesh.collapse_short_edges(
                mesh, self.size_absolute, preserve_feature=True)
            mesh, _ = pymesh.remove_obtuse_triangles(
                mesh, self.max_angle, self.max_iterations)

            if mesh.num_vertices == num_vertices:
                break

            num_vertices = mesh.num_vertices

        mesh = pymesh.resolve_self_intersection(mesh)
        mesh, _ = pymesh.remove_duplicated_faces(mesh)
        mesh = pymesh.compute_outer_hull(mesh)
        mesh, _ = pymesh.remove_duplicated_faces(mesh)
        mesh, _ = pymesh.remove_isolated_vertices(mesh)

        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class CellEdges(Filter):
    dimensions = [2, 3]

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        mesh = self.mesh.pyvista.extract_all_edges()
        return self.mesh.mesh_class(1)(mesh, parents=[self.mesh])
