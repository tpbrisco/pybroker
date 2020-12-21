#!/bin/bash
set -eou pipefail

# CURL_FLAGS -- e.g. put "-k" in your environment if your certificates aren't right
CURL_FLAGS=${CURL_FLAGS:-''}

# set broker URL - default to cfdev environment
URL=${BROKER_URL:-"http://broker.dev.cfdev.sh"}
if [[ ${URL} =~ ^http.* ]];
then
    echo "Using broker URL ${URL}"
else
    echo BROKER_URL needs to indicate http or https
    echo ${URL} does not
    exit 1
fi

# fetch the catalog that the market place would bind to
echo Discovering service and plans
curl ${CURL_FLAGS} -sS -u user:pass -H "X-Broker-API-Version: 2.10" \
     ${URL}/v2/catalog | \
    jq '.services[] | {service_id: .id, plan_id: .plans[].id}'

# get a plan id for provisioning it
PLAN_ID=$(curl ${CURL_FLAGS} -sS -u user:pass -H "X-Broker-API-Version: 2.10" \
	       ${URL}/v2/catalog | \
	      jq '.services[0].plans[0].id')
SVC_ID=$(curl ${CURL_FLAGS} -sS -u user:pass -H "X-Broker-API-Version: 2.10" \
	      ${URL}/v2/catalog | \
	     jq '.services[0].id')

# note, SVC_ID and PLAN_ID are already wrapped in double-quotes
echo Create service instance
echo "{\"service_id\": ${SVC_ID}, \"plan_id\": ${PLAN_ID}}" > /tmp/broker_data
INSTANCE_ID=$(uuidgen)
curl ${CURL_FLAGS} -sS -u user:pass -X PUT \
     -H 'X-Broker-API-Version: 2.12' \
     -H "Content-Type: application/json" \
     -d @/tmp/broker_data \
     -o /dev/null \
     ${URL}/v2/service_instances/${INSTANCE_ID}
rm -f /tmp/broker_data

# verify that it is there
FETCH_ID=$(curl ${CURL_FLAGS} -sS -u user:pass -X GET -H 'X-Broker-API-Version: 2.12' \
		${URL}/console | \
	       jq ".instances[\"${INSTANCE_ID}\"].id")
if [[ $FETCH_ID != \"$INSTANCE_ID\" ]];
then
    echo Created instance id wasnt found
    exit 1
else
    echo Found created ID $INSTANCE_ID
fi

# bind to a app (the broker itself)
BIND_ID=$(uuidgen)
echo "{\"service_id\": ${SVC_ID}, \"plan_id\": ${PLAN_ID}}" > /tmp/bind_data
curl ${CURL_FLAGS} -sS -u user:pass -X PUT \
     -H 'X-Broker-API-Version: 2.12' \
     -H "Content-Type: application/json" \
     -d @/tmp/bind_data \
     -o /dev/null \
     ${URL}/v2/service_instances/${INSTANCE_ID}/service_bindings/${BIND_ID}
rm -f /tmp/bind_data
echo "Bound (${BIND_ID}) to instance ${INSTANCE_ID}"

# delete the created ID
curl ${CURL_FLAGS} -sS -u user:pass -X DELETE \
     -H 'X-Broker-API-Version: 2.12' \
     -o /dev/null \
     ${URL}/v2/service_instances/${INSTANCE_ID}/service_bindings/${BIND_ID}
echo Deleted service instance $INSTANCE_ID

##
##
# clean up all instances
#
echo Cleaning up all bindings
for guid in $(curl ${CURL_FLAGS} -sS -X GET ${URL}/console | jq '.instances[].id');
do
    echo "  $guid"
    foo=$(echo $guid | sed -e's/\"//g');
    curl ${CURL_FLAGS} -sS -u user:pass -X DELETE \
	 -o /dev/null \
	 ${URL}/v2/service_instances/$foo;
done
