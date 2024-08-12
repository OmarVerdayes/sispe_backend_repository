from decimal import Decimal
from unittest.mock import patch, MagicMock
import unittest
import json
from sqlalchemy.exc import SQLAlchemyError
from get_films_by_fk_category.get_films_by_fk_category import lambda_handler
import binascii


class MyTestCase(unittest.TestCase):

    @patch('get_films_by_fk_category.get_films_by_fk_category.create_engine')
    def test_missing_category_id(self, mock_create_engine):
        event = {
            'pathParameters': {}  # Sin 'fk_category'
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)

        expected_body = 'Category ID is required in path parameters'
        self.assertEqual(json.loads(response['body']), expected_body)


    @patch('get_films_by_fk_category.get_films_by_fk_category.create_engine')
    def test_invalid_category_id_format(self, mock_create_engine):
        # Simular el evento con un ID de categoría en formato hexadecimal inválido
        event = {
            'pathParameters': {
                'fk_category': 'invalid_hex_id'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), "Invalid Category ID format: Non-hexadecimal digit found")

    @patch('get_films_by_fk_category.get_films_by_fk_category.create_engine')
    def test_sqlalchemy_error(self, mock_create_engine):
        mock_conn = MagicMock()
        mock_create_engine.return_value.connect.return_value = mock_conn

        mock_conn.execute.side_effect = SQLAlchemyError("Database connection error")

        category_id_hex = '01010101010101010101010101010101'

        # Simular el evento con una categoría válida
        event = {
            'pathParameters': {
                'fk_category': category_id_hex
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error fetching films')

    @patch('get_films_by_fk_category.get_films_by_fk_category.create_engine')
    def test_general_exception(self, mock_create_engine):
        mock_conn = MagicMock()
        mock_create_engine.return_value.connect.return_value = mock_conn

        def raise_exception(*args, **kwargs):
            raise Exception("Unexpected error")

        mock_conn.execute.side_effect = raise_exception

        category_id_hex = '01010101010101010101010101010101'

        event = {
            'pathParameters': {
                'fk_category': category_id_hex
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        #self.assertEqual(json.loads(response['body']), 'Exception: Unexpected error')


if __name__ == '__main__':
    unittest.main()
