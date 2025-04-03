from typing import Any, Iterable, Mapping, MutableMapping, Optional
import requests
import asyncio
from urllib.parse import urlparse, parse_qs
from config import FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD

from lib.no_relational_database import get_database_client
from doi import fetch_multiple_doi

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

    def iter_all(self, size: int, page: int) -> Iterable[Mapping[str, Any]]:
        next_url = f"{self.base_url}/fairsharing_records/?fairsharing_registry={record_type}&page%5Bnumber%5D={page}&page%5Bsize%5D={size}"
        while next_url:
            res = self.session.get(next_url).json()
            for record in res["data"]:
                yv = process_record(record)
                if yv:
                    yield yv
            next_url = res["links"].get("next")
            last_url = res["links"].get("last")
            last_page_count = parse_qs(urlparse(last_url).query)['page[number]'][0]
            current_url = res["links"].get("self")
            current_page_count = parse_qs(urlparse(current_url).query)['page[number]'][0]
            print("%s out of %s" % (current_page_count, last_page_count))

    def iter_databases(self, size: int, page: int) -> Iterable[Mapping[str, Any]]:
        yield from self.iter_records(size, page, 'database')

    def iter_standards(self, size: int, page: int) -> Iterable[Mapping[str, Any]]:
        yield from self.iter_records(size, page, 'standard')

    def iter_policies(self, size: int, page: int) -> Iterable[Mapping[str, Any]]:
        yield from self.iter_records(size, page, 'Policy')

    def iter_records(self, size: int, page: int, record_type: str) -> Iterable[Mapping[str, Any]]:
        next_url = f"{self.base_url}/search/fairsharing_records/?fairsharing_registry={record_type}&page%5Bnumber%5D={page}&page%5Bsize%5D={size}"
        while next_url:
            res = self.session.post(next_url).json()
            for record in res["data"]:
                yv = process_record(record)
                if yv:
                    yield yv
            next_url = res["links"].get("next")
            last_url = res["links"].get("last")
            last_page_count = parse_qs(urlparse(last_url).query)['page[number]'][0]
            current_url = res["links"].get("self")
            current_page_count = parse_qs(urlparse(current_url).query)['page[number]'][0]
            print("%s out of %s" % (current_page_count, last_page_count))


def remove_prefix(s: Optional[str], prefix) -> Optional[str]:
    if s is None:
        return None
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s


async def add_doi_data(collection_name: str):
    database = get_database_client()
    collection = database[collection_name]

    with_doi = [(x['doi'], x['id']) for x in collection.find({'doi_data': {'$exists': False}}) if x.get('doi', None) is not None]

    async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
        collection.update_one(
            {'id': idd},
            {'$set': {'doi_data': doi_data}},
        )


async def extract_and_store(username: str, password: str):
    database = get_database_client()
    client = FairsharingClient(username, password)

    collection_repo = database['fairsharing']
    collection_repo.create_index('id', unique=True)
    with_doi = []
    for rr in client.iter_databases(size=25, page=1):
        collection_repo.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )
        doi = rr.get('doi', None)
        if doi:
            with_doi.append((doi, rr['id']))

    async for (doi_data, (_, idd)) in fetch_multiple_doi(with_doi, 25, 1):
        collection_repo.update_one(
            {'_id': idd},
            {'$set': {'doi_data': doi_data}},
        )

    collection_standard = database['standards']
    collection_standard.create_index('id', unique=True)
    for rr in client.iter_standards(size=25, page=1):
        collection_standard.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )

    collection_policy = database['policies']
    collection_policy.create_index('id', unique=True)
    for rr in client.iter_policies(size=25, page=1):
        collection_policy.update_one(
            {'_id': rr['id']},
            {'$set': rr},
            upsert=True,
        )


if __name__ == "__main__":
    # ToDo: Tambien puedo extraer las organizaciones de fairsharing
        # Hay registros en fairsharing que no estan en ROR
        #  será pq no cumplen el criterio de ser considerados organizaciones por fairsharing? (eg: independencia)
        # ¿y viceversa? hay en ror que no esten indexados por fairsharing?
        # Tiene tipos diferentes:
        # En ror:
        # Education,
        # Healthcare,
        # Company,
        # Archive,
        # Nonprofit,
        # Government,
        # Facility,
        # Funder,
        # Other,
        #
        # En fairsharing:
        # "Charitable foundation"
        # "Company"
        # "Consortium"
        # "Government body"
        # "Lab"
        # "Publisher"
        # "Research institute"
        # "Undefined"
        # "University"
    # asyncio.run(extract_and_store(username=FAIRSHARING_USERNAME, password=FAIRSHARING_PASSWORD))
    asyncio.run(add_doi_data('fairsharing'))
    # asyncio.run(add_doi_data('standards'))
    # asyncio.run(add_doi_data('policies'))
