from typing import Any, Iterable, Mapping, MutableMapping, Optional
import requests
import asyncio
from urllib.parse import urlparse, parse_qs
from config import FAIRSHARING_USERNAME, FAIRSHARING_PASSWORD
import httpx

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


FAIRSHARING_GRAPHQL_ENDPOINT = 'https://api.fairsharing.org/graphql'
X_CLIENT_ID = '3154b8ec21a2e46c935d25484378ca0a75ba14dc99b3e047dec46045f052b147701340182ed5cbe1b06abeaf52250a31b5a2a6718bf2c9966405aa236fa1aabf'


RELATIONS_G_QUERY = '''
query relations($page: Int, $perPage: Int) {
  # searchFairsharingRecords(page: 0,perPage: 0,q: "",searchAnd: "",status: "",fairsharingRegistry: "",recordType: "",id: "",ids: "",excludeId: "",countries: "",subjects: "",domains: "",taxonomies: "",userDefinedTags: "",objectTypes: "",licences: "",organisations: "",grants: "",journals: "",orderBy: "",isRecommended: "",isApproved: "",isMaintained: "",hasPublication: "",isImplemented: "",usesPersistentIdentifier: "",dataPreservationPolicy: "",resourceSustainability: "",dataAccessCondition: "",dataCuration: "",dataDepositionCondition: "",citationToRelatedPublications: "",dataAccessForPrePublicationReview: "",dataContactInformation: "",dataVersioning: "") {
  fairsharingRecords(page: $page, perPage: $perPage) {
    records {
      # metadata
      id
      name
      organisationLinks {
        id
        grant {
          id
          name
        }
        organisation {
          id
          name
          rorLink
        }
        relation
      }
      objectTypes {
        definitions
        id
        iri
        label
      }
      recordAssociations {
        id
        fairsharingRecord {
          id
          doi
          registry
        }
        linkedRecord {
          id
          doi
          registry
        }
        recordAssocLabel
      }
      licenceLinks {
        id
        fairsharingRecord {
          id
          doi
          registry
        }
        licence {
          id
          name
          url
        }
        relation
      }
    }
    lastPage
    firstPage
    totalCount
  }
}
'''


ORGS_G_QUERY = '''
query orgs($page: Int, $perPage: Int) {
  organisations(page: $page, perPage: $perPage) {
    records {
      id
      # homepage
      # alternativeNames
      # organisationLinks
      # fairsharingRecords
      # organisationTypes {
      #   id
      #   name
      # }
      # types
      # parentOrganisations {
      #   id
      #   name
      # }
      rorLink
    }
    lastPage
    firstPage
    totalCount
  }
}
'''


async def query_graphql_orgs(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    repository_metadata_response = await http_client.post(FAIRSHARING_GRAPHQL_ENDPOINT, json={
        "query": ORGS_G_QUERY,
        "variables": {'page': page, 'perPage': per_page},
    }, timeout=60, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'x-client-id': X_CLIENT_ID,
    })
    if repository_metadata_response.status_code != 200:
        raise Exception('bad status code')
    json_data = repository_metadata_response.json()
    if 'errors' in json_data:
        raise Exception(json_data['errors'])
    if 'error' in json_data:
        raise Exception(json_data['error'])
    data = json_data['data']['fairsharingRecords']
    is_last_page = data['lastPage']
    records = data['records']
    return not is_last_page, records


async def walk_graphql_orgs(chunk_size: int, sleep: float, from_page: int=None):
    has_next_page = True
    page = from_page
    async with httpx.AsyncClient() as httpClient:
        while has_next_page:
            (has_next_page, records) = await query_graphql_orgs(httpClient, page, chunk_size)
            page += 1
            if has_next_page:
                for record in records:
                    yield record
                await asyncio.sleep(sleep)


async def query_graphql_relations(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    repository_metadata_response = await http_client.post(FAIRSHARING_GRAPHQL_ENDPOINT, json={
        "query": RELATIONS_G_QUERY,
        "variables": {'page': page, 'perPage': per_page},
    }, timeout=60, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'x-client-id': X_CLIENT_ID,
    })
    if repository_metadata_response.status_code != 200:
        raise Exception('bad status code')
    json_data = repository_metadata_response.json()
    if 'errors' in json_data:
        raise Exception(json_data['errors'])
    if 'error' in json_data:
        raise Exception(json_data['error'])
    data = json_data['data']['fairsharingRecords']
    is_last_page = data['lastPage']
    records = data['records']
    return not is_last_page, records


async def walk_graphql_relations(chunk_size: int, sleep: float, from_page: int=None):
    has_next_page = True
    page = from_page
    async with httpx.AsyncClient() as httpClient:
        while has_next_page:
            (has_next_page, records) = await query_graphql_relations(httpClient, page, chunk_size)
            page += 1
            if has_next_page:
                for record in records:
                    yield record
                await asyncio.sleep(sleep)


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

    fs_relations = database['fs_relations']
    fs_relations.create_index('id', unique=True)
    async for rr in walk_graphql_relations(20, 2, 1):
        fs_relations.update_one(
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
    asyncio.run(extract_and_store(username=FAIRSHARING_USERNAME, password=FAIRSHARING_PASSWORD))
    # asyncio.run(add_doi_data('fairsharing'))
    # asyncio.run(add_doi_data('standards'))
    # asyncio.run(add_doi_data('policies'))
