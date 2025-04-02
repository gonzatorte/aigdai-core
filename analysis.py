from lib.no_relational_database import get_database_client
import pandas
import itertools
import datetime
import re

from onto.cts import dfg_subjects


# import matplotlib.pyplot as plt
# import seaborn

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

def re3data_dataproviders():
    # Cuantos son al menos data providers y cuantos directamente no declaran nada?
    database = get_database_client()
    collection = database['drepo']
    not_declared = collection.count_documents({'providerType.0': {'$exists': False}}) # 5
    data_providers = collection.count_documents({'providerType': 'dataProvider'}) # ~3000
    print(not_declared, data_providers)

def re3data_doi():
    # Cuantos usan DOI y cuantos usan DOI junto con otro sistema de identificadores?
    database = get_database_client()
    collection = database['drepo']
    not_declared = collection.count_documents({'pidSystems.0': {'$exists': False}}) # ~500
    uses_only_doi = collection.count_documents({'$and': [
        {'pidSystems': {'$all': ['DOI']}},
        {'pidSystems': {'$size': 1}},
    ]}) # ~847

    uses_at_least_doi = collection.count_documents({'pidSystems': 'DOI'}) # ~1500
    print(not_declared, uses_at_least_doi, uses_only_doi)

def re3data_certificated():
    # Cuantos tienen certificados?
    database = get_database_client()
    re3data_coll = database['drepo']

    qa_yes = re3data_coll.count_documents({'qualityManagement': True}) # 1704
    qa_no = re3data_coll.count_documents({'qualityManagement': False}) # 53
    qa_undeclared = re3data_coll.count_documents({'qualityManagement': None}) # 1439
    print(qa_yes, qa_no, qa_undeclared)

    # Correlacion QA y certificacion?

    not_or_none_declared = re3data_coll.count_documents({'certificates.0': {'$exists': False}}) # ~2923
    not_declared = re3data_coll.count_documents({'certificates': {'$exists': False}}) # ~40
    # cuantos tienen solo other?
    only_other = re3data_coll.count_documents({'$and': [
        {'certificates': {'$all': ['other']}},
        {'certificates': {'$size': 1}},
    ]}) # ~124
    # cuantos tienen uno que sea other?
    some_but_other = re3data_coll.count_documents({'certificates': 'other'}) # ~168
    # cuantos tienen uno que no sea other?
    some_but_not_other = re3data_coll.count_documents({"certificates.0": {'$exists': True}, "certificates": {'$ne': 'other'}}) # ~105
    print(not_or_none_declared, not_declared, only_other, some_but_other, some_but_not_other)

    all_certs = re3data_coll.find({'certificates.0': {'$exists': True}}, {'certificates': True})
    all_possible_certs = set(sum([[y.lower() for y in x['certificates']] for x in all_certs], []))
    print(all_possible_certs)
    #  'clarin certificate b',
    #  'din 31644',
    #  'dini certificate',
    #  'dsa',
    #  'iso 16363',
    #  'other',
    #  'ratswd',
    #  'trusted digital repository',
    #  'wds',

