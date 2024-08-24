from lib.no_relational_database import get_database_client
import pandas
import matplotlib.pyplot as plt
import seaborn


def analysis():
    database = get_database_client()
    collection = database['datacite']
    infos = collection.find()
    def reformat(xx):
        return {
            'uid': xx['uid'],
            'subjects': xx['datacite_graphql_data.datasets.fieldsOfScienceCombined'],
            # 'subjects': set(xx['datacite_graphql_data.datasets.fieldsOfScience'] + xx['datacite_graphql_data.datasets.fieldsOfScienceCombined'] + xx['datacite_graphql_data.datasets.fieldsOfScienceRepository']),
        }
    repository_info = pandas.DataFrame(map(reformat, infos))

if __name__ == '__main__':
    analysis()
    # async def run():
    #     await main()
    # asyncio.run(run())
