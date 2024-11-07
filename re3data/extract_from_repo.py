from re3data.extractor import extract, list_repositories, raw_extract
import asyncio
from lib import run_in_parallel
from lib.no_relational_database import get_database_client, get_database_client_async
import httpx
from re3data.xsd_transform import load_schema, refine_repository_info


# mal formateados de alguna manera (posiblemente por tags repetidos o atributos requeridos faltantes). Errores del estilo:
#   Unexpected child with tag 'dataLicense' at position XX. Tag 'dataAccess' expected.
#   Unexpected child with tag 'keyword' at position XX. Tag 'providerType' expected.
#   Unexpected child with tag 'size' at position XX. Tag 'type' expected.
#   Unexpected child with tag 'subject' at position XX. Tag 'repositoryLanguage' expected.
#   Unexpected child with tag 'missionStatementURL' at position XX. Tag 'subject' expected.
BLACKLIST = [
    'r3d100011532',
    'r3d100012053',
    'r3d100012228',
    'r3d100012247',
    'r3d100012326',
    'r3d100012645',
    'r3d100012688',
    'r3d100012791',
    'r3d100012832',
    'r3d100012857',
    'r3d100012891',
    'r3d100013068',
    'r3d100013143',
    'r3d100013224',
    'r3d100013225',
    'r3d100013260',
    'r3d100013263',
    'r3d100013468',
    'r3d100013486',
    'r3d100013504',
    'r3d100013586',
    'r3d100013688',
    'r3d100013698',
    'r3d100013722',
    'r3d100013765',
    'r3d100013815',
    'r3d100013820',
    'r3d100013886',
    'r3d100013895',
    'r3d100013938',
    'r3d100014110',
    'r3d100014186',
    'r3d100014188',
    'r3d100014227',
    'r3d100014231',
    'r3d100014239',
    'r3d100014257',
    'r3d100014264',
    'r3d100012335',
    'r3d100014357',
    'r3d100014382',
    'r3d100014401',
]

async def raw():
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo']
    repo_ids = list_repositories()
    async with httpx.AsyncClient() as client:
        counter = 0

        async def process(x):
            return await raw_extract(x, client)

        async for (repository_info, repo_id) in run_in_parallel(process, repo_ids, 20, 2):
            counter += 1
            if counter % 10 == 0:
                print("raw fetched %s out of %s" % (counter, len(repo_ids)))

            raw_drepo_collection.update_one({'idd': repo_id}, {'$set': {'data': repository_info.decode("utf-8"), 'bin': repository_info}}, upsert=True)


async def refine():
    schema = load_schema()
    database = get_database_client_async()
    raw_drepo_collection = database['raw_drepo']
    instances = raw_drepo_collection.find({})
    instances = [x async for x in instances]

    drepo_collection = database['drepo']
    # ids = {instance['idd'] for instance in drepo_collection.find({}, {'idd': 1})}

    async def refine_and_insert(instance):
        if instance['idd'] in BLACKLIST:
            return
        rr = refine_repository_info(schema, instance['bin'])
        return await drepo_collection.update_one({'idd': instance['idd']}, {'$set': rr}, upsert=True)

    async for _ in run_in_parallel(refine_and_insert, iter(instances), 100, 0):
        pass


async def main():
    database = get_database_client()
    drepo_collection = database['drepo']
    instances = {instance['idd'] for instance in database['drepo'].find({}, {'idd': 1})}
    repo_ids = list_repositories()
    async with httpx.AsyncClient() as client:
        counter = 0

        async def process(x):
            if x not in instances:
                data = await extract(x, client)
                data['idd'] = data['re3data.orgidentifier']
                return data
            return None

        async for (repository_info, repo_id) in run_in_parallel(process, repo_ids, 20, 2):
            counter += 1
            if counter % 100 == 0:
                print("fetched %s out of %s" % (counter, len(repo_ids)))

            if repository_info:
                drepo_collection.insert_one(repository_info)


if __name__ == '__main__':
    # asyncio.run(main())
    # asyncio.run(raw())
    asyncio.run(refine())
