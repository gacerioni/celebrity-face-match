#!/bin/bash
# Deploy Celebrity Face Match to EC2
# Usage: ./deploy-to-ec2.sh <ec2-ip> [use-nginx]

set -e

EC2_IP="${1:-34.238.135.24}"
USE_NGINX="${2:-no}"

if [ -z "$EC2_IP" ]; then
    echo "❌ Error: EC2 IP address required"
    echo "Usage: ./deploy-to-ec2.sh <ec2-ip> [use-nginx]"
    exit 1
fi

echo "🚀 Deploying Celebrity Face Match to EC2"
echo "========================================="
echo "EC2 IP: $EC2_IP"
echo "Use Nginx: $USE_NGINX"
echo ""

# Determine WebSocket URL based on nginx usage
if [ "$USE_NGINX" = "yes" ]; then
    WS_URL="ws://${EC2_IP}/api/ws"
    API_URL="http://${EC2_IP}/api"
    echo "📡 Using Nginx reverse proxy"
else
    WS_URL="ws://${EC2_IP}:8080/ws"
    API_URL="http://${EC2_IP}:8080"
    echo "📡 Direct connection to containers"
fi

echo "WebSocket URL: $WS_URL"
echo "API URL: $API_URL"
echo ""

# Step 1: Build and push backend
echo "🔨 Step 1: Building backend..."
./build-backend.sh

# Step 2: Build and push frontend with production URLs
echo "🔨 Step 2: Building frontend with production URLs..."
./build-frontend.sh latest "$WS_URL" "$API_URL"

echo ""
echo "✅ Images built and pushed to Docker Hub"
echo ""
echo "📋 Next steps on EC2:"
echo "===================="
echo ""
echo "1. SSH into your EC2 instance:"
echo "   ssh ubuntu@${EC2_IP}"
echo ""
echo "2. Pull the latest images:"
echo "   docker pull gacerioni/celebrity-face-match-backend:latest"
echo "   docker pull gacerioni/celebrity-face-match-frontend:latest"
echo ""
echo "3. Restart the containers:"
echo "   cd ~/celebrity"
echo "   docker compose -f docker-compose.prod.yml down"
echo "   docker compose -f docker-compose.prod.yml up -d"
echo ""

if [ "$USE_NGINX" = "yes" ]; then
    echo "4. Configure Nginx (if not already done):"
    echo "   sudo cp nginx-simple-http.conf /etc/nginx/sites-available/celebrity-face-match"
    echo "   sudo ln -sf /etc/nginx/sites-available/celebrity-face-match /etc/nginx/sites-enabled/"
    echo "   sudo nginx -t"
    echo "   sudo systemctl reload nginx"
    echo ""
    echo "5. Access the app at: http://${EC2_IP}/"
else
    echo "4. Access the app at: http://${EC2_IP}:3080/"
fi

echo ""
echo "🔍 Verify deployment:"
echo "   docker ps"
echo "   docker logs celeb-backend-prod"
echo "   docker logs celeb-frontend-prod"
echo "   curl http://${EC2_IP}:8080/"
echo ""

