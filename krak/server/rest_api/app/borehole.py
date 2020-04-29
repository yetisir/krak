from flask import make_response, abort

from . import tables, sql


def read_all():

    boreholes = tables.Borehole.query.order_by(
        tables.Borehole.borehole_id).all()
    schema = tables.Borehole.__marshmallow__(many=True)
    return schema.dump(boreholes)


def read_one(borehole_id):
    borehole_id_match = (
        tables.Borehole.query
        .filter(tables.Borehole.borehole_id == borehole_id)
        .one_or_none()
    )

    if not borehole_id_match:
        abort(404, f'Borehole id {borehole_id} not found')

    schema = tables.Borehole.__marshmallow__()
    return schema.dump(borehole_id_match)


def create(body):
    borehole = body
    borehole_name = borehole.get('name')

    borehole_name_match = (
        tables.Borehole.query
        .filter(tables.Borehole.name == borehole_name)
        .one_or_none()
    )

    if borehole_name_match:
        abort(409, f'Borehole {borehole_name} exists already')

    schema = tables.Borehole.__marshmallow__()
    new_borehole = schema.load(borehole, session=sql.session)

    sql.session.add(new_borehole)
    sql.session.commit()

    return schema.dump(new_borehole), 201


def update(body, borehole_id):
    borehole = body
    borehole_name = borehole.get('name')

    borehole_id_match = (
        tables.Borehole.query
        .filter(tables.Borehole.borehole_id == borehole_id)
        .one_or_none()
    )

    if not borehole_id_match:
        abort(404, f'Borehole with id {borehole_id} does not exist')

    borehole_name_match = (
        tables.Borehole.query
        .filter(tables.Borehole.name == borehole_name)
        .one_or_none()
    )

    if (
            borehole_name_match is not None and
            borehole_name_match.borehole_id != borehole_id):
        abort(409, f'Borehole name {borehole_name} already exists')

    schema = tables.Borehole.__marshmallow__()
    update = schema.load(borehole, session=sql.session)
    update.borehole_id = borehole_id

    sql.session.merge(update)
    sql.session.commit()

    return schema.dump(update), 201


def delete(borehole_id):

    borehole_id_match = (
        tables.Borehole.query
        .filter(tables.Borehole.borehole_id == borehole_id)
        .one_or_none()
    )

    if not borehole_id_match:
        abort(404, f'Borehole id {borehole_id} not found')

    sql.session.delete(borehole_id_match)
    sql.session.commit()
    return make_response(f'Borehole id {borehole_id} deleted')
