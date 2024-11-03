import asyncio
from timeit import default_timer as timer
import typing
import httpx

from doi import fetch_multiple_doi
from lib import run_in_block, AsyncPeepIterator
from lib.no_relational_database import get_database_client_async

GRAPHQL_ENDPOINT = 'https://api.datacite.org/graphql'

async def query_cursor(http_client: httpx.AsyncClient, first: int=None, cursor: str=None):
    repository_metadata_response = await http_client.post(GRAPHQL_ENDPOINT, json={
        "query": '''
        query Foo1($first: Int, $cursor: String) {
          repositories(first: $first, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
        ''',
        "variables": {'first': first, 'cursor': cursor},
    }, timeout=60)
    json_data = repository_metadata_response.json()
    if 'errors' in json_data:
        raise Exception(json_data['errors'])
    data = json_data['data']['repositories']
    has_next_page = data['pageInfo']['hasNextPage']
    end_cursor = data['pageInfo']['endCursor']
    return has_next_page, end_cursor

async def query_cursors(chunk_size: int, sleep: float, from_cursor: str=None):
    has_next_page = True
    end_cursor = from_cursor
    async with httpx.AsyncClient() as httpClient:
        while has_next_page:
            (has_next_page, end_cursor) = await query_cursor(httpClient, chunk_size, end_cursor)
            if has_next_page:
                yield end_cursor
                await asyncio.sleep(sleep)

DATASET_FACETS = [
    'personToWorkTypesMultilevel',
    'authors',
    'affiliations',
    'creatorsAndContributors',
    'registrationAgencies',
    'openLicenseResourceTypes',
    'fieldsOfScience',
    'fieldsOfScienceCombined',
    'fieldsOfScienceRepository',
    'funders',
    'languages',
    'licenses',
    'published',
]

DATASET_EXTRA_FACETS = []

REPOSITORY_ATTRS = [
    'clientId',
    're3dataUrl',
    're3dataDoi',
    'type',
    'repositoryType',
    'alternateName',
    'pidSystem',
    'certificate',
    'downloadCount',
    'viewCount',
    'providerType',
    ('subject', '''
    {
      termCode
      description
      inDefinedTermSet
      name
    }
    '''),
    ('dataAccess', '''
    {
      restriction {
        text
      }
      type
    }
    '''),
    'citationCount',
    ('dataUpload', '''
    {
      restriction {
        text
      }
      type
    }
    '''),
    'keyword',
    'language',
]

REPOSITORY_EXTRA_ATTRS = []

DATASET_ATTRS = [
    'viewCount',
    ('rights', '''
    {
      rights
      rightsIdentifier
      rightsUri
      rightsIdentifierScheme
      schemeUri
    }
    '''),
    ('titles', '''
    {
      lang
      title
      titleType
    }
    '''),
    ('identifiers', '''
    identifiers {
      identifierType
      identifier
    }
    '''),
]
DATASET_EXTRA_ATTRS = []

def get_repo_graphql_info(attrs: list[str | tuple[str, str]], update_flow: bool=False):
    dataset_facets = DATASET_EXTRA_FACETS[:]
    if not update_flow:
        dataset_facets.extend(DATASET_FACETS)
    facet_attrs = ["%s %s" % x if isinstance(x, tuple) else x for x in dataset_facets]
    query_facets = ""
    if len(facet_attrs):
        query_facets = '''
        datasets {
          totalCount
          %s
        }
        ''' % (
            '\n'.join([
                '''
                  %s {
                    count
                    id
                    title
                  }
                ''' % (aa,) for aa in facet_attrs
            ]),
        )
    simple_attrs = ["%s %s" % x if isinstance(x, tuple) else x for x in attrs]
    return '''
      %s
      %s
    ''' % ('\n'.join(simple_attrs), query_facets)

def get_repositories_graphql_query_str(attrs: list[str | tuple[str, str]], update_flow: bool=False):
    return '''
    query repositoriesPageQuery($first: Int!, $cursor: String) {
      repositories(first: $first, after: $cursor) {
        edges {
          node {
            uid
            %s
          }
        }
      }
    }
    ''' % (get_repo_graphql_info(attrs, update_flow),)

def get_repository_graphql_query_str(attrs: list[str | tuple[str, str]], update_flow: bool=False):
    return '''
    query repositoriesSingle($uid: ID!) {
      repository(id: $uid) {
        uid
        %s
      }
    }
    ''' % (get_repo_graphql_info(attrs, update_flow),)

class CannotGetName(Exception):
    pass

