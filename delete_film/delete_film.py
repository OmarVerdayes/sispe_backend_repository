import os
import logging
import json
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, Enum, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.types import DECIMAL

# Configuración del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración de la base de datos
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
db_connection_str = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
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
              Column('length', DECIMAL, nullable=False),
              Column('status', Enum('Activo', 'Inactivo', name='status_enum'), nullable=False),
              Column('fk_category', BINARY(16), ForeignKey('categories.category_id'), nullable=False),
              Column('front_page', String(255), nullable=False),
              Column('file', String(255), nullable=False),
              Column('banner', String(255), nullable=True)
              )

# Función Lambda para eliminar una película
def lambda_handler(event, context):
    try:
        logger.info("Deleting film")

        # Obtener film_id desde los parámetros de la ruta
        film_id_hex = event['pathParameters']['film_id']

        conn = db_connection.connect()
        query = films.select().where(films.c.film_id == bytes.fromhex(film_id_hex))
        result = conn.execute(query)
        existing_film = result.fetchone()
        if not existing_film:
            conn.close()
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Film not found')
            }

        query = films.delete().where(films.c.film_id == bytes.fromhex(film_id_hex))
        result = conn.execute(query)
        conn.close()
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Film deleted')
        }
    except SQLAlchemyError as e:
        logger.error(f"Error deleting film: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error deleting film')
        }
    except KeyError as e:
        logger.error(f"Missing parameter in path: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Missing film_id in path parameters')
        }
    except ValueError as e:
        logger.error(f"Invalid film_id format: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Invalid film_id format')
        }
