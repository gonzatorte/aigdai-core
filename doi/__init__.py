import typing
import httpx
from lib import run_in_parallel

T = typing.TypeVar('S')

DOI_ENDPOINT = 'https://api.datacite.org/dois/'
async def fetch_multiple_doi(doi_list: iter((str, T)), chunk_size: int, sleep: float):
    async with httpx.AsyncClient() as http_client:
        async def fetch_single_doi_local(dd: (str, T)):
            return await fetch_single_doi(dd[0], http_client)
        async for (metadata, doi_w_context) in run_in_parallel(fetch_single_doi_local, doi_list, chunk_size, sleep):
            yield metadata, doi_w_context

async def fetch_single_doi(dd: str, http_client: httpx.AsyncClient):
    print('metadata of', dd)
    doi_url = "%s%s" % (DOI_ENDPOINT, dd)
    doi_metadata_response = await http_client.get(doi_url, timeout=20)
    if doi_metadata_response.status_code == 404:
        return None
    doi_metadata = doi_metadata_response.json()
    return doi_metadata['data']
