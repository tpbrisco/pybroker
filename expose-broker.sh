set -e

if [[ -z "BROKER_URL" ]]; then
    echo "BROKER_URL should be set to the ... url"
    exit 1
fi
# set broker URL if defined
URL=${BROKER_URL:-"http://broker.dev.cfdev.sh"}
echo "Using broker URL ${URL}"

# use "--space-scoped" if not admin
cf create-service-broker dream user pass ${URL}
cf enable-service-access dream
