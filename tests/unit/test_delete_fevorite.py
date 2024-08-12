from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from delete_favorite.delete_favorite import lambda_handler



class MyTestCase(unittest.TestCase):

    @patch('delete_favorite.delete_favorite.logger')
    def test_invalid_body_response(self, mock_logger):
        event = {
            'body': None
        }
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Entrada invalida, cuerpo no encontrado')

    @patch('delete_favorite.delete_favorite.logger')
    def test_missing_user_and_film(self, mock_logger):
        event = {
            'body': json.dumps({})
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'usuario y pelicula necesario')

    @patch('delete_favorite.delete_favorite.logger')
    def test_invalid_user_or_film_id(self, mock_logger):
        event = {
            'body': json.dumps({
                'fk_user': 'invalid_user_id',
                'fk_film': 'invalid_film_id'
            })
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'ID de usuario o película no es válido')

    @patch('delete_favorite.delete_favorite.db_connection.connect')
    @patch('delete_favorite.delete_favorite.logger')
    def test_user_not_found(self, mock_logger, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = None

        event = {
            'body': json.dumps({
                'fk_user': '1234567890abcdef1234567890abcdef',
                'fk_film': 'abcdef1234567890abcdef1234567890'
            })
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Usuario no encontrado')

    @patch('delete_favorite.delete_favorite.db_connection.connect')
    @patch('delete_favorite.delete_favorite.logger')
    def test_film_not_in_favorites(self, mock_logger, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value={'user_id': '1234567890abcdef1234567890abcdef'})),
            MagicMock(fetchone=MagicMock(return_value=None))  # Película no está en favoritos
        ]

        event = {
            'body': json.dumps({
                'fk_user': '1234567890abcdef1234567890abcdef',
                'fk_film': 'abcdef1234567890abcdef1234567890'
            })
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Pelicula no esta en la lista de favoritos')

    @patch('delete_favorite.delete_favorite.db_connection.connect')
    @patch('delete_favorite.delete_favorite.logger')
    def test_successful_deletion(self, mock_logger, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        # Configura el side_effect para manejar todas las llamadas a execute
        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value={'user_id': '1234567890abcdef1234567890abcdef'})),
            # Usuario existe
            MagicMock(fetchone=MagicMock(return_value={'favorite_id': 'abcdef1234567890abcdef1234567890'})),
            # Película en favoritos
            MagicMock()  # Simular la acción de eliminación (sin devolver nada)
        ]

        event = {
            'body': json.dumps({
                'fk_user': '1234567890abcdef1234567890abcdef',
                'fk_film': 'abcdef1234567890abcdef1234567890'
            })
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), 'Se ha eliminado la pelicula de la lista de favoritos')

    @patch('delete_favorite.delete_favorite.db_connection.connect')
    @patch('delete_favorite.delete_favorite.logger')
    def test_database_error(self, mock_logger, mock_connect):
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        event = {
            'body': json.dumps({
                'fk_user': '1234567890abcdef1234567890abcdef',
                'fk_film': 'abcdef1234567890abcdef1234567890'
            })
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), 'Error al eliminar la pelicula de la lista de favoritos')

    @patch('delete_favorite.delete_favorite.logger')
    def test_invalid_json_format(self, mock_logger):
        event = {
            'body': '{invalid_json}'
        }

        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body']), 'Formato invalido')


if __name__ == '__main__':
    unittest.main()
