from typing import Any, Iterable, Mapping, MutableMapping, Optional
import httpx
import requests
import asyncio

from lib.no_relational_database import get_database_client
from doi import fetch_single_doi

REDUNDANT_FIELDS = {
    "fairsharing_licence",
    "type",
}

FAIRSHARING_DOI_PREFIX = "10.25504/"

def process_record(
        in_record: MutableMapping[str, Any]
) -> Optional[MutableMapping[str, Any]]:
    attributes = in_record.pop("attributes")
    record = {**in_record, **attributes}
    if "id" not in record:
        print(f"{record} has no id")
        return None
    doi = record.get("doi", None)
    if doi is not None and doi.startswith(FAIRSHARING_DOI_PREFIX):
        record["doi_id"] = remove_prefix(doi, FAIRSHARING_DOI_PREFIX)

    record["description"] = remove_prefix(
        record.get("description"), "This FAIRsharing record describes: "
    )
    record["name"] = remove_prefix(record.get("name"), "FAIRsharing record for: ")
    for key in REDUNDANT_FIELDS:
        if key in record:
            del record[key]
    return record


class FairsharingClient:
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.base_url = base_url or "https://api.fairsharing.org"
        self.username = username
        self.password = password
        self.jwt = self.get_jwt()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt}",
            }
        )

    def get_jwt(self) -> str:
        payload = {
            "user": {
                "login": self.username,
                "password": self.password,
            },
        }
        res = requests.post(f"{self.base_url}/users/sign_in", json=payload).json()
        return res["jwt"]

    def iter_records(self, size: int = 25, page: int = 1) -> Iterable[Mapping[str, Any]]:
        yield from self._iter_records_helper(f"{self.base_url}/fairsharing_records/?fairsharing_registry=database&page%5Bnumber%5D={page}&page%5Bsize%5D={size}")

    def _iter_records_helper(self, url: str) -> Iterable[Mapping[str, Any]]:
        res = self.session.get(url).json()
        for record in res["data"]:
            yv = process_record(record)
            if yv:
                yield yv
        next_url = res["links"].get("next")
        last_url = res["links"].get("last")
        current_url = res["links"].get("self")
        print("%s out of %s" % (current_url, last_url))
        if next_url:
            yield from self._iter_records_helper(next_url)


def remove_prefix(s: Optional[str], prefix) -> Optional[str]:
    if s is None:
        return None
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


async def extract_and_store(username: str, password: str):
    database = get_database_client()
    collection = database['fairsharing']
    collection.create_index('id', unique=True)

    # "gonzatorte+test@gmail.com"
    client = FairsharingClient(username, password)
    async with httpx.AsyncClient() as http_client:
        for rr in client.iter_records(size=25, page=1):
            collection.insert_one(
                {'_id': rr['id'], **rr},
            )
            # collection.update_one(
            #     {'_id': rr['id']},
            #     {'$set': rr},
            #     upsert=True,
            # )
            doi = rr.get('doi', None)
            if doi:
                doi_data = await fetch_single_doi(doi, http_client)
                collection.update_one(
                    {'_id': rr['id']},
                    {'$set': {'doi_data': doi_data}},
                )

async def add_doi_data():
    database = get_database_client()
    collection = database['fairsharing']

    async with httpx.AsyncClient() as http_client:
        for rr in collection.find({'doi_data': {'$exists': False}}):
            doi = rr.get('doi', None)
            if doi:
                doi_data = await fetch_single_doi(doi, http_client)
                collection.update_one(
                    {'_id': rr['id']},
                    {'$set': {'doi_data': doi_data}},
                )

async def extract_and_store(username: str, password: str):
    database = get_database_client()
    collection = database['fairsharing']
    collection.create_index('id', unique=True)

    # "gonzatorte+test@gmail.com"
    client = FairsharingClient(username, password)
    async with httpx.AsyncClient() as http_client:
        for rr in client.iter_records(size=25, page=1):
            collection.insert_one(
                {'_id': rr['id'], **rr},
            )
            # collection.update_one(
            #     {'_id': rr['id']},
            #     {'$set': rr},
            #     upsert=True,
            # )
            doi = rr.get('doi', None)
            if doi:
                doi_data = await fetch_single_doi(doi, http_client)
                collection.update_one(
                    {'_id': rr['id']},
                    {'$set': {'doi_data': doi_data}},
                )

if __name__ == "__main__":
    asyncio.run(extract_and_store(username="gonzatortetest", password="GT_@pr0y3ctD41"))
    # asyncio.run(add_doi_data())
