import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class MinioUploader(object):
    def __init__(self, endpoint_url, minio_secret, minio_secret_key,
                 region_name):

        self.client = boto3.client('s3',
                                   endpoint_url=endpoint_url,
                                   aws_access_key_id=minio_secret,
                                   aws_secret_access_key=minio_secret_key,
                                   config=Config(signature_version='s3v4'),
                                   region_name=region_name,
                                   use_ssl=False)

    def create_bucket(self, bucket_name):
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            bucket = {'Bucket': bucket_name}
            self.client.create_bucket(**bucket)

    def upload_to_bucket(self, blob_name, bucket_name, file_to_upload):
        self.create_bucket(bucket_name)
        self.client.upload_file(file_to_upload, bucket_name, blob_name)
        return "s3://{}/{}".format(bucket_name, blob_name)
