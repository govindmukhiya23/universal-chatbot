# Deployment Guide

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit .env file with your settings**

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   Open your browser and go to `http://localhost:5000`

## Docker Deployment

### Build Docker Image

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

### Docker Compose Setup

```yaml
version: '3.8'

services:
  chatbot:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - LIBRETRANSLATE_URL=http://libretranslate:5000
    depends_on:
      - libretranslate
    volumes:
      - ./logs:/app/logs

  libretranslate:
    image: libretranslate/libretranslate
    ports:
      - "5001:5000"
    environment:
      - LT_LOAD_ONLY=en,es,fr,de,it,pt,ru,ja,ko,zh,ar,hi
    volumes:
      - lt_data:/app/db

volumes:
  lt_data:
```

## Production Deployment

### 1. Using Gunicorn + Nginx

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Run with Gunicorn:**
```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Using Systemd Service

**Create service file:** `/etc/systemd/system/universal-chatbot.service`
```ini
[Unit]
Description=Universal Language Support Chatbot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
sudo systemctl enable universal-chatbot
sudo systemctl start universal-chatbot
```

### 3. Cloud Deployment

#### Heroku
1. Create `Procfile`:
   ```
   web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
   ```

2. Add buildpacks:
   ```bash
   heroku buildpacks:add heroku/python
   heroku buildpacks:add https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
   ```

#### AWS EC2
1. Launch Ubuntu instance
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-pip nginx ffmpeg portaudio19-dev
   ```
3. Clone repository and setup
4. Configure Nginx as reverse proxy
5. Use systemd service for process management

#### Google Cloud Run
1. Build Docker image:
   ```bash
   docker build -t gcr.io/your-project/universal-chatbot .
   ```

2. Push to registry:
   ```bash
   docker push gcr.io/your-project/universal-chatbot
   ```

3. Deploy:
   ```bash
   gcloud run deploy --image gcr.io/your-project/universal-chatbot --platform managed
   ```

## Environment Variables for Production

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-super-secret-production-key

# LibreTranslate Configuration
LIBRETRANSLATE_URL=http://your-libretranslate-instance:5000
LIBRETRANSLATE_API_KEY=your-production-api-key

# Whisper Configuration
WHISPER_MODEL=base  # Use 'base' for production for faster processing
WHISPER_DEVICE=cpu  # Use 'cuda' if GPU available

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/chatbot.log

# Performance
GUNICORN_WORKERS=1  # Keep at 1 for WebSocket support
GUNICORN_TIMEOUT=120
```

## Performance Optimization

1. **Use CDN for static files**
2. **Enable gzip compression in Nginx**
3. **Use Redis for session storage**
4. **Implement rate limiting**
5. **Monitor with tools like New Relic or DataDog**
6. **Use load balancer for high traffic**

## Security Considerations

1. **Use HTTPS in production**
2. **Implement CORS properly**
3. **Add rate limiting**
4. **Validate all user inputs**
5. **Keep dependencies updated**
6. **Use environment variables for secrets**
7. **Implement proper logging and monitoring**

## Monitoring and Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/chatbot.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```
