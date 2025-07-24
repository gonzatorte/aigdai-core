import asyncio
import typing

import pymongo.collection

from config import FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD
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


async def extract_and_store(username: str, password: str):
    database = get_database_client()
    # client = FairsharingClient(username, password)

    # collection_repo = database['fairsharing']
    # collection_repo.create_index('id', unique=True)
    # with_doi = []
    # for rr in client.iter_databases(size=25, page=1):
    #     collection_repo.update_one(
    #         {'_id': rr['id']},
    #         {'$set': rr},
    #         upsert=True,
    #     )
    #     doi = rr.get('doi', None)
    #     if doi:
    #         with_doi.append((doi, rr['id']))
    #
    # async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
    #     collection_repo.update_one(
    #         {'_id': idd},
    #         {'$set': {'doi_data': doi_data}},
    #     )
    #
    # collection_standard = database['standards']
    # collection_standard.create_index('id', unique=True)
    # for rr in client.iter_standards(size=25, page=1):
    #     collection_standard.update_one(
    #         {'_id': rr['id']},
    #         {'$set': rr},
    #         upsert=True,
    #     )
    #
    # collection_policy = database['policies']
    # collection_policy.create_index('id', unique=True)
    # for rr in client.iter_policies(size=25, page=1):
    #     collection_policy.update_one(
    #         {'_id': rr['id']},
    #         {'$set': rr},
    #         upsert=True,
    #     )

    # fs_licence = database['fs_licence']
    # fs_licence.create_index('id', unique=True)
    # await store_entity(fs_licence, walk_graphql_licence(20, 2, 1))
    #
    # fs_keyword = database['fs_keyword']
    # fs_keyword.create_index('id', unique=True)
    # await store_entity(fs_keyword, walk_graphql_keywords(20, 2, 1))

    fs_orgs = database['fs_orgs']
    fs_orgs.create_index('id', unique=True)
    await store_entity(fs_orgs, walk_graphql_orgs(100, 2, 1))

    # fs_grants = database['fs_grants']
    # fs_grants.create_index('id', unique=True)
    # await store_entity(fs_grants, walk_graphql_grants(20, 2, 1))
    #
    # fs_subjects = database['fs_subjects']
    # fs_subjects.create_index('id', unique=True)
    # await store_entity(fs_subjects, walk_graphql_subjects(20, 2, 1))
    #
    # fs_object_types = database['fs_object_types']
    # fs_object_types.create_index('id', unique=True)
    # await store_entity(fs_object_types, walk_graphql_object_types(20, 2, 1))
    #
    # fs_registry = database['fs_registry']
    # fs_registry.create_index('id', unique=True)
    # await store_entity(fs_registry, walk_graphql_registry(10, 3, 1))
    #
    # fs_country = database['fs_country']
    # fs_country.create_index('id', unique=True)
    # await store_entity(fs_country, walk_graphql_countries(20, 2, 1))

    # fs_relations = database['fs_relations']
    # fs_relations.create_index('id', unique=True)
    # count = 0
    # async for (rr, total_count) in walk_graphql_relations(20, 2, 1):
    #     if count % 10:
    #         print("%s out of %s" % (count * 20, total_count))
    #     fs_relations.update_one(
    #         {'_id': rr['id']},
    #         {'$set': rr},
    #         upsert=True,
    #     )
    #     count += 1

    # async for rr in walk_graphql_all(2, 2, 1):
    #     print(rr)


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
    asyncio.run(extract_and_store(username=FAIRSHARING_USERNAME, password=FAIRSHARING_PASSWORD))
    # asyncio.run(add_doi_data('fairsharing'))
    # asyncio.run(add_doi_data('standards'))
    # asyncio.run(add_doi_data('policies'))
