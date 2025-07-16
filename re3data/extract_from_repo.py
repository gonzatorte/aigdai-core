from re3data.extractor import extract, list_repositories, raw_extract
import asyncio
from lib import run_in_parallel
from lib.no_relational_database import get_database_client, get_database_client_async
import httpx
from re3data.xsd_transform import load_schema, refine_repository_info
from doi import fetch_multiple_doi
import re

# mal formateados de alguna manera (posiblemente por tags repetidos o atributos requeridos faltantes). Errores del estilo:
#   Unexpected child with tag 'dataLicense' at position XX. Tag 'dataAccess' expected.
#   Unexpected child with tag 'keyword' at position XX. Tag 'providerType' expected.
#   Unexpected child with tag 'size' at position XX. Tag 'type' expected.
#   Unexpected child with tag 'subject' at position XX. Tag 'repositoryLanguage' expected.
#   Unexpected child with tag 'missionStatementURL' at position XX. Tag 'subject' expected.
BLACKLIST = [
    'r3d100014568',
    'r3d100014583',
    'r3d100014595',
    'r3d100014616',
    'r3d100014625',
    'r3d100014629',
    'r3d100014636',
    'r3d100014642',
    'r3d100014648',
    'r3d100014650',
    'r3d100014525',
    'r3d100014526',
    'r3d100014528',
    'r3d100014529',
    'r3d100014531',
    'r3d100014532',
    'r3d100014534',
    'r3d100014536',
    'r3d100014537',
    'r3d100014538',
    'r3d100014539',
    'r3d100014540',
    'r3d100014541',
    'r3d100014543',
    'r3d100014545',
    'r3d100014546',
    'r3d100014552',
    'r3d100014553',
    'r3d100014554',
    'r3d100014555',
    'r3d100014557',
    'r3d100014558',
    'r3d100014560',
    'r3d100014561',
    'r3d100014562',
    'r3d100014563',
    'r3d100014564',
    'r3d100014567',
    'r3d100014569',
    'r3d100014570',
    'r3d100014571',
    'r3d100014572',
    'r3d100014573',
    'r3d100014574',
    'r3d100014575',
    'r3d100014578',
    'r3d100014584',
    'r3d100014586',
    'r3d100014587',
    'r3d100014588',
    'r3d100014590',
    'r3d100014593',
    'r3d100014594',
    'r3d100014596',
    'r3d100014597',
    'r3d100014600',
    'r3d100014604',
    'r3d100014605',
    'r3d100014606',
    'r3d100014607',
    'r3d100014614',
    'r3d100014617',
    'r3d100014618',
    'r3d100014619',
    'r3d100014620',
    'r3d100014621',
    'r3d100014622',
    'r3d100014624',
    'r3d100014627',
    'r3d100014628',
    'r3d100014631',
    'r3d100014632',
    'r3d100014633',
    'r3d100014634',
    'r3d100014643',
    'r3d100014645',
    'r3d100014646',
    'r3d100014649',
    'r3d100013890',
    'r3d100014506',
    'r3d100014507',
    'r3d100014509',
    'r3d100014511',
    'r3d100014512',
    'r3d100014513',
    'r3d100014515',
    'r3d100014516',
    'r3d100014517',
    'r3d100014518',
    'r3d100014519',
    'r3d100014520',
    'r3d100014521',
    'r3d100014522',
    'r3d100014637',
    'r3d100014638',
    'r3d100014640',
    'r3d100014641',

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

async def download_and_store_raw():
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo_2']
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


async def raw_and_store_refined():
    schema = load_schema()
    database = get_database_client_async()
    raw_drepo_collection = database['raw_drepo_2']
    instances = raw_drepo_collection.find({})
    instances = [x async for x in instances]

    drepo_collection = database['drepo_2']
    # ids = {instance['idd'] for instance in drepo_collection.find({}, {'idd': 1})}

    async def refine_and_insert(instance):
        if instance['idd'] in BLACKLIST:
            return None
        rr = refine_repository_info(schema, instance['bin'])
        await drepo_collection.update_one({'idd': instance['idd']}, {'$set': rr}, upsert=True)
        return rr

    with_doi = []
    counter_re3data = 0
    async for (repository_info, _) in run_in_parallel(refine_and_insert, iter(instances), 100, 0):
        counter_re3data += 1
        if counter_re3data % 100 == 0:
            print("re3data fetched %s out of %s" % (counter_re3data, len(instances)))

        if repository_info is None:
            continue
        for iddd in repository_info['ids']:
            iddd_match = re.match('^((?:fairsharing[:_]doi)|(?:doi)):(?P<doi>.+)', iddd, re.IGNORECASE)
            if iddd_match:
                doi = iddd_match.groupdict().get('doi').replace(' ', '')
                with_doi.append((doi, repository_info['id']))
                continue

    counter_doi = 0
    async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
        await drepo_collection.update_one(
            {'_id': idd},
            {'$set': {'doi_data': doi_data}},
        )
        counter_doi += 1
        if counter_doi % 10 == 0:
            print("doi fetched %s out of %s" % (counter_doi, len(with_doi)))


async def download_and_store_refined():
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
    # asyncio.run(download_and_store_refined())
    # asyncio.run(download_and_store_raw())
    asyncio.run(raw_and_store_refined())
