from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable
from sqlalchemy.orm import mapper

from . import sql, ma


class Borehole(sql.Model):
    borehole_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)
    easting = sql.Column(sql.Float(), nullable=False)
    northing = sql.Column(sql.Float(), nullable=False)
    elevation = sql.Column(sql.Float(), nullable=False)


class Survey(sql.Model):
    survey_id = sql.Column(sql.Integer(), primary_key=True)
    borehole_id = sql.Column(
            sql.Integer(), sql.ForeignKey('borehole.borehole_id'))
    depth = sql.Column(sql.Float(), nullable=False)
    survey_id = sql.Column(sql.Integer(), primary_key=True, nullable=False)
    azimuth = sql.Column(sql.Float(), nullable=False)
    dip = sql.Column(sql.Float(), nullable=False)


class Lithology(sql.Model):
    lithology_id = sql.Column(sql.Integer(), primary_key=True)
    name = sql.Column(sql.String(64), nullable=False)


class LithologyLog(sql.Model):
    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('borehole.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    lithology_id = sql.Column(
            sql.Integer(), sql.ForeignKey('lithology.lithology_id'),
            nullable=False)
    comments = sql.Column(sql.String(1024))


class CorePhotoLog(sql.Model):
    borehole_id = sql.Column(
        sql.Integer(), sql.ForeignKey('borehole.borehole_id'),
        primary_key=True)
    depth_from = sql.Column(sql.Float(), primary_key=True)
    depth_to = sql.Column(sql.Float(), nullable=False)
    path = sql.Column(sql.String(1024), nullable=False)
    comments = sql.Column(sql.String(1024))


def generate_sql(sql_file_path):
    sql_queries = []

    for table in sql.Model.metadata.tables.values():
        table_sql = CreateTable(table).compile(dialect=postgresql.dialect())
        sql_queries.append(str(table_sql).strip() + ';')

    with open(sql_file_path, 'w') as sql_file:
        sql_file.write('-- Automatically generated queries from tables.py\n')
        sql_file.write('\n\n'.join(sql_queries))


def setup_schema():
    for cls in sql.Model._decl_class_registry.values():
        if not hasattr(cls, '__tablename__'):
            continue

        class Meta:
            model = cls
            sqla_session = sql.session
            load_instance=True

        schema_class_name = f'{cls.__name__}Schema'
        schema_class = type(
            schema_class_name, (ma.SQLAlchemyAutoSchema, ), {'Meta': Meta})

        setattr(cls, '__marshmallow__', schema_class)