def re3data_openness():
    # cuantos se los puede considerar abiertos?
    database = get_database_client()
    re3data_coll = database['drepo']

    # tienen al menos un access de tipo open (en database o data)
    no_access_declared = re3data_coll.count_documents({'$and': [{'dataAccess.0': {'$exists': False}}, {'databaseAccess': {'$exists': False}}]})
    print(no_access_declared) # 4
    no_database_access_declared = re3data_coll.count_documents({'$and': [{'databaseAccess': {'$exists': False}}]})
    print(no_database_access_declared) # 0
    no_open_data_access_declared = re3data_coll.count_documents({'$and': [{'dataAccess.0': {'$exists': False}}]})
    print(no_open_data_access_declared) # 0

    # data open implica database open
    open_access = re3data_coll.count_documents({'$and': [{'dataAccess': {'$elemMatch': {'type': 'open'}}}]})
    print(open_access) # 2724
    only_open_access = re3data_coll.count_documents({'dataAccess': {'$size': 1, '$elemMatch': {'type': 'open'}}})
    print(only_open_access) # 1452

    # Ver si el estado CLOSED se relacion más a que el servidor esté offline en vez de los temas de permisos
    re3data_coll.count_documents({'databaseAccess.type': 'closed'})  # 22
    re3data_coll.count_documents({'databaseAccess.type': 'restricted'})  # 161

    # Verificacion de consistencia de datos
    re3data_coll.count_documents({'dataAccess': {'$elemMatch': {'type': 'open', 'restriction.0': {'$exists': True}}}}) # 5
    re3data_coll.count_documents({'dataAccess': {'$size': 1, '$elemMatch': {'type': 'open', 'restriction.0': {'$exists': True}}}}) # 1
    re3data_coll.count_documents({'databaseAccess.type': 'open', 'databaseAccess.restriction.0': {'$exists': True}}) # 3
    re3data_coll.count_documents({'dataAccess': {'$elemMatch': {'type': 'restricted', 'restriction.0': {'$exists': False}}}}) # 18
    re3data_coll.count_documents({'databaseAccess.type': 'restricted', 'databaseAccess.restriction.0': {'$exists': False}}) # 2
    re3data_coll.count_documents({'dataAccess': {'$elemMatch': {'type': 'closed', 'restriction.0': {'$exists': True}}}})  # 7
    re3data_coll.count_documents({'databaseAccess.type': 'closed', 'databaseAccess.restriction.0': {'$exists': True}})  # 0

    fee_required = re3data_coll.count_documents({'dataAccess.restriction': 'feerequired'})
    print(fee_required) # 224

