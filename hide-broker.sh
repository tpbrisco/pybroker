set -e

if [[ -z "BROKER_URL" ]]; then
    echo "BROKER_URL should be set to the ... url"
    exit 1
fi

# ignore errors -- forge through the decommissioning
set +e
cf disable-service-access dream
cf delete-service-broker dream -f
