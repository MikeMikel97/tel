#!/bin/bash
set -e

# Deploy script for fresh server with HTTPS
# Usage: ./deploy-fresh-server.sh calls4ai.ru admin@calls4ai.ru

DOMAIN=${1:-calls4ai.ru}
EMAIL=${2:-admin@calls4ai.ru}

echo "🚀 Deploying to fresh server..."
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"

# 1. Update system
echo "📦 Updating system..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 3. Install Docker Compose
echo "📦 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 4. Clone repository
echo "📥 Cloning repository..."
cd /opt
if [ -d "telephony" ]; then
    cd telephony
    git pull
else
    git clone https://github.com/MikeMikel97/tel.git telephony
    cd telephony
fi

# 5. Setup environment
echo "⚙️ Setting up environment..."
if [ ! -f backend/.env ]; then
    cp backend/env.example backend/.env 2>/dev/null || touch backend/.env
    
    # Generate JWT secret
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Create .env file
    cat > backend/.env << EOF
DATABASE_URL=postgresql+psycopg2://telephony_user:telephony_password_2024@postgres:5432/telephony
JWT_SECRET_KEY=$JWT_SECRET
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
OPENROUTER_API_KEY=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
SONIOX_API_KEY=f0eef8f6b132f7fdf39b90260b6a6d869ff85a151cee0cfe01204b8467bee130

ASTERISK_HOST=asterisk
ASTERISK_ARI_PORT=8088
ASTERISK_ARI_USER=ai-agent
ASTERISK_ARI_PASSWORD=aiagent_secret_password_2024
ASTERISK_CONFIG_PATH=/etc/asterisk
RECORDINGS_PATH=/var/spool/asterisk/recording

API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
EOF
fi

# 6. Create directories for SSL
echo "🔐 Creating SSL directories..."
mkdir -p certbot/conf certbot/www

# 7. Start services without SSL first (for Certbot challenge)
echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d postgres asterisk backend frontend

echo "⏳ Waiting for services to be ready..."
sleep 30

# 8. Run migrations and create test data
echo "📊 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

echo "👥 Creating test data..."
docker-compose -f docker-compose.prod.yml exec -T backend python create_test_data.py || true

# 9. Create temporary nginx for SSL challenge
echo "🔧 Creating temporary nginx for SSL..."
cat > nginx-temp.conf << 'NGINX'
server {
    listen 80;
    server_name _;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'Server is ready for SSL setup';
        add_header Content-Type text/plain;
    }
}
NGINX

docker run -d --name temp-nginx \
    -p 80:80 \
    -v $(pwd)/nginx-temp.conf:/etc/nginx/conf.d/default.conf:ro \
    -v $(pwd)/certbot/www:/var/www/certbot:ro \
    nginx:alpine

# 10. Obtain SSL certificate
echo "🔐 Obtaining SSL certificate for $DOMAIN..."
docker run --rm \
    -v $(pwd)/certbot/conf:/etc/letsencrypt \
    -v $(pwd)/certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# 11. Stop temporary nginx
echo "🛑 Stopping temporary nginx..."
docker stop temp-nginx
docker rm temp-nginx
rm nginx-temp.conf

# 12. Start full stack with SSL
echo "🚀 Starting full stack with SSL..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your services are now available:"
echo "   - Frontend: https://$DOMAIN"
echo "   - Admin Panel: https://$DOMAIN/admin"
echo "     Login: admin"
echo "     Password: D7eva123qwerty"
echo "   - API Docs: https://$DOMAIN/docs"
echo ""
echo "📝 Operator UI test credentials:"
echo "   Login: testuser"
echo "   Password: Test123!"
echo ""
echo "🔄 SSL certificate will auto-renew every 12 hours"
echo ""