def re3data_licences():
    # cuantos se los puede considerar abiertos?
    database = get_database_client()
    re3data_coll = database['drepo']

    # no tienen informacion de licencia (ni en database ni data)
    no_licence_info = re3data_coll.count_documents({'$and': [{'databaseLicense.0': {'$exists': False}}, {'dataLicense.0': {'$exists': False}}]})
    print(no_licence_info) # 54
    no_db_licence_info = re3data_coll.count_documents({'$and': [{'databaseLicense.0': {'$exists': False}}]})
    print(no_db_licence_info) # 2566
    no_data_licence_info = re3data_coll.count_documents({'$and': [{'dataLicense.0': {'$exists': False}}]})
    print(no_data_licence_info) # 55

    # sacar todos los enumerados posibles de licence (tomando el name lowercase o la url)
    record_w_licence_info = list(re3data_coll.find({}, {'databaseLicense': True, 'dataLicense': True, 'idd': True}))
    record_w_licence_info_normalized = [
        [y['name'].lower() for y in x.get('databaseLicense', [])] + [y['name'].lower() for y in
                                                                     x.get('dataLicense', [])]
        for x in record_w_licence_info
    ]
    all_possible_licences = set(sum(record_w_licence_info_normalized, []))
    print(all_possible_licences)
    #     ToDo: Se puede normalizar a nivel de datos los valores obtenidos
    #  'apache license 2.0',
    #  'bsd',
    #  'cc',
    #  'cc0',
    #  'copyrights',
    #  'none',
    #  'odc',
    #  'ogl',
    #  'oglc',
    #  'other',
    #  'public domain',
    #  'rl',
    # tienen al menos una licencia abierta aceptada (en data o database)
    open_licences = {
        'apache license 2.0',
        'bsd',
        'cc', # creative common
        'cc0', # creative common 0
        'odc', # open data commons
        'ogl', # open government commons
        'oglc', # open government commons CANADA?
        'public domain', # same as cc0? Or expired licence. Same as CC-PDDC?
        'rl',
    }
    some_open_licence = len(list(filter(lambda x: len(x) != 0 and len(set(x) & open_licences) != 0, record_w_licence_info_normalized)))
    print(some_open_licence) # 1881
    closed_licences = {
        'copyrights',
    }
    some_closed_licence = len(list(filter(lambda x: len(x) != 0 and len(set(x) & closed_licences) != 0, record_w_licence_info_normalized)))
    print(some_closed_licence) # 1339
    only_closed_licence = len(list(filter(lambda x: set(x) == closed_licences, record_w_licence_info_normalized)))
    print(only_closed_licence) # 557
    no_licences = {
         'none',
    }
    no_licence = len(list(filter(lambda x: len(x) != 0 and len(set(x) & no_licences) != 0, record_w_licence_info_normalized)))
    print(no_licence) # 0

    no_info_licences = {
         'other',
    }
    non_determinant_licence = len(list(filter(lambda x: len(x) != 0 and len(set(x) & no_info_licences) != 0, record_w_licence_info_normalized)))
    print(non_determinant_licence) # 1181
    record_w_other_licence = list(re3data_coll.find({'$or': [{'databaseLicense.name': 'other'}, {'dataLicense.name': 'other'}]}, {'databaseLicense.url': True, 'dataLicense.url': True}))
    record_w_other_licence_normalized = [
        [y['url'].lower() for y in x.get('databaseLicense', [])] + [y['url'].lower() for y in
                                                                     x.get('dataLicense', [])]
        for x in record_w_other_licence
    ]
    other_licences = set(sum(record_w_other_licence_normalized, []))
    spdx_licences = [ll for ll in other_licences if 'spdx' in ll]
    print(spdx_licences)
    # [ll for ll in other_licences if 'wiki' in ll]
    # [ll for ll in other_licences if 'gnu' in ll]
    # [ll for ll in other_licences if 'apache' in ll]
    # [ll for ll in other_licences if 'odbl' in ll]
    # [ll for ll in other_licences if 'mit' in ll]
    # [ll for ll in other_licences if 'bsd' in ll]
    # [ll for ll in other_licences if 'gpl' in ll]
    # [ll for ll in other_licences if 'opendatacommons' in ll]
    # [ll for ll in other_licences if 'opendefinition' in ll]
    # [ll for ll in other_licences if 'creativecommons' in ll]

def re3data_metadata_standards():
    # cuales son los posibles enumerados de metadataStandards?
    database = get_database_client()
    collection = database['drepo']
    count_w_metadata_standards = collection.count_documents({'metadataStandards.0': {'$exists': True}})
    print(count_w_metadata_standards) # 1308
    record_metadata_standard = list(collection.find({}, {'metadataStandards': True}))
    metadata_standards = set(sum([
        [y['name'].lower() for y in x.get('metadataStandards', [])]
        for x in record_metadata_standard
    ], []))
    # ToDo: Documentar que el catalogo parece provenir de https://www.dcc.ac.uk/guidance/standards/metadata
    # ToDo: Agregar a este tipo de cosas, el conteo de cuantas veces aparece y el conteo de cuantos repositorios tienen el valor...
    # {'abcd - access to biological collection data',
    #  'avm - astronomy visualization metadata',
    #  'cf (climate and forecast) metadata conventions',
    #  'cif - crystallographic information framework',
    #  'cim - common information model',
    #  'csmd-cclrc core scientific metadata model',
    #  'darwin core',
    #  'datacite metadata schema',
    #  'dcat - data catalog vocabulary',
    #  'ddi - data documentation initiative',
    #  'dif - directory interchange format',
    #  'dublin core',
    #  'eml - ecological metadata language',
    #  'fgdc/csdgm - federal geographic data committee content standard for digital geospatial metadata',
    #  'fits - flexible image transport system',
    #  'genome metadata',
    #  'international virtual observatory alliance technical specifications',
    #  'isa-tab',
    #  'iso 19115',
    #  'mibbi - minimum information for biological and biomedical investigations',
    #  'midas-heritage',
    #  'oai-ore - open archives initiative object reuse and exchange',
    #  'other',
    #  'prov',
    #  'qudex - qualitative data exchange format',
    #  'rdf data cube vocabulary',
    #  'repository-developed metadata schemas',
    #  'sdmx - statistical data and metadata exchange',
    #  'spase data model'}
    print(len(metadata_standards)) # 29
    record_w_other_metadata_standard = collection.count_documents({'metadataStandards.name': 'other'})
    print(record_w_other_metadata_standard) # 15
    record_w_other2_metadata_standard = collection.count_documents({'metadataStandards.name': 'repository-developed metadata schemas'})
    print(record_w_other2_metadata_standard) # 217

