# LibreTranslate Setup Guide

## Option 1: Using Public Instance (libretranslate.de)
The application is configured to use the public LibreTranslate instance at `https://libretranslate.de` by default.

### Pros:
- No setup required
- Works immediately
- Free for moderate usage

### Cons:
- Rate limited
- May require API key for heavy usage
- Privacy concerns (data sent to external server)

## Option 2: Self-Hosted LibreTranslate (Recommended)

### Prerequisites
- Docker installed on your system
- At least 4GB RAM available

### Setup Steps

1. **Pull the LibreTranslate Docker image:**
   ```bash
   docker pull libretranslate/libretranslate
   ```

2. **Run LibreTranslate container:**
   ```bash
   docker run -d -p 5000:5000 libretranslate/libretranslate
   ```

3. **With API key protection (optional):**
   ```bash
   docker run -d -p 5000:5000 \
     -e LT_API_KEYS=true \
     -e LT_API_KEYS_DB_PATH=/app/api_keys.db \
     -e LT_API_KEYS_SECRET=your-secret-key \
     libretranslate/libretranslate
   ```

4. **Create API key (if using protection):**
   ```bash
   curl -X POST "http://localhost:5000/create_api_key" \
     -H "Content-Type: application/json" \
     -d '{"api_key": "your-admin-key"}'
   ```

5. **Update your .env file:**
   ```
   LIBRETRANSLATE_URL=http://localhost:5000
   LIBRETRANSLATE_API_KEY=your-api-key
   ```

### Alternative: Python Installation

1. **Install LibreTranslate via pip:**
   ```bash
   pip install libretranslate
   ```

2. **Download language models:**
   ```bash
   libretranslate --load-only en,es,fr,de,it,pt,ru,ja,ko,zh,ar,hi
   ```

3. **Run LibreTranslate:**
   ```bash
   libretranslate --host 0.0.0.0 --port 5000
   ```

## Testing Your Setup

1. **Test translation endpoint:**
   ```bash
   curl -X POST "http://localhost:5000/translate" \
     -H "Content-Type: application/json" \
     -d '{"q": "Hello world", "source": "en", "target": "es"}'
   ```

2. **Expected response:**
   ```json
   {"translatedText": "Hola mundo"}
   ```

## Performance Tips

- Use smaller language models for faster translation
- Increase Docker memory allocation for better performance
- Consider using GPU acceleration for large deployments
- Cache frequent translations in your application

## Troubleshooting

### LibreTranslate not starting:
- Check if port 5000 is already in use
- Ensure sufficient memory is available
- Check Docker logs: `docker logs <container-id>`

### Translation errors:
- Verify the LibreTranslate URL in your .env file
- Check if the service is accessible: `curl http://localhost:5000/languages`
- Ensure your API key is correct (if using authentication)

### Slow translations:
- Use a more powerful machine
- Reduce the number of supported languages
- Consider using the 'base' model instead of 'large'
