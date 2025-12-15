#!/bin/bash
# Deployment script for News Simplifier on Proxmox LXC

set -e

echo "=== News Simplifier Deployment ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Variables
APP_DIR="/opt/news-simplifier"
CONTAINER_IP=$(hostname -I | awk '{print $1}')

echo "Container IP: $CONTAINER_IP"
echo "App directory: $APP_DIR"
echo ""

# Update system
echo ">>> Updating system..."
apt-get update && apt-get upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo ">>> Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo ">>> Installing Docker Compose..."
    apt-get install -y docker-compose-plugin
fi

# Create app directory
echo ">>> Setting up application..."
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or update repository (replace with your repo URL)
if [ -d ".git" ]; then
    echo ">>> Updating repository..."
    git pull
else
    echo ">>> Cloning repository..."
    # git clone https://github.com/yourusername/news-simplifier.git .
    echo "NOTE: Copy your application files to $APP_DIR"
fi

# Check if Firebase credentials exist
if [ ! -f backend/firebase-credentials.json ]; then
    echo ""
    echo "=== Firebase Credentials Required ==="
    echo "Create backend/firebase-credentials.json with your Firebase service account:"
    echo ""
    echo "1. Go to https://console.firebase.google.com"
    echo "2. Select your project > Project Settings > Service Accounts"
    echo "3. Click 'Generate new private key'"
    echo "4. Save the JSON file as: backend/firebase-credentials.json"
    echo ""
    echo "Or paste the JSON content using:"
    echo "  cat > backend/firebase-credentials.json << 'EOF'"
    echo "  {paste your JSON here}"
    echo "  EOF"
    echo ""
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file not found!"
    echo "Copy deploy/.env.production to .env and configure it:"
    echo "  cp deploy/.env.production .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

# Build and start containers
echo ">>> Building Docker containers..."
docker compose build

echo ">>> Starting containers..."
docker compose up -d

# Wait for services
echo ">>> Waiting for services to start..."
sleep 10

# Health check
echo ">>> Checking service health..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "  ✅ Backend is running"
else
    echo "  ❌ Backend not responding"
fi

if curl -s http://localhost:8501/ > /dev/null; then
    echo "  ✅ Frontend is running"
else
    echo "  ❌ Frontend not responding"
fi

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. On nginx-proxy, copy nginx config:"
echo "   - Copy deploy/nginx-news.boxwoodtech.shop.conf to /etc/nginx/sites-available/"
echo "   - Replace 10.0.0.XXX with: $CONTAINER_IP"
echo ""
echo "2. Enable the site:"
echo "   ln -s /etc/nginx/sites-available/news.boxwoodtech.shop /etc/nginx/sites-enabled/"
echo ""
echo "3. Add SSL certificate:"
echo "   certbot certonly -d news.boxwoodtech.shop"
echo ""
echo "4. Test nginx config and reload:"
echo "   nginx -t && systemctl reload nginx"
echo ""