def re3data_keywords():
    # cuales son los posibles enumerados de keywords?
    database = get_database_client()
    collection = database['drepo']
    count_w_keywords = collection.count_documents({'keywords.0': {'$exists': True}})
    # cuantas keywords suele tener un repositorio? Demasiadas keywords dejan de ser realmente de ayuda...
    print(count_w_keywords) # 3149
    count_w_keywords = list(collection.aggregate([{'$match': {'keywords': {'$exists': True}}}, {'$addFields': {'ks': {'$size': '$keywords'}}}, {'$group': {'_id': '$idd', 'kc': {'$sum': '$ks'}}}, {'$sort': {'kc': 1}}]))
    record_keyword = list(collection.find({}, {'keywords': True}))
    keywords = set(sum([
        x.get('keywords', []) for x in record_keyword
    ], []))
    print(len(keywords)) # 10756

def re3data_institutions():
    # cuales son los posibles enumerados de responsibilityType?
    database = get_database_client()
    collection = database['drepo']
    count_w_institutions = collection.count_documents({'institutions.0': {'$exists': True}})
    print(count_w_institutions)
    responsibility_types_arr = list(collection.find({}, {'institutions.responsibilityType': True, 'institutions.institutionType': True}))
    responsibility_types = set(sum([
        sum([
            xx.get('responsibilityType', []) for xx in x['institutions']
        ], []) for x in responsibility_types_arr
    ], []))
    print(responsibility_types)
    institution_types = set(sum([
        [
            xx['institutionType'] for xx in x['institutions']
        ] for x in responsibility_types_arr
    ], []))
    print(institution_types)

def re3data_policies():
    # cuales son los posibles enumerados de politicas?
    database = get_database_client()
    collection = database['drepo']
    count_w_metadata_policies = collection.count_documents({'policies.0': {'$exists': True}})
    print(count_w_metadata_policies) # 2824
    record_metadata_standard = list(collection.find({}, {'policies': True}))
    policies = set(sum([
        [y['name'].lower() for y in x.get('policies', [])]
        for x in record_metadata_standard
    ], []))
    print(len(policies)) # 3098 (vs 5149 sin repetir, el indice de reutilizacion es bajo)

def re3data_software():
    # cuantos de los repositorios tienen 1 solo software NO other?
    database = get_database_client()
    collection = database['drepo']
    count_w_softwares = collection.count_documents({'softwareNames.0': {'$exists': True}})
    print(count_w_softwares) # 2457
    record_software = list(collection.find({}, {'softwareNames': True}))
    aa = pandas.DataFrame(record_software)
    softwares = set(sum([
        x.get('softwareNames', []) for x in record_software
    ], []))
    print(len(softwares)) # 13
    count_w_no_other_softwares = collection.count_documents({'$and': [{'softwareNames.0': {'$exists': True}}, {'softwareNames.1': {'$exists': False}}]})
    print(len(count_w_no_other_softwares)) # 2430

    only_known_softwares = collection.count_documents({'$and': [{'softwareNames.0': {'$exists': True}}, {'softwareNames': {'$ne': 'other'}}, {'softwareNames': {'$ne': 'unknown'}}]})
    print(only_known_softwares) # 604

    all_w_softwares = list(collection.find({'softwareNames.0': {'$exists': True}}, {'softwareNames': True}))
    all_w_known_softwares = [
        [xx for xx in x.get('softwareNames', []) if xx not in ['unknown']] for x in all_w_softwares
    ]
    all_w_single_known_softwares = [
        x for x in all_w_known_softwares if len(x) == 1
    ]
    print(len(all_w_single_known_softwares)) # 1828

