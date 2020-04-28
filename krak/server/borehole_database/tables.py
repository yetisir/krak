import pathlib

import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable


Base = declarative_base()


class Surveys(Base):
    __tablename__ = 'surveys'

    survey_id = sql.Column(sql.Integer(), primary_key=True)
    borehole_id = sql.Column(
            sql.Integer(), sql.ForeignKey('boreholes.borehole_id'))
    depth = sql.Column(sql.Float(), nullable=False)
    survey_id = sql.Column(sql.Integer(), primary_key=True, nullable=False)
    azimuth = sql.Column(sql.Float(), nullable=False)
    dip = sql.Column(sql.Float(), nullable=False)


class Boreholes(Base):
    __tablename__ = 'boreholes'

    borehole_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)
    x = sql.Column(sql.Float(), nullable=False)
    y = sql.Column(sql.Float(), nullable=False)
    z = sql.Column(sql.Float(), nullable=False)


class Lithology_logs(Base):
    __tablename__ = 'lithology_logs'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('boreholes.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    lithology_id = sql.Column(sql.Float(), nullable=False)
    comments = sql.Column(sql.String(1024))


class PhotoLogs(Base):
    __tablename__ = 'photo_logs'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('boreholes.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    photo_id = sql.Column(sql.Float(), nullable=False)
    comments = sql.Column(sql.String(1024))


class Photos(Base):
    __tablename__ = 'photos'

    photo_id = sql.Column(sql.Integer(), primary_key=True)
    path = sql.Column(sql.String(1024), nullable=False)


class Lithologies(Base):
    __tablename__ = 'lithologies'

    lithology_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)


def generate_sql():
    sql_queries = []

    for table in Base.metadata.tables.values():
        sql_queries.append(
            str(CreateTable(table).compile(dialect=postgresql.dialect())))

    sql_file_path = pathlib.Path(__file__).with_suffix('.sql')

    with open(sql_file_path, 'w') as sql_file:
        sql_file.write('-- Automatically generated queries from tables.py\n')
        sql_file.write(''.join(sql_queries))
