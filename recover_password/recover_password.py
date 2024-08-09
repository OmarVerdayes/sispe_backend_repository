import json
import logging
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, UniqueConstraint, ForeignKey, Index, ForeignKeyConstraint
from sqlalchemy.orm import sessionmaker
import os

# Configuración del logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración de las credenciales de AWS
AWS_ACCESS_KEY_ID = 'AKIAR7477EOW7CWUCEHJ'
AWS_SECRET_ACCESS_KEY = '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'

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")

# Configuración de la conexión a la base de datos
db_connection_str = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
db_engine = create_engine(db_connection_str)
metadata = MetaData()
Session = sessionmaker(bind=db_engine)

# Definición de la tabla de usuarios
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
              Index('fk_subscription_idx', 'fk_subscription')
              )

def lambda_handler(event, __):
    client = boto3.client('cognito-idp', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    user_pool_id = "us-east-1_hpKh8IecL"
    client_id = "42dmr7oq6bkfoufph3q36paqta"

    try:
        body_parameters = json.loads(event["body"])
        email = body_parameters.get('email')
        logging.info(f"[EMAIL] {email}")

        # Verificar si el usuario existe
        session = Session()
        user = session.execute(users.select().where(users.c.email == email)).fetchone()
        session.close()

        if not user:
            return {
                'statusCode': 404,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps({"error_message": "User not found."})
            }

        if 'confirmation_code' in body_parameters and 'new_password' in body_parameters:
            # Confirmar la nueva contraseña usando el código de verificación
            confirmation_code = body_parameters.get('confirmation_code')
            new_password = body_parameters.get('new_password')

            logging.info(f"[confirmation_code] {confirmation_code}")
            logging.info(f"[new_password] {new_password}")

            response = client.confirm_forgot_password(
                ClientId=client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            logging.info(f"[RESPONSE] {response}")

            # Actualizar la contraseña en la base de datos
            session = Session()
            update_query = users.update().where(users.c.email == email).values(
                password=new_password
            )
            result = session.execute(update_query)
            session.commit()
            session.close()

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps({"message": "Password reset successfully."})
            }
        else:
            # Enviar código de verificación para restablecimiento de contraseña
            response = client.forgot_password(
                ClientId=client_id,
                Username=email
            )

            logging.info(f"[RESPONSE] {response}")

            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps({"message": "Verification code sent to email."})
            }

    except ClientError as e:
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({"error_message": str(e)})
        }