def record_is_still_up():
    # ToDo: cuantos de los repositorios siguen activos o vivos?
    #  usar endDate
    #  verificaciones del dominio si sigue vivo pueden ser suficiente (consultar los DNS server directamente, nslookup)
    #  mirar la cantidad de datasets publicados (o actualizados) en el último tiempo). Ojo que quizás no usan DOI y no son indexados
    pass

def record_is_accessible():
    # ToDo: cuantos repositorios (además de ser abiertos) prestan APIs para su integracion, tienen softwares conocidos y/o son abiertos?
    #  la palabra accessible quizas es adecuada puesto que requiere de ser eliminar barreras legales, técnicas y documentales/estandarizacion
    #  hay que refinar algunos filtros anteriores aqui
    database = get_database_client()
    re3data_coll = database['drepo']
    apis = re3data_coll.find({'apis.0': {'$exists': True}})
    api_types_by_repo = [
        [y['type'] for y in x['apis']] for x in apis
    ]
    api_types = set(sum(api_types_by_repo, []))
    print(api_types)
    # acorde a lo declarado, son todos estos los tipos
    # {'ftp',
    #  'netcdf',
    #  'oai-pmh',
    #  'opendap',
    #  'other',
    #  'rest',
    #  'soap',
    #  'sparql',
    #  'sword'}
    re3data_coll.count_documents({'apis.0': {'$exists': True}})
    re3data_coll.count_documents({'apis.1': {'$exists': True}})
    re3data_coll.count_documents({'apis.type': 'other'})

    dd = re3data_coll.find({'apiType': {'$exists': True}})
    pandas.DataFrame(dd)
    # ToDo: Ver cuantos tienen varias APIs declaradas
    #   y cuales tienen dos donde una de ellas es other
    # ToDo: Ver cuantos comparten las URLs

    datacite_coll = database['datacite']
    datacite_only_service_providers = datacite_coll.count_documents({'$and': [
        {'datacite_graphql_data.providerType': {'$all': ['serviceProvider']}},
        {'datacite_graphql_data.providerType': {'$size': 1}},
    ]})

def record_is_visible():
    pass

def record_is_plural():
    # ToDo: Medir la variedad de articulos publicados, ya sea solo considerando los contenedores de datos en comun (para no contar las diferentes
    #  partes de un mismo estudio repetidas veces) o los clusters de autores sin relaciones demasiado fuertes
    pass

def record_is_multidisciplinar():
    # ToDo: Medir la cantidad de estudios que abordan varias disciplinas al mismo tiempo, o aquellos que al contrario,
    #  albergan varios estudios de diferentes disciplinas pero cada estudio no se mezcla disciplinas.
    #  Quizas ver la correlación de ambas cosas con la disciplinaridad y las disciplinas declaradas
    #  eg: puede ser disciplinar pero definir educación y medicina, lo que significa que, para cada disciplina, no se mezclan sus estudios.
    #  Ver si las disciplinas en si mismo deberian poder tener más de 1 padre (eg: bioinformatica, pertenece a bio o a informatica según DFG o OECD?).
    pass

def intitutional_vs_disciplinar():
    # ToDo: ver que relacion hay entre disciplinar e intitucional y cuan disjuntos son ambos conceptos
    pass

def interop_score_between(repo1: str, repo2: str) -> int:
    pass


RE3DATA_PREFIX = 'https://www.re3data.org/repository/'


