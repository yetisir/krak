import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable


Base = declarative_base()


class Borehole(Base):
    __tablename__ = 'borehole'

    borehole_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)
    x = sql.Column(sql.Float(), nullable=False)
    y = sql.Column(sql.Float(), nullable=False)
    z = sql.Column(sql.Float(), nullable=False)


class Survey(Base):
    __tablename__ = 'survey'

    survey_id = sql.Column(sql.Integer(), primary_key=True)
    borehole_id = sql.Column(
            sql.Integer(), sql.ForeignKey('borehole.borehole_id'))
    depth = sql.Column(sql.Float(), nullable=False)
    survey_id = sql.Column(sql.Integer(), primary_key=True, nullable=False)
    azimuth = sql.Column(sql.Float(), nullable=False)
    dip = sql.Column(sql.Float(), nullable=False)


class Lithology(Base):
    __tablename__ = 'lithology'

    lithology_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)


class Lithology_log(Base):
    __tablename__ = 'lithology_log'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('borehole.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    lithology_id = sql.Column(
            sql.Integer(), sql.ForeignKey('lithology.lithology_id'),
            nullable=False)
    comments = sql.Column(sql.String(1024))


class CorePhotoLog(Base):
    __tablename__ = 'photo_log'

    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('borehole.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    path = sql.Column(sql.String(1024), nullable=False)
    comments = sql.Column(sql.String(1024))


def generate_sql(sql_file_path):
    sql_queries = []

    for table in Base.metadata.tables.values():
        table_sql = CreateTable(table).compile(dialect=postgresql.dialect())
        sql_queries.append(str(table_sql).strip() + ';')

    with open(sql_file_path, 'w') as sql_file:
        sql_file.write('-- Automatically generated queries from tables.py\n')
        sql_file.write('\n\n'.join(sql_queries))
