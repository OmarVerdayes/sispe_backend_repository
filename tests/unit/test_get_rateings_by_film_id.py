from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from get_rateing_by_film_id.get_rateing_by_film_id import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('get_rateing_by_film_id.get_rateing_by_film_id.db_connection.connect')
    def test_missing_film_id(self, mock_connect):
        event = {
            'pathParameters': {}
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Parameter film_id is required')

    @patch('get_rateing_by_film_id.get_rateing_by_film_id.db_connection.connect')
    def test_invalid_film_id_format(self, mock_connect):
        event = {
            'pathParameters': {
                'film_id': 'invalid_format'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Invalid film_id format')

    @patch('get_rateing_by_film_id.get_rateing_by_film_id.db_connection.connect')
    def test_no_rateings_found(self, mock_connect):
        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef'
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_connect.return_value = mock_conn

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), 'No rateings found for the given film')

    @patch('get_rateing_by_film_id.get_rateing_by_film_id.db_connection.connect')
    def test_sqlalchemy_error(self, mock_connect):
        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef'
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error fetching rateings')

    @patch('get_rateing_by_film_id.get_rateing_by_film_id.db_connection.connect')
    def test_unexpected_error(self, mock_connect):
        event = {
            'pathParameters': {
                'film_id': '1234567890abcdef'
            }
        }
        context = {}

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_connect.side_effect = Exception("Unexpected error")

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Internal server error')

if __name__ == '__main__':
    unittest.main()
