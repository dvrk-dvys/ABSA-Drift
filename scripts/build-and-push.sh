#!/bin/bash

# Build and push all Lambda Docker images for x86_64 architecture
# Usage: ./scripts/build-and-push.sh [ECR_REGISTRY] [TAG]

set -e

ECR_REGISTRY=${1:-"585315266445.dkr.ecr.us-east-1.amazonaws.com"}
TAG=${2:-"latest"}
REPO_NAME="absa-drift-ml-stg"

echo "Building and pushing Docker images for x86_64 architecture..."
echo "ECR Registry: $ECR_REGISTRY"
echo "Tag: $TAG"

# Build and push each service
SERVICES="extract transform monitor alert"

for service in $SERVICES; do
    dockerfile="src/lambdas/${service}/Dockerfile"
    local_tag="absa-drift-${service}:${TAG}"
    ecr_tag="${ECR_REGISTRY}/${REPO_NAME}:${service}-${TAG}"
    
    echo "Building $service..."
    docker build -t "$local_tag" -f "$dockerfile" .
    
    echo "Tagging $service for ECR..."
    docker tag "$local_tag" "$ecr_tag"
    
    echo "Pushing $service to ECR..."
    docker push "$ecr_tag"
    
    echo "✅ $service pushed successfully"
    echo ""
done

echo "🎉 All images built and pushed successfully!"