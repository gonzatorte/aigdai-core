import re
from re3data.extract_from_repo import BLACKLIST
import onto.cts as cts
from lib.no_relational_database import get_database_client
from re3data.xsd_transform import refine_repository_info, load_schema
from rdflib import Graph, Literal, URIRef, Namespace
from rdflib.namespace import RDF

my_ns = Namespace('http://test.org#')
Organizacion = URIRef("#organizacion", my_ns)
# Organizacion = my_ns.organizacion
Repositorio = URIRef("#repositorio", my_ns)
Pais = URIRef("#pais", my_ns)
BloqueComercial = URIRef("#bloque_comercial", my_ns)
Locacion = URIRef("#locacion", my_ns)
dfg_subject_ns = Namespace('http://dfgsubjects.org#')
Disciplina = URIRef("#disciplina", dfg_subject_ns)
es_sub_disciplina_de = URIRef("#es_sub_disciplina_de", dfg_subject_ns)
esquema_de_disciplina = URIRef("#esquema_de_disciplina", dfg_subject_ns)
nombre_de_disciplina = URIRef("#nombre_de_disciplina", dfg_subject_ns)
MotorDeRepositorio = URIRef("#motor_de_repositorio", my_ns)
Certificacion = URIRef("#certificacion", my_ns)
utiliza_motor = URIRef('#utiliza_motor', my_ns)
repositorio_afin_a_disciplina = URIRef('#repositorio_afin_a_disciplina', my_ns)
tiene_nombre_organizacion = URIRef('#tiene_nombre_organizacion', my_ns)
se_ubica_en = URIRef('#se_ubica_en', my_ns)
incluido_en = URIRef('#incluido_en', my_ns)
tiene_nombre_repositorio = URIRef('#tiene_nombre_repositorio', my_ns)

principles_ns = Namespace('http://principles.org#')
CriterioDeCalidad = URIRef("#criterio_de_calidad", principles_ns)
GrupoDeCriterio = URIRef("#grupo_de_criterio", principles_ns)
criterio_pertenece_a_grupo = URIRef("#criterio_pertenece_a_grupo", principles_ns)
extiende_de = URIRef("#extiende_de", principles_ns)
criterio_tiene_descripcion = URIRef("#criterio_tiene_descripcion", principles_ns)

IdDeOrganizacion = URIRef('#id_de_organizacion', my_ns)
id_de_organizacion_tiene_tipo = URIRef('#id_de_organizacion_tiene_tipo', my_ns)
id_de_organizacion_tiene_literal = URIRef('#id_de_organizacion_tiene_literal', my_ns)
tiene_periodo_de_relacion_con_organizacion = URIRef('#tiene_periodo_de_relacion_con_organizacion', my_ns)
tiene_tipo_de_organizacion = URIRef('#tiene_tipo_de_organizacion', my_ns)
tiene_tipo_de_relacion_con_organizacion = URIRef('#tiene_tipo_de_relacion_con_organizacion', my_ns)
RelacionRepositorioYOrganizacion = URIRef('#relacion_repositorio_y_organizacion', my_ns)
relacion_repositorio_y_organizacion_tiene_repositorio = URIRef('#relacion_repositorio_y_organizacion_tiene_repositorio', my_ns)
relacion_repositorio_y_organizacion_tiene_organizacion = URIRef('#relacion_repositorio_y_organizacion_tiene_organizacion', my_ns)

def refine_iterator(iterator, white_list: [str], allow_whitelist: bool):
    schema = load_schema()
    refined = []
    for x in iterator:
        if x['idd'] in BLACKLIST:
            continue
        # if allow_whitelist:
        #     if x['idd'] not in white_list:
        #         continue
        rrr = refine_repository_info(schema, x['bin'])
        refined.append(rrr)
    return refined


