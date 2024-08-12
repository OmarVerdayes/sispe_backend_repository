from unittest.mock import patch, MagicMock
import unittest
import json
from sqlalchemy.exc import SQLAlchemyError
from get_film_by_name.get_film_by_name import lambda_handler

class MyTestCase(unittest.TestCase):

    @patch('get_film_by_name.get_film_by_name.db_connection')
    def test_no_films_found(self, mock_db_connection):
        event = {
            'pathParameters': {
                'title': 'Titulo falso'
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_db_connection.connect.return_value = mock_conn
        mock_conn.execute.return_value = []

        response = lambda_handler(event, context)


        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), 'No films found')

    @patch('get_film_by_name.get_film_by_name.db_connection')
    def test_film_found(self, mock_db_connection):
        # Arrange
        event = {
            'pathParameters': {
                'title': 'ExistingTitle'  # Un título que debería existir en la base de datos
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_db_connection.connect.return_value = mock_conn
        mock_result = [
            {'film_id': b'\x01\x02\x03\x04', 'title': 'ExistingTitle', 'description': 'A movie', 'length': 120.00,
             'status': 'Activo', 'fk_category': b'\x01\x02\x03\x04', 'front_page': 'front.jpg', 'file': 'file.mp4',
             'banner': 'banner.jpg'}
        ]
        mock_conn.execute.return_value = mock_result

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        expected_body = [
            {'film_id': '01020304', 'title': 'ExistingTitle', 'description': 'A movie', 'length': 120.00,
             'status': 'Activo', 'fk_category': '01020304', 'front_page': 'front.jpg', 'file': 'file.mp4',
             'banner': 'banner.jpg'}
        ]
        self.assertEqual(json.loads(response['body']), expected_body)

    @patch('get_film_by_name.get_film_by_name.db_connection')
    def test_database_error(self, mock_db_connection):
        event = {
            'pathParameters': {
                'title': 'AnyTitle'  # Puede ser cualquier título ya que el error simulado es por base de datos
            }
        }
        context = {}
        mock_conn = MagicMock()
        mock_db_connection.connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Database connection error")

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error fetching films')

    @patch('get_film_by_name.get_film_by_name.db_connection')
    def test_general_exception(self, mock_db_connection):
        event = {
            'pathParameters': {
                'title': 'AnyTitle'
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_db_connection.connect.return_value = mock_conn
        mock_conn.execute.side_effect = Exception("General error")

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Exception: General error')


if __name__ == '__main__':
    unittest.main()
