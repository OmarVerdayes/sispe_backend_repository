import os
import logging
import json
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Parámetros de conexión a la base de datos
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Cadena de conexión a la base de datos
db_connection_str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Crear el engine de SQLAlchemy con un pool de conexiones configurado
db_connection = create_engine(
    db_connection_str,
    pool_size=5,
    max_overflow=10,
    pool_timeout=60  # Timeout en segundos
)

metadata = MetaData()

# Definición de la tabla
users = Table(
    'users', metadata,
    Column('user_id', BINARY(16), primary_key=True),
    Column('name', String(60), nullable=False),
    Column('lastname', String(60), nullable=False),
    Column('email', String(100), nullable=False),
    Column('password', String(255), nullable=False),
    Column('fk_rol', BINARY(16), nullable=False),
    Column('fk_subscription', BINARY(16), nullable=False)
)

COMMON_HEADERS = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}

def lambda_handler(event, context):
    try:
        email = event['pathParameters'].get('email')
        if not email:
            return {
                'statusCode': 400,
                'headers': COMMON_HEADERS,
                'body': json.dumps({
                    'message': 'El correo es requerido'
                })
            }

        # Usar un bloque `with` para manejar la conexión
        with db_connection.connect() as conn:
            query = users.select().where(users.c.email == email)
            result = conn.execute(query)
            user = result.fetchone()

        if not user:
            return {
                'statusCode': 404,
                'headers': COMMON_HEADERS,
                'body': json.dumps({
                    'message': 'Usuario no encontrado'
                })
            }

        user_data = {column.name: value.hex() if isinstance(value, bytes) else value for column, value in zip(users.columns, user)}

        return {
            'statusCode': 200,
            'headers': COMMON_HEADERS,
            'body': json.dumps({
                'user': user_data
            })
        }
    except SQLAlchemyError as e:
        logger.error(f"Error fetching user: {e}")
        return {
            'statusCode': 500,
            'headers': COMMON_HEADERS,
            'body': json.dumps({
                'message': 'Error al obtener los datos'
            })
        }
