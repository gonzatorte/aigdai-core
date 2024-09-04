import asyncio
from timeit import default_timer as timer
import typing
import httpx
from lib import run_in_parallel, run_in_block, AsyncPeepIterator
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
]

REPOSITORY_EXTRA_ATTRS = [
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

DATASET_EXTRA_ATTRS = [
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

def get_repo_graphql_info(attrs: list[str | tuple[str, str]], update_flow: bool=False):
    dataset_facets = DATASET_EXTRA_FACETS[:]
    if not update_flow:
        dataset_facets.extend(DATASET_FACETS)
    facet_attrs = ["%s %s" % x if isinstance(x, tuple) else x for x in dataset_facets]
    query_facets = ""
    if len(facet_attrs):
        query_facets = '''
        datasets {
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

async def cursor_walk(page_size: int, chunk_size: int, chunk_count: int, sleep: float, from_cursor: str=None, update_flow: bool=False):
    cnt = 0
    async def cursor_generator():
        yield from_cursor
        async for xxx in query_cursors(page_size, 0.8, from_cursor):
            yield xxx
    async with httpx.AsyncClient() as httpClient:
        async def query_page(cursor: str):
            return await query_repositories_w_retry(httpClient, page_size, cursor, update_flow)
        async for x in run_in_block(
            query_page,
            AsyncPeepIterator(cursor_generator()),
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
        print(f'Taska failed, msg={message}, exception={exception}')

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
    return enrich_generated(update_flow, cursor_walk(5, 5, 400, 2, from_cursor, update_flow))

async def bunch_fetch(uid_s: [str], chunk_size: int, sleep: float, update_flow: bool=False):
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

def sync_specific_bunch(uid_s: [str], update_flow: bool=False):
    # async def async_wrap(to_wrap: [typing.Any]):
    #     chunk_size = len(to_wrap) // 10
    #     for ii in range(chunk_size):
    #         yield [to_wrap[(chunk_size*ii):(chunk_size*(ii+1))]]
    return enrich_generated(update_flow, bunch_fetch(uid_s, 5, 2, update_flow))

if __name__ == '__main__':
    failed = [
        'vl6cvzr',
        '1d9c1kq',
        '1d9c1oy',
        '1d9c493',
        '1d9c41v',
        '1d9c4e4',
        '1d9c4nv',
        '1d9c7e',
        '1d9cjye',
        '1d9cl2l',
        '1d9cl47',
        '1d9clo2',
        '1d9clnk',
        '1d9cl51',
        '1d9clv1',
        '1d9cq5n',
        '1d9cqqo',
        '1d9cqgy',
        '1d9cr36',
        '1d9crqr',
        '1d9cr5q',
        '1d9crnr',
        '1d9crw6',
        '213c1do',
        '213c1v9',
        '213c9g7',
        '213ceoq',
        '213co7l',
        '213cone',
        '213col6',
        '213covg',
        '213cy19',
        '213cydk',
        '3znc63e',
        '3znc6dl',
        '3znc6wz',
        '3znc6o6',
        '3znc6xz',
        '3znc6ze',
        '3znc967',
        '3zncj1k',
        '3zncjgx',
        '3zncjlk',
        '3zncn6w',
        '3zncnj4',
        '3zncngj',
        '3zncx2x',
        '4ygc8jw',
        '4ygc918',
        '3zncxzg',
        '4ygc734',
        '4ygc9ex',
        '4ygcg1r',
        '4ygcg9q',
        '4ygcnx8',
        '4ygcrqk',
        '51qc27v',
        '4ygcrzk',
        '51qc2vv',
        '51qc8qn',
        '51qc8kq',
        '51qc7g9',
        '51qc2ye',
        '51qckyg',
        '51qck98',
        '6eyc298',
        '6eyc2x2',
        '6eyc4zq',
        '6eyc82v',
        '6eyc8v5',
        '6eyc83g',
        '6eyck2e',
        '6eycx4d',
        '6eycvve',
        '6eycxgo',
        '7exc8ww',
        '6eycxvd',
        '7excdk3',
        '7excr4l',
        '7excrdk',
        '7excrq2',
        '7excw4z',
        '7excw8r',
        '7excwqv',
        '7excwer',
        '8orc494',
        '7excwzz',
        '8orcz5x',
        '8orcnrq',
        '8orcv7e',
        '8orcv8e',
        '8orczqy',
        '8orcznj',
        '9z2c136',
        '9z2c5x1',
        '9z2c8vg',
        '9z2cd2d',
        '9z2cdqg',
        '9z2cdk4',
        '9z2cv6q',
        '9z2cv4y',
        '9z2cre1',
        '9z2cv7o',
        '9z2cvrq',
        '9z2cvxy',
        'dl6c56e',
        'dl6c5ke',
        'dl6c5qe',
        'dl6c5lk',
        'dl6c768',
        'dl6ckgv',
        'dl6clnl',
        'dl6clro',
        'dl6cnj',
        'dl6cwj7',
        'dl6cwn4',
        'dl6cwo7',
        'dl6cwrn',
        'dl6cy19',
        'dl6cye9',
        'eqjc563',
        'eqjc5en',
        'eqjc81e',
        'eqjck1r',
        'eqjck5o',
        'eqjc8d7',
        'eqjck7y',
        'g69c46z',
        'g69c3vk',
        'eqjcky8',
        'eqjcwkq',
        'g69cgdv',
        'g69c4j7',
        'g69clkq',
        'g69clny',
        'g69cnzx',
        'g69cr9z',
        'jjgc13q',
        'jjgc1dq',
        'jjgc6dv',
        'jjgc987',
        'jjgcl2w',
        'jjgcl4k',
        'jjgclo1',
        'jjgcl7k',
        'jjgcvwl',
        'jjgcx38',
        'jjgcxl9',
        'jjgcxn2',
        'jjgcxr2',
        'jjgcy3o',
        'jjgcyq8',
        'k6qc1l6',
        'k6qc5vg',
        'k6qc5ed',
        'k6qcjo2',
        'k6qc6g3',
        'k6qc65w',
        'k6qckg7',
        'k6qckq7',
        'k6qckj9',
        'k6qcrkq',
        'l4yc2y7',
        'l4yc5je',
        'l4yc5xz',
        'l4yc5qq',
        'l4ycrgx',
        'l4ycrkl',
        'l4ycwjl',
        'l4ycx7g',
        'l4ycxzn',
        'nxrc1n8',
        'nxrc19y',
        'nxrc22w',
        'nxrc24g',
        'nxrc9vj',
        'nxrcd3v',
        'nxrcq7n',
        'nxrcqk5',
        'or2c8k7',
        'or2c5vg',
        'or2c5r4',
        'or2c8ld',
        'or2c8w9',
        'or2clkv',
        'or2cooy',
        'or2co6w',
        'or2cvrx',
        'or2cvk1',
        'or2czly',
        'or2cvg2',
        'q98c6ed',
        'or2czr8',
        'q98c67j',
        'q98c68v',
        'q98c94w',
        'q98c96r',
        'q98c97l',
        'q98c9jg',
        'rv5c1q8',
        'rv5c1g9',
        'q98c9xl',
        'q98c9z3',
        'rv5c1yz',
        'rv5ce2o',
        'rv5ce7q',
        'rv5cekz',
        'rv5cov4',
        'rv5cow4',
        'rv5cqvv',
        'rv5cqoe',
        'rv5cwkj',
        'vl6c21v',
        'vl6c2lo',
        'vl6c4r9',
        'vl6ce67',
        'vl6ce37',
        'vl6cd51',
        'vl6cedx',
        'vl6clnr',
        'vl6cyoj',
        'wqjc239',
        'vl6cex7',
        'wqjc2r9',
        'wqjc2wo',
        'wqjc25k',
        'wqjc2l3',
        'wqjc2z9',
        'wqjc2zw',
        'wqjc2xw',
        'wqjc48y',
        'wqjcd7x',
        'wqjc4r2',
        'wqjcdn4',
        'wqjcd9r',
        'wqjcnk6',
        'wqjcn5g',
        'wqjcn2r',
        'wqjcnkj',
        'x3oc4q8',
        'x3oc4y8',
        'x3oc458',
        'x3oc85l',
        'x3oclj6',
        'y79c1e6',
        'y79cewe',
        'y79cedz',
        'y79cj3x',
        'y79cj7j',
        'y79cjg7',
        'y79ck1d',
        'y79co1o',
        'y79coz4',
        'y79ck8d',
        'y79covo',
        'y79cv9d',
        'y79cvo2',
        'zr3c5jd',
        'zr3c5nd',
        'zr3c9gq',
        'zr3c9nq',
        'zr3c5zk',
        'zr3c9d4',
        'zr3cevl',
        'zr3cr3g',
        'zr3cy5g',
        'zr3cyg9',
        'zr3cyqg'
    ]
    async def run():
        # await sync_cursor_walk('MS4wLDkyMjMzNzIwMzY4NTQ3NzU4MDcsenIzY2V2bA', True)
        await sync_specific_bunch(failed, True)
        # await sync_cursor_walk('MS4wLDkyMjMzNzIwMzY4NTQ3NzU4MDcsMWQ5YzFveQ')
    asyncio.run(run())