def refine_and_insert_on_rdf():
    # database = get_database_async()
    database = get_database_client()
    # drepo_collection = database['drepo']
    raw_drepo_collection = database['raw_drepo']
    skip_count = 0
    limit_count = 20
    instances = raw_drepo_collection.find({}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    # instances_count = raw_drepo_collection.count_documents({})
    instance_ids = raw_drepo_collection.find({}, {'idd': True}).sort({'idd': -1}).skip(skip_count).limit(limit_count)
    instance_ids = [x['idd'] for x in instance_ids]

    g = Graph()
    # g = Graph(store="BerkeleyDB")
    # g.open("/some/folder/location")
    # g.close()
    # g.parse("....")
    g.bind('', my_ns)

    # rdf_ids = {x: URIRef("#repositorio/%s" % (x,), my_ns) for x in instance_ids}
    # not_repeated_ids = [x for x in instance_ids if rdf_ids[x] not in g[rdf_ids[x]]]
    not_repeated_ids = instance_ids

    def process(repository_info):
        repositorio = URIRef("#repositorio/%s" % (repository_info['id'], ), my_ns)
        g.set((repositorio, RDF.type, Repositorio))
        g.set((repositorio, tiene_nombre_repositorio, Literal(repository_info['repositoryName'])))

        for db_instance in repository_info['institutions']:
            id_org = db_instance['id'].replace(' ', '')
            r_instance = URIRef("#organizacion/%s" % (id_org,), my_ns)
            # g.set((r_instance, RDF.type, Organizacion))
            g.set((r_instance, tiene_nombre_organizacion, Literal(db_instance['institutionName'])))
            if db_instance['institutionCountry'] != 'EEC':
                location = URIRef("#pais/%s" % (db_instance['institutionCountry'],), my_ns)
                g.set((location, RDF.type, Pais))
            else:
                location = URIRef("#bloque_comercial/%s" % ('UE',), my_ns)
                g.set((location, RDF.type, BloqueComercial))
            g.set((r_instance, se_ubica_en, location))

            g.add((r_instance, tiene_tipo_de_organizacion, Literal(db_instance['institutionType'])))

            id_match = re.match('^(?P<type>.+(?=[:;.])|CrossrefFunderID)', id_org)
            if not id_match:
                print(id_org, repository_info['id'])
                continue
            tipo_de_id_de_organizacion_str = id_match.groupdict().get('type')
            tipo_de_id_de_organizacion = URIRef("#tipo_de_id_de_organizacion/%s" % (tipo_de_id_de_organizacion_str.upper(),), my_ns)

            id_de_organizacion = URIRef("#id_de_organizacion/%s" % (id_org,), my_ns)
            g.set((id_de_organizacion, RDF.type, IdDeOrganizacion))
            # ToDo: tipo_de_id_de_organizacion puede ser ROR, RRID, local y que otro?
            g.set((id_de_organizacion, id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
            g.set((id_de_organizacion, id_de_organizacion_tiene_literal, Literal(db_instance['id'])))

            # ToDo: Falta el tipo de relacion que tiene con el repositorio
            #     <DatatypeDefinition>
            #         <Datatype IRI="tipo_de_organizacion"/>
            #         <DataOneOf>
            #             <Literal>comercial</Literal>
            #             <Literal>no-comercial</Literal>
            #         </DataOneOf>
            #     </DatatypeDefinition>
            #     <DatatypeDefinition>
            #         <Datatype IRI="tipo_de_relacion_con_organizacion"/>
            #         <DataOneOf>
            #             <Literal>administrativa</Literal>
            #             <Literal>financiamiento</Literal>
            #             <Literal>técnica</Literal>
            #         </DataOneOf>
            #     </DatatypeDefinition>

            for responsibilityType in db_instance.get('responsibilityType', []):
                # ToDo: responsibilityType puede ser general, profit, non-profit, y que otro?
                relacion_repositorio_y_organizacion = URIRef("#relacion_repositorio_y_organizacion/%s-%s-%s" % (id_org, repository_info['id'], responsibilityType), my_ns)
                g.set((relacion_repositorio_y_organizacion, RDF.type, RelacionRepositorioYOrganizacion))
                g.set((relacion_repositorio_y_organizacion, relacion_repositorio_y_organizacion_tiene_repositorio, repositorio))
                g.set((relacion_repositorio_y_organizacion, relacion_repositorio_y_organizacion_tiene_organizacion, r_instance))
                # g.set((relacion_repositorio_y_organizacion, tiene_periodo_de_relacion_con_organizacion, ))
                g.set((relacion_repositorio_y_organizacion, tiene_tipo_de_relacion_con_organizacion, Literal(responsibilityType)))

        software_names = [x for x in repository_info['softwareNames'] if x != 'unknown']
        software_name = software_names[0] if len(software_names) >= 1 else None
        if software_name == 'other':
            software_name = "other_%s" % (repository_info['id'],)
        if software_name is not None:
            # ToDo: El literal esta mal usado aca
            motor = URIRef("#motor_de_repositorio/%s" % (Literal(software_name), ), my_ns)
            g.set((motor, RDF.type, MotorDeRepositorio))
            g.set((repositorio, utiliza_motor, motor))

        # for api in repository_info['apis']:
        #     r_instance = Api(
        #         id=api['url'],
        #         type=api['type'],
        #     )
        #     session.add(r_instance)
        #     result = r_instance

        for db_instance in repository_info['subjects']:
            r_instance = URIRef("#disciplina/%s" % (db_instance,), dfg_subject_ns)
            g.add((repositorio, repositorio_afin_a_disciplina, r_instance))

    repository_infos = refine_iterator(instances, not_repeated_ids, True)
    total = len(repository_infos)
    print("To process %s" % (total, ))
    counter = 0
    for r_info in repository_infos:
        process(r_info)
        counter += 1
        if counter % 10 == 0:
            print("ready %s out of %s" % (counter, total))
    g.serialize(destination='../owl/instances.xml', format="xml")
    # print(g.serialize(destination='../owl/instances.xml', format="pretty-xml"))

CERTIFICACIONES = []
LENGUAJES = []
PID_ESQUEMA = []

async def seed(g: Graph):
    criterio_de_calidad_coar = URIRef("#criterio_de_calidad/coar", principles_ns)
    g.set((criterio_de_calidad_coar, RDF.type, CriterioDeCalidad))
    for (idd, category, description, importance) in cts.metricas_coar:
        criterio_de_calidad = URIRef("#criterio_de_calidad/%s" % (idd,), principles_ns)
        g.set((criterio_de_calidad, RDF.type, CriterioDeCalidad))
        g.set((criterio_de_calidad, criterio_tiene_descripcion, Literal(description)))
        grupo_de_criterio = URIRef("#grupo_de_criterio/%s" % (category,), principles_ns)
        g.set((grupo_de_criterio, RDF.type, GrupoDeCriterio))
        g.set((criterio_de_calidad, extiende_de, criterio_de_calidad_coar))

    for (idd, name, url) in cts.criterios_de_calidad:
        criterio_de_calidad = URIRef("#criterio_de_calidad/%s" % (idd,), principles_ns)
        g.set((criterio_de_calidad, RDF.type, CriterioDeCalidad))

    for (target_criterio_id, criterios_extends_to, criterios_considered) in cts.criterio_de_calidad_extiende_de:
        target_criterio = URIRef("#criterio_de_calidad/%s" % (target_criterio_id,), principles_ns)
        g.set((target_criterio, RDF.type, CriterioDeCalidad))
        for criterio_extends_to_id in criterios_extends_to:
            criterio_extends_to = URIRef("#criterio_de_calidad/%s" % (criterio_extends_to_id,), principles_ns)
            g.set((criterio_extends_to, RDF.type, CriterioDeCalidad))
            g.set((target_criterio, extiende_de, criterio_extends_to))

    def tree_walk_disciplina(forest, parent):
        for tr in forest:
            disciplina = URIRef("#disciplina/%s" % (tr[0],), dfg_subject_ns)
            g.set((disciplina, RDF.type, Disciplina))
            g.set((disciplina, nombre_de_disciplina, Literal(tr[1])))
            g.set((disciplina, esquema_de_disciplina, Literal('dfg')))

            if parent is not None:
                parent_g = URIRef("#disciplina/%s" % (parent,), dfg_subject_ns)
                g.set((disciplina, es_sub_disciplina_de, parent_g))
            if len(tr) >= 3:
                children = tr[2]
                tree_walk_disciplina(children, tr[0])
    tree_walk_disciplina(cts.dfg_subjects, None)
    # ToDo: All different the disciplines

    # session.add_all([
    #     Certificacion(
    #         id=x['id'],
    #         nombre=x['name'],
    #     ) for x in CERTIFICACIONES
    # ])

    # cys = []
    # planeta_tierra = planeta('tierra')
    # planeta_tierra = Locacion(id='AAA', name='tierra')
    # session.add(planeta_tierra)
    # for country_or_block in cts.countries:
    #     if len(country_or_block) >= 3:
    #         # continue
    #         loc = Locacion(id=country_or_block[0], name=country_or_block[1])
    #         session.add(loc)
    #         bl = BloqueComercial(localizacion=loc)
    #         session.add(bl)
    #         # bl.incluido_en.append(planeta_tierra)
    #         for country in country_or_block[2]:
    #             loc = Locacion(id=country[0], name=country[1])
    #             session.add(loc)
    #             cy = Pais(alfa_3=country[0], localizacion=loc, bloque=bl)
    #             session.add(cy)
    #             # cys.append(cy)
    #     else:
    #         loc = Locacion(id=country_or_block[0], name=country_or_block[1])
    #         session.add(loc)
    #         cy = Pais(alfa_3=country_or_block[0], localizacion=loc)
    #         session.add(cy)
    #         # cy.incluido_en.append(planeta_tierra)
    #         # cys.append(cy)
    #         # break
    # # ow.AllDifferent(cys)
    # # session.add_all(cys)


if __name__ == '__main__':
    refine_and_insert_on_rdf()
