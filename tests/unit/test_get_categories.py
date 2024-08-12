from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from get_categories.get_categories import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('get_categories.get_categories.create_engine')
    @patch('get_categories.get_categories.db_connection.connect')
    def test_no_categories_found(self, mock_connect, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = []  # Simular que no hay datos

        event = {}
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), 'No categories found')

    @patch('get_categories.get_categories.create_engine')
    def test_database_error(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Simulated database error")

        event = {}
        context = {}

        response = lambda_handler(event, context)
        expected_response = {
            'statusCode': 500,
            'body': json.dumps('Internal server error. Could not fetch categories.')
        }
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_categories.get_categories.create_engine')
    def test_unexpected_error(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_conn.execute.side_effect = Exception("Simulated unexpected error")

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 500,
            'body': json.dumps('Internal server error. Could not fetch categories.')
        }

        # Verifica la respuesta
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_categories.get_categories.create_engine')
    @patch('get_categories.get_categories.db_connection.connect')
    def test_categories_found(self, mock_connect, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.return_value = [
            {'category_id': b'\x00\x01\x02\x03', 'name': 'Category1'},
            {'category_id': b'\x00\x01\x02\x04', 'name': 'Category2'}
        ]

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 200,
            'body': json.dumps([
                {'category_id': '00010203', 'name': 'Category1'},
                {'category_id': '00010204', 'name': 'Category2'}
            ])
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))


if __name__ == '__main__':
    unittest.main()
