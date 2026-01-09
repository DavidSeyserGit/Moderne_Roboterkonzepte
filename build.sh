#!/bin/bash
# Fast Docker build script with BuildKit caching enabled

# Enable Docker BuildKit for faster builds with cache mounts
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

echo "Building with Docker BuildKit enabled (faster builds with cache)..."
docker-compose build "$@"
