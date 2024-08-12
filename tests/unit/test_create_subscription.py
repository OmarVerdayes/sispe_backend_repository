from unittest.mock import patch, MagicMock
import json
import unittest
from sqlalchemy.exc import SQLAlchemyError
from create_subscription.create_subscription import lambda_handler


class MyTestCase(unittest.TestCase):

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_subscription.create_subscription.db_connection.connect")
    @patch("create_subscription.create_subscription.boto3.client")
    def test_missing_required_data(self, mock_boto_client, mock_db_connection):
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        event = {
            'body': json.dumps({
                'lastname': 'Verdayes',
                'email': '20213tn042@utez.edu.mx',
                'fkRol': '0123456789abcdef0123456789abcdef'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps('Faltan datos obligatorios'))

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_subscription.create_subscription.db_connection.connect")
    @patch("create_subscription.create_subscription.boto3.client")
    def test_invalid_fk_rol_format(self, mock_boto_client, mock_db_connection):
        # Mock the database connection
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        # Mock the boto3 client
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Define the event with an invalid fk_rol format
        event = {
            'body': json.dumps({
                'name': 'Omar',
                'lastname': 'Verdayes',
                'email': '20213tn042@utez.edu.mx',
                'fkRol': 'invalid_hex_format'  # Invalid fk_rol format
            })
        }

        # Call the Lambda handler function
        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], json.dumps('Formato de fk_rol inválido'))

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_subscription.create_subscription.db_connection")
    @patch("create_subscription.create_subscription.boto3.client")
    def test_successful_user_registration(self, mock_boto_client, mock_db_connection):
        # Mock the database connection and execution
        mock_conn = MagicMock()
        mock_db_connection.connect.return_value = mock_conn

        # Mock the boto3 client and its methods
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Define a valid event
        event = {
            'body': json.dumps({
                'name': 'Omar',
                'lastname': 'Verdayes',
                'email': '20213tn042@utez.edu.mx',
                'fkRol': '0123456789abcdef0123456789abcdef'  # Valid hexadecimal string for fk_rol
            })
        }

        # Call the Lambda handler function
        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], json.dumps('Usuario registrado, verifica tu correo electrónico'))
        self.assertEqual(response['headers'], {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        })

        # Ensure that the database connection was opened and queries were executed
        mock_db_connection.connect.assert_called_once()
        self.assertTrue(mock_conn.execute.called, "Expected 'execute' to be called on the connection.")

        # Ensure that the connection was closed
        mock_conn.close.assert_called_once()

        # Capture the arguments passed to admin_create_user
        create_user_call_args = mock_client.admin_create_user.call_args

        # Assert that the expected parameters were passed, ignoring the TemporaryPassword
        self.assertEqual(create_user_call_args.kwargs['UserPoolId'], 'us-east-1_hpKh8IecL')
        self.assertEqual(create_user_call_args.kwargs['Username'], '20213tn042@utez.edu.mx')
        self.assertEqual(create_user_call_args.kwargs['UserAttributes'], [
            {'Name': 'email', 'Value': '20213tn042@utez.edu.mx'},
            {'Name': 'email_verified', 'Value': 'true'}
        ])

        # Ensure that the Cognito client methods were called correctly
        mock_client.admin_add_user_to_group.assert_called_once_with(
            UserPoolId='us-east-1_hpKh8IecL',
            Username='20213tn042@utez.edu.mx',
            GroupName='cliente',
        )

    @patch.dict("os.environ", {"DB_USER": "user", "DB_PASSWORD": "password", "DB_NAME": "database", "DB_HOST": "host"})
    @patch("create_subscription.create_subscription.db_connection.connect")
    @patch("create_subscription.create_subscription.boto3.client")
    def test_internal_server_error(self, mock_boto_client, mock_db_connect):
        # Mock the database connection to raise an exception
        mock_db_connect.side_effect = Exception("Simulated exception")

        # Mock the boto3 client to prevent any actual AWS interaction
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Define a valid event
        event = {
            'body': json.dumps({
                'name': 'Omar',
                'lastname': 'Verdayes',
                'email': '20213tn042@utez.edu.mx',
                'fkRol': '0123456789abcdef0123456789abcdef'  # Valid hexadecimal string for fk_rol
            })
        }

        # Call the Lambda handler function
        response = lambda_handler(event, None)

        # Assert the response status code and body
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['headers'], {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        })

        # Assert that the body contains the correct error message
        response_body = json.loads(response['body'])
        self.assertIn("error_message", response_body)
        self.assertEqual(response_body["error_message"], "Simulated exception")


if __name__ == '__main__':
    unittest.main()
