import logging
import json
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, Enum, ForeignKey, func, select
from sqlalchemy.types import DECIMAL
from sqlalchemy.exc import SQLAlchemyError
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')

db_connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

db_connection = create_engine(db_connection_str)
metadata = MetaData()

# Definición de la tabla de categorías
categories = Table('categories', metadata,
                   Column('category_id', BINARY(16), primary_key=True),
                   Column('name', String(45), nullable=False))

# Definición de la tabla de films
films = Table('films', metadata,
              Column('film_id', BINARY(16), primary_key=True),
              Column('title', String(60), nullable=False),
              Column('description', String(255), nullable=False),
              Column('length', DECIMAL(4, 2), nullable=False),
              Column('status', Enum('Activo', 'Inactivo', name='status_enum'), nullable=False),
              Column('fk_category', BINARY(16), ForeignKey('categories.category_id'), nullable=False),
              Column('front_page', String(255), nullable=False),
              Column('file', String(255), nullable=False),
              Column('banner', String(255), nullable=True)
              )


def lambda_handler(event, context):
    try:
        conn = db_connection.connect()

        query = select(
            films.c.film_id, films.c.title, films.c.description, films.c.length, films.c.status, films.c.fk_category,
            films.c.front_page, films.c.file, films.c.banner).order_by(func.rand()).limit(10)

        result = conn.execute(query)
        film_list = [
            {column: value.hex() if isinstance(value, bytes) else (
                float(value) if isinstance(value, Decimal) else value)
             for column, value in zip(result.keys(), row)}
            for row in result
        ]
        conn.close()

        if not film_list:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('No se encontraron películas registradas')
            }

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps(film_list)
        }

    except SQLAlchemyError as e:
        logger.error(f"Error fetching films: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error fetching films')
        }

    except Exception as ex:
        logger.error(f"Exception: {str(ex)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps(f"Exception: {str(ex)}")
        }
