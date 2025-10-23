"""
Custom storage backends for AWS S3
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for media files (user uploads)
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'public-read'


class StaticStorage(S3Boto3Storage):
    """
    Storage backend for static files (CSS, JS, images)
    """
    location = 'static'
    default_acl = 'public-read'
