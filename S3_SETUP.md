# AWS S3 Setup Guide

This guide will help you configure your Django application to store uploaded files directly to Amazon S3 bucket: **file-upload-lambda-bucket-2025**

## Prerequisites

- AWS Account
- AWS IAM User with S3 access
- S3 bucket created (file-upload-lambda-bucket-2025)

## Step 1: Create/Configure S3 Bucket

### 1.1 Create S3 Bucket (if not already created)

```bash
# Using AWS CLI
aws s3 mb s3://file-upload-lambda-bucket-2025 --region us-east-1
```

Or via AWS Console:
1. Go to AWS Console → S3
2. Click "Create bucket"
3. Bucket name: `file-upload-lambda-bucket-2025`
4. Region: `us-east-1` (or your preferred region)
5. Click "Create bucket"

### 1.2 Configure Bucket Policy

Add a bucket policy to allow public read access (if needed):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::file-upload-lambda-bucket-2025/*"
        }
    ]
}
```

Apply this policy:
1. Go to S3 → file-upload-lambda-bucket-2025 → Permissions
2. Scroll to "Bucket policy"
3. Click "Edit" and paste the policy above
4. Click "Save changes"

### 1.3 Configure CORS (if needed for web uploads)

Add CORS configuration:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
    }
]
```

Apply CORS:
1. Go to S3 → file-upload-lambda-bucket-2025 → Permissions
2. Scroll to "Cross-origin resource sharing (CORS)"
3. Click "Edit" and paste the configuration above
4. Click "Save changes"

### 1.4 Block Public Access Settings

For a public bucket:
1. Go to S3 → file-upload-lambda-bucket-2025 → Permissions
2. Click "Edit" on "Block public access"
3. Uncheck "Block all public access"
4. Save changes

**Note:** Only do this if you need public access. For private files, keep these settings enabled.

## Step 2: Create IAM User and Get Credentials

### 2.1 Create IAM User

```bash
# Using AWS CLI
aws iam create-user --user-name drobe-s3-user
```

Or via AWS Console:
1. Go to IAM → Users
2. Click "Add users"
3. Username: `drobe-s3-user`
4. Access type: "Programmatic access"
5. Click "Next"

### 2.2 Create IAM Policy

Create a policy file `s3-policy.json`:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::file-upload-lambda-bucket-2025",
                "arn:aws:s3:::file-upload-lambda-bucket-2025/*"
            ]
        }
    ]
}
```

Apply the policy:

```bash
# Create policy
aws iam create-policy --policy-name DrobeS3Policy --policy-document file://s3-policy.json

# Attach policy to user
aws iam attach-user-policy --user-name drobe-s3-user --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/DrobeS3Policy
```

Or via AWS Console:
1. Go to IAM → Policies
2. Click "Create policy"
3. Switch to JSON tab and paste the policy above
4. Name it: `DrobeS3Policy`
5. Click "Create policy"
6. Go to IAM → Users → drobe-s3-user
7. Click "Add permissions" → "Attach policies directly"
8. Select `DrobeS3Policy` and click "Add permissions"

### 2.3 Get Access Keys

```bash
# Create access key
aws iam create-access-key --user-name drobe-s3-user
```

This will output:
- `AccessKeyId`
- `SecretAccessKey`

**IMPORTANT:** Save these credentials securely. You won't be able to see the secret key again.

Or via AWS Console:
1. Go to IAM → Users → drobe-s3-user
2. Click "Security credentials" tab
3. Click "Create access key"
4. Choose "Application running outside AWS"
5. Copy the Access Key ID and Secret Access Key

## Step 3: Configure Django Application

### 3.1 Update .env File

Create/update your `.env` file in the project root:

```env
# AWS S3 Configuration
USE_S3=True
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=your-secret-access-key-here
AWS_STORAGE_BUCKET_NAME=file-upload-lambda-bucket-2025
AWS_S3_REGION_NAME=us-east-1

# Optional: If using CloudFront CDN
# AWS_S3_CUSTOM_DOMAIN=d123456abcdef.cloudfront.net
```

### 3.2 Verify Configuration

The following files have been configured for S3:

1. **requirements.txt**: Added `boto3` and `django-storages`
2. **Drobe/storage_backends.py**: Custom storage backends for media and static files
3. **Drobe/settings.py**: S3 configuration based on `USE_S3` environment variable
4. **docker-compose.yml**: AWS environment variables added to services

## Step 4: Test S3 Upload

### 4.1 Rebuild Docker Containers

```bash
# Rebuild with new dependencies
docker-compose down
docker-compose build
docker-compose up -d
```

### 4.2 Test Upload via Django Admin

1. Access Django Admin: http://your-domain.com/admin/
2. Go to any model with file/image fields
3. Upload a file
4. Check your S3 bucket to verify the file was uploaded

### 4.3 Verify Upload via AWS CLI

```bash
# List files in bucket
aws s3 ls s3://file-upload-lambda-bucket-2025/media/ --recursive
```

### 4.4 Test File Access

Files should be accessible at:
```
https://file-upload-lambda-bucket-2025.s3.amazonaws.com/media/your-file.jpg
```

## Step 5: Collect Static Files to S3 (Optional)

To also serve static files from S3:

```bash
# Collect static files to S3
docker-compose exec web python manage.py collectstatic --noinput
```

This will upload all static files (CSS, JS, images) to S3.

## Troubleshooting

### Error: "NoCredentialsError"

**Cause:** AWS credentials not configured properly.

**Solution:**
```bash
# Check environment variables are set
docker-compose exec web env | grep AWS

# Verify .env file has correct credentials
cat .env | grep AWS
```

### Error: "AccessDenied"

**Cause:** IAM user doesn't have permission to access the bucket.

**Solution:**
- Verify IAM policy is attached to the user
- Check bucket policy allows the action
- Ensure bucket name is correct in .env

### Error: "bucket does not exist"

**Cause:** Bucket name is incorrect or in different region.

**Solution:**
```bash
# List your buckets
aws s3 ls

# Verify bucket exists
aws s3 ls s3://file-upload-lambda-bucket-2025
```

### Files Not Publicly Accessible

**Cause:** Bucket or object ACL is private.

**Solution:**
- Check bucket policy allows public read
- Check "Block public access" settings
- In `storage_backends.py`, verify `default_acl = 'public-read'`

### Files Upload but Not Visible in Admin

**Cause:** MEDIA_URL not configured correctly.

**Solution:**
- Check `MEDIA_URL` in settings points to S3
- Verify `USE_S3=True` in .env
- Restart containers: `docker-compose restart web daphne`

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `.env` to `.gitignore`
   - Use environment variables

2. **Use IAM roles on EC2** (recommended for production)
   ```bash
   # Attach IAM role to EC2 instance
   # No need for access keys in .env
   ```

3. **Enable bucket versioning** (optional backup)
   ```bash
   aws s3api put-bucket-versioning \
     --bucket file-upload-lambda-bucket-2025 \
     --versioning-configuration Status=Enabled
   ```

4. **Enable server-side encryption**
   ```bash
   aws s3api put-bucket-encryption \
     --bucket file-upload-lambda-bucket-2025 \
     --server-side-encryption-configuration '{
       "Rules": [{
         "ApplyServerSideEncryptionByDefault": {
           "SSEAlgorithm": "AES256"
         }
       }]
     }'
   ```

5. **Set up lifecycle policies** (optional cleanup)
   - Delete old temporary files
   - Archive old media files to Glacier

## Using CloudFront CDN (Optional)

For better performance, use CloudFront CDN:

### 1. Create CloudFront Distribution

```bash
aws cloudfront create-distribution \
  --origin-domain-name file-upload-lambda-bucket-2025.s3.amazonaws.com \
  --default-root-object index.html
```

Or via AWS Console:
1. Go to CloudFront → Create Distribution
2. Origin domain: Select your S3 bucket
3. Create distribution

### 2. Update .env

```env
AWS_S3_CUSTOM_DOMAIN=d123456abcdef.cloudfront.net
```

### 3. Restart Application

```bash
docker-compose restart web daphne
```

Now files will be served via CloudFront CDN for faster delivery.

## Monitoring and Costs

### Monitor S3 Usage

```bash
# Get bucket size
aws s3 ls s3://file-upload-lambda-bucket-2025 --recursive --human-readable --summarize
```

### Estimate Costs

S3 pricing (us-east-1):
- Storage: ~$0.023 per GB/month
- PUT requests: $0.005 per 1,000 requests
- GET requests: $0.0004 per 1,000 requests
- Data transfer out: First 100 GB/month is free

Example for 10 GB storage with 1,000 uploads/month:
- Storage: 10 GB × $0.023 = $0.23
- Uploads: 1,000 × $0.005/1000 = $0.005
- **Total: ~$0.24/month**

## Additional Features

### Signed URLs (for private files)

If you need private file access with temporary URLs:

1. Update `storage_backends.py`:
```python
class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = 'private'  # Changed to private
    querystring_auth = True  # Enable signed URLs
    querystring_expire = 3600  # URL expires in 1 hour
```

2. Update settings.py:
```python
AWS_QUERYSTRING_AUTH = True
AWS_S3_SIGNATURE_VERSION = 's3v4'
```

### Different Storage for Different Models

Create separate storage classes:

```python
# In storage_backends.py
class ProfilePictureStorage(S3Boto3Storage):
    location = 'media/profiles'

class DocumentStorage(S3Boto3Storage):
    location = 'media/documents'
    default_acl = 'private'
```

Use in models:
```python
from Drobe.storage_backends import ProfilePictureStorage, DocumentStorage

class UserProfile(models.Model):
    avatar = models.ImageField(storage=ProfilePictureStorage())

class Document(models.Model):
    file = models.FileField(storage=DocumentStorage())
```

## Support

For issues:
- AWS S3 Documentation: https://docs.aws.amazon.com/s3/
- django-storages Documentation: https://django-storages.readthedocs.io/
- boto3 Documentation: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
