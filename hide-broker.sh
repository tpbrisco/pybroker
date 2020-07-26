set -e

# set broker URL - default to cfdev environment
URL=${BROKER_URL:-"http://broker.dev.cfdev.sh"}
echo "Using broker URL ${URL}"

cf disable-service-access dream
cf delete-service-broker dream -f
