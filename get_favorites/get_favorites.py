import os
import logging
import json
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, Integer, ForeignKey, select, DECIMAL, Enum
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

# Configuración del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración de la base de datos
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')

db_connection_str = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
db_connection = create_engine(db_connection_str)
metadata = MetaData()

# Definición de la tabla category
category = Table('categories', metadata,
                 Column('category_id', BINARY(16), primary_key=True),
                 Column('name', String(60), nullable=False))

# Definición de la tabla users
users = Table('users', metadata,
              Column('user_id', BINARY(16), primary_key=True),
              Column('name', String(60), nullable=False),
              Column('lastname', String(60), nullable=False),
              Column('email', String(100), nullable=False),
              Column('password', String(225), nullable=False))

# Definición de la tabla films
films = Table('films', metadata,
              Column('film_id', BINARY(16), primary_key=True),
              Column('title', String(60), nullable=False),
              Column('description', String(255), nullable=False),
              Column('length', DECIMAL(4, 2), nullable=False),
              Column('status', Enum('Activo', 'Inactivo', name='status_enum'), nullable=False),
              Column('fk_category', BINARY(16), ForeignKey('categories.category_id'), nullable=False),
              Column('front_page', String(255), nullable=False),
              Column('file', String(255), nullable=False))

# Definición de la tabla favorites
favorites = Table('favorites', metadata,
                  Column('favorite_id', BINARY(16), primary_key=True),
                  Column('fk_user', BINARY(16), ForeignKey('users.user_id'), nullable=False),
                  Column('fk_film', BINARY(16), ForeignKey('films.film_id'), nullable=False))

def is_hex(s):
    return len(s) == 32 and all(c in '0123456789abcdefABCDEF' for c in s)

def custom_converter(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.hex()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

def lambda_handler(event, context):
    try:
        # Obtener el pathParameters del evento
        path_params = event.get('pathParameters', {})
        fk_user = path_params.get('userId')

        if not fk_user:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Usuario necesario')
            }

        if not is_hex(fk_user):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('El ID de usuario no es válido')
            }

        user_id = bytes.fromhex(fk_user)

        conn = db_connection.connect()

        # Verificar si el usuario existe
        user_query = select([users]).where(users.c.user_id == user_id)
        user_result = conn.execute(user_query).fetchone()
        if user_result is None:
            conn.close()
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Usuario no encontrado')
            }

        # Obtener los favoritos del usuario
        query = select([favorites.c.fk_film, films.c.title, films.c.description, films.c.length, films.c.status, films.c.front_page, films.c.file, category.c.name.label('category_name')])\
                .select_from(favorites.join(films, favorites.c.fk_film == films.c.film_id).join(category, films.c.fk_category == category.c.category_id))\
                .where(favorites.c.fk_user == user_id)
        result = conn.execute(query)
        rows = result.fetchall()
        conn.close()

        if not rows:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Favoritos no encontrados')
            }

        # Convertir filas a diccionarios y convertir tipos no serializables
        favorites_list = []
        for row in rows:
            row_dict = dict(row)
            row_dict['fk_film'] = row_dict['fk_film'].hex()  # Convertir binario a hexadecimal
            favorites_list.append(row_dict)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps(favorites_list, default=custom_converter)
        }
    except SQLAlchemyError as e:
        logger.error(f'Error fetching favorites: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error al obtener favoritos')
        }
    except json.JSONDecodeError as e:
        logger.error(f'Error de formato JSON: {e}')
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error de formato JSON')
        }
    except TypeError as e:
        logger.error(f'Error de tipo: {e}')
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error al procesar los datos')
        }
