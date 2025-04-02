import json

# File built based on execution of this query at the fairsharing "frontend used" graphql endpoint (https://api.fairsharing.org/graphql)
# user-agent: any valid browser (eg: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36)
# x-client-id: get it by fairsharing frontend inspection (eg: 3154b8ec21a2e46c935d25484378ca0a75ba14dc99b3e047dec46045f052b147701340182ed5cbe1b06abeaf52250a31b5a2a6718bf2c9966405aa236fa1aabf)
# query ALL_ORGS {
#   allOrganisations {
#     id
#     name
#     homepage
#     types
#     rorLink
#   }
# }
FAIRSHARING_ROR_MAPPING_FILEPATH = './ror_fairsharing_map.json'
ROR_PREFIX = 'https://ror.org/'

def fairsharing_2_ror(fairsharing_org_id: int):
    with open(FAIRSHARING_ROR_MAPPING_FILEPATH, 'r') as file:
        registries = json.load(file)
        found_ids = [x for x in registries if x['id'] == fairsharing_org_id]
        if len(found_ids) == 0:
            return None
        if len(found_ids) == 1:
            found = found_ids[0]['rorLink']
            if found is None:
                return None
            if not found.startswith(ROR_PREFIX):
                raise Exception('')
            return found[len(ROR_PREFIX):]
        raise Exception('Multiple matching orgs')

def ror_2_fairsharing(ror_id: str):
    if not ror_id.startswith(ROR_PREFIX):
        ror_id = ROR_PREFIX + ror_id
    with open(FAIRSHARING_ROR_MAPPING_FILEPATH, 'r') as file:
        registries = json.load(file)
        found_ids = [x for x in registries if x['rorLink'] == ror_id]
        if len(found_ids) == 0:
            return None
        if len(found_ids) == 1:
            found = found_ids[0]['id']
            if found is None:
                return None
            return found
        raise Exception('Multiple matching orgs')

def guess_fairsharing_org_into_ror(org_data):
    # See some proposed approachs at
    # https://github.com/ror-community/ror-utilities/blob/main/general-scripts/search-by-name-affiliation.py
    # https://github.com/ror-community/ror-utilities/blob/main/fairsharing-match-scripts/matching_urls.py
    # https://github.com/ror-community/ror-utilities/blob/main/fairsharing-match-scripts/matching_name_shortname.py
    pass

if __name__ == "__main__":
    assert fairsharing_2_ror(6) == '05rex1605'
    assert fairsharing_2_ror(1) is None
    assert fairsharing_2_ror(1111111) is None

    assert ror_2_fairsharing('05rex1605') == 6
    assert ror_2_fairsharing('cafecafec') is None
