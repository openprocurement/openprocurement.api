import os


DB_HOST = os.environ.get('DB_HOST', 'localhost')
PARTIAL_MOCK_CONFIG = {
    "config":{
        "db":{
            "url":"{host}:5984".format(host=DB_HOST),
            "db_name":"db_tests",
            "writer":{
                "password":"op",
                "name":"op"
            },
            "type":"couchdb"
        },
        "auth":{
            "src":"auth.ini",
            "type":"file"
        },
        "main":{
            "api_version": "2.5"
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
