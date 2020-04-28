import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Surveys(Base):
    __tablename__ = 'surveys'

    survey_id = sql.Column(sql.Integer(), primary_key=True)
    borehole_id = sql.Column(
            sql.Integer(), sql.ForeignKey('boreholes.borehole_id'))
    depth = sql.Column(sql.Float())
    survey_id = sql.Column(sql.Integer(), primary_key=True)
    azimuth = sql.Column(sql.Float())
    dip = sql.Column(sql.Float())


class Boreholes(Base):
    __tablename__ = 'boreholes'

    borehole_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64))
    x = sql.Column(sql.Float())
    y = sql.Column(sql.Float())
    z = sql.Column(sql.Float())


class Lithology_logs(Base):
    __tablename__ = 'lithology_logs'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('boreholes.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float())
    lithology_id = sql.Column(sql.Float())
    comments = sql.Column(sql.String(1024))


class PhotoLogs(Base):
    __tablename__ = 'photo_logs'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('boreholes.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float())
    photo_id = sql.Column(sql.Float())
    comments = sql.Column(sql.String(1024))


class Photos(Base):
    __tablename__ = 'photos'

    photo_id = sql.Column(sql.Integer(), primary_key=True)
    path = sql.Column(sql.string(1024))


class Lithologies(Base):
    __tablename__ = 'lithologies'

    lithology_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.string(1024))
