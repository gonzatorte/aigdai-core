"""Project configuration, read from the environment.

Variables are taken from the environment and, if it exists, from the `.env` file at the
repository root (see `.env.example`). The same variables are used by `docker-compose*.yml`,
so development credentials are defined once and are not versioned.
"""
import os
import pathlib
import urllib.parse

from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parent
# File the variables are read from. It is always this one, not whatever the library finds on its own.
ENV_FILE = BASE_DIR / '.env'

# Variables already defined in the environment take precedence over the ones in the file.
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _build_mongo_url() -> str:
    explicit = os.environ.get('MONGO_URL')
    if explicit:
        return explicit
    host = os.environ.get('MONGO_HOST', 'localhost')
    port = os.environ.get('MONGO_PORT', '27017')
    database = os.environ.get('MONGO_DB', 'aigdai')
    user = os.environ.get('MONGO_USER', '')
    password = os.environ.get('MONGO_PASSWORD', '')
    if not user:
        return 'mongodb://%s:%s/%s' % (host, port, database)
    credentials = '%s:%s' % (urllib.parse.quote_plus(user), urllib.parse.quote_plus(password))
    return 'mongodb://%s@%s:%s/%s?authSource=admin' % (credentials, host, port, database)


MONGO_URL = _build_mongo_url()

JENA_BASE_PATH = os.environ.get('JENA_BASE_PATH', 'http://localhost:3030/')
JENA_DATASET = os.environ.get('JENA_DATASET', 'aigdai')

FAIRSHARING_USERNAME = os.environ.get('FAIRSHARING_USERNAME', '')
FAIRSHARING_PASSWORD = os.environ.get('FAIRSHARING_PASSWORD', '')

JAVA_EXE_PATH = os.environ.get('JAVA_EXE_PATH', '/usr/bin/java')


def require_fairsharing_credentials() -> tuple[str, str]:
    if not FAIRSHARING_USERNAME or not FAIRSHARING_PASSWORD:
        raise RuntimeError(
            'Missing FAIRSHARING_USERNAME and FAIRSHARING_PASSWORD. Define them in the environment or in %s (see .env.example).' % (ENV_FILE,)
        )
    return (FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD)
