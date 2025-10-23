"""
Custom storage backends for AWS S3
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    Storage backend for media files (user uploads)
    Uses bucket policy for public access instead of ACLs
    """
    location = 'media'
    file_overwrite = False
    default_acl = None  # Use bucket policy instead of ACLs


class StaticStorage(S3Boto3Storage):
    """
    Storage backend for static files (CSS, JS, images)
    Uses bucket policy for public access instead of ACLs
    """
    location = 'static'
    default_acl = None  # Use bucket policy instead of ACLs
