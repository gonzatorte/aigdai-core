import re

from rdflib import Literal, RDF, Graph, XSD, URIRef
import onto.populator.rdf_types as rdf_types
import onto.cts as cts
from onto.populator.utils import owl_all_different

locacion_internacional = rdf_types.Locacion.child_uri_ref('global')

CatalogoFAIRSharing = rdf_types.CatalogoDeRepositorios.child_uri_ref('FAIRSharing')
CatalogoRe3Data = rdf_types.CatalogoDeRepositorios.child_uri_ref('Re3Data')
CatalogoSciCrunch = rdf_types.CatalogoDeRepositorios.child_uri_ref('SciCrunch')
CatalogoDummy = rdf_types.CatalogoDeRepositorios.child_uri_ref('dummy')
catalogos = [CatalogoFAIRSharing, CatalogoRe3Data, CatalogoSciCrunch, CatalogoDummy]


# Certifications that are also quality criteria: the sources name them without a version, so they point to the
# unversioned criterion (cts.criterios_de_calidad), which is not declared different from the versioned ones.
CERTIFICATION_CRITERIA = {
    'cts': 'cts',
}


def certification_ref(cert_id: str) -> URIRef:
    if cert_id in CERTIFICATION_CRITERIA:
        return rdf_types.CriterioDeCalidad.child_uri_ref(CERTIFICATION_CRITERIA[cert_id])
    return rdf_types.Certificacion.child_uri_ref(cert_id)


def normalize_doi(doi: str) -> str:
    # DOIs are case insensitive and sometimes come as a resolver URL or with the doi: scheme
    return re.sub(r'^(https?://(dx\.)?doi\.org/|doi:)', '', doi.strip(), flags=re.IGNORECASE).lower()


def catalogo_doi(doi: str) -> URIRef:
    # The catalog that issues a DOI is identified by the DOI prefix, that is, by who registered it:
    # doi-10.17616 is re3data and doi-10.25504 is FAIRsharing.
    # ToDo: relate each doi-<prefix> catalog with the catalog that registers those DOIs (see tech-debt.md)
    return rdf_types.CatalogoDeRepositorios.child_uri_ref('doi-%s' % (normalize_doi(doi).split('/')[0],))


