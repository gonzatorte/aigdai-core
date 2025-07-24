from rdflib import URIRef, Literal, RDF, Graph
import onto.populator.rdf_types as rdf_types
import onto.cts as cts
from onto.populator.utils import owl_all_different

locacion_internacional = URIRef("locacion/global", rdf_types.my_ns)

CatalogoFAIRSharing = URIRef("%s/%s" % (rdf_types.CatalogoDeRepositorios.toPython(), 'FAIRSharing',), rdf_types.my_ns)
CatalogoRe3Data = URIRef("%s/%s" % (rdf_types.CatalogoDeRepositorios.toPython(), 'Re3Data',), rdf_types.my_ns)
CatalogoDoi = URIRef("%s/%s" % (rdf_types.CatalogoDeRepositorios.toPython(), 'DOI',), rdf_types.my_ns)
CatalogoSciCrunch = URIRef("%s/%s" % (rdf_types.CatalogoDeRepositorios.toPython(), 'SciCrunch',), rdf_types.my_ns)
catalogos = [CatalogoFAIRSharing, CatalogoRe3Data, CatalogoDoi, CatalogoSciCrunch]


def seed_catalogos(gg: Graph):
    for catalogo in catalogos:
        gg.set((catalogo, RDF.type, rdf_types.CatalogoDeRepositorios))
    owl_all_different(gg, catalogos)


CERTIFICACIONES = []
ORG_ID_SCHEMAS = [
    (
        x[0],
        x[1],
        URIRef("%s/%s" % (rdf_types.TipoDeIdDeOrganizacion.toPython(), x[0],), rdf_types.my_ns)
    ) for x in [
        ('ROR', ['ROR', 'ROR:ROR']),
        ('DOI', ['other:doi']),
        ('FAIRSHARING', ['other:FAIRsharing_doi']),
        ('GND', ['GND']),
        ('VIAF', ['VIAF']),
        ('RRID', ['RRID', 'ROR:RRID', 'RRID:RRID']),
        ('FUNDREF', ['FUNDREF', 'CrossrefFunderID']),
        ('GRID', ['GRID', 'GRID:GRID']),
        ('ISNI', ['ISNI']),
        ('WIKIDATA', ['WIKIDATA']),
        ('LOCAL', ['LOCAL']),
    ]
]
ror_id_schema = ORG_ID_SCHEMAS[0][2]

def seed_locaciones(g: Graph):
    cys = []
    internacional = locacion_internacional
    cys.append(internacional)
    g.set((internacional, RDF.type, rdf_types.Locacion))
    for country_or_block in cts.countries:
        if len(country_or_block) >= 3:
            bl = URIRef("%s/%s" % (rdf_types.Locacion.toPython(), country_or_block[0],), rdf_types.my_ns)
            cys.append(bl)
            g.set((bl, RDF.type, rdf_types.Locacion))
            g.set((bl, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
            g.set((bl, rdf_types.incluido_en, internacional))
            for country in country_or_block[2]:
                cy = URIRef("%s/%s" % (rdf_types.Pais.toPython(), country[0],), rdf_types.my_ns)
                cys.append(cy)
                g.set((cy, RDF.type, rdf_types.Pais))
                g.set((cy, rdf_types.incluido_en, bl))
                g.set((cy, rdf_types.alfa_3_de_pais, Literal(country[0])))
                g.set((cy, rdf_types.nombre_de_locacion, Literal(country[1])))
        else:
            cy = URIRef("%s/%s" % (rdf_types.Pais.toPython(), country_or_block[0],), rdf_types.my_ns)
            cys.append(cy)
            g.set((cy, RDF.type, rdf_types.Pais))
            g.set((cy, rdf_types.incluido_en, internacional))
            g.set((cy, rdf_types.alfa_3_de_pais, Literal(country_or_block[0])))
            g.set((cy, rdf_types.nombre_de_locacion, Literal(country_or_block[1])))
    owl_all_different(g, cys)
    return (g,)


def seed_commons(g: Graph):
    g.bind('', rdf_types.my_ns)

    for (org_id_name, prefixes, uri_ref) in ORG_ID_SCHEMAS:
        g.set((uri_ref, RDF.type, rdf_types.TipoDeIdDeOrganizacion))
        # for prefix in prefixes:
        #     pass

    for (my_type, items) in [
        (rdf_types.Software, cts.softwares),
        (rdf_types.EsquemaDeIdDeAutor, cts.esquemas_de_id_de_autor),
        (rdf_types.EsquemaDeIdPersistente, cts.esquemas_de_id_persistente),
        (rdf_types.EsquemaDeMetadatos, cts.esquemas_de_metadatos),
        (rdf_types.Licencia, cts.licencias),
        (rdf_types.TipoDeDato, cts.tipos_de_dato),
        (rdf_types.ApiParaCosecha, cts.apis_para_cosecha),
        (rdf_types.RedSocial, cts.red_social),
        (rdf_types.ExportacionDeCitas, cts.formatos_de_exportacion_de_citas),
    ]:
        items_g = []
        for item_id in items:
            old_id = item_id
            if type(item_id) is tuple:
                item_id = item_id[0]
            item = URIRef("%s/%s" % (my_type.toPython(), item_id), rdf_types.my_ns)
            items_g.append(item)
            g.set((item, RDF.type, my_type))
        owl_all_different(g, items_g)

    for (esquema_de_metadatos, esquema_hijos) in cts.esquemas_de_metadatos:
        item = URIRef("%s/%s" % (rdf_types.EsquemaDeMetadatos.toPython(), esquema_de_metadatos, ), rdf_types.my_ns)
        for esquema_hijo in esquema_hijos:
            item_hijo = URIRef("%s/%s" % (rdf_types.EsquemaDeMetadatos.toPython(), esquema_hijo, ), rdf_types.my_ns)
            g.set((item, rdf_types.extiende_a_esquema_de_metadatos, item_hijo))

    formatos = []
    for formato in cts.formatos_de_archivo:
        item = URIRef("%s/%s" % (rdf_types.FormatoDeArchivo.toPython(), formato,), rdf_types.my_ns)
        formatos.append(item)
        g.set((item, RDF.type, rdf_types.FormatoDeArchivo))
    for (formato, _) in cts.formatos_de_archivo_abierto:
        item = URIRef("%s/%s" % (rdf_types.FormatoDeArchivo.toPython(), formato.lower(),), rdf_types.my_ns)
        formatos.append(item)
        g.set((item, RDF.type, rdf_types.FormatoDeArchivoAbierto))
    owl_all_different(g, formatos)

    seed_catalogos(g)

    return (g,)
