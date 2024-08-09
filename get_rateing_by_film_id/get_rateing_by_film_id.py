import logging
import json
from sqlalchemy import create_engine, MetaData, Table, Column, BINARY, DECIMAL, VARCHAR, String, ForeignKeyConstraint, Index, UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
import os
import binascii

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

# Definición de la tabla de rateings
rateings = Table('rateings', metadata,
                 Column('rateing_id', BINARY(16), primary_key=True),
                 Column('grade', DECIMAL(2, 1), nullable=False),
                 Column('comment', VARCHAR(255)),
                 Column('fk_user', BINARY(16)),
                 Column('fk_film', BINARY(16)))

# Definición de la tabla de users
users = Table('users', metadata,
              Column('user_id', BINARY(16), primary_key=True),
              Column('name', String(60), nullable=False),
              Column('lastname', String(60), nullable=False),
              Column('email', String(100), nullable=False),
              Column('password', String(255), nullable=False),
              Column('fk_rol', BINARY(16), nullable=False),
              Column('fk_subscription', BINARY(16), nullable=False),
              UniqueConstraint('email', name='unique_email'),
              ForeignKeyConstraint(['fk_rol'], ['roles.rol_id'], name='fk_rol'),
              ForeignKeyConstraint(['fk_subscription'], ['subscriptions.subscription_id'], name='fk_subscription'),
              Index('fk_rol_idx', 'fk_rol'),
              Index('fk_subscription_idx', 'fk_subscription'))

def lambda_handler(event, context):
    try:
        logger.info("Fetching rateings for a specific film")

        film_id = event['pathParameters'].get('film_id')

        if not film_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Parameter film_id is required')
            }

        # Convierte el film_id a binario
        try:
            fk_film = binascii.unhexlify(film_id)
        except binascii.Error:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Invalid film_id format')
            }

        conn = db_connection.connect()
        query = rateings.select().where(rateings.c.fk_film == fk_film)
        result = conn.execute(query)
        rateing_list = []
        for row in result:
            rateing_dict = dict(row)
            # Convertir valores BINARY a cadenas hexadecimales
            rateing_dict['rateing_id'] = binascii.hexlify(rateing_dict['rateing_id']).decode('utf-8')
            fk_user = binascii.hexlify(rateing_dict['fk_user']).decode('utf-8')
            rateing_dict['fk_film'] = binascii.hexlify(rateing_dict['fk_film']).decode('utf-8')

            # Convertir Decimal a float
            if isinstance(rateing_dict['grade'], Decimal):
                rateing_dict['grade'] = float(rateing_dict['grade'])

            # Obtener el email del usuario
            user_query = users.select().where(users.c.user_id == row['fk_user'])
            user_result = conn.execute(user_query).fetchone()
            if user_result:
                rateing_dict['email'] = user_result['email']
            else:
                rateing_dict['email'] = None

            # Eliminar fk_user del resultado
            del rateing_dict['fk_user']

            rateing_list.append(rateing_dict)
        conn.close()

        if not rateing_list:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('No rateings found for the given film')
            }

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps(rateing_list)
        }
    except SQLAlchemyError as e:
        logger.error(f"Error fetching rateings: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error fetching rateings')
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Internal server error')
        }
