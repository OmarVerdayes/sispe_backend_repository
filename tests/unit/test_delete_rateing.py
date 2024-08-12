from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from delete_rateing.delete_rateing import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch('delete_rateing.delete_rateing.create_engine')
    def test_rateing_deletion_error(self, mock_create_engine):
        # Configura el mock de la base de datos
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn

        # Configura el mock para que lance una excepción al intentar ejecutar la consulta
        mock_conn.execute.side_effect = Exception("Database error")

        # Simula el evento y contexto de la Lambda
        event = {
            'pathParameters': {'id': '00010203'}
        }
        context = {}

        # Llama a la función lambda_handler
        response = lambda_handler(event, context)

        # Esperado
        expected_response = {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Error deleting rateing')
        }

        # Verifica la respuesta
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['headers'], expected_response['headers'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))


    @patch('delete_rateing.delete_rateing.create_engine')
    @patch('delete_rateing.delete_rateing.Table')
    @patch('delete_rateing.delete_rateing.db_connection')
    def test_rateing_not_found(self, mock_db_connection, mock_table, mock_create_engine):
        # Configura el mock de la base de datos
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_db_connection.connect.return_value = mock_conn

        # Simula que no se encontró ningún registro para eliminar
        mock_conn.execute.return_value.rowcount = 0

        # Simula el evento y contexto de la Lambda
        event = {
            'pathParameters': {'id': '00010203'}
        }
        context = {}

        # Llama a la función lambda_handler
        response = lambda_handler(event, context)

        # Esperado
        expected_response = {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Rateing not found')
        }

        # Verifica la respuesta
        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(response['headers'], expected_response['headers'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('delete_rateing.delete_rateing.create_engine')
    @patch('delete_rateing.delete_rateing.Table')
    def test_rateing_deleted(self, mock_table, mock_create_engine):
        # Configura el mock de la base de datos
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn

        # Simula que se ha ejecutado la eliminación con éxito
        mock_conn.execute.return_value.rowcount = 1

        # Simula el evento y contexto de la Lambda
        event = {
            'pathParameters': {'id': '00010203'}
        }
        context = {}

        # Llama a la función lambda_handler
        response = lambda_handler(event, context)

        # Esperado
        expected_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('Rateing deleted')
        }

        # Verifica la respuesta
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers'], expected_response['headers'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))


if __name__ == '__main__':
    unittest.main()
