from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from get_user_by_email.get_user_by_email import lambda_handler


class MyTestCase(unittest.TestCase):
    @patch('get_user_by_email.get_user_by_email.db_connection')
    def test_missing_email(self, mock_db_connection):
        event = {
            'pathParameters': {}
        }
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'El correo es requerido'
            })
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_user_by_email.get_user_by_email.db_connection')
    def test_user_not_found(self, mock_db_connection):
        event = {
            'pathParameters': {
                'email': 'notfound@example.com'
            }
        }
        context = {}

        mock_db_connection.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = None

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 404,
            'body': json.dumps({
                'message': 'Usuario no encontrado'
            })
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_user_by_email.get_user_by_email.db_connection')
    def test_user_found(self, mock_db_connection):
        event = {
            'pathParameters': {
                'email': 'found@example.com'
            }
        }
        context = {}

        mock_db_connection.connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = (
            b'\x00' * 16,
            'John',
            'Doe',
            'john@example.com',
            'hashed_password',
            b'\x00' * 16,
            b'\x00' * 16
        )

        response = lambda_handler(event, context)

        expected_user_data = {
            'user_id': '00000000000000000000000000000000',
            'name': 'John',
            'lastname': 'Doe',
            'email': 'john@example.com',
            'password': 'hashed_password',
            'fk_rol': '00000000000000000000000000000000',
            'fk_subscription': '00000000000000000000000000000000'
        }

        expected_response = {
            'statusCode': 200,
            'body': json.dumps({
                'user': expected_user_data
            })
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_user_by_email.get_user_by_email.db_connection')
    def test_database_error(self, mock_db_connection):
        event = {
            'pathParameters': {
                'email': 'error@example.com'
            }
        }
        context = {}

        mock_db_connection.connect.return_value.__enter__.return_value.execute.side_effect = SQLAlchemyError(
            "Database error")

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error al obtener los datos'
            })
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))


if __name__ == '__main__':
    unittest.main()
