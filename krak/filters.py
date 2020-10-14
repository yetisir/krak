from abc import ABC, abstractmethod

import numpy as np
import pymesh
import pyvista
import tetgen
# from tqdm import tqdm
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

    def __init__(self, mesh, direction=(0, 0, 1), distance=None):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction)
        if distance is not None:
            self.direction = self.direction.scale(distance)

    def filter(self):
        transform = vtk.vtkTransform()
        transform.Translate(self.direction)
        transformed_mesh = self.transform(transform, self.mesh)

        return self.mesh.mesh_class()(
            transformed_mesh, parents=[self.mesh])


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
            transformed_mesh, parents=[self.mesh])


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
            transformed_mesh, parents=[self.mesh])


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
            self, mesh, surface=None, bounds=None, plane=None, origin=None,
            normal=(0, 0, -1), flip=False, closed=False):
        super().__init__(mesh)
        origin = origin or mesh.center

        if flip:
            normal = [-i for i in normal]
        if plane is None:
            plane = spatial.Plane(origin=origin, normal=normal)
        self.plane = plane

        self.closed = closed

        if surface is not None:
            # TODO: implement surface clipping
            raise NotImplementedError
        if bounds is not None:
            # TODO: implement bounds clipping
            raise NotImplementedError
        self.surface = surface
        self.bounds = bounds

    def filter(self):
        mesh = self.mesh.pyvista.clip(
            normal=self.plane.normal, origin=self.plane.origin)

        clipped = self.mesh.mesh_class()(mesh, parents=[self.mesh])

        if not self.closed:
            return clipped

        if not self.mesh.manifold:
            raise ValueError(
                'Cannot close surface on non-manifold surface')

        caps = self._caps(clipped)

        return self.mesh.mesh_class()(
            caps.merge(clipped.pyvista.extract_surface()), parents=[self.mesh])

    def _caps(self, mesh):
        boundaries = mesh.clean().boundary().pyvista.split_bodies()

        caps = None

        for boundary in boundaries:
            boundary = mesh.load_mesh(boundary)
            points = self._order_points(boundary.cells)

            vtk_points = vtk.vtkPoints()
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(len(points))

            for i, point in enumerate(points):
                vtk_points.InsertPoint(i, boundary.points.loc[point].values)
                polygon.GetPointIds().SetId(i, i)

            polygon_list = vtk.vtkCellArray()
            polygon_list.InsertNextCell(polygon)

            cap = vtk.vtkPolyData()
            cap.SetPoints(vtk_points)
            cap.SetPolys(polygon_list)

            cap = pyvista.wrap(cap).triangulate()

            if caps is None:
                caps = cap
            else:
                caps = caps.merge(cap)

        return caps

    def _order_points(self, edges):

        ordered_points = edges.loc[0].to_list()
        edges = edges.drop(0)

        while len(edges):
            start = ordered_points[-1]
            connected_edge = edges[(edges == start).any(axis=1)]
            end = [i for i in connected_edge.iloc[0] if i != start]
            ordered_points.extend(end)
            edges = edges.drop(connected_edge.index)

        return ordered_points


class Flatten(Filter):
    dimensions = [0, 1, 2]

    def __init__(self, mesh, plane=None, origin=None, normal=(0, 0, 1)):
        super().__init__(mesh)
        if origin is None:
            origin = mesh.center
        if plane is None:
            plane = spatial.Plane(origin=origin, normal=normal)
        self.plane = plane

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().project_points_to_plane(
            origin=self.plane.origin, normal=self.plane.orientation)
        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class Merge(Filter):
    dimensions = [0, 1, 2, 3]

    def __init__(self, mesh, other, merge_points=False):
        super().__init__(mesh)
        if mesh.dimension != other.dimension:
            raise ValueError(
                'Merge only possible for meshes of same dimension')

        self.other = other
        self.merge_points = merge_points

    def filter(self):
        merged_mesh = self.mesh.pyvista.merge(
            self.other.pyvista, merge_points=self.merge_points)

        return self.mesh.mesh_class()(merged_mesh, parents=[self.mesh])


class Extrude(Filter):
    dimensions = [0, 1]  # , 2] TODO: add 2d to 3d extrusion

    def __init__(self, mesh, direction=(0, 0, 1), distance=None):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().extrude(self.direction)
        return self.mesh.mesh_class(offset=1)(mesh, parents=[self.mesh])


class ExtrudeSurface(Filter):
    dimensions = [2]

    def __init__(self, mesh, direction=(0, 0, 1), distance=None):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)

    def filter(self):
        mesh = self.mesh.pyvista.extract_surface().extrude(self.direction)
        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class Triangulate(Filter):
    dimensions = [2]

    def filter(self):
        triangle_filter = vtk.vtkTriangleFilter()
        triangle_filter.SetInputData(self.mesh.pyvista.extract_surface())
        triangle_filter.Update()
        return self.mesh.mesh_class()(
            pyvista.wrap(triangle_filter.GetOutput()), parents=[self.mesh])


