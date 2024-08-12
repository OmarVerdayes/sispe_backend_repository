from unittest.mock import patch, MagicMock
import unittest
import json
from sqlalchemy.exc import SQLAlchemyError
from get_films.get_films import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch('get_films.get_films.db_connection.connect')
    def test_no_films_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value = iter([])  # Simula un resultado vacío

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps('No films found')
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_films.get_films.db_connection.connect')
    def test_films_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_result = [
            {'film_id': b'123', 'title': 'Test Film', 'description': 'A test film', 'length': 120.00,
             'status': 'Activo', 'fk_category': b'456', 'front_page': 'front.jpg', 'file': 'file.mp4',
             'banner': 'banner.jpg'}
        ]
        mock_conn.execute.return_value = iter(mock_result)

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_film_list = [
            {
                'film_id': '313233',
                'title': 'Test Film',
                'description': 'A test film',
                'length': 120.00,
                'status': 'Activo',
                'fk_category': '343536',
                'front_page': 'front.jpg',
                'file': 'file.mp4',
                'banner': 'banner.jpg'
            }
        ]
        expected_response = {
            'statusCode': 200,
            'body': json.dumps(expected_film_list)
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_films.get_films.db_connection.connect')
    def test_error_fetching_films(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 500,
            'body': json.dumps('Error fetching films')
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))

    @patch('get_films.get_films.db_connection.connect')

    def test_exception(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_connect.side_effect = Exception("General exception")

        event = {}
        context = {}

        response = lambda_handler(event, context)


        expected_response = {
            'statusCode': 500,
            'body': json.dumps('Exception: General exception')
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(json.loads(response['body']), json.loads(expected_response['body']))


if __name__ == '__main__':
    unittest.main()
