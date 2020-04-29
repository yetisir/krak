from flask import make_response, abort

from . import tables, sql


def read_all():

    photos = tables.CorePhotoLog.query.all()
    schema = tables.CorePhotoLog.__marshmallow__(many=True)
    return schema.dump(photos)

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
