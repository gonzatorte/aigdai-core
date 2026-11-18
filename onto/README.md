# Ontology

The AIGDAI ontology and everything needed to build the knowledge base from the data that the
extractors leave in Mongo.

## Folders

- [`owl/`](./owl): the OWL artifacts. The TBox (`aigdai-tbox.owl`), the ontologies of criteria,
  languages and disciplines, and the vocabularies imported from third parties. See
  [`owl/README.md`](./owl/README.md).
- [`populator/`](./populator): builds the knowledge base in RDF from the raw Mongo data. There is one
  module per source in [`populator/sources/`](./populator/sources), and the result is written to an
  N-Triples file to load into Fuseki (see [Populating Fuseki](#populating-fuseki)).
  Run it with `uv run python -m onto.populator.populate --help`.
- [`competency_questions/`](./competency_questions): the questions the knowledge base must be able to
  answer, each with its SPARQL query and an explanation.

## Modules

- `cts.py`: the controlled vocabularies and catalogs used to seed the knowledge base — DFG and OECD
  disciplines, certifications, FAIR maturity models, the COAR metrics and the ISO 639 languages.
- `quality_criteria.py`: fetches the indicators of the FAIRplus Data Maturity model (DSM) from its
  repository and turns them into statements. Run it with `uv run python -m onto.quality_criteria`.
- `capacities.py`: draft of the tree of repository capabilities, with the naming convention for the
  `soporte_para_` relations. It is a design note: no code consumes it yet.

## Populating Fuseki

The populator builds the whole graph (TBox, seeds, sources and the ROR organizations they mention),
materializes the reasoning and writes it to an N-Triples file. It does not touch Fuseki: loading the
file, and the setup and cleanup around it, are done by hand.

```sh
# 1. Generate the file (choose one)
uv run python -m onto.populator.populate --output graph.nt --full --seeds commons,locaciones  # all the records
uv run python -m onto.populator.populate --output graph.nt                                   # a sample
uv run python -m onto.populator.populate --output graph.nt --sources dummy                   # the dummy source

# 2. Setup: stop Fuseki and empty the database of the dataset (here with_data)
docker stop st_fuseki
docker run --rm --volumes-from st_fuseki --entrypoint rm stain/jena-fuseki:5.1.0 -rf /fuseki/databases/with_data

# 3. Load
docker run --rm --volumes-from st_fuseki -v "$PWD":/staging:ro --entrypoint java stain/jena-fuseki:5.1.0 \
  -cp /jena-fuseki/fuseki-server.jar tdb2.tdbloader --loader=parallel --loc /fuseki/databases/with_data /staging/graph.nt

# 4. Cleanup: start Fuseki again
docker start st_fuseki
```

- `--output` is required, and the file is overwritten.
- Loads are complete, not incremental: there is no way to load only the schema or only the data.
- The database has to be emptied before each load. `tdb2.tdbloader` adds to what is there: the
  triples with IRIs are not repeated, but every blank node structure (unions, lists,
  `owl:AllDifferent`) is duplicated. The previous content is deleted without a copy: back it up first
  from the Fuseki interface if needed.
- The dataset has to exist in Fuseki (create it from its interface, as TDB2). Its database directory
  is the `tdb2:location` of `fuseki-data/configuration/<dataset>.ttl`.
- `tdb2.tdbloader` writes straight into the database, so Fuseki has to be stopped during the load.
  The loader runs in a container of the Fuseki image with its volumes, so the database files keep the
  owner Fuseki uses.
- Datasets defined over the same database, such as `allservice` (a reasoner over `with_data`, in
  `fuseki-data/config.ttl`), see the new content too.
- `--reduced` (the default) and `--full`, `--sources`, `--seeds`, `--skip` and `--limit` choose what
  goes into the graph.

The loader used to insert over HTTP with `INSERT DATA` requests of 80 triples. It was removed: it
took about 27 minutes for the full graph, against about 20 s now, and it split the blank nodes whose
triples fell in two requests. The `--what` and `--loader` options went with it.

## A note on language

The vocabulary of the ontology is in Spanish on purpose (`repositorio`, `criterio_de_calidad`,
`esquema_de_metadatos`), and so are the file names tied to its IRIs (`criterios.owl`,
`lenguajes.owl`, `disciplinas.xml`). The COAR metric descriptions in `cts.py` are kept in Spanish as
well, because they quote the Spanish edition of that framework. Everything else — comments,
docstrings and command-line messages — is in English.
