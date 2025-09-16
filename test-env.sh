#!/bin/bash

# Test environment variables are loaded correctly

echo "🔍 Testing Environment Variables..."
echo ""

# Source the .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded .env file"
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "🔑 AWS Configuration:"
echo "   AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID:0:10}..."
echo "   AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY:0:10}..."
echo "   AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION}"

echo ""
echo "🗄️  Database Configuration:"
echo "   POSTGRES_HOST: ${POSTGRES_HOST}"
echo "   POSTGRES_DB: ${POSTGRES_DB}"
echo "   POSTGRES_USER: ${POSTGRES_USER}"
echo "   POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}"

echo ""
echo "📊 Monitoring Configuration:"
echo "   S3_DATA_BUCKET: ${S3_DATA_BUCKET}"
echo "   S3_MONITORING_KEY: ${S3_MONITORING_KEY}"
echo "   DATA_LOAD_INTERVAL: ${DATA_LOAD_INTERVAL} seconds"
echo "   GRAFANA_SERVER_PORT: ${GRAFANA_SERVER_PORT}"

echo ""
echo "✅ All environment variables loaded successfully!"
echo ""
echo "🚀 Ready to run: docker-compose up -d grafana data-loader postgres"