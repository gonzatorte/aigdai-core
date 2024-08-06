# from re3data.extractor import load_from_file, extract as extract_re3data
from dataset_extractor.dataverse.probe import probe as probe_dataverse
from dataset_extractor.dataverse.extractor import DataverseDrepo
# from ckan.probe import probe as probe_ckan
# from ckan.extractor import extract as extract_ckan
import asyncio

from lib import run_in_parallel
from lib.no_relational_database import get_database_client


async def extract_all(known_instances, drepo_dataverse_collection, dataset_collection):
    probed_instances = list(drepo_dataverse_collection.find({}, {'instanceId': 1, 'info': 1}))
    up_probed_instances = [str(x['instanceId']) for x in probed_instances if x['info'] is not None]

    probed_instances = [str(x['instanceId']) for x in probed_instances]
    not_probed_instances = [(x, DataverseDrepo(x['repositoryURL'][0])) for x in known_instances if
                            str(x['_id']) not in probed_instances]

    extracted_instances = list(dataset_collection.aggregate([{'$group': {'_id': '$instanceId'}}]))
    extracted_instances = [str(x['_id']) for x in extracted_instances]

    to_extract_instances = [(x, DataverseDrepo(x['repositoryURL'][0])) for x in known_instances if
                            str(x['_id']) not in extracted_instances and str(x['_id']) not in up_probed_instances]

    async def get_info_from_api(xx):
        api: DataverseDrepo = xx[1]
        info = await api.check_is_up()
        if info is None:
            return None, None
        metrics = None
        # metrics = await api.metrics()
        return info, metrics

    async for ((info_from_instance, metrics_from_instance), (known_instance, _)) in run_in_parallel(
            get_info_from_api,
            iter(not_probed_instances), 5, 0, lambda x: print('info from repos', x), lambda x: print('error from', x)):
        drepo_dataverse_collection.update_one(
            {'instanceId': known_instance['_id']},
            {'$set': {'metrics': metrics_from_instance, 'info': info_from_instance}},
            upsert=True,
        )

    async for (datasets_from_instance, (known_instance, _)) in run_in_parallel(
            lambda x: x[1].extract(),
            iter(to_extract_instances), 5, 0, lambda x: print('extracted from repos', x),
            lambda x: print('error from', x)):
        dataset_collection.insert_many([{**x, 'instanceId': known_instance['_id']} for x in datasets_from_instance])


async def probe_all(unknown_instances):
    found = []
    async for (dataverse_probe_result, unknown_instance) in run_in_parallel(
            lambda x: probe_dataverse(x['repositoryURL']),
            unknown_instances, 10):
        if dataverse_probe_result is None:
            print("%s probe failed" % unknown_instance['re3data.orgidentifier'])
        elif dataverse_probe_result:
            print("%s is dataverse" % unknown_instance['re3data.orgidentifier'])
            found.append({'software': 'dataverse', 'instance': unknown_instance})
            # extract_dataverse(unknown_instance)
        else:
            print("%s NOT is dataverse" % unknown_instance['re3data.orgidentifier'])

        # if probe_ckan(unknown_instance):
        #     extract_ckan(unknown_instance)

    return found


async def main():
    database = get_database_client()
    # database['drepo'].insert_many(instances)
    instances = database['drepo'].find()
    dataset_collection = database['dataset']
    drepo_dataverse_collection = database['drepo_dataverse']
    accessible_instances = list(filter(
        lambda x: x['repositoryURL'] is not None,
        instances
    ))
    unknown_instances = filter(
        lambda x: len(x['softwareNames']) != 0 and x['softwareNames'][0] in [None, "unknown", "other"],
        accessible_instances
    )
    known_instances = list(filter(
        lambda x: len(x['softwareNames']) != 0 and x['softwareNames'][0] is not None and x['softwareNames'][
            0].lower() == "dataverse",
        accessible_instances
    ))

    await extract_all(known_instances, drepo_dataverse_collection, dataset_collection)
    # probed_instances = await probe_all(unknown_instances)
    # await extract_all(probed_instances, dataset_collection)


if __name__ == '__main__':
    asyncio.run(main())
