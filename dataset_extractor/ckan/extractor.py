# ToDo: Usar httpx mejor...
import urllib.request
import json
import pprint
# pip install ckanapi
from ckanapi import RemoteCKAN

def extract(base_url: str):
    request = urllib.request.Request('http://demo.ckan.org/api/3/action/group_list')
    # ToDo: API reference does not document which endpoints need authentication and which doesnt
    # request.add_header('Authorization', 'XXX')
    data_string = b'{}'
    response = urllib.request.urlopen(request, data_string).read()
    assert response.code == 200
    response_dict = json.loads(response.read())

    assert response_dict['success'] is True
    result = response_dict['result']
    pprint.pprint(result)

    ua = 'ckanapiexample/1.0 (+http://example.com/my/website)'

    demo = RemoteCKAN('https://demo.ckan.org', user_agent=ua, get_only=True, apikey='')

    groups = demo.action.group_list(id='data-explorer')
    print(groups)


if __name__ == '__main__':
    extract('https://demo.ckan.org')
