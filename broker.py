#
# a fairly trivial (but fully implemented - I think) service broker
# for cloud foundry.
#
import os
import sys
from flask import Flask, json, request, \
    make_response, abort, url_for, send_file
from functools import wraps
import logging
import uuid

X_BROKER_API_MAJOR_VERSION = 2
X_BROKER_API_MINOR_VERSION = 10
X_BROKER_API_VERSION_NAME = 'X-Broker-Api-Version'

content_headers = {'Content-Type': 'text/json'}

# broker requirements are outlined at
# https://github.com/openservicebrokerapi/servicebroker/blob/v2.12/spec.md#provisioning
big_dreams = {
    "id": str(uuid.uuid4()),  # note that ID change each time you start
    "name": "big_dreams",
    "description": "A Big Dream",
    "free": False,
    "plan_updateable": True,
    "metadata": {
        "bullets": [
            "Dreams are cheap",
            "Even big dreams",
        ],
    }
}
small_dreams = {
    "id": str(uuid.uuid4()),  # note that ID change each time you start
    "name": "small_dreams",
    "description": "A Small Dream",
    "plan_updateable": True,
    "metadata": {
        "bullets": [
            "Small dreams barely worth having"
        ]
    },
    "free": True
}
dream_service = {
    "id": str(uuid.uuid4()),  # note that ID change each time you start
    "name": "dream",
    "description": "Imaginary Service",
    "bindable": True,
    "dashboard_client": {
        "id": "user",
        "secret": "pass",
        "redirect_uri": ""
    },
    "metadata": {
        "listing": {
            "imageUrl": "",     # while this is documented as here - see below
            "blurb": "dreams are cheap",
            "longDescription": "Dream services ranging from free to cheap"
        },
        "bullets": [
            "Dreams of all sizes"
        ],
        "imageUrl": "",  # this is where the imageUrl actually works(see above)
        "displayName": "Broker of dreams"
    },
    "bindable": True,
    "plans": [big_dreams, small_dreams]
}
services = {"services": [dream_service]}

app = Flask(__name__)

app.config['logger'] = logging.getLogger('dream_broker')
app.config['logger'].setLevel(logging.INFO)
app.config['logger'].addHandler(logging.StreamHandler())

#
# define error handler for checking API version number
#


# verify version number
def api_version_is_valid(api_version):
    version_data = api_version.split('.')
    result = True
    if (float(version_data[0]) < X_BROKER_API_MAJOR_VERSION or
        (float(version_data[0]) == X_BROKER_API_MAJOR_VERSION and
         float(version_data[1]) < X_BROKER_API_MINOR_VERSION)):
        result = False
    return result


