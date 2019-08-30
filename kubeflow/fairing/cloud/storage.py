import six
import abc
from google.cloud import storage
from urllib.parse import urlparse

def lookup_storage_class(url):
    scheme = urlparse(url).scheme
    if scheme in ["gcs", "gs"]:
        return GCSStorage
    else:
        return None

def get_storage_class(url):
    res = lookup_storage_class(url)
    if res:
        return res
    else:
        raise RuntimeError(
            "can't find a suitable storage class for {}".format(url))


@six.add_metaclass(abc.ABCMeta)
class Storage:

    # Using shell commands to do the file copy instead of using python libs
    # CLIs like gsutil, s3cmd are optimized and can be easily configured by
    # the user using boto.cfg in the base docker image.
    @abc.abstractmethod
    def copy_cmd(self, src_url, dst_url, recursive=True):
        """gets a command to copy files from/to remote storage from/to local FS"""
        raise NotImplementedError('Storage.copy_cmd')

    @abc.abstractmethod
    def exists(self, url):
        """checks if the url exists in the given storage"""
        raise NotImplementedError('Storage.exists')


class GCSStorage(Storage):

    def __init__(self):
        self.client = storage.Client()

    def copy_cmd(self, src_url, dst_url, recursive=True):
        if recursive:
            rcmd = "-r"
        else:
            rcmd = ""
        return "gsutil cp {} {} {}".format(rcmd, src_url, dst_url)

    @classmethod
    def _check_prefix(cls, bucket, prefix):
        # url points to a dir like resource
        # Checking if at least one blob exists
        blobs = [x for x in bucket.list_blobs(prefix=prefix, max_results=1)]
        if len(blobs) == 1:
            return True
        return False

    def exists(self, url):
        url_parts = urlparse(url)
        bucket_name = url_parts.netloc
        bucket = self.client.bucket(bucket_name)
        if not url_parts.path or url_parts.path == "/":
            return True
        if bucket:
            prefix_key = url_parts.path[1:]
            if prefix_key.endswith("/"):
                return GCSStorage._check_prefix(bucket, prefix_key)
            elif bucket.get_blob(prefix_key):
                return True
            else:
                return GCSStorage._check_prefix(bucket, prefix_key + "/")
        return False
