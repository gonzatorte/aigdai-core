import asyncio
from timeit import default_timer as timer
import typing
import httpx
from lib import run_in_parallel, run_in_block, PeepIterator, AsyncPeepIterator
from lib.no_relational_database import get_database_client_async

T = typing.TypeVar('S')

DOI_ENDPOINT = 'https://api.datacite.org/dois/'
async def fetch_multiple_doi(doi_list: iter((str, T)), chunk_size: int, sleep: float):
    async with httpx.AsyncClient() as httpClient:
        async def fetch_single_doi(dd: (str, T)):
            print('metadata of', dd[0])
            doi_metadata_response = await httpClient.get("%s/%s" % (DOI_ENDPOINT, dd[0]), timeout=20)
            if doi_metadata_response.status_code == 404:
                return None
            doi_metadata = doi_metadata_response.json()
            return doi_metadata['data']
        async for (metadata, doi_w_context) in run_in_parallel(fetch_single_doi, doi_list, chunk_size, sleep):
            yield metadata, doi_w_context

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

def get_query_str(attrs: list[str]):
    repository_stats = [
        'downloadCount',
        'viewCount',
    ]
    repository_summary = '''
      personToWorkTypesMultilevel {
        count
        id
        title
      }
      authors {
        count
        id
        title
      }
      affiliations {
        count
        id
        title
      }
      creatorsAndContributors {
        count
        id
        title
      }
      registrationAgencies {
        count
        id
        title
      }
      openLicenseResourceTypes {
        count
        id
        title
      }
      fieldsOfScience {
        count
        id
        title
      }
      fieldsOfScienceCombined {
        count
        id
        title
      }
      fieldsOfScienceRepository {
        count
        id
        title
      }
      funders {
        count
        id
        title
      }
      languages {
        count
        id
        title
      }
      licenses {
        count
        id
        title
      }
      published {
        count
        id
        title
      }
    '''

    # '''
    # identifiers {
    #   identifierType
    #   identifier
    # }
    # '''
    query_repository = '''
        %s
        %s
        datasets {
          totalCount
          %s
        }
        dataManagementPlans {
          totalCount
          nodes {
            doi
          }
        }
    ''' % ('\n'.join(attrs), '\n'.join(repository_stats), repository_summary)
    return '''
    query Foo($first: Int!, $cursor: String) {
      repositories(first: $first, after: $cursor) {
        edges {
          node {
            uid
            %s
          }
        }
      }
    }
    ''' % (query_repository,)

class CannotGetName(Exception):
    pass

async def query_repositories(http_client: httpx.AsyncClient, attrs: list[str], first: int=None, cursor: str=None):
    print("fetching", cursor)
    repository_metadata_response = await http_client.post(GRAPHQL_ENDPOINT, json={
        "query": get_query_str(attrs),
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

async def query_repositories_w_retry(http_client: httpx.AsyncClient, first: int=None, cursor: str=None):
    attrs = [
        'name',
        'clientId',
        're3dataUrl',
        're3dataDoi',
        'type',
        'repositoryType',
        'alternateName',
        'pidSystem',
        'certificate',
    ]
    try:
        return await query_repositories(http_client, attrs, first, cursor)
    except CannotGetName:
        attrs.remove('name')
        return await query_repositories(http_client, attrs, first, cursor)

async def walk_page(chunk_size: int, chunk_count: int, sleep: float, from_cursor: str=None):
    cnt = 0
    async def cursor_generator():
        yield from_cursor
        async for xx in query_cursors(chunk_size, 0.8, from_cursor):
            yield xx
    async with httpx.AsyncClient() as httpClient:
        async def query_page(cursor: str):
            return await query_repositories_w_retry(httpClient, chunk_size, cursor)
        async for x in run_in_block(query_page, AsyncPeepIterator(cursor_generator()), chunk_size, sleep, lambda x: print('info from repos', x), lambda x, y: print('error from', y, x) or True):
            for xx in x:
                cnt += 1
                yield xx[0]
            if cnt >= chunk_count:
                break

async def walk_all(from_cursor: str=None):
    asyncio.current_task().name = "fetch_all"
    def exception_handler(_loop, context):
        exception = context['exception']
        message = context['message']
        print(f'Taska failed, msg={message}, exception={exception}')

    loop = asyncio.get_running_loop()
    loop.set_exception_handler(exception_handler)

    last_time = timer()
    database = get_database_client_async()
    datacite_collection = database['datacite']
    async for datacite_graphql_repos_chunk in walk_page(3, 400, 2, from_cursor):
        no_doi_chunk = [x for x in datacite_graphql_repos_chunk.items() if x[1]['re3dataDoi'] is None]
        async def store_in_mongo(uid: str, datacite_graphql_repo):
            asyncio.current_task().name = "store_in_mongo_%s" % (uid,)
            datacite_collection.update_one({'uid': uid}, {'$set': {
                'doi_metadata': None,
                'datacite_graphql_data': datacite_graphql_repo,
            }}, upsert=True)
        db_update_status_elems = await asyncio.gather(
            *[
                store_in_mongo(uid, datacite_graphql_repo) for (uid, datacite_graphql_repo) in no_doi_chunk
            ],
            return_exceptions=True,
        )
        print('db_update_status_elems', db_update_status_elems)
        doi_chunk = [(x[1]['re3dataDoi'], x[1]) for x in datacite_graphql_repos_chunk.items() if x[1]['re3dataDoi'] is not None]
        async for (doi_metadata, (doi, datacite_graphql_repo)) in fetch_multiple_doi(doi_chunk, 4, 2):
            await datacite_collection.update_one({'uid': datacite_graphql_repo['uid']}, {'$set': {
                'doi_metadata': doi_metadata if doi_metadata is not None else 'error',
                'datacite_graphql_data': datacite_graphql_repo,
            }}, upsert=True)
        this_time = timer()
        print("iteration took", this_time - last_time)
        last_time = this_time


if __name__ == '__main__':
    async def run():
        await walk_all('MS4wLDE3MjI5NTIwNjAwMDAsenIzY2o0eg')
        # await fetch_all('MS4wLDkyMjMzNzIwMzY4NTQ3NzU4MDcsMWQ5YzFveQ')

    asyncio.run(run())