def add_doi_id(gg: Graph, doi: str, repositorio: URIRef):
    # Identifier of a repository record given by a DOI, issued by the catalog of its prefix. The IRI only depends on
    # the DOI, so every source that states the same DOI builds the same identifier node.
    doi = normalize_doi(doi)
    catalogo = catalogo_doi(doi)
    gg.add((catalogo, RDF.type, rdf_types.CatalogoDeRepositorios))
    id_repo = rdf_types.IdDeRepositorio.child_uri_ref('doi-%s' % (doi,))
    gg.add((id_repo, RDF.type, rdf_types.IdDeRepositorio))
    gg.add((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
    gg.add((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(doi, datatype=XSD.string)))
    gg.add((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, catalogo))


def seed_catalogos(gg: Graph):
    for catalogo in catalogos:
        gg.add((catalogo, RDF.type, rdf_types.CatalogoDeRepositorios))
    owl_all_different(gg, catalogos)


CERTIFICACIONES = []
ORG_ID_SCHEMAS = [
    (
        x[0],
        x[1],
        rdf_types.TipoDeIdDeOrganizacion.child_uri_ref(x[0])
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
    g.add((internacional, RDF.type, rdf_types.Locacion))
    for country_or_block in cts.countries:
        if len(country_or_block) >= 3:
            bl = rdf_types.Locacion.child_uri_ref(country_or_block[0])
            cys.append(bl)
            g.add((bl, RDF.type, rdf_types.Locacion))
            g.add((bl, rdf_types.nombre_de_locacion, Literal(country_or_block[1], datatype=XSD.string)))
            g.add((bl, rdf_types.locacion_incluida_en, internacional))
            for country in country_or_block[2]:
                cy = rdf_types.Locacion.child_uri_ref(country[0])
                cys.append(cy)
                g.add((cy, RDF.type, rdf_types.Pais))
                g.add((cy, rdf_types.locacion_incluida_en, bl))
                g.set((cy, rdf_types.alfa_3_de_pais, Literal(country[0], datatype=XSD.string)))
                g.add((cy, rdf_types.nombre_de_locacion, Literal(country[1], datatype=XSD.string)))
        else:
            cy = rdf_types.Locacion.child_uri_ref(country_or_block[0])
            cys.append(cy)
            g.add((cy, RDF.type, rdf_types.Pais))
            g.add((cy, rdf_types.locacion_incluida_en, internacional))
            g.set((cy, rdf_types.alfa_3_de_pais, Literal(country_or_block[0], datatype=XSD.string)))
            g.add((cy, rdf_types.nombre_de_locacion, Literal(country_or_block[1], datatype=XSD.string)))
    owl_all_different(g, cys)
    return (g,)


def seed_commons(g: Graph):
    g.bind('', rdf_types.my_ns)

    for (org_id_name, prefixes, uri_ref) in ORG_ID_SCHEMAS:
        g.add((uri_ref, RDF.type, rdf_types.TipoDeIdDeOrganizacion))
        # for prefix in prefixes:
        #     pass

    for (my_type, items, name_data_prop) in [
        (rdf_types.Licencia, cts.licencias, None),
        (rdf_types.RedSocial, cts.red_social, None),
        (rdf_types.Software, cts.softwares, None),
        (rdf_types.ProtocoloDeCosecha, cts.apis_para_cosecha, None),
        (rdf_types.EsquemaDeIdDeAutor, cts.esquemas_de_id_de_autor, rdf_types.tiene_nombre_estandar),
        (rdf_types.EsquemaDeIdPersistente, cts.esquemas_de_id_persistente, rdf_types.tiene_nombre_estandar),
        (rdf_types.EsquemaDeMetadatos, cts.esquemas_de_metadatos, rdf_types.tiene_nombre_estandar),
        (rdf_types.TipoDeDato, cts.tipos_de_dato, None),
        (rdf_types.FormatoDeExportacionDeCitas, cts.formatos_de_exportacion_de_citas, rdf_types.tiene_nombre_estandar),
        (rdf_types.FormatoDeSindicacion, cts.formatos_de_sindicacion, rdf_types.tiene_nombre_estandar),
        (rdf_types.ProtocoloDeMetricas, cts.protocolo_de_metricas, rdf_types.tiene_nombre_estandar),
    ]:
        items_g = []
        for item_id in items:
            old_id = item_id
            if type(item_id) is tuple:
                item_id = item_id[0]
            item = my_type.child_uri_ref(item_id)
            items_g.append(item)
            g.add((item, RDF.type, my_type))
            if name_data_prop is not None:
                g.add((item, name_data_prop, Literal(item_id, datatype=XSD.string)))
        owl_all_different(g, items_g)

    for (esquema_de_metadatos, esquema_hijos) in cts.esquemas_de_metadatos:
        item = rdf_types.EsquemaDeMetadatos.child_uri_ref(esquema_de_metadatos)
        for esquema_hijo in esquema_hijos:
            item_hijo = rdf_types.EsquemaDeMetadatos.child_uri_ref(esquema_hijo)
            g.add((item, rdf_types.extiende_a_esquema_de_metadatos, item_hijo))

    formatos = []
    for formato in cts.formatos_de_archivo:
        item = rdf_types.FormatoDeArchivo.child_uri_ref(formato.lower())
        formatos.append(item)
        g.add((item, RDF.type, rdf_types.FormatoDeArchivo))
    for (formato, _) in cts.formatos_de_archivo_abierto:
        item = rdf_types.FormatoDeArchivo.child_uri_ref(formato.lower())
        formatos.append(item)
        g.add((item, RDF.type, rdf_types.FormatoDeArchivoAbierto))
    owl_all_different(g, formatos)

    seed_catalogos(g)

    return (g,)
