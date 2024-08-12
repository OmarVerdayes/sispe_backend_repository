from unittest.mock import patch, MagicMock
import unittest
import json
from get_favorites.get_favorites import lambda_handler
from decimal import Decimal

mock_event = {
    "pathParameters": {
        "fk_user": "qwertyuiop1234567890abcdef1234567890"
    }
}


class MyTestCase(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_user_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.side_effect = [None, []]

        result = lambda_handler(mock_event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(json.loads(result["body"]), 'Usuario necesario')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_invalid_user_id(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_event = {
            "pathParameters": {
                "userId": "invalid_user_id"  # ID de usuario inválido
            }
        }

        result = lambda_handler(mock_event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(json.loads(result["body"]), 'El ID de usuario no es válido')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_user_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.return_value.fetchone.return_value = None

        mock_event = {
            "pathParameters": {
                "userId": "1234567890abcdef1234567890abcdef"  # ID de usuario en formato válido
            }
        }

        result = lambda_handler(mock_event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(json.loads(result["body"]), 'Usuario no encontrado')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_favorites_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.return_value.fetchall.return_value = []

        mock_event = {
            "pathParameters": {
                "userId": "1234567890abcdef1234567890abcdef"  # ID de usuario en formato válido
            }
        }

        result = lambda_handler(mock_event, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"]), 'Favoritos no encontrados')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_favorites_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_favorites = [
            {
                'fk_film': bytes.fromhex('1234567890abcdef1234567890abcdef'),
                'title': 'Test Movie',
                'description': 'A test movie',
                'length': Decimal('120.00'),
                'status': 'Activo',
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'category_name': 'Test Category'
            }
        ]

        mock_conn.execute.return_value.fetchall.return_value = [mock_favorites[0]]

        mock_event = {
            "pathParameters": {
                "userId": "1234567890abcdef1234567890abcdef"  # ID de usuario en formato válido
            }
        }

        result = lambda_handler(mock_event, None)

        self.assertEqual(result["statusCode"], 200)

        expected_favorites = [
            {
                'fk_film': '1234567890abcdef1234567890abcdef',
                'title': 'Test Movie',
                'description': 'A test movie',
                'length': 120.00,
                'status': 'Activo',
                'front_page': 'http://example.com/front_page.jpg',
                'file': 'http://example.com/file.mp4',
                'category_name': 'Test Category'
            }
        ]

        self.assertEqual(json.loads(result["body"]), expected_favorites)

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("get_favorites.get_favorites.db_connection.connect")
    def test_lambda_handler_type_error(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Parchear json.dumps para lanzar un TypeError
        with patch('get_favorites.get_favorites.json.dumps', side_effect=TypeError("Error de tipo")):
            mock_event = {
                "pathParameters": {
                    "userId": "1234567890abcdef1234567890abcdef"  # ID de usuario en formato válido
                }
            }

            with self.assertRaises(TypeError):
                lambda_handler(mock_event, None)

if __name__ == '__main__':
    unittest.main()
