import base64

import boto3
from botocore.exceptions import ClientError

secrets_client = boto3.client('secretsmanager')

config_dictionary = {
    'tumblr_call_tracker': 0,
    'follows': {
        'archive': False,
        'unfollow': False,
        'refollow': False,
    },
    'likes': {
        'archive': False,
        'capture': True,
        'unlike': True,
        'relike': False,
    },
    'posts': {
        'archive': False,
        'capture': False,
        'delete': False
    },
    'run_options': {
        'continuous_run': True,
    },
    'credentials': {
        'load_from': 'aws', # allows values: 'config' or 'aws'
        'secrets': {
            'consumer_key': 'red',
            'consumer_secret': 'gold',
            'oauth_token': 'green',
            'oauth_secret': 'blue'
        }
    },
    'supplemental_editor': {
        'do': False
    },
    'paths': {
        'path_archives': '../resources/archives/',
        'path_binaries': '../resources/captures/',
        'path_logs': '../resources/logs/'
    }
}


def get_secret():
    secret_name = "tumblr_creds"
    region_name = "us-west-2"
    profile = "admin"

    # Create a Secrets Manager client
    session = boto3.session.Session(profile_name=profile)
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret_dictionary_as_a_string = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return secret_dictionary_as_a_string
