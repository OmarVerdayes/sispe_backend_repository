from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from create_rateing.create_rateing import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_rateing.create_rateing.db_connection.connect")
    def test_create_rateing_success(self, mock_db_connection):
        # Mock the connection and execution
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        event = {
            'body': json.dumps({
                'grade': 4.5,
                'comment': 'Great film!',
                'fk_user': '0123456789abcdef0123456789abcdef',
                'fk_film': 'abcdef0123456789abcdef0123456789'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps('Rateing creado'))

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_rateing.create_rateing.db_connection.connect")
    def test_create_rateing_error(self, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn
        mock_conn.execute.side_effect = SQLAlchemyError("Database error")

        event = {
            'body': json.dumps({
                'grade': 4.5,
                'comment': 'Great film!',
                'fk_user': '0123456789abcdef0123456789abcdef',
                'fk_film': 'abcdef0123456789abcdef0123456789'
            })
        }

        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps('Error creating rateing'))

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_rateing.create_rateing.db_connection.connect")
    def test_invalid_json_format(self, mock_db_connection):
        # Mock the connection to ensure it is never used
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        # Define the event with invalid JSON format (simulate JSONDecodeError)
        event = {
            'body': "{invalid_json_format"  # This is intentionally malformed
        }

        # Call the Lambda handler function
        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps('Invalid JSON format'))

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_rateing.create_rateing.db_connection.connect")
    def test_internal_server_error(self, mock_db_connection):
        # Mock the connection to raise a generic Exception
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn
        mock_conn.execute.side_effect = Exception("Unexpected error")

        # Define the event with valid data
        event = {
            'body': json.dumps({
                'grade': 4.5,
                'comment': 'Good film',
                'fk_user': '0123456789abcdef0123456789abcdef',
                'fk_film': 'fedcba9876543210fedcba9876543210'
            })
        }

        # Call the Lambda handler function
        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], json.dumps('Internal server error'))





if __name__ == '__main__':
    unittest.main()
