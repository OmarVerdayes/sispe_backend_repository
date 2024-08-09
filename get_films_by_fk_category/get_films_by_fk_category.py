import logging
import json
from decimal import Decimal
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, Enum, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func  # Importar las funciones SQL correctamente
import os
import binascii

# Configuración del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración de la base de datos
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
# Cadena de conexión
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
              Column('length', DECIMAL(4, 2), nullable=False),
              Column('status', Enum('Activo', 'Inactivo', name='status_enum'), nullable=False),
              Column('fk_category', BINARY(16), ForeignKey('categories.category_id'), nullable=False),
              Column('front_page', String(255), nullable=False),
              Column('file', String(255), nullable=False),
              Column('banner', String(255), nullable=True)
              )

# Función Lambda para obtener películas de una categoría específica
def lambda_handler(event, context):
    try:
        # Obtener el ID de la categoría de los parámetros de la ruta
        category_id_str = event['pathParameters'].get('fk_category')
        if not category_id_str:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Category ID is required in path parameters')
            }

        # Convertir el ID de categoría de hexadecimal a bytes
        try:
            category_id = binascii.unhexlify(category_id_str)
        except (TypeError, ValueError) as e:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps(f'Invalid Category ID format: {str(e)}')
            }

        logger.info(f"Fetching films for category: {category_id_str}")
        conn = db_connection.connect()

        # Definir explícitamente las columnas a seleccionar en la consulta y limitar a 7 resultados aleatorios
        query = films.select().where(films.c.fk_category == category_id).order_by(func.rand()).limit(7)

        result = conn.execute(query)
        film_list = []
        for row in result:
            film = {
                'film_id': row[0].hex(),
                'title': row[1],
                'description': row[2],
                'length': float(row[3]),
                'status': row[4],
                'fk_category': row[5].hex(),
                'front_page': row[6],
                'file': row[7],
                'banner': row[8]
            }
            film_list.append(film)

        conn.close()

        if not film_list:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps(f'No films found for category: {category_id_str}')
            }

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
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
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error fetching films')
        }
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps(f'Exception: {str(e)}')
        }
