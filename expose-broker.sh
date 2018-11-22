set -e
cf create-service-broker dream user pass http://broker.local.pcfdev.io
cf enable-service-access dream
