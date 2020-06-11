from . import mesh


cell_dimension_map = {
    1: 0,
    2: 0,
    3: 1,
    4: 1,
    5: 2,
    6: 2,
    7: 2,
    8: 2,
    9: 2,
    10: 3,
    11: 3,
    12: 3,
    13: 3,
    14: 3,
}

dimension_mesh_map = {
    0: mesh.PointMesh,
    1: mesh.LineMesh,
    2: mesh.SurfaceMesh,
    3: mesh.VolumeMesh,
}
