import boto3
import os
import streamlit as st

from botocore.exceptions import NoCredentialsError

S3_BUCKET_NAME_PROJECTS = st.secrets['S3_BUCKET_NAME_PROJECTS']
AWS_ACCESS_KEY_PROJECTS = st.secrets['AWS_ACCESS_KEY_PROJECTS']
AWS_SECRET_KEY_PROJECTS = st.secrets['AWS_SECRET_KEY_PROJECTS']



def upload_to_s3(file_path, object_path_in_s3):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        s3_client.upload_file(file_path, S3_BUCKET_NAME_PROJECTS, object_path_in_s3) 
    except NoCredentialsError:
        print('Credentials not available')


def upload_to_s3_obj(file_obj, object_path_in_s3):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        s3_client.upload_fileobj(file_obj, S3_BUCKET_NAME_PROJECTS, object_path_in_s3)
    except Exception as e:
        print(f'Failed to upload file to S3: {e}')
        return 0

def download_from_s3(object_path_in_s3, file_path):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        file = s3_client.download_file(S3_BUCKET_NAME_PROJECTS, object_path_in_s3, file_path)
        print(f'Object {object_path_in_s3} has been downloaded from {S3_BUCKET_NAME_PROJECTS} to {file_path}')
    except NoCredentialsError:
        print('Credentials not available')
    except Exception as e:
        print(f'An error occurred: {e}')

def get_from_s3(object_path_in_s3):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        return s3_client.get_object(Bucket=S3_BUCKET_NAME_PROJECTS, Key=object_path_in_s3)
    except NoCredentialsError:
        print('Credentials not available')
    except Exception as e:
        print(f'An error occurred: {e}')
    return 0 

def delete_folder_from_s3(folder_path):  # sourcery skip: use-named-expression
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        # List all objects within the folder
        objects_to_delete = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME_PROJECTS, Prefix=folder_path)
        
        # Extract object keys from the response
        object_keys = [obj['Key'] for obj in objects_to_delete.get('Contents', [])]
        
        # Delete the objects
        if object_keys:
            response = s3_client.delete_objects(
                Bucket=S3_BUCKET_NAME_PROJECTS,
                Delete={
                    'Objects': [{'Key': obj_key} for obj_key in object_keys]
                }
            )
            print(f'Deleted objects: {object_keys}')
        else:
            print(f'No objects found in folder: {folder_path}')
    except NoCredentialsError:
        print('Credentials not available')
    except Exception as e:
        print(f'An error occurred: {e}')

def delete_object_from_s3(object_key):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)

    try:
        response = s3_client.delete_object(
            Bucket=S3_BUCKET_NAME_PROJECTS,
            Key=object_key
        )
        print(response)
        print(f'Deleted object: {object_key}')
    except NoCredentialsError:
        print('Credentials not available')
    except Exception as e:
        print(f'An error occurred: {e}')


def read_s3_file(bucket_name, file_key):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)
    try:
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        return s3_object['Body'].read().decode('utf-8')
    except s3_client.exceptions.NoSuchKey:
        return ""
    except Exception as e:
        print(f"Error reading file from S3: {e}")
        return ""

def write_to_s3(bucket_name, file_key, content):
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_PROJECTS, aws_secret_access_key=AWS_SECRET_KEY_PROJECTS)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=file_key, Body=content.encode('utf-8'))
        print(f'File has been uploaded to {bucket_name}/{file_key}')
    except Exception as e:
        print(f"Error writing file to S3: {e}")