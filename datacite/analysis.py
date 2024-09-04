from lib.no_relational_database import get_database_client
import pandas
import itertools
import matplotlib.pyplot as plt
import seaborn

def analysis():
    database = get_database_client()
    collection = database['datacite']
    infos = collection.find(
        {},
        {
            'datacite_graphql_data.datasets.fieldsOfScienceCombined': True,
            'datacite_graphql_data.datasets.totalCount': True,
            'uid': True,
        },
    )

    def reformat(xx):
        return {
            'uid': xx['uid'],
            'subjects': xx['datacite_graphql_data']['datasets']['fieldsOfScienceCombined'],
            'totalCount': xx['datacite_graphql_data']['datasets']['totalCount'],
            # 'subjects': set(xx['datacite_graphql_data.datasets.fieldsOfScience'] + xx['datacite_graphql_data.datasets.fieldsOfScienceCombined'] + xx['datacite_graphql_data.datasets.fieldsOfScienceRepository']),
        }
    repository_info = pandas.DataFrame(map(reformat, infos))
    # ToDo: Hacer matriz de covarianza como las propuesta en el informe
    #  la idea es que eso ayude a detectar correlaciones (ppalmente semánticas) entre atributos
    #   tb relaciones no semánticas pueden verse y usarse para completar información faltante

def counting_analysis():
    database = get_database_client()
    collection = database['datacite']
    collection.aggregate([
        {
            "$project": {
                "name": '$datacite_graphql_data.name',
                "datasetCount": '$datacite_graphql_data.datasets.totalCount',
                "uid": '$uid',
                "_id": False,
            },
        },
        {
            "$sort": {
                "datasetCount": -1,
            },
        }
    ])

def re3data_analysis():
    RE3DATA_PREFIX = 'https://www.re3data.org/repository/'
    database = get_database_client()
    collection = database['datacite']
    urls_count = collection.count_documents({"doi_metadata.attributes.url": {"$exists": True}})
    urls = map(
        lambda x: x['doi_metadata']['attributes']['url'],
        collection.find({"doi_metadata.attributes.url": {"$exists": True}}, {"doi_metadata.attributes.url": True})
    )
    ids = [x[len(RE3DATA_PREFIX):] for x in urls if x.startswith(RE3DATA_PREFIX)]
    print(urls_count, len(ids))
    print(ids)
    # 'https://www.re3data.org/repository/r3d100011372'

