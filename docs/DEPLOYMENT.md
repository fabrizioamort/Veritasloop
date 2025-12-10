# Deployment Guide

Complete guide for deploying VeritasLoop to production environments.

## Production Deployment

### Backend (FastAPI)

#### Option 1: Using Docker (Recommended)

**Create Dockerfile:**
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t veritasloop-backend .
docker run -p 8000:8000 --env-file .env veritasloop-backend
```

**Docker Compose** (see Full Stack section below)

#### Option 2: Using systemd

**Create service file:**
```ini
# /etc/systemd/system/veritasloop-api.service
[Unit]
Description=VeritasLoop FastAPI Backend
After=network.target

[Service]
Type=simple
User=veritasloop
WorkingDirectory=/opt/veritasloop
Environment="PATH=/opt/veritasloop/.venv/bin"
EnvironmentFile=/opt/veritasloop/.env
ExecStart=/opt/veritasloop/.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable veritasloop-api
sudo systemctl start veritasloop-api
sudo systemctl status veritasloop-api
```

#### Option 3: Using Gunicorn + Uvicorn Workers

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Run:**
```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile /var/log/veritasloop/access.log \
  --error-logfile /var/log/veritasloop/error.log
```

**Why multiple workers?**
- Better utilization of multi-core CPUs
- Handle concurrent verification requests
- Improved fault tolerance

**Recommended workers**: CPU cores × 2 + 1

### Frontend (React)

#### Build for Production

```bash
cd frontend
npm run build
```

This creates optimized static files in `frontend/dist/`.

**Optimizations applied:**
- Minification (removes whitespace, shortens variable names)
- Tree shaking (removes unused code)
- Code splitting (separate chunks for faster loading)
- Asset optimization (compress images, inline small files)

#### Option 1: Serve with Nginx

**Install Nginx:**
```bash
sudo apt update
sudo apt install nginx
```

**Create Nginx configuration:**
```nginx
# /etc/nginx/sites-available/veritasloop
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend static files
    root /var/www/veritasloop/frontend/dist;
    index index.html;

    # SPA routing (all routes serve index.html)
    location / {
        try_files $uri $uri/ /index.html;
    }

    # WebSocket proxy (for /ws/ endpoint)
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # API proxy (if you add REST endpoints)
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/veritasloop /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl reload nginx
```

**Copy built files:**
```bash
sudo mkdir -p /var/www/veritasloop/frontend
sudo cp -r frontend/dist/* /var/www/veritasloop/frontend/
```

#### Option 2: Deploy to Vercel

**Install Vercel CLI:**
```bash
npm install -g vercel
```

**Deploy:**
```bash
cd frontend
vercel --prod
```

**Configure environment variable:**
Create `frontend/.env.production`:
```bash
VITE_API_URL=wss://api.yourdomain.com/ws/verify
```

Update `frontend/src/App.jsx`:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'ws://localhost:8000/ws/verify';
```

**Vercel Configuration** (`vercel.json`):
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

#### Option 3: Deploy to Netlify

**Install Netlify CLI:**
```bash
npm install -g netlify-cli
```

**Deploy:**
```bash
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

**Netlify Configuration** (`netlify.toml`):
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

### Full Stack Deployment

#### Docker Compose Setup

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: veritasloop-backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - BRAVE_SEARCH_API_KEY=${BRAVE_SEARCH_API_KEY}
      - NEWS_API_KEY=${NEWS_API_KEY}
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: nginx:alpine
    container_name: veritasloop-frontend
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

  # Optional: Redis for distributed caching
  redis:
    image: redis:7-alpine
    container_name: veritasloop-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always

volumes:
  redis_data:
```

**Start all services:**
```bash
docker-compose up -d
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop services:**
```bash
docker-compose down
```

## SSL/TLS Configuration

### Using Let's Encrypt (Certbot)

**Install Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

**Obtain certificate:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Auto-renewal:**
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

**Updated Nginx config (with HTTPS):**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration from above
    # Change ws:// to wss:// in VITE_API_URL
}
```

## Environment Variables for Production

**Backend `.env`:**
```bash
# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Search & News
BRAVE_SEARCH_API_KEY=...
NEWS_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Production settings
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: Redis
REDIS_URL=redis://localhost:6379
```

**Frontend `.env.production`:**
```bash
VITE_API_URL=wss://yourdomain.com/ws/verify
```

## Performance Optimization

### Backend

**1. Use Multiple Workers**
```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker
```

**2. Enable Response Compression**
- Nginx gzip (shown above)
- FastAPI middleware: `gzip_middleware`

**3. Redis Caching**
Replace in-memory cache with Redis for distributed deployments.

**4. Connection Pooling**
Configure database connection pools if using persistent storage.

**5. Monitor Performance**
- Enable Phoenix tracing in production (with authentication)
- Use application monitoring (New Relic, DataDog, etc.)

### Frontend

**1. CDN for Static Assets**
- Use Vercel Edge Network
- Or configure CloudFlare CDN

**2. Enable Compression**
- Nginx gzip (shown above)
- Brotli compression for better compression ratios

**3. Caching Headers**
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

**4. Service Worker (PWA)**
Add service worker for offline support and faster load times.

## Security Considerations

### 1. HTTPS/WSS Only
- **Never** use HTTP/WS in production
- Redirect all HTTP to HTTPS
- Use WSS (`wss://`) for WebSocket connections

### 2. CORS Configuration
```python
# api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Not "*" !!!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. API Key Security
- Store in environment variables
- Never commit to Git
- Rotate keys regularly
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)

### 4. Rate Limiting
```python
# Install: pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.websocket("/ws/verify")
@limiter.limit("5/minute")  # 5 verifications per minute per IP
async def websocket_endpoint(websocket: WebSocket):
    ...
```

### 5. Input Validation
- Already implemented via Pydantic
- Add additional sanitization for URLs
- Implement content security policy (CSP)

### 6. Security Headers
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

### 7. Regular Updates
```bash
# Backend
pip list --outdated
pip install -U <package>

# Frontend
npm audit
npm update
```

## Monitoring & Logging

### Application Logs

**Backend logging:**
```python
# src/utils/logger.py already implements structured logging
# Configure log level in .env:
LOG_LEVEL=INFO  # or WARNING for production
```

**Log rotation:**
```bash
# /etc/logrotate.d/veritasloop
/var/log/veritasloop/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 veritasloop veritasloop
    sharedscripts
    postrotate
        systemctl reload veritasloop-api
    endscript
}
```

### Health Checks

**Add health endpoint:**
```python
# api/main.py
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}
```

**Monitor with:**
- UptimeRobot (external monitoring)
- Prometheus + Grafana (metrics dashboard)
- AWS CloudWatch (if on AWS)

### Phoenix Tracing in Production

**Secure Phoenix:**
```bash
# Add authentication proxy (Nginx basic auth)
location /phoenix/ {
    auth_basic "Phoenix Tracing";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:6006/;
}
```

## Backup Strategy

### Data to Backup

1. **Environment variables**: `.env` file
2. **Phoenix traces**: `data/phoenix/traces.db`
3. **Cache data** (optional): Can be regenerated
4. **Logs**: `/var/log/veritasloop/`

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/veritasloop"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup database
cp /opt/veritasloop/data/phoenix/traces.db "$BACKUP_DIR/$DATE/"

# Backup .env (encrypted!)
gpg --encrypt --recipient your@email.com /opt/veritasloop/.env > "$BACKUP_DIR/$DATE/.env.gpg"

# Backup logs
tar -czf "$BACKUP_DIR/$DATE/logs.tar.gz" /var/log/veritasloop/

# Remove backups older than 30 days
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} +
```

## Scaling Strategies

### Horizontal Scaling

**Multiple backend instances:**
```yaml
# docker-compose.yml
services:
  backend1:
    build: .
    ports:
      - "8001:8000"
    ...

  backend2:
    build: .
    ports:
      - "8002:8000"
    ...

  nginx:
    # Load balancer configuration
```

**Nginx load balancing:**
```nginx
upstream veritasloop_backend {
    least_conn;  # or ip_hash for sticky sessions
    server backend1:8000;
    server backend2:8000;
}

location /ws/ {
    proxy_pass http://veritasloop_backend;
    ...
}
```

### Vertical Scaling

- Increase worker count
- Allocate more CPU/RAM to containers
- Use faster Redis instance
- Optimize database queries

## Troubleshooting

### Backend Issues

**Service won't start:**
```bash
sudo systemctl status veritasloop-api
sudo journalctl -u veritasloop-api -n 50
```

**High memory usage:**
- Reduce number of workers
- Check for memory leaks in Phoenix
- Monitor with `htop` or `docker stats`

### Frontend Issues

**404 errors on routes:**
- Ensure Nginx `try_files $uri $uri/ /index.html`
- Check SPA routing configuration

**WebSocket connection fails:**
- Verify WebSocket proxy in Nginx
- Check CORS settings
- Ensure WSS (not WS) in production

### Performance Issues

**Slow responses:**
- Check cache hit rate
- Monitor API latency (Phoenix traces)
- Verify external API response times

**High CPU usage:**
- Reduce concurrent verifications
- Optimize LLM calls
- Consider async processing queue

## Related Documentation

- [Installation Guide](INSTALLATION.md) - Setup instructions
- [Architecture Overview](ARCHITECTURE.md) - System design
- [Development Guide](DEVELOPMENT.md) - Contributing guidelines
