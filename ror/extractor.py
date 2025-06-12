from rdflib.namespace import RDF
import onto.populator.rdf as rdf_types
from rdflib import Graph, Literal, URIRef
import json
import os

ROR_PREFIX = 'https://ror.org/'
def normalize_id(idd: str):
    if not idd.startswith(ROR_PREFIX):
        raise Exception('')
    return idd[len(ROR_PREFIX):].lower()

def common_parse(registry):
    idd = normalize_id(registry['id'])
    established = registry['established']
    return idd, established

# def v1_parse(registry):
#     rr = common_parse(registry)
#     return [*list(rr), names]

def v2_parse(registry):
    #     {
    #         "status": "active",
    #         "types": [
    #             "education",
    #             "funder"
    #         ],
    #         "admin": {
    #             "created": {
    #                 "date": "2018-11-14",
    #                 "schema_version": "1.0"
    #             },
    #             "last_modified": {
    #                 "date": "2024-05-13",
    #                 "schema_version": "2.0"
    #             }
    #         }
    #     },
    idd, established = common_parse(registry)
    external_ids = sum([[(x['type'], y) for y in x['all']] for x in registry['external_ids']], [])
    if any(map(lambda x: x[0] not in ['fundref', 'grid', 'isni', 'wikidata'], external_ids)):
        raise Exception()
    children = [normalize_id(x['id']) for x in registry['relationships'] if x['type'] == 'child']
    relateds = [normalize_id(x['id']) for x in registry['relationships'] if x['type'] == 'related']
    parents = [normalize_id(x['id']) for x in registry['relationships'] if x['type'] == 'parent']
    predecessors = [normalize_id(x['id']) for x in registry['relationships'] if x['type'] == 'predecessor']
    successors = [normalize_id(x['id']) for x in registry['relationships'] if x['type'] == 'successor']
    names = [x['value'] for x in registry['names']]
    # names = [x['lang'] for x in registry['names']]
    countries = [x['geonames_details']['country_code'] for x in registry['locations']]
    domains = registry['domains']
    types = registry['types']
    invalid_types = [x for x in types if x not in ['education', 'funder', 'healthcare', 'company', 'archive', 'nonprofit', 'government', 'facility', 'other']]
    if len(invalid_types) != 0:
        raise Exception('invalid type')
    # types = ["%s-%s" % (x, idd) if x == 'other' else x for x in types]
    status = registry['status']

    return (
        idd,
        established,
        names,
        countries,
        domains,
        types,
        status,
        external_ids,
        children,
        relateds,
        parents,
        predecessors,
        successors,
    )

