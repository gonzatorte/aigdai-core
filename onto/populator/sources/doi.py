import re

from rdflib import Graph, Literal
from rdflib.namespace import RDF, XSD

import onto.populator.common as common
import onto.populator.rdf_types as rdf_types
from onto.populator.sources.datacite import normalize_lang_code

RE3DATA_RECORD_URL = re.compile(r'^https?://(www\.)?re3data\.org/repository/(r3d\d+)$')


def text_literal(text: str, lang: str = None) -> Literal:
    # The FAIRsharing DOIs do not declare the language of their titles and descriptions
    text = text.replace('@', '')
    if lang:
        return Literal(text, lang=normalize_lang_code(lang.replace('@', '')))
    return Literal(text, datatype=XSD.string)


class DoiSource:
    """Metadata fetched by DOI (api.datacite.org/dois/<doi>).

    The extractors store it next to the record that states the DOI:
    - the re3data DOIs that DataCite lists (re3dataDoi), in the doi_metadata field of the datacite collection;
    - the DOIs of the FAIRsharing databases, in the doi_data field of fs_registry.
    Each DOI becomes a record of its own, issued by the catalog of its prefix (doi-10.17616 for re3data, doi-10.25504
    for FAIRsharing). It shares the DOI identifier with the record that states it. For re3data DOIs, the URL is the
    re3data page, which gives the re3data identifier: that is how DataCite -> DOI -> re3data are linked in the
    reconciliation, with no rule of its own.
    """
    def __init__(self, gg: Graph):
        self.gg = gg

    def process(self, doi_record):
        # doi_record is what api.datacite.org/dois/<doi> returns in "data" (None or 'error' when it could not be fetched)
        if not doi_record or doi_record == 'error' or not doi_record.get('attributes', None):
            return
        gg = self.gg
        doi_metadata = doi_record['attributes']
        doi = common.normalize_doi(doi_metadata['doi'])
        repositorio = rdf_types.Repositorio.child_uri_ref('doi-%s' % (doi,))
        gg.add((repositorio, RDF.type, rdf_types.Repositorio))
        common.add_doi_id(gg, doi, repositorio)

        # The record DOI points at the re3data page: same identifier IRI that re3data and FAIRsharing build
        url_match = RE3DATA_RECORD_URL.match(doi_metadata.get('url') or '')
        if url_match:
            r3d = url_match.group(2)
            id_repo = rdf_types.IdDeRepositorio.child_uri_ref('re3data-%s' % (r3d,))
            gg.add((id_repo, RDF.type, rdf_types.IdDeRepositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_repositorio, repositorio))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_literal, Literal(r3d, datatype=XSD.string)))
            gg.add((id_repo, rdf_types.id_de_repositorio_tiene_catalogo, common.CatalogoRe3Data))

        if doi_metadata['schemaVersion'] != 'http://datacite.org/schema/kernel-4':
            raise Exception()
        for _ in doi_metadata['identifiers']:
            raise Exception('always empty until now. not implemented')
        for _ in doi_metadata['alternateIdentifiers']:
            raise Exception('always empty until now. not implemented')
        for _ in doi_metadata['rightsList']:
            raise Exception('always empty until now. not implemented')
        for _ in doi_metadata['formats']:
            raise Exception('always empty until now. not implemented')
        for _ in doi_metadata['geoLocations']:
            raise Exception('always empty until now. not implemented')
        for _ in doi_metadata['viewsOverTime']:
            raise Exception('always empty until now. not implemented')
        # ToDo: have to create a model on ontology
        # for facetOverTime in doi_metadata['citationsOverTime']:
        #     print(int(facetOverTime["year"]), int(facetOverTime["total"]))
        for title in doi_metadata['titles']:
            if title.get('title'):
                gg.add((repositorio, rdf_types.tiene_nombre_repositorio, text_literal(title['title'], title.get('lang'))))
        for description in doi_metadata['descriptions']:
            # The re3data DOIs use Abstract; the FAIRsharing ones, Other ("This FAIRsharing record describes: ...")
            if description['descriptionType'] not in ('Abstract', 'Other'):
                raise Exception()
            gg.add((repositorio, rdf_types.tiene_descripcion_repositorio, text_literal(description['description'], description.get('lang'))))
        if len(doi_metadata['dates']) > 1:
            raise Exception('always only issue date until now. not implemented')
        # publicationYear is the year the record was registered in re3data and isActive is whether the DOI is
        # findable (all of them are). Neither says when the repository was created or whether it is active, so they
        # are not mapped.
        # ToDo: have to create a model on ontology
        # for facetOverTime in doi_metadata['downloadsOverTime']:
        #     print(int(facetOverTime["year"]), int(facetOverTime["total"]))

        # ToDo: Still have to map: doi_metadata
        #   sizes
        #   fundingReferences funderName + grant?
