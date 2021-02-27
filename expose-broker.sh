set -e
# set broker URL if defined
URL=${BROKER_URL:-"http://broker.dev.cfdev.sh"}
echo "Using broker URL ${URL}"

# use "--space-scoped" if not admin
cf create-service-broker dream user pass ${URL}
cf enable-service-access dream
