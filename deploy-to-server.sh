#!/bin/bash
set -e

# =============================================================================
# AI Call Agent - Server Deployment Script
# =============================================================================

# Configuration
SERVER_IP="46.254.18.120"
SERVER_USER="${1:-root}"  # Default to root if not specified
SERVER_PASSWORD="${2}"
PROJECT_DIR="/opt/telephony"
DOMAIN="${3:-$SERVER_IP}"  # Use IP if domain not provided

echo "🚀 Starting deployment to $SERVER_IP"
echo "📁 Project will be installed to: $PROJECT_DIR"
echo "🌐 Domain/IP: $DOMAIN"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to execute command on server
ssh_exec() {
    if [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
    else
        ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$1"
    fi
}

# Function to copy file to server
scp_file() {
    if [ -n "$SERVER_PASSWORD" ]; then
        sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$1" "$SERVER_USER@$SERVER_IP:$2"
    else
        scp -o StrictHostKeyChecking=no "$1" "$SERVER_USER@$SERVER_IP:$2"
    fi
}

echo -e "${YELLOW}Step 1/8: Checking server access...${NC}"
if ssh_exec "echo 'Server access OK'"; then
    echo -e "${GREEN}✅ Server access confirmed${NC}"
else
    echo -e "${RED}❌ Cannot access server. Please check credentials.${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 2/8: Installing system dependencies...${NC}"
ssh_exec "apt-get update && apt-get install -y curl git apt-transport-https ca-certificates gnupg lsb-release ufw"

echo -e "${YELLOW}Step 3/8: Installing Docker...${NC}"
ssh_exec "
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
    echo '✅ Docker installed'
else
    echo '✅ Docker already installed'
fi
"

echo -e "${YELLOW}Step 4/8: Installing Docker Compose...${NC}"
ssh_exec "
if ! command -v docker-compose &> /dev/null; then
    curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo '✅ Docker Compose installed'
else
    echo '✅ Docker Compose already installed'
fi
"

echo -e "${YELLOW}Step 5/8: Cloning repository...${NC}"
ssh_exec "
if [ -d '$PROJECT_DIR' ]; then
    echo '📁 Project directory exists, updating...'
    cd $PROJECT_DIR && git pull
else
    echo '📁 Cloning repository...'
    git clone https://github.com/MikeMikel97/tel.git $PROJECT_DIR
fi
"

echo -e "${YELLOW}Step 6/8: Configuring environment...${NC}"
ssh_exec "
cd $PROJECT_DIR

# Update docker-compose.yml with server IP
sed -i 's/localhost/$DOMAIN/g' frontend/*.js || true

# Create .env if not exists
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    
    # Generate random passwords
    JWT_SECRET=\$(openssl rand -hex 32)
    
    # Update .env with server-specific settings
    sed -i \"s|DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://telephony_user:telephony_password_2024@postgres:5432/telephony|\" backend/.env
    sed -i \"s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=\$JWT_SECRET|\" backend/.env
    
    echo '✅ Environment configured'
fi
"

echo -e "${YELLOW}Step 7/8: Setting up firewall...${NC}"
ssh_exec "
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 5060/udp  # SIP
ufw allow 5060/tcp  # SIP
ufw allow 8088/tcp  # WebRTC/WS
ufw allow 10000:10100/udp  # RTP
ufw reload
echo '✅ Firewall configured'
"

echo -e "${YELLOW}Step 8/8: Starting services...${NC}"
ssh_exec "
cd $PROJECT_DIR
docker-compose down || true
docker-compose up -d --build
echo '✅ Services starting...'
sleep 10
docker-compose ps
"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📱 Access your application:"
echo "   🎯 Operator UI:  http://$DOMAIN:3003"
echo "   🔧 Admin Panel:  http://$DOMAIN:8000/admin"
echo "   📚 API Docs:     http://$DOMAIN:8000/docs"
echo ""
echo "🔑 Default credentials:"
echo "   Admin: admin / D7eva123qwerty"
echo "   Operator: operator / operator123"
echo ""
echo "📝 Next steps:"
echo "   1. Update frontend WebRTC config with server IP/domain"
echo "   2. Set up SSL certificate (Let's Encrypt)"
echo "   3. Configure reverse proxy (Nginx)"
echo "   4. Add SIP trunk in admin panel"
echo ""
echo "🔍 Check logs:"
echo "   ssh $SERVER_USER@$SERVER_IP 'cd $PROJECT_DIR && docker-compose logs -f'"
echo ""
