from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from delete_film.delete_film import lambda_handler



class MyTestCase(unittest.TestCase):

    @patch('delete_film.delete_film.db_connection.connect')
    def test_film_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None

        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef1234567890abcdef'
            }
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), 'Film not found')


    @patch('delete_film.delete_film.db_connection.connect')
    def test_film_deleted(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.return_value.fetchone.return_value = {
            'film_id': b'\x12\x34\x56\x78\x90\xab\xcd\xef\x12\x34\x56\x78\x90\xab\xcd\xef'
        }

        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef1234567890abcdef'
            }
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), 'Film deleted')

    @patch('delete_film.delete_film.db_connection.connect')
    def test_error_deleting_film(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Error deleting film")

        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef1234567890abcdef'
            }
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error deleting film')

    def test_missing_film_id(self):
        event = {
            'pathParameters': {}
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Missing film_id in path parameters')

    @patch('delete_film.delete_film.db_connection.connect')
    def test_invalid_film_id_format(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        event = {
            'pathParameters': {
                'film_id': 'invalid_film_id_format'
            }
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Invalid film_id format')


if __name__ == '__main__':
    unittest.main()
