from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from get_category_films_by_film_id.get_category_films_by_film_id import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_missing_film_id(self, mock_db_connection):
        event = {
            'pathParameters': {}
        }
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 400,
            'body': json.dumps('film_id parameter is required')
        }
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"], '"film_id parameter is required"')

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_invalid_film_id_format(self, mock_db_connection):
        event = {
            'pathParameters': {
                'film_id': 'invalid_hex'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(response["body"],  '"Invalid film_id format"')

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_film_not_found(self, mock_db_connection):
        event = {
            'pathParameters': {
                'film_id': '00000000000000000000000000000000'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(response["body"], '"No films found in the category"')

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_film_not_found_with_headers(self, mock_db_connection):
        event = {
            'pathParameters': {
                'film_id': '00000000000000000000000000000000'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(response["body"], '"No films found in the category"')

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_film_list_found(self, mock_db_connection):
        event = {
            'pathParameters': {
                'film_id': '00000000000000000000000000000000'  # Ejemplo de film_id que existe
            }
        }
        context = {}

        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        mock_category_query_result = MagicMock()
        mock_category_query_result.fetchone.return_value = {
            'fk_category': bytes.fromhex('00000000000000000000000000000002')
        }
        mock_connection.execute.return_value = mock_category_query_result

        mock_film_query_result = [
            {
                'film_id': bytes.fromhex('00000000000000000000000000000001'),
                'title': 'Example Film 1',
                'description': 'An example film description.',
                'length': 120.00,
                'status': 'Activo',
                'fk_category': bytes.fromhex('00000000000000000000000000000002'),
                'front_page': 'front_page_url',
                'file': 'file_url',
                'banner': 'banner_url'
            }
        ]

        mock_connection.execute.side_effect = [mock_category_query_result, mock_film_query_result]

        response = lambda_handler(event, context)

        expected_body = json.dumps([
            {
                'film_id': '00000000000000000000000000000001',
                'title': 'Example Film 1',
                'description': 'An example film description.',
                'length': 120.00,
                'status': 'Activo',
                'fk_category': '00000000000000000000000000000002',
                'front_page': 'front_page_url',
                'file': 'file_url',
                'banner': 'banner_url'
            }
        ])

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], expected_body)

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_internal_server_error(self, mock_db_connection):
        # Crear un evento con un film_id que provocará un error
        event = {
            'pathParameters': {
                'film_id': '00000000000000000000000000000000'  # Ejemplo de film_id
            }
        }
        context = {}

        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        mock_connection.execute.side_effect = SQLAlchemyError("Simulated database error")

        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 500)
        self.assertEqual(response["body"], json.dumps('Error fetching films: Simulated database error'))

    @patch('get_category_films_by_film_id.get_category_films_by_film_id.db_connection')
    def test_internal_server_error_exception(self, mock_db_connection):
        event = {
            'pathParameters': {
                'film_id': '00000000000000000000000000000000'  # Ejemplo de film_id
            }
        }
        context = {}

        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        mock_connection.execute.side_effect = Exception("Simulated general error")

        response = lambda_handler(event, context)

        self.assertEqual(response["statusCode"], 500)
        self.assertEqual(response["body"], json.dumps('Exception: Simulated general error'))


if __name__ == '__main__':
    unittest.main()