async def query_repositories(http_client: httpx.AsyncClient, attrs: list[str | tuple[str, str]], first: int=None, cursor: str=None, update_flow: bool=False):
    # We do not currently impose per account rate limits.
    # However, there is a top level hard limit imposed by DataCite's firewall which is based on IP address,
    # and this is around 3000 requests in a 5 minute window.
    # There is also an upper limit for requests that come via doi.org Content Negotiation
    # of 1000 requests in a 5 minute window.
    print("fetching", cursor)
    query_str = get_repositories_graphql_query_str(attrs, update_flow)
    repository_metadata_response = await http_client.post(GRAPHQL_ENDPOINT, json={
        "query": query_str,
        "variables": {'first': first, 'cursor': cursor},
    }, timeout=90)
    json_data = repository_metadata_response.json()
    # if 'errors' in json_data:
    #     if isinstance(json_data['errors'], list):
    #         if json_data['errors'][0]['message'] == 'Cannot return null for non-nullable field Repository.name':
    #             raise CannotGetName()
    #     raise Exception(json_data['errors'])
    data = json_data['data']['repositories']
    return {dd['node']['uid']: dd['node'] for dd in data['edges'] if dd['node'] is not None}

async def query_repository(http_client: httpx.AsyncClient, attrs: list[str | tuple[str, str]], uid: str, update_flow: bool):
    print("fetching", uid)
    query_str = get_repository_graphql_query_str(attrs, update_flow)
    repository_metadata_response = await http_client.post(GRAPHQL_ENDPOINT, json={
        "query": query_str,
        "variables": {'uid': uid},
    }, timeout=60)
    json_data = repository_metadata_response.json()
    if 'errors' in json_data:
        if isinstance(json_data['errors'], list):
            if json_data['errors'][0]['message'] == 'Cannot return null for non-nullable field Repository.name':
                raise CannotGetName()
        raise Exception(json_data['errors'])
    return json_data['data']['repository']

async def query_repositories_w_retry(http_client: httpx.AsyncClient, first: int=None, cursor: str=None, update_flow: bool=False):
    attrs = REPOSITORY_EXTRA_ATTRS[:]
    if not update_flow:
        attrs.extend(REPOSITORY_ATTRS)
    else:
        attrs.append('name')
    try:
        return await query_repositories(http_client, attrs, first, cursor, update_flow)
    except CannotGetName:
        attrs.remove('name')
        return await query_repositories(http_client, attrs, first, cursor, update_flow)

async def query_repository_w_retry(http_client: httpx.AsyncClient, uid: str, update_flow: bool):
    attrs = REPOSITORY_EXTRA_ATTRS[:]
    if not update_flow:
        attrs.extend(REPOSITORY_ATTRS)
    else:
        attrs.append('name')
    try:
        return await query_repository(http_client, attrs, uid, update_flow)
    except CannotGetName:
        attrs.remove('name')
        return await query_repository(http_client, attrs, uid, update_flow)

async def cursor_fetch(page_size: int, chunk_size: int, chunk_count: int, sleep: float, cursor_generator: typing.AsyncGenerator[str | None, typing.Any], update_flow: bool=False):
    cnt = 0
    async with httpx.AsyncClient() as httpClient:
        async def query_page(cursor: str):
            return await query_repositories_w_retry(httpClient, page_size, cursor, update_flow)
        async for x in run_in_block(
            query_page,
            AsyncPeepIterator(cursor_generator),
            chunk_size,
            sleep,
            lambda qw: print('info from repos', qw),
            lambda qs, y: print('error from', y, qs) or True
        ):
            for xx in x:
                cnt += 1
                yield xx[0]
            if cnt >= chunk_count:
                break

async def cursor_walk(page_size: int, chunk_size: int, chunk_count: int, sleep: float, from_cursor: str=None, update_flow: bool=False):
    async def cursor_generator():
        yield from_cursor
        async for xxx in query_cursors(page_size, 0.8, from_cursor):
            yield xxx
    async for tt in cursor_fetch(page_size, chunk_size, chunk_count, sleep, cursor_generator(), update_flow):
        yield tt

async def cursor_bulk(page_size: int, chunk_size: int, chunk_count: int, sleep: float, cursors: [str], update_flow: bool=False):
    async def cursor_generator():
        for xxx in cursors:
            yield xxx
    async for tt in cursor_fetch(page_size, chunk_size, chunk_count, sleep, cursor_generator(), update_flow):
        yield tt

