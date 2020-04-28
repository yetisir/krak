from flask import make_response, abort
from . import sql, tables


def read_all():

    boreholes = tables.Borehole.query.order_by(Borehole.id).all()
    schema = tables.Borehole.__marshmallow__(many=True)
    return schema.dump(boreholes)


def read_one(borehole_id):
    borehole = _borehole(borehole_id)

    if not borehole:
        abort(404, f'Borehole id {borehole_id} not found')

    schema = tables.Borehole.__marshmallow__()
    return schema.dump(borehole)


def create(borehole):

    borehole_id = borehole.get('borehole_id')
    if _borehole(borehole_id):
        abort(409, f'Borehole with id {borehole_id} exists already')

    schema = tables.Borehole.__marshmallow__()
    new_borehole = schema.load(borehole, session=sql.session)

    sql.session.add(new_borehole)
    db.session.commit()

    return schema.dump(new_borehole), 201


def update(borehole_id, borehole):

     borehole_id = borehole.get('borehole_id')
     if not _borehole(borehole_id):
         abort(409, f'Borehole with id {borehole_id} doesnt exist')

     schema = tables.Borehole.__marshmallow__()
     update = schema.load(borehole, session=sql.session)

     sql.session.merge(new_borehole)
     db.session.commit()

     return schema.dump(update), 201


def delete(borehole_id):

    borehole = _borehole(borehole_id)

    if not borehole:
        abort(404, f'Borehole id {borhole_id} not found')

    sql.session.delete(borehole)
    sql.session.commit
    return make_response(f'Borehole id {borehole_id) deleted')


def _borehole(borehole_id):
     borehole_exists = (
         tables.Borehole.query
         .filter(tables.Borehole.borehole_id = borhole_id)
         .one_or_none()
     )



