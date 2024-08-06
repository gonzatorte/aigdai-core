import httpx
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
from sqlalchemy import select

from relational_schema import Repositorio
from lib import run_in_parallel
from lib.no_relational_database import get_database_client, get_database_client_async
from re3data.extractor import raw_extract, list_repositories
from re3data.xsd_transform import refine_repository_info, load_schema, TransformError


async def get_sessions():
    engine = create_async_engine("postgresql+psycopg://ontopuser:ontoppass@127.0.0.1/ontopdb", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Repositorio.metadata.create_all)
    return async_session
    # await engine.dispose()


BLACKLIST = [
    # unico con 2 instituciones o mas
    'r3d100000002',
    # mal formateados de alguna manera. Errores del estilo:
    #   Unexpected child with tag 'dataLicense' at position XX. Tag 'dataAccess' expected.
    #   Unexpected child with tag 'keyword' at position XX. Tag 'providerType' expected.
    #   Unexpected child with tag 'size' at position XX. Tag 'type' expected.
    #   Unexpected child with tag 'subject' at position XX. Tag 'repositoryLanguage' expected.
    #   Unexpected child with tag 'missionStatementURL' at position XX. Tag 'subject' expected.
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
]


def refine_on_memory():
    schema = load_schema()
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo']
    instances = raw_drepo_collection.find({})
    refined = []
    for x in instances:
        try:
            rr = refine_repository_info(schema, x['bin'])
        except TransformError as err:
            print(x['idd'], err)
        else:
            refined.append(rr)
    return refined


async def refine_and_insert_on_relational_db():
    async_session = await get_sessions()
    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    instances = raw_drepo_collection.find({})
    instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True})
    instance_ids = [x['idd'] for x in instance_ids]

    async with async_session() as session2:
        already_loaded_repos_stm = select(Repositorio.id)
        already_loaded_repos = await session2.execute(already_loaded_repos_stm)
        already_loaded_repos = [x[0] for x in already_loaded_repos]
        not_repeated_ids = [x for x in instance_ids if x not in already_loaded_repos]

    schema = load_schema()

    def process_factory(whitelist_ids):
        async def process(repository_info):
            if repository_info['idd'] in BLACKLIST:
                return
            if repository_info['idd'] not in whitelist_ids:
                return
            rr = refine_repository_info(schema, repository_info['bin'])

            async with async_session() as session:
                async with session.begin():
                    statement = select(Repositorio).where(Repositorio.id == rr['id'])
                    result = await session.scalar(statement)
                    if result is None:
                        r_instance = Repositorio(
                            id=rr['id'],
                            nombre=rr['repositoryName'],
                            descripcion=rr['description'],
                            sitio_web=rr['repositoryURL'],
                            organizacion_id=None,
                            motor_id=None,
                        )
                        session.add(r_instance)
                        return r_instance
                    else:
                        return result
        return process

    async for _ in run_in_parallel(process_factory(not_repeated_ids), instances, 10, 1, lambda x: print("raw fetched %s out of %s" % (x, instances_count)), print):
        pass


async def download_and_insert_on_relational_db():
    async_session = await get_sessions()

    repo_ids = list_repositories()

    schema = load_schema()
    async with httpx.AsyncClient() as client:
        counter = 0
        error_counter = 0

        async def process(x):
            return await raw_extract(x, client)

        async for (repository_info, repo_id) in run_in_parallel(process, repo_ids, 20, 2):
            counter += 1
            if counter % 10 == 0:
                print("raw fetched %s out of %s. Errors: %s" % (counter, len(repo_ids), error_counter))

            try:
                rr = refine_repository_info(schema, repository_info)

                async with async_session() as session:
                    async with session.begin():
                        session.add_all([
                            Repositorio(
                                id=rr['id'],
                                nombre=rr['repositoryName'],
                                descripcion=rr['description'],
                                sitio_web=rr['repositoryURL'],
                                organizacion_id=None,
                                motor_id=None,
                            )
                        ])
            except BaseException as e:
                error_counter += 1
                print(e)
    print("errors %s" % (error_counter,))

if __name__ == '__main__':
    rr = refine_on_memory()
    print(rr)
    # asyncio.run(refine_and_insert_on_relational_db())
    # asyncio.run(download_and_insert_on_relational_db())
