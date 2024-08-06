import httpx
from lxml import html
import asyncio

from re3data.xsd_transform import refine_repository_info, load_schema

RE3_DATA_BASE_URL = 'https://www.re3data.org/'


def list_repositories():
    # URL = f"{RE3_DATA_BASE_URL}api/beta/repositories"
    re3data_response = httpx.get(f"{RE3_DATA_BASE_URL}api/v1/repositories", timeout=60)
    re3data_response_content = re3data_response.content
    tree = html.fromstring(re3data_response_content)
    return tree.xpath("repository/id/text()")


async def raw_extract(this_repo_id: str, client: httpx.AsyncClient):
    repository_metadata_response = await client.get(f"{RE3_DATA_BASE_URL}api/beta/repository/%s" % this_repo_id,
                                                    follow_redirects=True)
    return repository_metadata_response.content


async def extract(this_repo_id: str, client: httpx.AsyncClient):
    schema = load_schema()
    repository_metadata_response_content = await raw_extract(this_repo_id, client)
    # ToDo: No estoy seguro si es correcto filtrar este caso
    # filter out repositories with no information on APIs
    # if len(repository_info["api"]) > 0:
    #     return None
    return refine_repository_info(schema, repository_metadata_response_content)


if __name__ == '__main__':
    async def my_test():
        async with httpx.AsyncClient() as clientTest:
            res = await extract('r3d100000001', clientTest)
            print(res)


    asyncio.run(my_test())