def extract_re3data_id(re3data_url: str) -> str | None:
    return re3data_url[len(RE3DATA_PREFIX):] if re3data_url.startswith(RE3DATA_PREFIX) else None

def compose_re3data_url(re3data_id: str) -> str:
    return "%s%s" % (RE3DATA_PREFIX, re3data_id,)

def datacite_re3data_integration_analysis():
    database = get_database_client()
    collection = database['datacite']
    urls_count = collection.count_documents({"doi_metadata.attributes.url": {"$exists": True}})
    urls = map(
        lambda x: (x['uid'], x['doi_metadata']['attributes']['url']),
        collection.find({"doi_metadata.attributes.url": {"$exists": True}}, {"doi_metadata.attributes.url": True, "uid": True})
    )
    ids = [(x[0], extract_re3data_id(x[1])) for x in urls if extract_re3data_id(x[1]) is not None]
    print(urls_count, len(ids))
    print(ids)
    # En realidad la culpa de que no tengan el DOI en la api de re3data es de re3data, pues ellos figuran como el publisher de ese DOI...
    # ToDo: Comparar el fieldOfScience con el subject del repositorio?
#     collection.find_one({'uid': ids[6][0]})['datacite_graphql_data']['subject']
#     collection2 = database['drepo']
#     collection2.find_one({'idd': ids[6][1]})['subjects']

def fields_of_science_analysis_part2():
    # Ver si los disciplinarios tienen pocas disciplinas y si en cambio los institucionales tienen muchas...?
    # Corroborar que las disciplinas de re3data se mapean a fieldOfScienceRepository
    # los datasets solo pueden pertener a 1 disciplina? En ese caso, el conteo de datasets debería ser menor que la suma de cada categoría
    #   o hay datasets que NO tienen declarada disciplina
    pass

def fields_of_science_analysis():
    # Obtener todos los valores posibles de fieldOfScience (y luego ver de mapearlos a frascatti/OECD)

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

def known_repos():
    database = get_database_client()
    datacite_coll = database['datacite']
    re3data_coll = database['drepo']

    def compare_data_sources(datacite_uid: str):
        datacite_record = datacite_coll.find_one({'uid': datacite_uid})
        subjects1 = set([x['termCode'] for x in datacite_record['datacite_graphql_data']['subject']])
        url_re3data = (datacite_record.get('doi_metadata', {}) or {}).get('attributes', {}).get('url', None)
        id_re3data = url_re3data and extract_re3data_id(url_re3data)
        if not id_re3data:
            print('not found on re3data')
            return
        re3data_record = re3data_coll.find_one({'idd': id_re3data})
        subjects2 = set(re3data_record['subjects'])
        print(subjects1.intersection(subjects2), subjects1.difference(subjects2), subjects2.difference(subjects1))

    id_datacite_unr = '9z2c8d3' # re3data = 'r3d100013960'
    id_datacite_lattes = '51qc79x' # re3data not found

    id_datacite_redata = 'r3d100014380' # aun no indexado por datacite?

    compare_data_sources(id_datacite_unr)
    compare_data_sources(id_datacite_lattes)

