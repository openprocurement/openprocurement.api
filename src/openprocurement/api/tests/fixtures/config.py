PARTIAL_MOCK_CONFIG = {
    "config":{
        "db":{
            "url":"localhost:5984",
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
