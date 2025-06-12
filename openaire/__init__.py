import typing
import httpx
from lib import run_in_parallel

T = typing.TypeVar('S')

BASE_PATH = 'https://api.openaire.eu/graph/v1/'
async def fetch_multiple_doi(doi_list: iter((str, T)), chunk_size: int, sleep: float):
    async with httpx.AsyncClient() as http_client:
        async def fetch_single_doi_local(dd: (str, T)):
            return await fetch_single_doi(dd[0], http_client)
        async for (metadata, doi_w_context) in run_in_parallel(fetch_single_doi_local, doi_list, chunk_size, sleep):
            yield metadata, doi_w_context

async def fetch_single_org_page(next: str, http_client: httpx.AsyncClient):
    doi_url = "%sorganizations" % (BASE_PATH, dd)
    doi_metadata_response = await http_client.get(doi_url, timeout=20)
    if doi_metadata_response.status_code == 404:
        return None
    doi_metadata = doi_metadata_response.json()
    return doi_metadata['data']

# Organizations
# The following query parameters are available for organizations:
#
# Parameter	Description
# search	Search in the content of the organization.
# legalName	The legal name of the organization.
# legalShortName	The legal name of the organization in short form.
# id	The OpenAIRE id of the organization.
# pid	The persistent identifier of the organization.
# countryCode	The country code of the organization.
# relCommunityId	Retrieve organizations connected to the community (with OpenAIRE id).
# relCollectedFromDatasourceId	Retrieve organizations collected from the data source (with OpenAIRE id).
# debugQuery	Retrieve debug information for the search query.
# page	Page number of the results.
# pageSize	Number of results per page.
# cursor	Cursor-based pagination. Initial value: cursor=*
# sortBy	The field to set the sorting order of the results. Should be provided in the format fieldname sortDirection, where the sortDirection can be either ASC for ascending order or DESC for descending order - organizations can only be sorted by relevance.


# https://api.openaire.eu/graph/v1/organizations?pid=https://ror.org/0576by029
# https://api.openaire.eu/graph/v1/researchProducts?search="knowledge graphs"&pageSize=100&cursor=*&sortBy=influence DESC
# {
#     header: {
#         numFound: 36818386,
#         maxScore: 1,
#         queryTime: 21,
#         page: 1,
#         pageSize: 10
#     },
#     results: [
#         {
#             "legalShortName": null,
#             "legalName": "Centre National de la Recherche Scientifique/Institut de Pharmacologie et de Biologie Structurale",
#             "websiteUrl": null,
#             "alternativeNames": null,
#             "country": {
#                 "code": "FR",
#                 "label": "France"
#             },
#             "id": "anr_________::000c8db5a189f8b8776c3a24ebd2c97d",
#             "pids": [
#                 {
#                     "scheme": "RNSR",
#                     "value": "RNSR:199911775H"
#                 }
#             ] | null
#         },
#     ]
# }