def service_providers_dont_declare_contentes():
    database = get_database_client()
    datacite_coll = database['datacite']
    re3data_coll = database['drepo']

    datacite_only_service_providers = datacite_coll.count_documents({'$and': [
        {'datacite_graphql_data.providerType': {'$all': ['serviceProvider']}},
        {'datacite_graphql_data.providerType': {'$size': 1}},
    ]})
    print(datacite_only_service_providers) # 172
    re3data_only_service_providers = re3data_coll.count_documents({'isDataProvider': False, 'isServiceProvider': True})
    print(re3data_only_service_providers) # 255

    a = [x['repositoryName'] for x in re3data_coll.find({'isDataProvider': False, 'isServiceProvider': True}) if x['published']]

    aa = [x['datacite_graphql_data'] for x in datacite_coll.find({'$and': [
        {'datacite_graphql_data.providerType': {'$all': ['serviceProvider']}},
        {'datacite_graphql_data.providerType': {'$size': 1}},
    ]})]
    aaa = [(x['name'] if ('name' in x) else (x['alternateName'][0] if len(x['alternateName']) > 0 else None), x['datasets']['published'][-1:][0]['count'] if len(x['datasets']['published'][-1:]) > 0 else None) for x in aa]
    aaaa = [x for x in aaa if x[1] is not None and x[1] > 0]
    print(aaaa) # 18

    # fairsharing_re3data_id = 'r3d100010142'
    # fairsharing_datacite_id = '8orc2q6'
    # fairsharing_datacite_id_2 = 'l4ycr1l'
    # datacite_coll.find_one({'re3dataUrl': compose_re3data_url(fairsharing_re3data_id)})
    # datacite_coll.find_one({'uid': fairsharing_datacite_id})
    # datacite_coll.find_one({'uid': fairsharing_datacite_id_2})

def fairsharing_enums():
    database = get_database_client()
    fairsharing = database['fairsharing']
    records = list(fairsharing.find({}))
    record_types_list = [y['record_type'] for y in records]
    record_types_set = set(record_types_list)
    #  {'collection',
    #  'funder',
    #  'identifier_schema',
    #  'institution',
    #  'journal',
    #  'journal_publisher',
    #  'knowledgebase',
    #  'knowledgebase_and_repository',
    #  'metric',
    #  'model_and_format',
    #  'project',
    #  'reporting_guideline',
    #  'repository',
    #  'society',
    #  'terminology_artefact'}
    repos_count = fairsharing.count_documents({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}})
    print(repos_count) # 1337
    # legacy_ids_records = fairsharing.count_documents({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}, 'legacy_ids.0': {'$exists': True}})
    # print(repos_count) # 1337
    with_doi = fairsharing.count_documents({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}, 'doi': {'$ne': None}})
    print(with_doi) # 1212
    with_cross_ref = fairsharing.count_documents({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}, 'metadata.cross_references.0': {'$exists': True}})
    print(with_cross_ref) # 688

    with_cross_ref_portal = list(fairsharing.find({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}, 'metadata.cross_references.0': {'$exists': True}}))
    with_cross_ref_portal_normalized = [
        [y['portal'] for y in x['metadata']['cross_references']] for x in with_cross_ref_portal
    ]
    portals = set(sum(with_cross_ref_portal_normalized, []))
    print(portals)
    # {'BioPortal', 'Other', 'SciCrunch', 're3data'}
    with_re3data_cross_refs = fairsharing.count_documents({'record_type': {'$in': ['knowledgebase_and_repository', 'repository']}, 'metadata.cross_references.portal': 're3data'})
    print(with_re3data_cross_refs) # 685

    # revisar cuantos estan activos. Ver el status, deprecation_reason, deprecation_date, tombstone, resource_sustainability
    deprecated_repos = fairsharing.count_documents({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        'metadata.status': 'deprecated',
    })
    print(deprecated_repos) # 201
    active_but_not_updated_repos = list(fairsharing.find({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        'metadata.status': {'$ne': 'deprecated'},
        # 'updated_at': {'$expr': { '$gt': [
        #     {
        #         '$dateFromString': {
        #             'dateString': "$updated_at"
        #         },
        #     },
        #     {
        #         '$dateFromString': {
        #             'dateString': "2017-02-08T12:10:40.787",
        #         },
        #     },
        # ]}},
    }))
    dd = [
        {
            'id': x['id'],
            'year': datetime.datetime.fromisoformat(x['updated_at'][0:-1]).year,
        } for x in active_but_not_updated_repos
    ]
    aa = pandas.DataFrame(dd)
    print(aa.groupby('year').count())
    # print(aa['year'].value_counts())
    #        id
    # year
    # 2021    1
    # 2022    1
    # 2023  611
    # 2024  523

    active_repos = fairsharing.count_documents({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        'metadata.status': 'ready',
    })
    print(active_repos) # 1111

    # revisar cuantos son abiertos, o sea, cuantos tienen en data_access_condition o data_deposition_condition el valor controlled?
    no_open_access_repos = fairsharing.count_documents({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        'metadata.data_access_condition.type': 'controlled',
    })
    print(no_open_access_repos) # 88
    no_open_upload_repos = fairsharing.count_documents({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        'metadata.data_deposition_condition.type': 'controlled',
    })
    print(no_open_upload_repos) # 388

    # revisar cuantos son de educacion
    # fairsharing.count_documents({'doi_data.attributes.subjects': {'$exists': False}})
    education_subjects = ['Education Science', 'Applied Linguistics', 'Educational Psychologyncit', 'Professional Socialization', 'Research on Teaching, Learning and Training']
    education_count = fairsharing.find({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        # 'doi_data.attributes.subjects': {'$exists': False},
        'subjects': {'$in': education_subjects},
        'metadata.certifications_and_community_badges.0': {'$exists': True}
    })
    print(education_count) # 17
    # revisar tambien los multidisciplinarios
    education_records = list(fairsharing.find({
        'record_type': {'$in': ['knowledgebase_and_repository', 'repository']},
        # 'doi_data.attributes.subjects': {'$exists': False},
        'subjects': {'$in': education_subjects},
        'metadata.status': {'$ne': 'deprecated'},
    }))
    print([(x['metadata']['name'], x['metadata']['status'], x['countries']) for x in education_records])

    # revisar cuantos estan certificados
    bb = [
        {'id': x['id'], 'certs': [re.sub(r"\s+", "", y['name'].lower()).strip() for y in x['metadata']['certifications_and_community_badges']]}
        # [re.sub(r"\s+", " ", y['name'].lower()).strip() for y in x['metadata']['certifications_and_community_badges']]
        for x in fairsharing.find({'metadata.certifications_and_community_badges.0': {'$exists': True}})
    ]
    print(len(bb)) # 32
    yy = [['coretrustseal' if y.startswith('coretrustseal') else y for y in x['certs']] for x in bb]
    certs = set(sum(yy, []))
    tt = [{'id': x['id'], 'hascore': any([y.startswith('coretrustseal') for y in x['certs']])} for x in bb]
    cc = pandas.DataFrame(tt)
    print(cc.groupby('hascore').count())
    #          id
    # hascore
    # False     7
    # True     25


