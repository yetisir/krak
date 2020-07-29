def extrude_topography(surface, bottom_elevation):
    # TODO: rewrite to be coordinate system agnostic
    extruded_surface = surface.extrude(
        [0, 0, -1], surface.bounds[-1] - bottom_elevation)
    clipped_surface = extruded_surface.remesh().clip_closed(
        origin=[0, 0, bottom_elevation], normal=[0, 0, 1])
    return clipped_surface.remesh()
