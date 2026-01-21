#!/bin/bash
# =============================================================================
# Server Setup Script - Execute this ON THE SERVER
# =============================================================================

set -e

echo "🚀 AI Call Agent - Server Setup"
echo "================================"

# Update system
echo "📦 Step 1/8: Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo "📦 Step 2/8: Installing dependencies..."
apt-get install -y \
    curl \
    git \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    software-properties-common

# Install Docker
echo "🐳 Step 3/8: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🐙 Step 4/8: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Clone repository
echo "📁 Step 5/8: Cloning repository..."
PROJECT_DIR="/opt/telephony"
if [ -d "$PROJECT_DIR" ]; then
    echo "Directory exists, removing old version..."
    rm -rf "$PROJECT_DIR"
fi

git clone https://github.com/MikeMikel97/tel.git "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Configure environment
echo "⚙️  Step 6/8: Configuring environment..."
cp backend/.env.example backend/.env

# Generate secure secrets
JWT_SECRET=$(openssl rand -hex 32)
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" backend/.env

# Configure firewall
echo "🔥 Step 7/8: Configuring firewall..."
ufw --force enable
ufw allow 22/tcp           # SSH
ufw allow 80/tcp           # HTTP
ufw allow 443/tcp          # HTTPS
ufw allow 3003/tcp         # Frontend
ufw allow 8000/tcp         # Backend API
ufw allow 5060/udp         # SIP UDP
ufw allow 5060/tcp         # SIP TCP
ufw allow 8088/tcp         # WebRTC WebSocket
ufw allow 10000:10100/udp  # RTP media
ufw reload

echo "✅ Firewall configured"

# Start services
echo "🚀 Step 8/8: Starting services..."
cd "$PROJECT_DIR"
docker-compose down || true
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "📊 Service status:"
docker-compose ps

echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo "=========================================="
echo ""
echo "📱 Access URLs:"
echo "   Operator UI:  http://46.254.18.120:3003"
echo "   Admin Panel:  http://46.254.18.120:8000/admin"
echo "   API Docs:     http://46.254.18.120:8000/docs"
echo ""
echo "🔑 Default credentials:"
echo "   Admin:    admin / D7eva123qwerty"
echo "   Operator: operator / operator123"
echo ""
echo "📝 Next steps:"
echo "   1. Test operator login at :3003"
echo "   2. Configure SIP trunk in admin panel"
echo "   3. Set up domain name and SSL (optional)"
echo ""
