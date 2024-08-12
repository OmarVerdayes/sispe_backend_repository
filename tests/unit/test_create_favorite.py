from unittest.mock import patch, MagicMock
import unittest
import json
from create_favorite.create_favorite import lambda_handler
from create_favorite.sqlalchemy.exc import SQLAlchemyError


class TestLambdaHandler(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_success(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        response = lambda_handler({}, {})
        # Assertions
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'],'"Entrada invalida, cuerpo no encontrado"')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_invalid_id(self, mock_connect):
        # Setup mock
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Caso en el que el ID no es hex
        event = {
            'body': json.dumps({
                'fk_user': 'invalid_user_id',
                'fk_film': '00000000000000000000000000000000'
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body, 'El ID de usuario o pelicula no es válido')



    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_user_not_found(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.return_value.fetchone.return_value = None

        event = {
            'body': json.dumps({
                'fk_user': '00000000000000000000000000000000',  # ID válido
                'fk_film': '00000000000000000000000000000000'  # ID válido
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body, 'Usuario no encontrado')



    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_film_not_found_or_inactive(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Configurar el mock para simular que la película no existe o no está activa
        mock_conn.execute.side_effect = [
            # Simular que el usuario existe
            MagicMock(fetchone=MagicMock(return_value=(b'\x00'*16))),
            # Simular que la película no está activa
            MagicMock(fetchone=MagicMock(return_value=None))
        ]

        event = {
            'body': json.dumps({
                'fk_user': '00000000000000000000000000000000',  # ID válido
                'fk_film': '00000000000000000000000000000000'  # ID válido
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        # Assertions
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body, 'Película no encontrada o no está activa')


    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_film_already_favorite(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Configurar el mock para simular que la película ya está en favoritos
        mock_conn.execute.side_effect = [
            # Simular que el usuario existe
            MagicMock(fetchone=MagicMock(return_value=(b'\x00'*16))),
            # Simular que la película está activa
            MagicMock(fetchone=MagicMock(return_value=(b'\x00'*16))),
            # Simular que la película ya está en favoritos
            MagicMock(fetchone=MagicMock(return_value=(b'\x00'*16)))
        ]

        event = {
            'body': json.dumps({
                'fk_user': '00000000000000000000000000000000',  # ID válido
                'fk_film': '00000000000000000000000000000000'  # ID válido
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body, 'Película ya agregada a la lista de favoritos')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Configurar el mock para simular que la película fue agregada exitosamente
        mock_conn.execute.side_effect = [
            # Simular que el usuario existe
            MagicMock(fetchone=MagicMock(return_value=(b'\x00' * 16))),
            # Simular que la película está activa
            MagicMock(fetchone=MagicMock(return_value=(b'\x00' * 16))),
            # Simular que la película no está en favoritos
            MagicMock(fetchone=MagicMock(return_value=None)),
            # Simular la inserción de la película en favoritos
            MagicMock()
        ]

        event = {
            'body': json.dumps({
                'fk_user': '00000000000000000000000000000000',  # ID válido
                'fk_film': '00000000000000000000000000000000'  # ID válido
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body, 'Película agregada a la lista de favoritos')




    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_favorite.create_favorite.db_connection.connect")
    def test_lambda_handler_success(self, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Configurar el mock para simular que la película fue agregada exitosamente
        mock_conn.execute.side_effect = [
            # Simular que el usuario existe
            MagicMock(fetchone=MagicMock(return_value=(b'\x00' * 16))),
            # Simular que la película está activa
            MagicMock(fetchone=MagicMock(return_value=(b'\x00' * 16))),
            # Simular que la película no está en favoritos
            MagicMock(fetchone=MagicMock(return_value=None)),
            # Simular la inserción de la película en favoritos
            MagicMock()
        ]

        event = {
            'body': json.dumps({
                'fk_user': '00000000000000000000000000000000',  # ID válido
                'fk_film': '00000000000000000000000000000000'  # ID válido
            })
        }

        response = lambda_handler(event, {})

        response_body = json.loads(response['body'])

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body, 'Película agregada a la lista de favoritos')

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    def test_lambda_handler_invalid_json_format(self):
        # Evento con un cuerpo JSON inválido
        event = {
            'body': '{invalid json}'
        }

        response = lambda_handler(event, {})
        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body, 'Formato JSON inválido')


if __name__ == '__main__':
    unittest.main()
