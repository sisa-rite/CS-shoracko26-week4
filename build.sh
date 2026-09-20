#!/usr/bin/env bash
# Sestaví obrazy backendu i frontendu a označí je verzí.
#   ./build.sh          -> verze 1.0.0
#   ./build.sh 1.2.0    -> verze 1.2.0
set -euo pipefail

cd "$(dirname "$0")"

# Načte DOCKERHUB_USERNAME z .env do proměnných shellu
set -a
source .env
set +a

VERSION="${1:-1.0.0}"
USER_NS="${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME neni nastaveno v .env}"

echo "==> Build ${USER_NS}/lemp-backend:${VERSION}"
docker build -f backend/Dockerfile -t "${USER_NS}/lemp-backend:${VERSION}" .

echo "==> Build ${USER_NS}/lemp-frontend:${VERSION}"
docker build -f frontend/Dockerfile -t "${USER_NS}/lemp-frontend:${VERSION}" .

echo
echo "Hotovo:"
docker images "${USER_NS}/lemp-*" --format '  {{.Repository}}:{{.Tag}}  {{.Size}}'
echo
echo "Push na Docker Hub:"
echo "  docker login"
echo "  docker push ${USER_NS}/lemp-backend:${VERSION}"
echo "  docker push ${USER_NS}/lemp-frontend:${VERSION}"
