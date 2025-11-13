set -euxo pipefail

echo "### Starting MQTT broker"
docker-compose -f ./broker/docker-compose.yml up