def insert_on_rdf(only_org_ids: set[str] | None = None):
    # data_path = os.path.dirname(os.path.realpath(__file__))
    base_path = os.path.dirname(__file__)
    alfa2_alfa3_path = os.path.join(base_path, './data/alfa2_alfa3.json')
    with open(alfa2_alfa3_path, 'r') as file:
        alfa2_alfa3_pairs = json.load(file)
        alfa2_alfa3 = {x: y for [x, y] in alfa2_alfa3_pairs}
    data_path = os.path.join(base_path, './data/v1.49-2024-07-11-ror-data_schema_v2.json')
    with open(data_path, 'r') as file:
        registries = json.load(file)
        g_orgs = Graph()
        g_orgs.bind('', rdf_types.my_ns)
        # count_v1 = 0

        tipo_de_id_de_organizacion_ror = URIRef("tipo_de_id_de_organizacion/ROR", rdf_types.my_ns)
        g_orgs.set((tipo_de_id_de_organizacion_ror, RDF.type, rdf_types.TipoDeIdDeOrganizacion))

        # ToDo: Quitar esta limitacion de los 1eros 10
        for (idx, registry) in enumerate(registries[:10]):
            if idx % 50 == 0:
                print('idx', idx, 'out of', len(registries))
            # if registry['admin']['last_modified']['schema_version'] != '2.0':
            #     count_v1 += 1
            #     continue
            #     # raise Exception('')
            (
                idd,
                established,
                names,
                countries,
                domains, # ToDo: Integrate
                types,
                status,
                external_ids,
                children,
                relateds,
                parents,
                _predecessors,
                _successors,
            ) = v2_parse(registry)
            if status == 'withdrawn':
                continue
            idd_w_schema = 'ROR:%s' % (idd,)
            more_ids = []
            for (typee, external_id) in external_ids:
                # ToDo: Tendria que normalizar los tipo_de_id_de_organizacion (typee) con los usadas en re3data
                more_ids.append((typee.upper(), external_id))
            more_ids_formatted = {"%s:%s" % x for x in more_ids}
            if only_org_ids is not None and idd_w_schema not in only_org_ids and not more_ids_formatted.intersection(only_org_ids):
                continue
            organizacion = URIRef("organizacion/%s" % (idd_w_schema,), rdf_types.my_ns)
            g_orgs.set((organizacion, RDF.type, rdf_types.Organizacion))
            id_de_organizacion = URIRef("id_de_organizacion/%s" % (idd_w_schema,), rdf_types.my_ns)
            g_orgs.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
            g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion_ror))
            g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(idd)))
            g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, organizacion))

            for (typee, external_id) in more_ids:
                tipo_de_id_de_organizacion = URIRef("tipo_de_id_de_organizacion/%s" % (typee,), rdf_types.my_ns)
                # ToDo: Tendria que hacer que todos los tipo_de_id_de_organizacion descritos aqui sean diferentes entre si??
                external_idd = "%s:%s" % (typee, external_id)
                g_orgs.set((tipo_de_id_de_organizacion, RDF.type, rdf_types.TipoDeIdDeOrganizacion))

                id_de_organizacion = URIRef("id_de_organizacion/%s" % (external_idd, ), rdf_types.my_ns)
                g_orgs.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(external_id)))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, organizacion))

            is_active = status == 'active'
            g_orgs.set((organizacion, rdf_types.organizacion_esta_activa, Literal(is_active)))
            if established:
                g_orgs.set((organizacion, rdf_types.organizacion_fundada_en_anio, Literal(established)))

            for name in names:
                g_orgs.add((organizacion, rdf_types.tiene_nombre_organizacion, Literal(name)))

            for location_alfa2 in countries:
                if location_alfa2 not in alfa2_alfa3:
                    raise Exception("not found in alfa country code map")
                location_alfa3 = alfa2_alfa3[location_alfa2]
                location = URIRef("pais/%s" % (location_alfa3,), rdf_types.my_ns)
                g_orgs.set((location, RDF.type, rdf_types.Pais))
                g_orgs.add((organizacion, rdf_types.se_ubica_en, location))

            for typee in types:
                g_orgs.add((organizacion, rdf_types.tiene_tipo_de_organizacion, Literal(typee)))

            #
            #  Relationships to inactive records
            #  Records with status active cannot contain relationships to records with status inactive or withdrawn, except for relationships with type Predecessor.
            #  Records with status inactive or withdrawn may have relationships to records with status active for the sake of preserving the record data at the time the record status was changed to inactive or withdrawn. These are not considering current relationships and do not require corresponding relationships in related records.
            #
            for other_org_id_raw in children:
                other_org_id = "ROR:%s" % (other_org_id_raw,)
                other_org = URIRef("organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((other_org, RDF.type, rdf_types.Organizacion))
                g_orgs.set((organizacion, rdf_types.es_organizacion_padre, other_org))

                id_de_organizacion = URIRef("id_de_organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion_ror))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(other_org_id_raw)))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, other_org))

            for other_org_id_raw in parents:
                other_org_id = "ROR:%s" % (other_org_id_raw,)
                other_org = URIRef("organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((other_org, RDF.type, rdf_types.Organizacion))
                g_orgs.set((other_org, rdf_types.es_organizacion_padre, organizacion))

                id_de_organizacion = URIRef("id_de_organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion_ror))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(other_org_id_raw)))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, other_org))

            for other_org_id_raw in relateds:
                other_org_id = "ROR:%s" % (other_org_id_raw,)
                other_org = URIRef("organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((other_org, RDF.type, rdf_types.Organizacion))
                g_orgs.set((organizacion, rdf_types.es_organizacion_relacionada, other_org))

                id_de_organizacion = URIRef("id_de_organizacion/%s" % (other_org_id,), rdf_types.my_ns)
                g_orgs.set((id_de_organizacion, RDF.type, rdf_types.IdDeOrganizacion))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_tipo, tipo_de_id_de_organizacion_ror))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_literal, Literal(other_org_id_raw)))
                g_orgs.set((id_de_organizacion, rdf_types.id_de_organizacion_tiene_organizacion, other_org))

    # ToDo: Tendria que declarar que todas estas organizaciones son distintas entre si por ser verificadas por un mismo proveedor de datos?

    # print('count_v1', count_v1, 'out of', len(registries))
    return g_orgs

if __name__ == "__main__":
    insert_on_rdf()
