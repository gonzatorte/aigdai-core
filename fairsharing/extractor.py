import argparse
import asyncio
import typing

import pymongo.collection

from settings import require_fairsharing_credentials
from fairsharing.graphql_client import walk_graphql_registry, walk_graphql_licence, walk_graphql_keywords, \
    walk_graphql_orgs, walk_graphql_subjects, walk_graphql_grants, walk_graphql_object_types, walk_graphql_countries

from fairsharing.rest_client import FairsharingClient
from lib.no_relational_database import get_database_client
from doi import fetch_multiple_doi


async def add_doi_data(collection_name: str):
    database = get_database_client()
    collection = database[collection_name]

    with_doi = [(x['doi'], x['id']) for x in collection.find({'doi_data': {'$exists': False}}) if x.get('doi', None) is not None]

    async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
        collection.update_one(
            {'id': idd},
            {'$set': {'doi_data': doi_data}},
        )


async def store_entity(coll: pymongo.collection.Collection, walker: typing.AsyncGenerator[tuple[typing.Any, int], typing.Any]):
    count = 0
    async for (rr, total_count) in walker:
        if count % 100 == 0:
            print("%s out of %s" % (count, total_count))
        coll.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )
        count += 1


GRAPHQL_COLLECTIONS = {
    'licences': ('fs_licence', lambda: walk_graphql_licence(20, 2, 1)),
    'keywords': ('fs_keyword', lambda: walk_graphql_keywords(20, 2, 1)),
    'orgs': ('fs_orgs', lambda: walk_graphql_orgs(100, 2, 1)),
    'grants': ('fs_grants', lambda: walk_graphql_grants(20, 2, 1)),
    'subjects': ('fs_subjects', lambda: walk_graphql_subjects(20, 2, 1)),
    'object_types': ('fs_object_types', lambda: walk_graphql_object_types(20, 2, 1)),
    'registry': ('fs_registry', lambda: walk_graphql_registry(10, 3, 1)),
    'countries': ('fs_country', lambda: walk_graphql_countries(20, 2, 1)),
}
# Colecciones que se extraen con el cliente REST, no con GraphQL.
REST_COLLECTIONS = ('databases', 'standards', 'policies')
ALL_COLLECTIONS = tuple(GRAPHQL_COLLECTIONS) + REST_COLLECTIONS
DEFAULT_COLLECTIONS = tuple(GRAPHQL_COLLECTIONS)
DOI_COLLECTIONS = ('fairsharing', 'standards', 'policies')


async def store_rest_databases(database, client: FairsharingClient):
    collection_repo = database['fairsharing']
    collection_repo.create_index('id', unique=True)
    with_doi = []
    for rr in client.iter_databases(size=25, page=1):
        collection_repo.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )
        doi = rr.get('doi', None)
        if doi:
            with_doi.append((doi, rr['id']))

    async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
        collection_repo.update_one(
            {'_id': idd},
            {'$set': {'doi_data': doi_data}},
        )


async def store_rest_standards(database, client: FairsharingClient):
    collection_standard = database['standards']
    collection_standard.create_index('id', unique=True)
    for rr in client.iter_standards(size=25, page=1):
        collection_standard.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )


async def store_rest_policies(database, client: FairsharingClient):
    collection_policy = database['policies']
    collection_policy.create_index('id', unique=True)
    for rr in client.iter_policies(size=25, page=1):
        collection_policy.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )


REST_STORERS = {
    'databases': store_rest_databases,
    'standards': store_rest_standards,
    'policies': store_rest_policies,
}


async def extract_and_store(collections=DEFAULT_COLLECTIONS, username: str=None, password: str=None):
    database = get_database_client()

    rest_collections = [c for c in collections if c in REST_COLLECTIONS]
    if rest_collections:
        if not username or not password:
            (username, password) = require_fairsharing_credentials()
        client = FairsharingClient(username, password)
        for name in rest_collections:
            await REST_STORERS[name](database, client)

    for name in [c for c in collections if c in GRAPHQL_COLLECTIONS]:
        (collection_name, walker) = GRAPHQL_COLLECTIONS[name]
        coll = database[collection_name]
        coll.create_index('id', unique=True)
        await store_entity(coll, walker())


def _comma_separated(valid: tuple, kind: str):
    def parse(raw: str):
        if raw.strip() in ('', 'none'):
            return ()
        values = tuple(x.strip() for x in raw.split(',') if x.strip())
        unknown = [x for x in values if x not in valid]
        if unknown:
            raise argparse.ArgumentTypeError(
                '%s invalido(s): %s. Opciones: %s' % (kind, ', '.join(unknown), ', '.join(valid))
            )
        return values
    return parse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Extrae los registros de FAIRsharing y los guarda en Mongo.')
    parser.add_argument(
        '--collections', type=_comma_separated(ALL_COLLECTIONS, 'coleccion'), default=DEFAULT_COLLECTIONS,
        help=('Colecciones a extraer, separadas por coma (' + ', '.join(ALL_COLLECTIONS) + '). '
              'Las ultimas tres usan el cliente REST y piden credenciales. '
              'Por defecto: ' + ', '.join(DEFAULT_COLLECTIONS) + '.'),
    )
    parser.add_argument(
        '--doi', type=_comma_separated(DOI_COLLECTIONS, 'coleccion'), default=(),
        help=('Completar los metadatos de DOI faltantes en estas colecciones, separadas por coma ('
              + ', '.join(DOI_COLLECTIONS) + ').'),
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    async def run():
        if args.collections:
            await extract_and_store(collections=args.collections)
        for collection_name in args.doi:
            await add_doi_data(collection_name)

    asyncio.run(run())


if __name__ == "__main__":
    # ToDo: Tambien puedo extraer las organizaciones de fairsharing
        # Hay registros en fairsharing que no estan en ROR
        #  será pq no cumplen el criterio de ser considerados organizaciones por fairsharing? (eg: independencia)
        # ¿y viceversa? hay en ror que no esten indexados por fairsharing?
        # Tiene tipos diferentes:
        # En ror:
        # Education,
        # Healthcare,
        # Company,
        # Archive,
        # Nonprofit,
        # Government,
        # Facility,
        # Funder,
        # Other,
        #
        # En fairsharing:
        # "Charitable foundation"
        # "Company"
        # "Consortium"
        # "Government body"
        # "Lab"
        # "Publisher"
        # "Research institute"
        # "Undefined"
        # "University"
    main()