class Split(Filter):
    dimensions = [1]  # ?

    def __init__(self, mesh):
        super().__init__(mesh)

    def filter(self):
        # TODO: finish splitting algorithm
        raise NotImplementedError


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

    def __init__(
            self, mesh, direction=(0, 0, 1), distance=None, orientation=None,
            snap_to_axis=True, tolerance=1e-6, orientation_filter=0.5,
            quality_filter=0.01):
        super().__init__(mesh)
        self.direction = spatial.Direction(direction).scale(distance)
        self.tolerance = tolerance
        self.orientation_filter = orientation_filter
        self.quality_filter = quality_filter

        if orientation is None:
            orientation = mesh.orientation

        if snap_to_axis:
            snapped_orientation = [0, 0, 0]
            argmax = np.argmax(np.abs(orientation))
            snapped_orientation[argmax] = 1
            orientation = snapped_orientation

        self.orientation = spatial.Orientation(normal=orientation)

    def filter(self):
        function_map = {
            1: self._1D,
            2: self._2D,
        }
        return function_map[self.mesh.dimension]()

    def _1D(self):
        raise NotImplementedError

    def _get_leading_boundary(self):
        flattened_mesh = self.mesh.flatten(normal=self.orientation)

        boundary = flattened_mesh.boundary()
        size = self.mesh.size_magnitude
        thick_boundary = boundary.translate(
            direction=self.orientation,
            distance=size/20
        ).extrude(self.orientation.flip().scale(size/10))

        ray_direction = self.direction >> self.orientation

        obb_tree = vtk.vtkOBBTree()
        obb_tree.SetDataSet(thick_boundary.pyvista.extract_surface())
        obb_tree.BuildLocator()

        points = boundary.points
        cells = boundary.cells

        intersection_points = vtk.vtkPoints()
        intersection_cell_ids = vtk.vtkIdList()

        intersection_counts = []
        for point_id, point in points.iterrows():
            source = spatial.Position(
                point) + ray_direction.unit * size * self.tolerance
            target = source + ray_direction.unit * size
            obb_tree.IntersectWithLine(
                source, target, intersection_points, intersection_cell_ids)
            intersection_counts.append(intersection_cell_ids.GetNumberOfIds())
        remove_points = points[
            np.array(intersection_counts) != 0]
        cells = cells[(~cells.isin(remove_points.index)).all(axis=1)]

        return self.mesh.mesh_class(offset=-1)(
            self.mesh.boundary().pyvista.extract_cells(cells.index.values))

    def _2D(self):

        leading_boundary = self._get_leading_boundary()
        orientation = self.orientation
        flat_boundary = leading_boundary.flatten(normal=orientation)
        flat_boundary_points = flat_boundary.points

        ids = []
        dp = []
        for line_id, line_conectivity in flat_boundary.cells.iterrows():
            start = flat_boundary_points.loc[line_conectivity[0]].values
            end = flat_boundary_points.loc[line_conectivity[1]].values
            direction = spatial.Direction(start - end)

            orientation_diff = np.abs((
                (direction >> orientation).unit *
                (self.direction >> orientation).unit))
            if orientation_diff < self.orientation_filter:
                ids.append(line_id)
                dp.append(orientation_diff)

        leading_boundary = self.mesh.load_mesh(
            leading_boundary.pyvista.extract_cells(ids))

        extension = leading_boundary.extrude(direction=self.direction)

        mesh = self.mesh.merge(extension).clean()

        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class Expand(Filter):
    dimensions = [2]

    def __init__(self, mesh, distance):
        super().__init__(mesh)
        self.distance = distance

    def filter(self):
        primary_extension, orthogonal_extension, orientation = (
            self.mesh.oriented_axes)

        extrusions = [
            primary_extension.flip(),
            primary_extension,
            orthogonal_extension.flip(),
            orthogonal_extension,
        ]

        mesh = self.mesh
        for extrusion in extrusions:
            mesh = mesh.extend(
                orientation=orientation,
                direction=extrusion,
                distance=self.distance,
                snap_to_axis=False)

        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


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
            self.mesh.pyvista.extract_surface())
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
            self.mesh.pyvista, **self.kwargs)
        return self.mesh.mesh_class(offset=1)(
            voxelized_mesh, parents=[self.mesh])


class Boundary(Filter):
    dimensions = [1, 2]

    def filter(self):
        boundary = self.mesh.pyvista.extract_feature_edges(
            boundary_edges=True,
            manifold_edges=False,
            feature_edges=False,
            non_manifold_edges=False,
        )
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
    # TODO: implement remeshing for 1 and 3 dimensional meshes
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
            size_absolute = mesh.size_magnitude * size_relative

        self.size = size_absolute

    def filter(self):
        mesh = pymesh.form_mesh(
            self.mesh.points.values, self.mesh.cells.values)

        mesh, _ = pymesh.remove_degenerated_triangles(
            mesh, self.max_iterations)
        mesh, _ = pymesh.split_long_edges(mesh, self.size)
        num_vertices = mesh.num_vertices
        for _ in range(self.max_iterations):
            mesh, _ = pymesh.collapse_short_edges(
                mesh, self.size, preserve_feature=True)
            mesh, _ = pymesh.remove_obtuse_triangles(
                mesh, self.max_angle, self.max_iterations)

            if mesh.num_vertices == num_vertices:
                break

            num_vertices = mesh.num_vertices

        return self.mesh.mesh_class()(mesh, parents=[self.mesh])


class CellEdges(Filter):
    dimensions = [2, 3]

    def filter(self):
        mesh = self.mesh.pyvista.extract_all_edges()
        return self.mesh.mesh_class(1)(mesh, parents=[self.mesh])


class Intersection(Filter):
    dimensions = [2]

    def filter(self, other):
        # TODO
        pass


class Union(Filter):
    dimensions = [2]

    def filter(self):
        # TODO
        pass


class Subtract(Filter):
    dimensions = [2]

    def filter(self):
        # TODO
        pass
