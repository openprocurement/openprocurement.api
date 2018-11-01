import os
import uuid


DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5984')
DB_USER = os.environ.get('DB_USER', 'op')
DB_PASS = os.environ.get('DB_PASS', 'op')
API_VERSION = os.environ.get('API_VERSION', '2.5')
PARTIAL_MOCK_CONFIG = {
    "config":{
        "db":{
            "url":"{host}:{port}".format(host=DB_HOST, port=DB_PORT),
            "db_name":"db_tests_{}".format(uuid.uuid4().hex),
            "writer":{
                "password":DB_PASS,
                "name":DB_USER
            },
            "type":"couchdb"
        },
        "auth":{
            "src":"auth.ini",
            "type":"file"
        },
        "main":{
            "api_version": API_VERSION
        }
    },
    "plugins":{
        "api":{
            "plugins":{
                "transferring": None
            }
        }
    }
}
