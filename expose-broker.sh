set -e

if [[ -z "BROKER_URL" ]]; then
    echo "BROKER_URL should be set to the ... url"
    exit 1
fi

echo "Using broker URL ${BROKER_URL}"

# use "--space-scoped" if not admin
cf create-service-broker dream user pass ${BROKER_URL}
cf enable-service-access dream
