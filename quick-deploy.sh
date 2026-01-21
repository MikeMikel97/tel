#!/bin/bash
# ONE-LINER DEPLOYMENT SCRIPT
# Execute this ON THE SERVER as root user

{
echo "🚀 Starting AI Call Agent deployment..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker && systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    COMPOSE_VER=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VER}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update && apt-get install -y git ufw

# Clone project
echo "📁 Cloning project..."
rm -rf /opt/telephony
git clone https://github.com/MikeMikel97/tel.git /opt/telephony
cd /opt/telephony

# Configure environment
echo "⚙️  Configuring..."
cp backend/.env.example backend/.env
JWT_SECRET=$(openssl rand -hex 32)
sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" backend/.env

# Update frontend configs
sed -i 's/localhost/46.254.18.120/g' frontend/app.js
sed -i 's/localhost/46.254.18.120/g' frontend/webrtc.js

# Configure firewall
echo "🔥 Setting up firewall..."
ufw --force enable
ufw allow 22,80,443,3003,8000,8088/tcp
ufw allow 5060/udp
ufw allow 5060/tcp
ufw allow 10000:10100/udp
ufw reload

# Start services
echo "🚀 Starting services..."
docker-compose up -d --build

echo "⏳ Waiting 30 seconds for services to start..."
sleep 30

docker-compose ps

echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "📱 Access:"
echo "   http://46.254.18.120:3003 - Operator UI"
echo "   http://46.254.18.120:8000/admin - Admin Panel"
echo ""
echo "🔑 Login: operator / operator123"
echo "🔑 Admin: admin / D7eva123qwerty"
echo ""

} 2>&1 | tee /root/deployment.log
