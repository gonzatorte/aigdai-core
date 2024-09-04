from python_graphql_client import GraphqlClient
import base64

client = GraphqlClient(endpoint="https://api.datacite.org/graphql")

query = '''
query Foo1($first: Int, $cursor: String) {
  repositories(first: $first, after: $cursor) {
    pageInfo {
      endCursor
      startCursor
      hasNextPage
    }
    nodes {
      uid
    }
  }
}
'''

def get_one(cursor):
    qr = client.execute(query=query, variables={"cursor": cursor, "first": 2})
    data = qr['data']['repositories']
    page_info = data['pageInfo']
    return page_info['endCursor'], page_info['startCursor'], data['nodes'][0]['uid'], data['nodes'][1]['uid']

def ceil(nn, mul):
    return ((nn // mul) + (1 if nn % mul else 0)) * mul

def pad_base_64(ss):
    return ss.ljust(ceil(len(ss), 4), '=')

def decode_cursor(cursor):
    cursor_decoded = base64.b64decode(pad_base_64(cursor))
    [version, some_id, uid_extreme] = cursor_decoded.split(b',')
    # print(version, some_id, uid_extreme)
    return some_id

def sample(cursor):
    cn, cp, sample_uid_p, sample_uid_n = get_one(cursor)
    # print(sample_uid_p)
    print(sample_uid_n)
    # decode_cursor(cp)
    some_id = decode_cursor(cn)
    return cn, cp, some_id

prev_cn, prev_cp, prev_some_id = sample(None)
for x in range(0, 10):
    new_cn, new_cp, new_some_id = sample(prev_cn)
    print(int(new_some_id) - int(prev_some_id))
    prev_cn, prev_cp, prev_some_id = new_cn, new_cp, new_some_id

# Se determinó que usan el entry date para indexarlo en el paginado...
