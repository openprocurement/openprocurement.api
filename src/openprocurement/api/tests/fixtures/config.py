import os
import uuid


DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5984')
DB_USER = os.environ.get('DB_USER', 'op')
DB_PASS = os.environ.get('DB_PASS', 'op')
API_VERSION = os.environ.get('API_VERSION', '2.5')
PARTIAL_MOCK_CONFIG = {
    "config": {
        "db": {
            "url": "http://{host}:{port}".format(host=DB_HOST, port=DB_PORT),
            "db_name": "db_tests_{}".format(uuid.uuid4().hex),
            "writer": {
                "password": DB_PASS,
                "name": DB_USER
            },
            "type": "couchdb"
        },
        "auth": {
            "src": "auth.ini",
            "type": "file"
        },
        "main": {
            "api_version": API_VERSION
        }
    },
    "plugins": {
        "api": {
            "plugins": {
                "transferring": None
            }
        }
    }
}


# only for testing
RANDOM_PLUGINS = {
    "api": {
        "plugins": {
            "transferring": {
                "plugins": {
                    "auctions.transferring": None
                }
            },
            "auctions.core": {
                "plugins": {
                    "auctions.rubble.financial": {
                        "use_default": True,
                        "plugins": {
                            "rubble.financial.migration": None
                        },
                        "migration": False,
                        "accreditation": {
                            "edit": [
                                2
                            ],
                            "create": [
                                1
                            ]
                        },
                        "aliases": ["dgfFinancialAssets"]
                    },
                    "auctions.rubble.other": {
                        "use_default": True,
                        "plugins": {
                            "rubble.other.migration": None
                        },
                        "migration": True,
                        "accreditation": {
                            "edit": [
                                2
                            ],
                            "create": [
                                1
                            ]
                        },
                        "aliases": ["dgfOtherAssets"]
                    }
                }
            }
        }
    }
}
