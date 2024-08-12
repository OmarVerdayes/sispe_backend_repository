from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from create_film.create_film import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_film.create_film.db_connection.connect")
    def test_category_id_does_not_exist(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result

        event = {
            'body': json.dumps({
                'title': 'Test Film',
                'description': 'A test film',
                'length': 120.0,
                'status': 'Activo',
                'fk_category': '0123456789abcdef0123456789abcdef',
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'banner': 'http://example.com/banner.jpg'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        assert json.loads(response['body']) == 'Category ID does not exist'

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_film.create_film.db_connection.connect")
    def test_film_created_successfully(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        mock_result = MagicMock()
        mock_result.fetchone.return_value = {'category_id': b'0123456789abcdef'}
        mock_conn.execute.side_effect = [mock_result, None]

        event = {
            'body': json.dumps({
                'title': 'Test Film',
                'description': 'A test film',
                'length': 120.0,
                'status': 'Activo',
                'fk_category': '0123456789abcdef0123456789abcdef',  # ID de categoría existente
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'banner': 'http://example.com/banner.jpg'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        assert json.loads(response['body']) == 'Film created'

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_film.create_film.db_connection.connect")
    def test_error_creating_film(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        event = {
            'body': json.dumps({
                'title': 'Test Film',
                'description': 'A test film',
                'length': 120.0,
                'status': 'Activo',
                'fk_category': '0123456789abcdef0123456789abcdef',  # ID de categoría existente
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'banner': 'http://example.com/banner.jpg'
            })
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 500
        assert json.loads(response['body']) == 'Error creating film'

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_film.create_film.db_connection.connect")
    def test_invalid_json_format(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        event = {
            'body': '{"title": "Test Film", "description": "A test film", "length": 120.0'  # Malformed JSON
        }

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        assert json.loads(response['body']) == 'Invalid JSON format'

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_film.create_film.db_connection.connect")
    def test_missing_required_key(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        event = {
            'body': json.dumps({
                'description': 'A test film',
                'length': 120.0,
                'status': 'Activo',
                'fk_category': '0123456789abcdef0123456789abcdef',
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'banner': 'http://example.com/banner.jpg'
            })
        }

        response = lambda_handler(event, None)

        expected_message = '"Missing required key: \'Missing required key: title\'"'

        assert response['statusCode'] == 400
        assert response['body'] == expected_message


if __name__ == '__main__':
    unittest.main()
