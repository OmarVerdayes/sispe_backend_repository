import logging
import json
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY
from sqlalchemy.exc import SQLAlchemyError
import os

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

# Definición de la tabla de usuarios
users = Table('users', metadata,
              Column('user_id', BINARY(16), primary_key=True),
              Column('name', String(60), nullable=False),
              Column('lastname', String(60), nullable=False),
              Column('email', String(100), nullable=False),
              Column('password', String(255), nullable=False),
              Column('fk_rol', BINARY(16), nullable=False),
              Column('fk_subscription', BINARY(16), nullable=False))

globalHeaders = {
    "Access-Control-Allow-Headers": 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
    }

# Función Lambda para actualizar un usuario existente
def lambda_handler(event, context):
    try:
        logger.info("Updating user")
        data = json.loads(event['body'])

        conn = db_connection.connect()
        query = users.select().where(users.c.user_id == bytes.fromhex(data['user_id']))
        result = conn.execute(query)
        existing_user = result.fetchone()
        if not existing_user:
            conn.close()
            return {
                'statusCode': 404,
                'headers': globalHeaders,
                'body': json.dumps('User not found')
            }

        query = users.update().where(users.c.user_id == bytes.fromhex(data['user_id'])).values(
            name=data['name'],
            lastname=data['lastname'],
            email=data['email'],
            password=data['password'],
            fk_rol=bytes.fromhex(data['fk_rol']),
            fk_subscription=bytes.fromhex(data['fk_subscription'])
        )
        result = conn.execute(query)
        conn.close()
        return {
            'statusCode': 200,
            'headers': globalHeaders,
            'body': json.dumps('Usuario actualizado')
        }
    except SQLAlchemyError as e:
        logger.error(f"Error updating user: {e}")
        return {
            'statusCode': 500,
            'headers': globalHeaders,
            'body': json.dumps('Error updating user')
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return {
            'statusCode': 400,
            'headers': globalHeaders,
            'body': json.dumps('Invalid JSON format')
        }
