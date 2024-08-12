from decimal import Decimal
from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from sort_random_films.sort_random_films import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('sort_random_films.sort_random_films.db_connection.connect')
    def test_no_films_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result

        event = {}
        context = None
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 404)

        self.assertEqual(response['body'], json.dumps('No se encontraron películas registradas'))

    @patch('sort_random_films.sort_random_films.db_connection.connect')
    def test_film_list_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_result = MagicMock()

        mock_result.keys.return_value = ['film_id', 'title', 'description', 'length', 'status', 'fk_category',
                                         'front_page', 'file', 'banner']
        mock_result.__iter__.return_value = [
            (b'\x01', 'Title1', 'Description1', Decimal('120.00'), 'Activo', b'\x02', 'FrontPage1', 'File1', 'Banner1'),
            (
                b'\x03', 'Title2', 'Description2', Decimal('130.00'), 'Inactivo', b'\x04', 'FrontPage2', 'File2',
                'Banner2')
        ]
        mock_conn.execute.return_value = mock_result

        event = {}
        context = None
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)

        expected_film_list = [
            {
                'film_id': '01', 'title': 'Title1', 'description': 'Description1', 'length': 120.00, 'status': 'Activo',
                'fk_category': '02', 'front_page': 'FrontPage1', 'file': 'File1', 'banner': 'Banner1'
            },
            {
                'film_id': '03', 'title': 'Title2', 'description': 'Description2', 'length': 130.00,
                'status': 'Inactivo',
                'fk_category': '04', 'front_page': 'FrontPage2', 'file': 'File2', 'banner': 'Banner2'
            }
        ]
        expected_body = json.dumps(expected_film_list)
        self.assertEqual(response['body'], expected_body)

    @patch('sort_random_films.sort_random_films.db_connection.connect')
    def test_database_error(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        event = {}
        context = None
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps('Error fetching films'))

    @patch('sort_random_films.sort_random_films.db_connection.connect')
    def test_general_exception(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.side_effect = Exception("General error")

        event = {}
        context = None
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps('Exception: General error'))


if __name__ == '__main__':
    unittest.main()
