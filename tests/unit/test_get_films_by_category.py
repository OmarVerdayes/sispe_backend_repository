from unittest.mock import patch, MagicMock
import unittest
import json
from sqlalchemy.exc import SQLAlchemyError
from get_films_by_category.get_films_by_category import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('get_films_by_category.get_films_by_category.db_connection')
    def test_lambda_handler_no_films_found(self, mock_db_connection):
        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        mock_connection.execute.return_value.mappings.return_value = []

        event = {}
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), 'No films found')

    @patch('get_films_by_category.get_films_by_category.db_connection')
    def test_lambda_handler_films_found(self, mock_db_connection):
        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        # Simulamos el resultado de la consulta de categorías
        mock_connection.execute.side_effect = [
            MagicMock(mappings=MagicMock(return_value=[
                {'category_id': b'\x01', 'name': 'Category 1'},
                {'category_id': b'\x02', 'name': 'Category 2'}
            ])),
            MagicMock(mappings=MagicMock(return_value=[
                {'film_id': b'\x01', 'title': 'Film 1', 'description': 'Description 1', 'length': 120.00,
                 'status': 'Activo', 'fk_category': b'\x01', 'front_page': 'front1.jpg', 'file': 'file1.mp4',
                 'banner': 'banner1.jpg'},
                {'film_id': b'\x02', 'title': 'Film 2', 'description': 'Description 2', 'length': 150.00,
                 'status': 'Inactivo', 'fk_category': b'\x02', 'front_page': 'front2.jpg', 'file': 'file2.mp4',
                 'banner': 'banner2.jpg'}
            ]))
        ]

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_body = {
            'Category 1': [
                {'film_id': '01', 'title': 'Film 1', 'description': 'Description 1', 'length': 120.00,
                 'status': 'Activo', 'fk_category': '01', 'front_page': 'front1.jpg', 'file': 'file1.mp4',
                 'banner': 'banner1.jpg'}
            ],
            'Category 2': [
                {'film_id': '02', 'title': 'Film 2', 'description': 'Description 2', 'length': 150.00,
                 'status': 'Inactivo', 'fk_category': '02', 'front_page': 'front2.jpg', 'file': 'file2.mp4',
                 'banner': 'banner2.jpg'}
            ]
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_body)

    @patch('get_films_by_category.get_films_by_category.db_connection')
    def test_lambda_handler_error_fetching_films(self, mock_db_connection):
        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        mock_connection.execute.side_effect = SQLAlchemyError("Database error")

        event = {}
        context = {}

        response = lambda_handler(event, context)


        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error fetching films')

    @patch('get_films_by_category.get_films_by_category.db_connection')
    def test_lambda_handler_exception(self, mock_db_connection):
        mock_connection = MagicMock()
        mock_db_connection.connect.return_value = mock_connection

        # Simulamos que execute lanza una excepción genérica
        mock_connection.execute.side_effect = Exception("Generic exception")

        event = {}
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Exception: Generic exception')


if __name__ == '__main__':
    unittest.main()
