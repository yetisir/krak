from flask import make_response, abort

from . import tables, sql, app


def read_all():

    photos = tables.CorePhotoLog.query.all()
    schema = tables.CorePhotoLog.__marshmallow__(many=True)
    return schema.dump(photos)

def create(body):
    photo_data = body

    photo = body.get('photo')
    photo_hash = hash(photo)

    corners = []

    temp = tables.CorePhotoCorner.query.all()

    for corner in photo_data.get('crop_corners'):

        corner_schema = tables.CorePhotoCorner.__marshmallow__()
        new_corner = corner_schema.load(corner, session=sql.session)
        corners.append(new_corner)
        sql.session.add(new_corner)


    photo_data['hash'] = photo_hash
    photo_data['path'] = photo_hash
    photo_data['crop_corner_1'] = corners[0].corner_id
    photo_data['crop_corner_2'] = corners[1].corner_id
    photo_data['crop_corner_3'] = corners[2].corner_id
    photo_data['crop_corner_4'] = corners[3].corner_id


    #borehole_name_match = (
    #    tables.Borehole.query
    #    .filter(tables.Borehole.name == borehole_name)
    #    .one_or_none()
    #)

    #if borehole_name_match:
    #    abort(409, f'Borehole {borehole_name} exists already')

    app.logger.info('345345345&&&&&&&&&&&&&&&&&&&&&&&&**********')
    app.logger.info(photo_data)


    schema = tables.CorePhotoLog.__marshmallow__()
    new_photo = schema.load(photo_data, session=sql.session)

    sql.session.add(new_photo)
    sql.session.commit()


    return schema.dump(new_photo), 201
