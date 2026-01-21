#!/bin/bash
echo "🚀 Deploying to server 46.254.18.120"
echo ""
echo "📤 Uploading setup script..."
scp -o StrictHostKeyChecking=no server-setup.sh root@46.254.18.120:/root/

echo ""
echo "🔧 Executing setup on server..."
ssh -o StrictHostKeyChecking=no root@46.254.18.120 'bash /root/server-setup.sh'

echo ""
echo "✅ Deployment complete!"