# wrap endpoints with version checking
def requires_api_version(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_version = request.headers.get(X_BROKER_API_VERSION_NAME)
        if (not api_version or not api_version_is_valid(api_version)):
            abort(412)
        return f(*args, **kwargs)
    return decorated


# generate error if version mismatch
@app.errorhandler(412)
def version_mismatch(error):
    return 'Version mismatch. Expected: {}: {}.{}'.format(
        X_BROKER_API_VERSION_NAME, X_BROKER_API_MAJOR_VERSION,
        X_BROKER_API_MINOR_VERSION), 412  # precondition failed


#
# enforce authentication from the marketplace
#
def check_auth(username, password):
    if not (username == 'user' and password == 'pass'):
        app.config['logger'].warning('Authentication failed')
    return username == 'user' and password == 'pass'


def authenticate():
    return make_response(
        json.dumps({'WWW-Authenticate': 'Basic realm="Login Requred"'},
                   indent=2),
        401)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

#
# utility data structures
#


# template for allocating new services
service_template = {
    'id': '',
    'space_guid': '',
    'plan_id': '',
    'bindings': {}
}
# this is our database
instances = {
}


#
# utility functions
#


def find_instance(id):
    app.config['logger'].debug("find_instance: {}".format(id))
    if id in instances.keys():
        return instances[id]
    return None


def delete_instance(id):
    app.config['logger'].debug("service instances: {}".format(json.dumps(instances, indent=2)))
    if id in instances.keys():
        del instances[id]
    return {}


#
# define broker endpoints
#


# list catalog
@app.route('/v2/catalog')
@requires_api_version
@requires_auth
def catalog():
    app.config['logger'].info("catalog called")
    dream_service['dashboard_client']['redirect_uri'] = \
        request.url_root + url_for('service_console')[1:]
    dream_service['metadata']['imageUrl'] = \
        request.url_root + url_for('service_image')[1:]
    return make_response(json.dumps(services, indent=2), 200, content_headers)


# create/delete/update service instance
@app.route('/v2/service_instances/<instance_id>',
           methods=['PUT', 'DELETE', 'PATCH'])
def service_instances(instance_id):
    app.config['logger'].info("service_instances called")
    app.config['logger'].debug("instance: %s" % (instance_id))

    # validated request is for this broker
    app.config['logger'].debug("HTTP method {}".format(request.method))
    if request.method == 'PUT' or request.method == 'PATCH':
        app.config['logger'].info("Add/Update instance %s" % (instance_id))
        config = request.get_json()
        app.config['logger'].debug("config: %s" % (json.dumps(config, indent=2)))
        # check parameters are right for PUT/PATCH
        if config and not (
                (config['service_id'] == dream_service['id']) and
                ((config['plan_id'] == big_dreams['id']) or
                 (config['plan_id'] == small_dreams['id']))):
            app.config['logger'].debug("service mismatch")
            err_str = 'service (%s) or plan (%s) not me' % \
                (config['service_id'], config['plan_id'])
            err = {'description': err_str}
            return make_response(json.dumps(err, indent=2), 404, content_headers)

        if request.method == 'PUT':
            svc = service_template.copy()
            svc['id'] = instance_id
            if config:
                for k in config.keys():
                    svc[k] = config[k]
            instances[instance_id] = svc
        else:  # PATCH
            svc = find_instance(instance_id)
            if config:
                for k in config.keys():
                    svc[k] = config[k]
        if request.method == 'PUT':
            return make_response(json.dumps(svc), 201, content_headers)
        else:
            return make_response(json.dumps(svc), 200, content_headers)
    elif request.method == 'DELETE':
        delete_instance(instance_id)
        return make_response(json.dumps({}), 200, content_headers)
    elif request.method == 'GET':
        x = find_instance(instance_id)
        return make_response(json.dumps(x), 200, content_headers)
    else:
        app.config['logger'].warning("unknown HTTP method {}".format(request.method))
        return make_response(
            json.dumps({'description': 'unknown HTTP method'}),
            404,
            content_headers)


# bind/unbind service instance
@app.route('/v2/service_instances/<instance_id>/service_bindings/<binding_id>',
           methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def service_bindings(instance_id, binding_id):
    app.config['logger'].info("service_bindings called, method={}".format(request.method))
    app.config['logger'].debug("instance %s binding %s" %
                               (instance_id, binding_id))
    x = find_instance(instance_id)
    app.config['logger'].debug("found instance %s" % (json.dumps(x, indent=2)))
    if x is None:
        rcode = {'description': 'service instance %s not found' %
                 (instance_id)}
        return make_response(json.dumps(rcode), 410, content_headers)
    if request.method == 'GET':
        if binding_id in x['bindings'].keys():
            return make_response(json.dumps(x.bindings[binding_id], indent=2),
                                 200, content_headers)
        else:
            rcode = {'description': 'service binding %s not found' %
                     (binding_id)}
            return make_response(json.dumps(rcode), 404, content_headers)
    if request.method == 'PUT' or request.method == 'PATCH':
        config = request.get_json()
        x['bindings'][binding_id] = config
        if request.method == 'PUT':
            # when creating a new service, generate credentials to use it
            creds = {'username': 'user', 'password': 'pass'}
            x['bindings'][binding_id]['credentials'] = creds
            r_ok = 201
        else:
            r_ok = 200
        response = {'credentials': {'username': 'user', 'password': 'pass'}}
        return make_response(json.dumps(response), r_ok, content_headers)
    if request.method == 'DELETE':
        del x['bindings'][binding_id]
        return make_response(json.dumps(x), 200, content_headers)

    # just return an error as default
    rcode = {'description': 'HTTP method %s not known' % (request.method)}
    return make_response(json.dumps(rcode), 404, content_headers)


#
# meta-routes -- not part of the broker, but needed for the marketplace
# You should be able to manage the service here, but we just dump out
# the JSON data structure (as there's not really much to "manage")
@app.route('/console', methods=['GET'])
def service_console():
    app.config['logger'].info("service_console called\n")
    resp_dict = {'dream_service': dream_service,
                 'instances': instances}
    return make_response(json.dumps(resp_dict, indent=2),
                         200, content_headers)


# For some reason, we need "/image" and "/image/" -- cloud foundry
# appends a "/" onto the request, which doesn't match the "/image" route.
# The order is important, as url_for resolves to the second listed.
@app.route('/image/', methods=['GET'])
@app.route('/image', methods=['GET'])
def service_image():
    app.config['logger'].info("service_image called\n")
    return send_file('assets/batman.png',
                     attachment_filename="logo.png",
                     mimetype='image/png')


#
if __name__ == "__main__":
    port = int(os.getenv("VCAP_APP_PORT", "8000"))
    debug = os.isatty(sys.stdout.fileno())
    app.run(host='0.0.0.0', port=port, debug=debug)
