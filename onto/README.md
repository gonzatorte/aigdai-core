# Ontology

The AIGDAI ontology and everything needed to build the knowledge base from the data that the
extractors leave in Mongo.

## Folders

- [`owl/`](./owl): the OWL artifacts. The TBox (`aigdai-tbox.owl`), the ontologies of criteria,
  languages and disciplines, and the vocabularies imported from third parties. See
  [`owl/README.md`](./owl/README.md).
- [`populator/`](./populator): builds the knowledge base in RDF from the raw Mongo data. There is one
  module per source in [`populator/sources/`](./populator/sources), and the result is written either
  as XML files into `owl/` or into the Jena dataset. Run it with
  `uv run python -m onto.populator.populate --help`.
- [`competency_questions/`](./competency_questions): the questions the knowledge base must be able to
  answer, each with its SPARQL query and an explanation.

## Modules

- `cts.py`: the controlled vocabularies and catalogs used to seed the knowledge base — DFG and OECD
  disciplines, certifications, FAIR maturity models, the COAR metrics and the ISO 639 languages.
- `quality_criteria.py`: fetches the indicators of the FAIRplus Data Maturity model (DSM) from its
  repository and turns them into statements. Run it with `uv run python -m onto.quality_criteria`.
- `capacities.py`: draft of the tree of repository capabilities, with the naming convention for the
  `soporte_para_` relations. It is a design note: no code consumes it yet.

## A note on language

The vocabulary of the ontology is in Spanish on purpose (`repositorio`, `criterio_de_calidad`,
`esquema_de_metadatos`), and so are the file names tied to its IRIs (`criterios.owl`,
`lenguajes.owl`, `disciplinas.xml`). The COAR metric descriptions in `cts.py` are kept in Spanish as
well, because they quote the Spanish edition of that framework. Everything else — comments,
docstrings and command-line messages — is in English.
