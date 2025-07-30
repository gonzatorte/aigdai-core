import asyncio
import typing
import httpx


FAIRSHARING_GRAPHQL_ENDPOINT = 'https://api.fairsharing.org/graphql'
X_CLIENT_ID = '3154b8ec21a2e46c935d25484378ca0a75ba14dc99b3e047dec46045f052b147701340182ed5cbe1b06abeaf52250a31b5a2a6718bf2c9966405aa236fa1aabf'


async def query_graphql(query: str, http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    repository_metadata_response = await http_client.post(FAIRSHARING_GRAPHQL_ENDPOINT, json={
        "query": query,
        "variables": {'page': page, 'perPage': per_page},
    }, timeout=60, headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'x-client-id': X_CLIENT_ID,
    })
    if repository_metadata_response.status_code != 200:
        raise Exception('bad status code')
    json_res = repository_metadata_response.json()
    if 'data' not in json_res:
        raise Exception('bad graphql structure')
    json_data = json_res['data']
    if 'errors' in json_data:
        raise Exception(json_data['errors'])
    if 'error' in json_data:
        raise Exception(json_data['error'])
    return json_data


METADATA_FIELDS = [
    'homepage', # string
    'doi', # string, not with url
    'status', # enum
    'description', # string
    'abbreviation', # string
    'year_creation', # int
    'contacts', # array of contact_name, contact_email, contact_orcid
    'identifier', # int, same as fairsharing record id
    'data_versioning', # enum yes/no
    'associated_tools', # array of url, name
    'cross_references', # array of url, name, portal
    'support_links',  # array of url, name, type
    'data_access_condition', # url, type, notes
    'data_curation', # url, type, notes
    'data_preservation_policy', # url, type, notes
    'resource_sustainability', # url, type, notes
    'data_contact_information', # enum yes/no
    'data_processes_and_conditions', # array of url, name, type, access_method and documentation_url
    'citation_to_related_publications', # enum yes/no
    'data_access_for_pre_publication_review', # enum yes/no
    'certifications_and_community_badges', # array of url, name
]
def normalize_metadata_field(metadata_field):
    # ToDo: Algunos campos dependen de su validez del registry type o del record type
    # ToDo: Normalizar a arrays vacios todos los campos array
    return metadata_field