def fields_of_science_analysis():
    # Obtener todos los valores posibles de fieldOfScience (y luego ver de mapearlos a frascatti, OECD)

    database = get_database_client()
    collection = database['datacite']
    subject_records = collection.find({}, {
        "datacite_graphql_data.datasets.fieldsOfScience": 1,
        "datacite_graphql_data.datasets.fieldsOfScienceRepository": 1,
        "datacite_graphql_data.datasets.fieldsOfScienceCombined": 1,
    })
    subjects_pairs = set(map(lambda x: (x['id'].lower(), x['title'].lower()), itertools.chain(*[
        itertools.chain(
            x['datacite_graphql_data']['datasets']['fieldsOfScience'],
            x['datacite_graphql_data']['datasets']['fieldsOfScienceRepository'],
            x['datacite_graphql_data']['datasets']['fieldsOfScienceCombined'],
        ) for x in subject_records
    ])))
    subjects_enumerated = list(enumerate(subjects_pairs))
    name_duplicated_subjects = {
        c: len(list(filter(lambda xx: xx[1][0] == c[0] and idx_c != xx[0], subjects_enumerated)))
        for (idx_c, c) in subjects_enumerated
    }
    # Assert que todos tienen 0
    print(name_duplicated_subjects)
    print(subjects_pairs)

    # [('agriculture_forestry_and_fisheries', 'agriculture, forestry, and fisheries'),
    #  ('agriculture_forestry_and_fisheries', 'agriculture, forestry and fisheries')]

    # {('astronomy_including_astrophysics_space_science', 'astronomy (including astrophysics, space science)'),
    #  ('earth_and_related_environmental_science', 'earth and related environmental science'), ('sociology', 'sociology'),
    #  ('chemical_sciences', 'chemical sciences'), ('other_medical_sciences', 'other medical sciences'),
    #  ('arts_arts_history_of_arts_performing_arts_music', 'arts (arts, history of arts, performing arts, music)'),
    #  ('basic_medicine', 'basic medicine'), ('political_science', 'political science'),
    #  ('chemical_engineering', 'chemical engineering'), ('chemical_science', 'chemical science'),
    #  ('physical_sciences', 'physical sciences'), ('environmental_biotechnology', 'environmental biotechnology'),
    #  ('engineering_and_technology', 'engineering and technology'), ('humanities', 'humanities'),
    #  ('earth_and_related_environmental_sciences', 'earth and related environmental sciences'),
    #  ('mechanical_engineering', 'mechanical engineering'), ('law', 'law'),
    #  ('media_and_communications', 'media and communications'),
    #  ('agricultural_biotechnology', 'agricultural biotechnology'), ('nanotechnology', 'nanotechnology'),
    #  ('agriculture_forestry_and_fisheries', 'agriculture, forestry and fisheries'),
    #  ('medical_and_health_sciences', 'medical and health sciences'),
    #  ('industrial_biotechnology', 'industrial biotechnology'),
    #  ('computer_and_information_sciences', 'computer and information sciences'),
    #  ('medical_engineering', 'medical engineering'), ('other_agricultural_sciences', 'other agricultural sciences'),
    #  ('other_agricultural_science', 'other agricultural science'),
    #  ('biological_sciences_fos', 'biological sciences (fos)'), ('conopidae', 'conopidae'),
    #  ('other_engineering_and_technologies', 'other engineering and technologies'),
    #  ('natural_sciences', 'natural sciences'), ('electrical_engineering_electronic_engineering_information_engineering',
    #                                             'electrical engineering, electronic engineering, information engineering'),
    #  ('history_and_archaeology', 'history and archaeology'), ('veterinary_science', 'veterinary science'),
    #  ('health_sciences', 'health sciences'), ('environmental_engineering', 'environmental engineering'),
    #  ('philosophy_ethics_and_religion', 'philosophy, ethics and religion'),
    #  ('veterinary_sciences', 'veterinary sciences'), ('mathematics', 'mathematics'),
    #  ('economics_and_business', 'economics and business'), ('biological_sciences', 'biological sciences'),
    #  ('medical_biotechnology', 'medical biotechnology'), ('clinical_medicine', 'clinical medicine'),
    #  ('health_biotechnology', 'health biotechnology'), ('languages_and_literature', 'languages and literature'),
    #  ('animal_and_dairy_science', 'animal and dairy science'), ('materials_engineering', 'materials engineering'),
    #  ('other_humanities', 'other humanities'), ('chemical_sciences_fos', 'chemical sciences (fos)'),
    #  ('agricultural_sciences', 'agricultural sciences'), ('mechanical_engineering_fos', 'mechanical engineering (fos)'),
    #  ('glace_souterraine', 'glace souterraine'), ('social_sciences', 'social sciences'), ('psychology', 'psychology'),
    #  ('social_and_economic_geography', 'social and economic geography'),
    #  ('agriculture_forestry_fisheries_fos', 'agriculture, forestry, fisheries (fos)'),
    #  ('civil_engineering', 'civil engineering'), ('other_natural_sciences', 'other natural sciences'),
    #  ('educational_sciences', 'educational sciences'), ('nano-technology', 'nano-technology'), ('diptera', 'diptera'),
    #  ('phytoplankton', 'phytoplankton'), ('other_social_sciences', 'other social sciences'),
    #  ('physical_sciences_and_astronomy_fos', 'physical sciences and astronomy (fos)')}

    # aa = collection.aggregate([
    #     {
    #         "$group": {
    #             "_id": None,
    #             "subjects": {
    #                 "$concatArrays": [
    #                     "$datacite_graphql_data.datasets.fieldsOfScience",
    #                     # "$datacite_graphql_data.datasets.fieldsOfScienceRepository",
    #                     # "$datacite_graphql_data.datasets.fieldsOfScienceCombined",
    #                 ],
    #             },
    #         },
    #     },
    #     {
    #         "$addFields": {
    #             "subjects": {
    #                 "$setIntersection": ["$subjects", "$subjects"],
    #             },
    #         },
    #     },
    # ])
    # print(aa)

    # bb = collection.aggregate([
    #     {
    #         "$group": {
    #             "_id": "$uid",
    #         },
    #         "subjects": {
    #             "$concatArrays": [
    #                 "$datacite_graphql_data.datasets.fieldsOfScience",
    #                 "$datacite_graphql_data.datasets.fieldsOfScienceRepository",
    #                 "$datacite_graphql_data.datasets.fieldsOfScienceCombined",
    #             ],
    #         },
    #     },
    #     {
    #         "$addFields": {
    #             "subjects": {
    #                 "$setIntersection": ["$subjects", "$subjects"],
    #             },
    #         },
    #     },
    #     {
    #         "$addFields": {
    #             "sizee": {"$size": '$subjects'},
    #         },
    #     },
    # 	{
    #         "$sort": {
    #             "sizee": -1,
    #         },
    #     },
    # ])

    # Hay alguno donde el combined sea vacio pero los otros no?
    # db.datacite.count(
    # 	{
    # 		$and: [
    # 			{'datacite_graphql_data.datasets.fieldsOfScience.0': {$exists: false}},
    # 			{'datacite_graphql_data.datasets.fieldsOfScienceRepository.0': {$exists: false}},
    # 			{'datacite_graphql_data.datasets.fieldsOfScienceCombined.0':{$exists: true}}
    # 		]
    # 	}
    # )

    # Esto se podria hacer con un project mejor...
    # db.datacite.aggregate([
    #     {
    #         $group: {
    #             _id: "$uid",
    #             name: {
    #                 $first: '$datacite_graphql_data.name'
    #             },
    #             aa: {
    #                 $avg: '$datacite_graphql_data.datasets.totalCount'
    #             }
    #         }
    #     },
    #     {$sort: {aa: -1}},
    #     {$limit: 100},
    # ]).toArray()


    # mirar las facetas de certificates, years, repositoryTypes, software, etc
    # que son los members?


if __name__ == '__main__':
    # analysis()
    # fields_of_science_analysis()
    re3data_analysis()
    # async def run():
    #     await main()
    # asyncio.run(run())
