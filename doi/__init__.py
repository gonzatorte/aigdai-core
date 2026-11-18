import asyncio
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

# The DataCite API answers 429 above its rate limit (https://support.datacite.org/docs/rate-limit)
RATE_LIMIT_WAIT = 60
RATE_LIMIT_RETRIES = 10

async def fetch_single_doi(dd: str, http_client: httpx.AsyncClient):
    doi_url = "%s%s" % (DOI_ENDPOINT, dd)
    for _ in range(RATE_LIMIT_RETRIES):
        doi_metadata_response = await http_client.get(doi_url, timeout=20)
        if doi_metadata_response.status_code != 429:
            break
        await asyncio.sleep(float(doi_metadata_response.headers.get('retry-after') or RATE_LIMIT_WAIT))
    if doi_metadata_response.status_code == 404:
        return None
    if doi_metadata_response.status_code != 200:
        raise RuntimeError('DOI %s: HTTP %s %s' % (dd, doi_metadata_response.status_code, doi_metadata_response.text[:200]))
    doi_metadata = doi_metadata_response.json()
    return doi_metadata['data']
