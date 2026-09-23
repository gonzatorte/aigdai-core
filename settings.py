"""Configuración del proyecto, leída del entorno.

Las variables se toman del entorno y, si existe, del archivo `.env` de la raíz del
repositorio (ver `.env.example`). Las mismas variables las usa `docker-compose*.yml`,
así que las credenciales de desarrollo se definen una sola vez y no se versionan.
"""
import os
import pathlib
import urllib.parse

from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parent
# Archivo del que se leen las variables. Es siempre este y no el que la librería encuentre por su cuenta.
ENV_FILE = BASE_DIR / '.env'

# Las variables ya definidas en el entorno tienen prioridad sobre las del archivo.
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
            'Faltan FAIRSHARING_USERNAME y FAIRSHARING_PASSWORD. Definilas en el entorno o en %s (ver .env.example).' % (ENV_FILE,)
        )
    return (FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD)
