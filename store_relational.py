import asyncio
import httpx
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
from sqlalchemy import select

from relational_schema import Repositorio, Organizacion, Disciplina, Certificacion
from lib import run_in_parallel
from lib.no_relational_database import get_database_client
from re3data.extractor import raw_extract, list_repositories
from re3data.xsd_transform import refine_repository_info, load_schema, TransformError


async def get_sessions():
    engine = create_async_engine("postgresql+psycopg://ontopuser:ontoppass@127.0.0.1/ontopdb", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Repositorio.metadata.create_all)
    return async_session
    # await engine.dispose()


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


def refine_on_memory(white_list: [str], allow_whitelist: bool):
    database = get_database_client()
    raw_drepo_collection = database['raw_drepo']
    # instances = raw_drepo_collection.find({"idd": "r3d100012350"})
    instances = raw_drepo_collection.find({})
    return refine_iterator(instances, white_list, allow_whitelist)


def refine_iterator(iterator, white_list: [str], allow_whitelist: bool):
    schema = load_schema()
    refined = []
    for x in iterator:
        if x['idd'] in BLACKLIST:
            continue
        if allow_whitelist:
            if x['idd'] not in white_list:
                continue
        rrr = refine_repository_info(schema, x['bin'])
        refined.append(rrr)
    return refined


async def refine_and_insert_on_relational_db():
    async_session = await get_sessions()
    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    skip_count = 1000
    limit_count = 2000
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    instance_ids = [x['idd'] for x in instance_ids]

    async with async_session() as session2:
        already_loaded_repos_stm = select(Repositorio.id)
        already_loaded_repos = await session2.execute(already_loaded_repos_stm)
        already_loaded_repos = [x[0] for x in already_loaded_repos]
        not_repeated_ids = [x for x in instance_ids if x not in already_loaded_repos]

    async def process(repository_info):
        async with async_session() as session:
            async with session.begin():
                institutions = repository_info['institutions']
                d_institutions = []
                for institution in institutions:
                    statement = select(Organizacion).where(Organizacion.id == institution['id'])
                    result = await session.scalar(statement)
                    if result is None:
                        r_instance = Organizacion(
                            id=institution['id'],
                            nombre=institution['institutionName'],
                        )
                        session.add(r_instance)
                        result = r_instance
                    d_institutions.append(result)

                statement = select(Repositorio).where(Repositorio.id == repository_info['id'])
                result = await session.scalar(statement)
                if result is None:
                    r_instance = Repositorio(
                        id=repository_info['id'],
                        nombre=repository_info['repositoryName'],
                        descripcion=repository_info['description'],
                        sitio_web=repository_info['repositoryURL'],
                        api_type=repository_info['apiType'],
                        organizaciones=d_institutions,
                        motor_id=None,
                    )
                    session.add(r_instance)
                    return r_instance
                else:
                    return result

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    print(len(repository_infos))
    async for _ in run_in_parallel(process, iter(repository_infos), 1, 0.1):
        pass

DISCIPLINAS = []
CERTIFICACIONES = []
PAISES = []
LENGUAJES = []
PID_ESQUEMA = []

async def seed():
    async_session = await get_sessions()
    async with async_session() as session:
        async with session.begin():
            session.add_all([
                Disciplina(
                    id=x['id'],
                    nombre=x['name'],
                ) for x in DISCIPLINAS
            ])
            session.add_all([
                Certificacion(
                    id=x['id'],
                    nombre=x['name'],
                ) for x in CERTIFICACIONES
            ])


async def sync_records_on_relational_db(repo_ids: [str]):
    async_session = await get_sessions()
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
                repo_record = refine_repository_info(schema, repository_info)

                async with async_session() as session:
                    async with session.begin():
                        session.add_all([
                            Repositorio(
                                id=repo_record['id'],
                                nombre=repo_record['repositoryName'],
                                descripcion=repo_record['description'],
                                sitio_web=repo_record['repositoryURL'],
                                organizacion_id=None,
                                motor_id=None,
                            )
                        ])
            except BaseException as e:
                error_counter += 1
                print(e)
    print("errors %s" % (error_counter,))

if __name__ == '__main__':
    # refine_on_memory([], False)
    asyncio.run(refine_and_insert_on_relational_db())
