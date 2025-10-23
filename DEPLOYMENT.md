# Drobe Application - Docker Deployment Guide

This guide will help you deploy the Drobe Django application on an AWS EC2 Ubuntu server using Docker, Nginx, and uWSGI.

## Architecture

The application uses the following Docker services:
- **nginx**: Reverse proxy server (port 80)
- **web**: Django application with uWSGI (HTTP requests)
- **daphne**: Django ASGI server (WebSocket connections)
- **db**: PostgreSQL database
- **redis**: Redis server for Channels layer

## Prerequisites

- AWS EC2 instance running Ubuntu (20.04 or later)
- Domain name pointed to your EC2 instance (optional but recommended)
- SSH access to your server

## Step 1: Prepare EC2 Instance

### 1.1 Connect to your EC2 instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### 1.2 Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 1.4 Configure Security Group

Ensure your EC2 security group allows:
- Port 22 (SSH)
- Port 80 (HTTP)
- Port 443 (HTTPS) - if using SSL

## Step 2: Deploy Application

### 2.1 Clone or upload your project

```bash
# Option 1: Clone from Git
git clone <your-repo-url> /home/ubuntu/drobe
cd /home/ubuntu/drobe

# Option 2: Upload via SCP
# From your local machine:
# scp -i your-key.pem -r ./Drobe ubuntu@your-ec2-ip:/home/ubuntu/drobe
```

### 2.2 Create environment file

```bash
cd /home/ubuntu/drobe
cp .env.example .env
nano .env
```

Update the .env file with your production values:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-ec2-ip

# Database Configuration
DB_NAME=drobe
DB_USER=drobe_user
DB_PASSWORD=strong-database-password-here

# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key

# CORS Configuration (if needed)
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

To generate a strong SECRET_KEY:
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 2.3 Build and start containers

```bash
# Build the Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check if containers are running
docker-compose ps
```

### 2.4 Create Django superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

### 2.5 Verify deployment

```bash
# Check logs
docker-compose logs -f

# Test the application
curl http://localhost/health/
```

Your application should now be accessible at:
- HTTP: http://your-ec2-ip or http://your-domain.com
- Admin: http://your-domain.com/admin/
- WebSocket: ws://your-domain.com/ws/

## Step 3: SSL Configuration (Optional but Recommended)

### 3.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 3.2 Update Nginx configuration for SSL

Create a new file for SSL configuration:

```bash
sudo nano /home/ubuntu/drobe/nginx-ssl.conf
```

Add the following content:

```nginx
upstream django_http {
    server web:8000;
}

upstream django_websocket {
    server web:8001;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location /ws/ {
        proxy_pass http://django_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_read_timeout 86400;
    }

    location / {
        uwsgi_pass django_http;
        include /etc/nginx/uwsgi_params;
        uwsgi_read_timeout 300;
        uwsgi_send_timeout 300;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health/ {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

### 3.3 Obtain SSL certificate

```bash
# Stop nginx container temporarily
docker-compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Update docker-compose.yml to mount SSL certificates
```

Update your docker-compose.yml nginx service:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
    - static_volume:/app/staticfiles:ro
    - media_volume:/app/media:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  depends_on:
    - web
    - daphne
  restart: unless-stopped
```

Restart services:

```bash
docker-compose up -d
```

## Useful Docker Commands

```bash
# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Start services
docker-compose up -d

# Rebuild a service
docker-compose up -d --build [service_name]

# Execute command in container
docker-compose exec web python manage.py [command]

# Access database
docker-compose exec db psql -U drobe_user -d drobe

# Create database backup
docker-compose exec db pg_dump -U drobe_user drobe > backup.sql

# Restore database
docker-compose exec -T db psql -U drobe_user drobe < backup.sql
```

## Maintenance

### Update application code

```bash
cd /home/ubuntu/drobe
git pull  # or upload new files
docker-compose build web daphne
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

### Monitor resources

```bash
# Check container stats
docker stats

# Check disk usage
docker system df
```

### View application logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web

# Last 100 lines
docker-compose logs --tail=100 web
```

## Backup Strategy

### Database Backup

Create a backup script:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U drobe_user drobe > /home/ubuntu/backups/db_backup_$DATE.sql
# Keep only last 7 days
find /home/ubuntu/backups -name "db_backup_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add this line for daily backups at 2 AM
0 2 * * * /home/ubuntu/drobe/backup.sh
```

### Media Files Backup

```bash
# Backup media files
docker run --rm -v drobe_media_volume:/data -v /home/ubuntu/backups:/backup ubuntu tar czf /backup/media_backup_$(date +%Y%m%d).tar.gz -C /data .
```

## Troubleshooting

### Container won't start

```bash
docker-compose logs [service_name]
docker-compose ps
```

### Permission issues

```bash
docker-compose exec web chown -R appuser:appuser /app
```

### Database connection errors

Check that the database service is healthy:
```bash
docker-compose exec db pg_isready -U drobe_user
```

### Static files not loading

```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

## Security Checklist

- [ ] Set DEBUG=False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Set up SSL/TLS certificate
- [ ] Configure firewall (UFW)
- [ ] Use strong database passwords
- [ ] Configure CORS properly
- [ ] Keep Docker and packages updated
- [ ] Set up regular backups
- [ ] Monitor logs for suspicious activity

## Performance Tuning

### For high traffic:

1. Increase uWSGI workers in uwsgi.ini:
```ini
processes = 8
threads = 4
```

2. Add more Daphne instances in docker-compose.yml

3. Consider using a managed database service (RDS)

4. Implement caching with Redis

5. Use CDN for static files

## Support

For issues or questions, refer to:
- Django documentation: https://docs.djangoproject.com/
- Docker documentation: https://docs.docker.com/
- Project repository: [your-repo-url]
