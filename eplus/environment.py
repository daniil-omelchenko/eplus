# -*- encoding: UTF-8 -*-

import os
import sys

GAE_SDK_ROOT = os.environ.get('GAE_SDK_ROOT', '/opt/google_appengine')
APP_YAML_LOCAL_FILE = os.path.isfile('app-local.yaml') and 'app-local.yaml' or 'app.yaml'
APP_YAML_FILE = 'app.yaml'


# noinspection PyProtectedMember
def init(sdk_root=None):
    if not sdk_root:
        sdk_root = os.environ.get('GAE_SDK_ROOT', '/opt/google_appengine')

    if 'google' in sys.modules:
        del sys.modules['google']

    if sdk_root not in sys.path:
        sys.path.append(sdk_root)

    # from dev_appserver import fix_sys_path
    # fix_sys_path()

    from dev_appserver import _PATHS
    sys.path[1:1] = _PATHS.v2_extra_paths
    sys.path[1:1] = _PATHS._script_to_paths.get('dev_appserver.py')
    sys.path.append('.')


# noinspection PyPackageRequirements
def setup_remote():
    from google.appengine.tools.devappserver2.devappserver2 import PARSER
    options = PARSER.parse_args([APP_YAML_FILE, ])

    from google.appengine.tools.devappserver2.devappserver2 import application_configuration
    configuration = application_configuration.ApplicationConfiguration(options.config_paths, options.app_id)

    host = '%s.appspot.com' % configuration.modules[0].application_external_name
    os.environ['HTTP_HOST'] = host
    os.environ['APPLICATION_ID'] = configuration.app_id

    from google.appengine.ext.remote_api import remote_api_stub
    remote_api_stub.ConfigureRemoteApiForOAuth(host, '/_ah/remote_api')


# noinspection PyPackageRequirements,PyProtectedMember
def setup_local():
    from google.appengine.tools.devappserver2.devappserver2 import PARSER
    options = PARSER.parse_args([APP_YAML_LOCAL_FILE, ])

    from google.appengine.tools.devappserver2.devappserver2 import application_configuration
    configuration = application_configuration.ApplicationConfiguration(options.config_paths, options.app_id)

    # set the app ID to make stubs happy, esp. datastore
    os.environ['APPLICATION_ID'] = configuration.app_id
    os.environ['AUTH_DOMAIN'] = 'localhost'
    os.environ['SERVER_NAME'] = 'localhost'
    os.environ['SERVER_PORT'] = '8080'

    from google.appengine.tools.devappserver2.devappserver2 import _get_storage_path
    storage_path = _get_storage_path(options.storage_path, configuration.app_id)
    setup_stubs(storage_path, options, configuration)


# noinspection PyPackageRequirements
def setup_stubs(storage_path, options, configuration):
    datastore_path = options.datastore_path or os.path.join(storage_path, 'datastore.db')
    search_index_path = options.search_indexes_path or os.path.join(storage_path, 'search_indexes')
    blobstore_path = options.blobstore_path or os.path.join(storage_path, 'blobs')

    # Init the proxy map and stubs
    from google.appengine.api import apiproxy_stub_map
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()


    # DB
    from google.appengine.datastore import datastore_sqlite_stub
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', datastore_sqlite_stub.DatastoreSqliteStub(configuration.app_id, datastore_path))

    # Search service
    from google.appengine.api.search import simple_search_stub
    apiproxy_stub_map.apiproxy.RegisterStub('search', simple_search_stub.SearchServiceStub(index_file=search_index_path))

    from google.appengine.api.blobstore import file_blob_storage
    blob_storage = file_blob_storage.FileBlobStorage(blobstore_path, configuration.app_id)

    from google.appengine.api.blobstore import blobstore_stub
    apiproxy_stub_map.apiproxy.RegisterStub('blobstore', blobstore_stub.BlobstoreServiceStub(blob_storage))


    from google.appengine.api.app_identity import app_identity_stub
    apiproxy_stub_map.apiproxy.RegisterStub('app_identity_service', app_identity_stub.AppIdentityServiceStub())

    # Capability
    from google.appengine.api.capabilities import capability_stub
    apiproxy_stub_map.apiproxy.RegisterStub('capability_service', capability_stub.CapabilityServiceStub())

    # Memcache
    from google.appengine.api.memcache import memcache_stub
    apiproxy_stub_map.apiproxy.RegisterStub('memcache', memcache_stub.MemcacheServiceStub())

    # Task queues
    from google.appengine.api.taskqueue import taskqueue_stub
    apiproxy_stub_map.apiproxy.RegisterStub('taskqueue', taskqueue_stub.TaskQueueServiceStub())

    # URLfetch service
    from google.appengine.api import urlfetch_stub
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub())


# noinspection PyPackageRequirements
def tear_down_local():
    from google.appengine.tools.devappserver2.api_server import cleanup_stubs
    cleanup_stubs()