def re3data_size_and_subject():
    database = get_database_client()
    datacite = database['datacite']
    datacite.count_documents(
        {
            'datacite_graphql_data.datasets.fieldsOfScienceCombined.9': {'$exists': True},
            'datacite_graphql_data.datasets.fieldsOfScienceCombined.9.count': {'$gt': 10},
        },
    )


def re3data_cs_soc():
    database = get_database_client()
    re3data = database['drepo']
    datacite = database['datacite']
    datacite.count_documents(
        {
            'datacite_graphql_data.datasets.fieldsOfScienceCombined.9': {'$exists': True},
            'datacite_graphql_data.datasets.fieldsOfScienceCombined.9.count': {'$gt': 10},
        },
    )
    datacite.count_documents({'datacite_graphql_data.subject.termCode': re.compile('^1')})
    re3data.count_documents({'subjects': re.compile('^1')})
    sizes = [x['size'] for x in re3data.find({'subjects': re.compile('^1'), 'size': {'$exists': True, '$ne': None}}, {'size': True})]
    sizes = [x for x in sizes if re.match('^[0-9]', x)]
    [(x[0], x[2]) for x in dfg_subjects]


if __name__ == '__main__':
    re3data_institutions()
    # service_providers_dont_declare_contentes()
    # analysis()
    # fields_of_science_analysis()
    # async def run():
    #     await main()
    # asyncio.run(run())
