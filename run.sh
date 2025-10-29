set -euxo pipefail

echo "### Starting MQTT broker"
docker compose up -f ./broker/docker-compose.yml