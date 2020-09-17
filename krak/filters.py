from abc import ABC, abstractmethod

import numpy as np
import pymesh
import pyvista
import tetgen
from tqdm import tqdm
import vtk

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


class Transform:
    def transform(self, transform, mesh):
        transform_filter = vtk.vtkTransformFilter()
        transform_filter.SetInputData(mesh.pyvista)
        transform_filter.SetTransform(transform)
        transform_filter.Update()

        return transform_filter.GetOutput()


class Translate(Filter, Transform):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, distance=None, direction=(0, 0, 1)):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction)
        if distance is not None:
            self.direction = self.direction.scale(distance)

    def filter(self):
        transform = vtk.vtkTransform()
        transform.Translate(self.direction)
        transformed_mesh = self.transform(transform, self.mesh)

        return self.mesh.mesh_class()(
            transformed_mesh, parents=[self.mesh]).clean()


class TranslateX(Translate):
    def __init__(self, mesh, distance=0):
        super().__init__(mesh, direction=(1, 0, 0), distance=distance)


class TranslateY(Translate):
    def __init__(self, mesh, distance=0):
        super().__init__(mesh, direction=(0, 1, 0), distance=distance)


class TranslateZ(Translate):
    def __init__(self, mesh, distance=0):
        super().__init__(mesh, direction=(0, 0, 1), distance=distance)


class Rotate(Filter, Transform):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, angle=0, origin=None, axis=(0, 0, 1)):
        super().__init__(mesh)
        self.axis = axis
        self.origin = origin or mesh.center
        self.angle = angle

    def filter(self):
        transform = vtk.vtkTransform()
        transform.Translate([-i for i in self.origin])
        transform.RotateWXYZ(self.angle, *self.axis)
        transform.Translate(self.origin)

        transformed_mesh = self.transform(transform, self.mesh)
        return self.mesh.mesh_class()(
            transformed_mesh, parents=[self.mesh]).clean()


class RotateX(Rotate):
    def __init__(self, mesh, angle=0, origin=None):
        super().__init__(mesh, axis=(1, 0, 0), origin=origin, angle=angle)


class RotateY(Rotate):
    def __init__(self, mesh, angle=0, origin=None):
        super().__init__(mesh, axis=(0, 1, 0), origin=origin, angle=angle)


class RotateZ(Rotate):
    def __init__(self, mesh, angle=0, origin=None):
        super().__init__(mesh, axis=(0, 0, 1), origin=origin, angle=angle)


class Scale(Filter, Transform):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, ratio=1, origin=None):
        super().__init__(mesh)
        self.ratio = ratio
        self.origin = origin or mesh.center

    def filter(self):
        transform = vtk.vtkTransform()
        transform.Translate([-i for i in self.origin])
        transform.Scale(self.ratio)
        transform.Translate(self.origin)
        transformed_mesh = self.transform(transform, self.mesh)

        return self.mesh.mesh_class()(
            transformed_mesh, parents=[self.mesh]).clean()


class ScaleX(Scale):
    def __init__(self, mesh, ratio=1, origin=None):
        super().__init__(mesh, origin=origin, ratio=(ratio, 0, 0))


class ScaleY(Scale):
    def __init__(self, mesh, ratio=1, origin=None):
        super().__init__(mesh, origin=origin, ratio=(0, ratio, 0))


class ScaleZ(Scale):
    def __init__(self, mesh, ratio=1, origin=None):
        super().__init__(mesh, origin=origin, ratio=(0, 0, ratio))


class Clip(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(
            self, mesh, plane=None, origin=None, normal=(0, 0, 1), flip=False):
        super().__init__(mesh)
        origin = origin or mesh.center

        if flip:
            normal = [-i for i in normal]
        if plane is None:
            plane = spatial.Plane(origin=origin, normal=normal)
        self.plane = plane

    def filter(self):
        mesh = self.mesh.pyvista.clip(
            normal=self.plane.normal, origin=self.plane.origin)

        return self.mesh.mesh_class()(mesh, parents=[self.mesh]).clean()


class ClipClosed(Clip):
    dimensions = [2]

    def filter(self):
        plane = self.plane.flip()
        vtk_plane = vtk.vtkPlane()
        vtk_plane.SetOrigin(plane.origin)
        vtk_plane.SetNormal(plane.orientation)

        plane_collection = vtk.vtkPlaneCollection()
        plane_collection.AddItem(vtk_plane)

        clipper = vtk.vtkClipClosedSurface()
        clipper.SetClippingPlanes(plane_collection)
        clipper.SetInputData(self.mesh.pyvista.extract_surface())
        clipper.Update()

        return self.mesh.mesh_class()(
            clipper.GetOutput(), parents=[self.mesh]).clean()


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


class Triangulate(Filter):
    dimensions = [2]

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().triangulate()
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
        return self.mesh.mesh_class()(
            mesh.clean(), parents=self.mesh.parents)


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
        return self.mesh.mesh_class(offset=1)(
            voxelized_mesh, parents=[self.mesh])


class Boundary(Filter):
    dimensions = [1, 2]

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

        super().__init__(mesh.triangulate())
        self.max_iterations = max_iterations
        self.max_length = max_length
        self.max_angle = max_angle
        self.tolerance = tolerance

        if size_absolute is None:
            bbox_diff = [bound[1] - bound[0] for bound in mesh.bounds]
            size_absolute = np.linalg.norm(bbox_diff) * size_relative

        self.size_absolute = size_absolute

    def filter(self):
        mesh = pymesh.form_mesh(
            self.mesh.points.values, self.mesh.cells.values)

        mesh, _ = pymesh.remove_degenerated_triangles(
            mesh, self.max_iterations)
        mesh, _ = pymesh.split_long_edges(mesh, self.size_absolute)
        num_vertices = mesh.num_vertices
        for _ in range(self.max_iterations):
            mesh, _ = pymesh.collapse_short_edges(
                mesh, self.size_absolute, preserve_feature=True)
            mesh, _ = pymesh.remove_obtuse_triangles(
                mesh, self.max_angle, self.max_iterations)

            if mesh.num_vertices == num_vertices:
                break

            num_vertices = mesh.num_vertices

        return self.mesh.mesh_class()(mesh, parents=[self.mesh]).clean()


class CellEdges(Filter):
    dimensions = [2, 3]

    def filter(self):
        mesh = self.mesh.pyvista.extract_all_edges()
        return self.mesh.mesh_class(1)(mesh, parents=[self.mesh])


class Intersection(Filter):
    dimensions = [2]
