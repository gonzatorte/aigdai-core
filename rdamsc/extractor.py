from lib.no_relational_database import get_database_client
import httpx
import asyncio
from typing import Any, Tuple, List, AsyncIterable, Coroutine, Callable
# import typing
# T = typing.TypeVar('S')

from rdflib.namespace import RDF
from rdflib import Graph, Literal, URIRef
import onto.populator.rdf_types as rdf_types
# import json

ItemsResponse = Tuple[List[Any], int]
Method = Callable[[int, int], Coroutine[Any, Any, Tuple[List[Any], int]]]

async def iter_items(method: Method, batch_size: int, start_offset: int) -> AsyncIterable[List[Any]]:
    offset = start_offset
    got_items, total_count = await method(batch_size, offset)
    offset += len(got_items)
    print("%s out of %s" % (offset - 1, total_count))
    yield got_items
    while offset - 1 < total_count:
        got_items, total_count = await method(batch_size, offset)
        offset += len(got_items)
        print("%s out of %s" % (offset - 1, total_count))
        yield got_items

class RdaMscClient:
    RDA_MSC_PREFIX = 'https://rdamsc.bath.ac.uk/api2/'

    async def call_api(self, service: str, page_size: int, offset: int) -> ItemsResponse:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get("%s%s" % (self.RDA_MSC_PREFIX, service), timeout=20, params=[('start', offset), ('pageSize', page_size)])
            if response.status_code != 200:
                raise Exception()
            response_data = response.json()
            return response_data['data']['items'], response_data['data']['totalItems']

    async def standards(self, page_size: int, offset: int):
        return await self.call_api('m', page_size, offset)

    async def mappings(self, page_size: int, offset: int):
        return await self.call_api('c', page_size, offset)

    async def relations(self, page_size: int, offset: int):
        return await self.call_api('rel', page_size, offset)

    async def tools(self, page_size: int, offset: int):
        return await self.call_api('t', page_size, offset)


async def extract_and_store():
    # database = get_database_client()
    client = RdaMscClient()

    # collection_repo = database['rdamsc']
    # collection_repo.create_index('id', unique=True)
    schemas = []
    async for rr in iter_items(client.standards, 25, 1):
        schemas.extend(rr)
        # collection_repo.update_one(
        #     {'_id': rr['id']},
        #     {'$set': rr},
        #     upsert=True,
        # )

    mappings = []
    async for rr in iter_items(client.mappings, 25, 1):
        mappings.extend(rr)
        # collection_repo.update_one(
        #     {'_id': rr['id']},
        #     {'$set': rr},
        #     upsert=True,
        # )

    # relations = []
    # async for rr in iter_items(client.relations, 25, 1):
    #     relations.extend(rr)
    #     # collection_repo.update_one(
    #     #     {'_id': rr['id']},
    #     #     {'$set': rr},
    #     #     upsert=True,
    #     # )

    g_meta = Graph()
    g_meta.bind('', rdf_types.my_ns)

    for schema in schemas:
        related_schemas = [(x['id'], x['role'] == 'child scheme') for x in schema['relatedEntities'] if x['role'] in ['parent scheme', 'child scheme']]
        esquema_de_metadatos = URIRef("esquema_de_metadatos/%s" % (schema['mscid'],), rdf_types.my_ns)
        g_meta.set((esquema_de_metadatos, RDF.type, rdf_types.EsquemaDeMetadatos))
        for related_schema, is_parent in related_schemas:
            extendido_esquema_de_metadatos = URIRef("esquema_de_metadatos/%s" % (related_schema,), rdf_types.my_ns)
            if is_parent:
                g_meta.set((esquema_de_metadatos, rdf_types.extiende_a_esquema_de_metadatos, extendido_esquema_de_metadatos))


if __name__ == "__main__":
    asyncio.run(extract_and_store())
