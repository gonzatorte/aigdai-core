from pymongo import MongoClient
import motor.motor_asyncio
client = motor.motor_asyncio.AsyncIOMotorClient()


MONGO_URL = "mongodb://aigdai-user:aigdai-password@localhost:27017/aigdai?authSource=admin"


def get_database_client():
    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    client = MongoClient(MONGO_URL)
    return client['aigdai']

    # db.coso.find({$expr: {$eq: [ {$getField: { $literal: 'a.b'} }, 1]}})
    # db.coso.find({ $expr: { $eq: [{ $arrayElemAt: [{ $getField: { $literal: 'a.b' } }, 1] }, 2] } })
    # db.drepo.aggregate([{$group: {_id: "$softwareName"}}])

    # database = get_database()
    # ff = lambda x: {kk: vv[0] if vv is not None and len(vv) >= 1 else None for (kk,vv) in x.items() if kk != '_id'}
    # instances = list(map(ff, instances))
    # database['drepo'].insert_many(instances)

    # instances = load_from_file()
    # instances = extract_re3data()

    # database = get_database()
    # database['drepo'].insert_many(instances)


def get_database_client_async():
    client2 = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    return client2['aigdai']
