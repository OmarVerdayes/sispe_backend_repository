import os
import random
import string
import boto3
import logging
import json
import stripe
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, MetaData, Table, Column, String, BINARY, UniqueConstraint, ForeignKey, Index, \
    ForeignKeyConstraint, DateTime, select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuración de la base de datos
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

db_connection_str = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
db_connection = create_engine(db_connection_str)
metadata = MetaData()

AWS_ACCESS_KEY_ID = "AKIAR7477EOW7CWUCEHJ"
AWS_SECRET_ACCESS_KEY = "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"

# Definición de tablas
users = Table('users', metadata,
              Column('user_id', BINARY(16), primary_key=True),
              Column('name', String(60), nullable=False),
              Column('lastname', String(60), nullable=False),
              Column('email', String(100), nullable=False),
              Column('password', String(255), nullable=False),
              Column('fk_subscription', BINARY(16), nullable=False),
              UniqueConstraint('email', name='unique_email'),
              Column('fk_rol', BINARY(16), nullable=False),
              ForeignKeyConstraint(['fk_rol'],['roles.rol_id'], name='fk_rol'),
              Index('fk_rol_idx', 'fk_rol'),
              ForeignKeyConstraint(['fk_subscription'], ['subscriptions.subscription_id'], name='fk_subscription'),
              Index('fk_subscription_idx', 'fk_subscription')
              )

subscriptions = Table('subscriptions', metadata,
                      Column('subscription_id', BINARY(16), primary_key=True),
                      Column('start_date', DateTime, nullable=False),
                      Column('end_date', DateTime, nullable=False),
                      Column('transaction', String(255), nullable=False))

roles = Table('roles', metadata,
              Column('rol_id', BINARY(16), primary_key=True),
              Column('name', String(50), nullable=False))

def generate_password(length=8):
    if length < 4:
        raise ValueError("Length of the password should be at least 4")
    special_characters = ',/$@'
    all_characters = string.ascii_letters + string.digits + special_characters
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice(special_characters)
    ]
    password += random.choices(all_characters, k=length - 4)
    random.shuffle(password)
    return ''.join(password)

def lambda_handler(event, context):
    data = json.loads(event['body'])
    user_id = uuid.uuid4().bytes
    name = data.get('name')
    lastname = data.get('lastname')
    email = data.get('email')
    fk_rol = data.get('fkRol')
    password = generate_password()
    role_name = "cliente"

    if not name or not lastname or not email or not fk_rol:
        logger.error("Faltan datos obligatorios en el cuerpo de la solicitud")
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Faltan datos obligatorios')
        }

    try:
        conn = db_connection.connect()

        # Convertir fk_rol a bytes desde su representación hexadecimal
        try:
            fk_rol = bytes.fromhex(fk_rol)
        except ValueError as e:
            logger.error(f"Formato de fk_rol inválido: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps('Formato de fk_rol inválido')
            }

        # Realizar el cobro con Stripe
        stripe_token = data.get('stripeToken')
        logger.debug(f"Attempting to charge card with token: {stripe_token}")

        try:
            charge = stripe.Charge.create(
                amount=9900,  # 99 MXN en centavos
                currency='mxn',
                description='Suscripción de 30 días',
                source=stripe_token  # token del cliente
            )
            transaction_id = charge['id']
            logger.debug(f"Charge successful: {charge}")
        except stripe.error.StripeError as e:
            logger.error(f"Error al realizar el cobro: {str(e)}")
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
                },
                'body': json.dumps({"error_message": str(e)})
            }

        # Registrar la suscripción en la base de datos
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        subscription_id = uuid.uuid4().bytes
        insert_subscription_query = subscriptions.insert().values(
            subscription_id=subscription_id,
            start_date=start_date,
            end_date=end_date,
            transaction=transaction_id
        )
        conn.execute(insert_subscription_query)

        # Registrar el usuario en la base de datos
        insert_user_query = users.insert().values(
            user_id=user_id,
            name=name,
            lastname=lastname,
            email=email,
            password=password,
            fk_rol=fk_rol,
            fk_subscription=subscription_id
        )
        conn.execute(insert_user_query)

        # Crear el usuario en Cognito
        client = boto3.client('cognito-idp', region_name='us-east-1', aws_access_key_id=AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        user_pool_id = 'us-east-1_hpKh8IecL'
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
            ],
            TemporaryPassword=password,
        )

        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username=email,
            GroupName=role_name,
        )

        conn.close()

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Usuario registrado, verifica tu correo electrónico')
        }

    except ClientError as e:
        logger.error(f"ClientError: {str(e)}")
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
        logger.error(f"Error inesperado: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({"error_message": str(e)})
        }
