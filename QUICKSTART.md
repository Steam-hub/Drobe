# Quick Start Guide - Deploy on EC2 Ubuntu

This is a simple guide to get your Django app running on AWS EC2 with Docker, Nginx, and uWSGI. All services (PostgreSQL, Redis, Django, Nginx) run in Docker containers - no manual installation needed!

## What You Get

- **PostgreSQL**: Database running in Docker
- **Redis**: WebSocket channel layer in Docker
- **Django + uWSGI**: Your app handling HTTP requests
- **Daphne**: WebSocket server for real-time features
- **Nginx**: Reverse proxy serving on port 80
- **S3 Storage**: Files uploaded via admin go directly to S3

## Step 1: Prepare EC2 Server

```bash
# Connect to your EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for docker group to take effect
exit
```

## Step 2: Upload Your Project

```bash
# From your local machine, upload the project
scp -i your-key.pem -r ./Drobe ubuntu@your-ec2-ip:/home/ubuntu/drobe

# Or clone from Git
ssh -i your-key.pem ubuntu@your-ec2-ip
cd /home/ubuntu
git clone <your-repo-url> drobe
cd drobe
```

## Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit the .env file
nano .env
```

Update these values in .env:

```env
# Django Settings
DEBUG=False
SECRET_KEY=generate-a-long-random-secret-key-here
ALLOWED_HOSTS=your-domain.com,your-ec2-public-ip

# Database Configuration
DB_NAME=drobe
DB_USER=drobe_user
DB_PASSWORD=choose-a-strong-password

# Gemini API Key
GEMINI_API_KEY=your-gemini-api-key

# AWS S3 Configuration (for file uploads)
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=file-upload-lambda-bucket-2025
AWS_S3_REGION_NAME=us-east-1

# CORS (optional)
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

To generate a Django secret key:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## Step 4: Configure EC2 Security Group

In AWS Console → EC2 → Security Groups, allow:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS) - if using SSL

## Step 5: Deploy!

```bash
# Build and start all containers
docker-compose build
docker-compose up -d

# Check if everything is running
docker-compose ps

# View logs
docker-compose logs -f
```

## Step 6: Create Admin User

```bash
# Create Django superuser
docker-compose exec web python manage.py createsuperuser
```

## Step 7: Access Your App

- **Website**: http://your-ec2-ip/
- **Admin Panel**: http://your-ec2-ip/admin/
- **Health Check**: http://your-ec2-ip/health/

## S3 File Upload Configuration

See [S3_SETUP.md](S3_SETUP.md) for detailed instructions on:
- Creating S3 bucket
- Setting up IAM user with proper permissions
- Getting AWS credentials

Quick test:
1. Go to Django Admin
2. Upload a file in any model with file/image field
3. Check your S3 bucket - file should appear there!

## Common Commands

```bash
# Stop all services
docker-compose down

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f web

# Restart a service
docker-compose restart web

# Run Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic

# Access database
docker-compose exec db psql -U drobe_user -d drobe

# Rebuild after code changes
docker-compose build web daphne
docker-compose up -d
```

## Backup Database

```bash
# Backup
docker-compose exec db pg_dump -U drobe_user drobe > backup.sql

# Restore
docker-compose exec -T db psql -U drobe_user drobe < backup.sql
```

## Troubleshooting

### Services not starting?
```bash
docker-compose logs [service-name]
```

### Can't access website?
- Check security group allows port 80
- Check containers are running: `docker-compose ps`
- Check nginx logs: `docker-compose logs nginx`

### Database connection error?
- Wait for db to be healthy: `docker-compose logs db`
- Check DB password in .env matches

### S3 upload not working?
- Check USE_S3=True in .env
- Verify AWS credentials are correct
- Check IAM user has S3 permissions
- See [S3_SETUP.md](S3_SETUP.md) for detailed troubleshooting

### Static files not loading?
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

## Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build web daphne
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
```

## Monitor Resources

```bash
# View container stats
docker stats

# Check disk usage
df -h
docker system df
```

## SSL/HTTPS Setup (Optional)

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed SSL configuration with Let's Encrypt.

Quick SSL:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Stop nginx container
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Update docker-compose.yml to mount certificates
# See DEPLOYMENT.md for details
```

## Architecture Overview

```
Internet
   ↓
Nginx (port 80) ← Docker Container
   ↓
   ├─→ uWSGI (port 8000) ← Django Web App (HTTP)
   └─→ Daphne (port 8001) ← Django WebSocket
           ↓
       PostgreSQL ← Database
       Redis ← WebSocket Channel Layer
```

When you upload files via Django Admin:
- Files are sent to Django
- Django uses boto3 to upload to S3
- Files are stored in: `s3://file-upload-lambda-bucket-2025/media/`

## Full Documentation

- Detailed deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- S3 configuration guide: [S3_SETUP.md](S3_SETUP.md)

## Support

For issues:
- Check logs: `docker-compose logs -f`
- Verify .env configuration
- See troubleshooting sections in documentation