async def page_query(query: str, results_keys: str, http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    res = await query_graphql(query, http_client, page, per_page)
    data = res[results_keys]
    # is_last_page = data['lastPage']
    total_count = data['totalCount']
    records = data['records']
    # print('total_count', total_count, is_last_page, len(records), records)
    return len(records) > 0, total_count, records


def get_relations_query(full: bool):
    return '''
query relations($page: Int, $perPage: Int) {
  # searchFairsharingRecords(page: 0,perPage: 0,q: "",searchAnd: "",status: "",fairsharingRegistry: "",recordType: "",id: "",ids: "",excludeId: "",countries: "",subjects: "",domains: "",taxonomies: "",userDefinedTags: "",objectTypes: "",licences: "",organisations: "",grants: "",journals: "",orderBy: "",isRecommended: "",isApproved: "",isMaintained: "",hasPublication: "",isImplemented: "",usesPersistentIdentifier: "",dataPreservationPolicy: "",resourceSustainability: "",dataAccessCondition: "",dataCuration: "",dataDepositionCondition: "",citationToRelatedPublications: "",dataAccessForPrePublicationReview: "",dataContactInformation: "",dataVersioning: "") {
  fairsharingRecords(page: $page, perPage: $perPage) {
    records {
      id
      %s
      grants {
        id
      }
      objectTypes {
        id
      }
      domains {
        id
      }
      subjects {
        id
      }
      taxonomies {
        id
      }
      userDefinedTags {
        id
      }
      countries {
        id
      }
      organisationLinks {
        id
        grant {
          id
        }
        organisation {
          id
        }
        relation
      }
      recordAssociations {
        id
        fairsharingRecord {
          id
        }
        linkedRecord {
          id
        }
        recordAssocLabel
      }
      licenceLinks {
        id
        fairsharingRecord {
          id
        }
        licence {
          id
        }
        relation
      }
    }
    lastPage
    firstPage
    totalCount
  }
}
''' % (('\n'.join([
        "doi",
        "name",
        "description",
        "abbreviation",
        "type",
        "registry",
        "status",
        "homepage",
        "exhaustiveLicences",
        "deprecationReason",
        "lastEdited",
        "lastReviewed",
        "updatedAt",
        "metadata",
    ]), ) if full else ('',))


ORGS_RELATIONS_G_QUERY = '''
query org_relations($page: Int, $perPage: Int) {
  organisations(page: $page, perPage: $perPage) {
    records {
      id
    }
    lastPage
    firstPage
    totalCount
  }
}
'''


def query_graphql_relations(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query(get_relations_query(False), 'fairsharingRecords', http_client, page, per_page)


def query_graphql_registry(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query(get_relations_query(True), 'fairsharingRecords', http_client, page, per_page)


def query_graphql_orgs(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query org_relations($page: Int, $perPage: Int) {
  organisations(page: $page, perPage: $perPage) {
    records {
      id
      name
      homepage
      alternativeNames
      organisationTypes {
        id
        name
      }
      types
      parentOrganisations {
        id
      }
      rorLink
    }
    lastPage
    firstPage
    totalCount
  }
}
      ''', 'organisations', http_client, page, per_page)


def query_graphql_countries(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_countries($page: Int, $perPage: Int) {
  countries(page: $page, perPage: $perPage) {
    records {
      alternativeNames
      code
      id
      name
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'countries', http_client, page, per_page)


def query_graphql_grants(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_grants($page: Int, $perPage: Int) {
  grants(page: $page, perPage: $perPage) {
    records {
      description
      id
      name
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'grants', http_client, page, per_page)


def query_graphql_object_type(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_objectTypes($page: Int, $perPage: Int) {
  objectTypes(page: $page, perPage: $perPage) {
    records {
      definitions
      iri
      id
      label
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'objectTypes', http_client, page, per_page)


def query_graphql_licence(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_licences($page: Int, $perPage: Int) {
  licences(page: $page, perPage: $perPage) {
    records {
      url
      id
      name
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'licences', http_client, page, per_page)


def query_graphql_keywords(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_keywords($page: Int, $perPage: Int) {
  userDefinedTags(page: $page, perPage: $perPage) {
    records {
      definitions
      id
      label
      synonyms
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'userDefinedTags', http_client, page, per_page)


def query_graphql_subjects(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_subjects($page: Int, $perPage: Int) {
  subjects(page: $page, perPage: $perPage) {
    records {
      definitions
      expandedNames
      id
      iri
      label
      synonyms
      parents {
        id
      }
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'subjects', http_client, page, per_page)


def query_graphql_domains(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_domains($page: Int, $perPage: Int) {
  domains(page: $page, perPage: $perPage) {
    records {
      definitions
      expandedNames
      id
      iri
      label
      synonyms
      parents {
        id
      }
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'subjects', http_client, page, per_page)


def query_graphql_taxonomies(http_client: httpx.AsyncClient, page: int=None, per_page: int=None):
    return page_query('''
query get_taxonomies($page: Int, $perPage: Int) {
  taxonomies(page: $page, perPage: $perPage) {
    records {
      definitions
      expandedNames
      id
      iri
      label
      synonyms
    }
    lastPage
    firstPage
    currentPage
    perPage
    totalCount
  }
}
    ''', 'subjects', http_client, page, per_page)


async def walk_pages(method: typing.Callable[[httpx.AsyncClient, int | None, int | None], typing.Coroutine[typing.Any, typing.Any, tuple[bool, int, typing.Any]]], chunk_size: int, sleep: float, from_page: int=None):
    has_next_page = True
    page = from_page
    async with httpx.AsyncClient() as httpClient:
        while has_next_page:
            (has_next_page, total_count, records) = await method(httpClient, page, chunk_size)
            page += 1
            if has_next_page:
                for record in records:
                    yield record, total_count
                await asyncio.sleep(sleep)


def walk_graphql_registry(chunk_size: int, sleep: float, from_page: int=None):
    return walk_pages(query_graphql_registry, chunk_size, sleep, from_page)


def walk_graphql_orgs(chunk_size: int, sleep: float, from_page: int=None):
    return walk_pages(query_graphql_orgs, chunk_size, sleep, from_page)


def walk_graphql_grants(chunk_size: int, sleep: float, from_page: int=None):
    return walk_pages(query_graphql_grants, chunk_size, sleep, from_page)


def walk_graphql_object_types(chunk_size: int, sleep: float, from_page: int=None):
    return walk_pages(query_graphql_object_type, chunk_size, sleep, from_page)


def walk_graphql_licence(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_licence, chunk_size, sleep, from_page)


def walk_graphql_keywords(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_keywords, chunk_size, sleep, from_page)


def walk_graphql_subjects(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_subjects, chunk_size, sleep, from_page)


def walk_graphql_countries(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_countries, chunk_size, sleep, from_page)


def walk_graphql_domains(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_domains, chunk_size, sleep, from_page)


def walk_graphql_taxonomies(chunk_size: int, sleep: float, from_page: int = None):
    return walk_pages(query_graphql_taxonomies, chunk_size, sleep, from_page)