async def update_mongo_record(uid: str, datacite_graphql_repo, db_collection):
    asyncio.current_task().name = "store_in_mongo_%s" % (uid,)
    kk_attrs = [x[0] if isinstance(x, tuple) else x for x in REPOSITORY_EXTRA_ATTRS]
    attrs = {"datacite_graphql_data.%s" % (x,): datacite_graphql_repo[x] for x in kk_attrs}
    kk_facets = [x[0] if isinstance(x, tuple) else x for x in DATASET_EXTRA_FACETS]
    facets = {"datacite_graphql_data.datasets.%s" % (x,): datacite_graphql_repo['datasets'][x] for x in kk_facets}
    setters = list(attrs.items())
    setters.extend(facets.items())
    setters = dict(setters)
    db_collection.update_one({'uid': uid}, {'$set': setters}, upsert=False)

async def insert_mongo_record(uid: str, datacite_graphql_repo, db_collection):
    asyncio.current_task().name = "store_in_mongo_%s" % (uid,)
    db_collection.update_one({'uid': uid}, {'$set': {
        'doi_metadata': None,
        'datacite_graphql_data': datacite_graphql_repo,
    }}, upsert=True)

async def enrich_generated(update_flow: bool, generator: typing.AsyncGenerator[typing.Coroutine[typing.Any, typing.Any, dict], typing.Any]):
    asyncio.current_task().name = "fetch_all"
    def exception_handler(_loop, context):
        exception = context['exception']
        message = context['message']
        print(f'Task failed, msg={message}, exception={exception}')

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(exception_handler)

    last_time = timer()
    database = get_database_client_async()
    datacite_collection = database['datacite']
    async for datacite_graphql_repos_chunk in generator:
        if update_flow:
            chunk = datacite_graphql_repos_chunk.items()
            await asyncio.gather(
                *[
                    update_mongo_record(uid, datacite_graphql_repo, datacite_collection) for (uid, datacite_graphql_repo) in chunk
                ],
                return_exceptions=True,
            )
        else:
            no_doi_chunk = [x for x in datacite_graphql_repos_chunk.items() if x[1]['re3dataDoi'] is None]
            await asyncio.gather(
                *[
                    insert_mongo_record(uid, datacite_graphql_repo, datacite_collection) for (uid, datacite_graphql_repo) in no_doi_chunk
                ],
                return_exceptions=True,
            )
            doi_chunk = [(x[1]['re3dataDoi'], x[1]) for x in datacite_graphql_repos_chunk.items() if x[1]['re3dataDoi'] is not None]
            async for (doi_metadata, (doi, datacite_graphql_repo)) in fetch_multiple_doi(doi_chunk, 4, 2):
                await datacite_collection.update_one({'uid': datacite_graphql_repo['uid']}, {'$set': {
                    'doi_metadata': doi_metadata if doi_metadata is not None else 'error',
                    'datacite_graphql_data': datacite_graphql_repo,
                }}, upsert=True)
        this_time = timer()
        print("iteration took", this_time - last_time)
        last_time = this_time

def sync_cursor_walk(from_cursor: str=None, update_flow: bool=False):
    return enrich_generated(update_flow, cursor_walk(5, 5, 800, 1, from_cursor, update_flow))

async def bunch_id_fetch(uid_s: [str], chunk_size: int, sleep: float, update_flow: bool=False):
    async with httpx.AsyncClient() as httpClient:
        async def query_page(uid: str):
            return await query_repository_w_retry(httpClient, uid, update_flow)
        async for x in run_in_block(
            query_page,
            uid_s,
            chunk_size,
            sleep,
            lambda qw: print('info from repos', qw),
            lambda qs, y: print('error from', y, qs) or True
        ):
            yield {xx[1]: xx[0] for xx in x}

def sync_specific_bunch_id(uid_s: [str], update_flow: bool=False):
    # async def async_wrap(to_wrap: [typing.Any]):
    #     chunk_size = len(to_wrap) // 10
    #     for ii in range(chunk_size):
    #         yield [to_wrap[(chunk_size*ii):(chunk_size*(ii+1))]]
    return enrich_generated(update_flow, bunch_id_fetch(uid_s, 5, 1, update_flow))

def sync_specific_bunch_cursor(cursors: [str], update_flow: bool=False):
    return enrich_generated(update_flow, cursor_bulk(1, 1, 800, 0, cursors, update_flow))

if __name__ == '__main__':
    async def run():
        await sync_cursor_walk(None)
        # await sync_specific_bunch(failed, True)
        # await sync_specific_bunch_cursor([])
    asyncio.run(run())
