#!/bin/bash

# ABSA Monitoring Setup Script

echo "🚀 Setting up ABSA Monitoring Dashboard..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Creating .env from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from template"
        echo "🔧 Please edit .env with your actual values before continuing"
        exit 1
    else
        echo "❌ No .env.example template found"
        exit 1
    fi
fi

# Test environment variables
echo "🔍 Testing environment variables..."
./test-env.sh

# Start the services
echo "📦 Starting Docker services..."
docker-compose up -d postgres grafana data-loader

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 30

echo "✅ Setup complete!"
echo ""
echo "🎯 Access points:"
echo "   Grafana Dashboard: http://localhost:3000"
echo "   Username: admin"
echo "   Password: admin"
echo ""
echo "   PostgreSQL: localhost:5432"
echo "   Database: absa_db"
echo "   Username: absa_user"
echo "   Password: absa_password"
echo ""
echo "📊 Your ABSA monitoring dashboard should be available at:"
echo "   http://localhost:3000/d/absa-monitoring"
echo ""
echo "🔄 Data is loaded every hour from S3 (synced with comment processor)."
echo "🏁 Setup complete! Happy monitoring!"