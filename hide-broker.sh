set -e
cf disable-service-access dream
cf delete-service-broker dream -f
