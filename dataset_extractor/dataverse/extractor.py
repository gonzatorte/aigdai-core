import typing
import httpx
import re
from pyDataverse.api import NativeApi, MetricsApi, OperationFailedError
import asyncio
import functools
from requests import ConnectionError, ConnectTimeout
from lib import run_in_parallel
from urllib.parse import urlparse
import re


# def extract(domain_name: str, api_key: str = None):
#     # -e git+https://github.com/IQSS/dataverse-client-python.git@5cdaadc2c3882d6fe23d3cb7cef5280fe83ba909#egg=dataverse
#     from dataverse import Connection
#     connection = Connection(domain_name, api_key)
#     collections = connection.get_dataverses()
#     print(collections[0].alias)
#     collection = connection.get_dataverse('test_123')
#     print(collection.alias, collection.is_published)
#     collection.get_collection_info()
#     collection.get_datasets()
#     dataset = collection.get_dataset_by_title('Enter the title of your paper here')
#     print(dataset.title, dataset.doi)
#     dataset_alias = collection.get_dataset_by_doi(dataset.doi)
#     dataset_metadata = dataset.get_metadata(version='latest', refresh=True)
#     return dataset_metadata['metadataBlocks']

class DataverseDrepo:
    def __init__(self, base_url: str, api_key: str = None):
        self.original_base_url = base_url
        parsed_base_url = urlparse(base_url)
        self.base_url = f'{parsed_base_url.scheme}://{parsed_base_url.hostname}/'
        url_match = re.match('^/dataverse/([^?/]*)', parsed_base_url.path)
        self.root_dataverse = url_match.groups()[0] if url_match is not None else ':root'
        self.api_key = api_key
        self.apiNative = NativeApi(self.base_url.strip('/'), self.api_key)
        self.apiMetrics = MetricsApi(self.base_url.strip('/'), self.api_key)

    async def check_is_up(self):
        async def get_info_version():
            try:
                return (await asyncio.wait_for(asyncio.to_thread(self.apiNative.get_info_version), 20)).json()['data']
            except OperationFailedError as err:
                if str(err.args[0]).startswith('ERROR: GET HTTP 404'):
                    return None
                else:
                    return None
            except asyncio.TimeoutError:
                print(self.original_base_url, 'timed out')
                return None
            except ConnectionError:
                return None
            except BaseException as err:
                raise err

        async def get_info_server():
            try:
                return (await asyncio.wait_for(asyncio.to_thread(self.apiNative.get_info_server), 20)).json()['data']
            except OperationFailedError as err:
                if str(err.args[0]).startswith('ERROR: GET HTTP 404'):
                    return None
                else:
                    return None
            except asyncio.TimeoutError:
                print(self.original_base_url, 'timed out')
                return None
            except ConnectionError:
                return None
            except BaseException as err:
                raise err

        version = await get_info_version()
        server = await get_info_server()
        return version, server

    async def extract(self):
        # self.api.get_info_api_terms_of_use().json()['data']
        # self.api.get_user_api_token_expiration_date()
        # metadata_blocks = api.get_metadatablocks().json()['data']
        # metadata_block = api.get_metadatablock(metadata_blocks[0]['name']).json()['data']

        # ToDo: Falta Available Standard License Terms https://guides.dataverse.org/en/latest/api/native-api.html#manage-available-standard-license-terms
        # ToDo: Falta Getting File Download Count: https://guides.dataverse.org/en/latest/api/native-api.html#getting-file-download-count

        async def get_collection(alias: str):
            return (await asyncio.to_thread(self.apiNative.get_dataverse, alias, None)).json()['data']

        async def get_collection_contents(alias: str):
            return (await asyncio.to_thread(self.apiNative.get_dataverse_contents, alias, False)).json()['data']

        async def get_dataset(alias: str):
            # api.get_datafiles_metadata()
            # api.get_datafile_metadata()
            return (await asyncio.to_thread(self.apiNative.get_dataset, **{'identifier': alias})).json()['data']

        async def walk(start_elem):
            datasets = []
            depth = 0
            start_elem['parent'] = None
            next_level = [start_elem]
            while len(next_level) > 0:
                print('depth', depth, 'wide', len(next_level))
                m_contents = [x async for x in
                              run_in_parallel(
                                  lambda x: get_collection_contents(x['alias'] if 'alias' in x else x['id']),
                                  iter(next_level), 20, 5, lambda x: print(x, 'walked from level'))]
                contents = functools.reduce(
                    lambda ac, x: [*ac, *[{**xx, 'parent': x[1]} for xx in x[0]]], m_contents, []
                )
                next_level = [x for x in contents if x['type'] == 'dataverse']
                datasets.extend(filter(lambda x: x['type'] == 'dataset', contents))
                depth += 1
            return datasets

        root_elem = await get_collection(self.root_dataverse)
        return await walk(root_elem)

    async def metrics(self):
        async def get_datasets_by_subject():
            return (await asyncio.to_thread(self.apiMetrics.get_datasets_by_subject)).json()['data']

        async def get_dataverses_by_subject():
            return (await asyncio.to_thread(self.apiMetrics.get_dataverses_by_subject)).json()['data']

        async def get_dataverses_by_category():
            return (await asyncio.to_thread(self.apiMetrics.get_dataverses_by_category)).json()['data']

        # async def get_datasets_by_data_location(location: str):
        #     return (await asyncio.to_thread(self.apiMetrics.get_datasets_by_data_location, location)).json()['data']

        pp = await asyncio.gather(
            get_datasets_by_subject(),
            get_dataverses_by_subject(),
            get_dataverses_by_category(),
            # get_datasets_by_data_location(),
        )
        return pp
        # self.apiMetrics.past_days('dataverses', 'datasets', 'files' 'downloads')
        # self.apiMetrics.total('dataverses', 'datasets', 'files' 'downloads')

    async def make_data_count(self, persistent_id: str):
        async def fetch_metric(metric_name: str):
            # ToDo: viewsTotal/2019-02
            #  Please note that for each of these endpoints
            #  except the “citations” endpoint,
            #  you can optionally pass the query parameter “country” with a two letter code (e.g. “country=us”) and
            #  you can specify a particular month by adding it in yyyy-mm format after the requested metric (e.g. “viewsTotal/2019-02”).
            metric_response = httpx.get(
                f"{self.base_url}/api/datasets/:persistentId/makeDataCount/{metric_name}?persistentId={persistent_id}",
                timeout=60)
            if not metric_response.is_success:
                raise Exception(f'Metric {metric_name} Error')
            metric_value_json = metric_response.json()
            if metric_value_json['status'] != 'OK':
                raise Exception(f'Metric {metric_name} Error')
            metric_value = metric_value_json['data']['message'] if 'message' in metric_value_json['data'] else \
                metric_value_json['data']
            if type(metric_value) is list:
                if len(metric_value) == 0:
                    metric_value = 0
                elif len(metric_value) == 1:
                    metric_value = metric_value[0]
                else:
                    metric_value = metric_value[0]
            elif type(metric_value) is str and re.match('^No metrics available', metric_value) is not None:
                metric_value = 0
            return metric_name, metric_value

        dimensions = [
            'viewsTotal',
            'viewsUnique',
            'downloadsTotal',
            'downloadsTotalRegular',
            'downloadsTotalMachine',
            'downloadsUnique',
            'downloadsUniqueRegular',
            'downloadsUniqueMachine',
            'citations',
        ]
        results = await asyncio.gather(
            *map(fetch_metric, dimensions)
        )
        return zip(results, dimensions)


if __name__ == '__main__':
    # print(list(asyncio.run(DataverseDrepo('https://demo.dataverse.org').make_data_count('doi:10.70122/FK2/GQLGSU'))))
    # asyncio.run(DataverseDrepo('https://demo.dataverse.org').extract()))
    asyncio.run(DataverseDrepo('https://dataverse.unr.edu.ar').extract())
