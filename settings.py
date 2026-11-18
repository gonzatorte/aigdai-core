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

# Java runtime of the reasoners (HermiT and Jena run in the same JVM, through jpype). Jena 5 needs Java 17 or later;
# the default is the JRE downloaded into reasoner/jre (see onto/README.md). The heap is shared by both reasoners.
REASONER_JAVA_HOME = os.environ.get('REASONER_JAVA_HOME', 'reasoner/jre/jdk-21.0.12.1+1-jre')
REASONER_HEAP = os.environ.get('REASONER_HEAP', '16g')

FAIRSHARING_USERNAME = os.environ.get('FAIRSHARING_USERNAME', '')
FAIRSHARING_PASSWORD = os.environ.get('FAIRSHARING_PASSWORD', '')


def require_fairsharing_credentials() -> tuple[str, str]:
    if not FAIRSHARING_USERNAME or not FAIRSHARING_PASSWORD:
        raise RuntimeError(
            'Missing FAIRSHARING_USERNAME and FAIRSHARING_PASSWORD. Define them in the environment or in %s (see .env.example).' % (ENV_FILE,)
        )
    return (FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD)
