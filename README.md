# AIGDAI-core

## Modules

| Module | What it does | How to run it |
|---|---|---|
| [`datacite/`](./datacite) | Extractor for the DataCite GraphQL API (repositories and their statistics). Also holds `oecd_dfg_mapping.py`, the DFG 2014 ↔ OECD 2006 discipline mapping table. | `uv run python -m datacite.extractor --help` |
| [`re3data/`](./re3data) | Extractor for the re3data API, plus the XSD-driven refinement (`xsd_transform.py`) and the schema variants needed to parse malformed records. | `uv run python -m re3data.extract_from_repo --help` |
| [`fairsharing/`](./fairsharing) | Extractor for FAIRsharing, over GraphQL (`graphql_client.py`) and REST (`rest_client.py`, which requires credentials). | `uv run python -m fairsharing.extractor --help` |
| [`ror/`](./ror) | Extractor working from a dump of the official ROR site (the dump goes in `ror/data/`, not versioned), plus `fairsharing_mapper.py`, the ROR ↔ FAIRsharing id map. | `uv run python -m ror.extractor` |
| [`openaire/`](./openaire) | Survey of the OpenAIRE organizations API. **Not in use and does not run**; kept as a note for future work, see [`tech-debt.md`](./tech-debt.md) section 3. | — |
| [`doi/`](./doi) | Looks up DOI metadata against the DataCite API. Used by the extractors to complete records. | library |
| [`onto/`](./onto) | The ontology: OWL artifacts, the populator that builds the knowledge base, the controlled vocabularies and the competency questions. See [`onto/README.md`](./onto/README.md). | `uv run python -m onto.populator.populate --help` |
| [`reasoner/`](./reasoner) | Runs the ELK and HermiT reasoners over the ontology through `jpype`. The jars are vendored here. | `uv run python reasoner/elk_reasoner.py` |
| [`lib/`](./lib) | Shared helpers: batched and parallel execution of async tasks (`run_in_parallel`) and the Mongo client (`no_relational_database.py`). | library |
| [`explorer/`](./explorer) | Web interface (React + esbuild) for exploring the schema and the instances against the SPARQL endpoint. See [`explorer/README.md`](./explorer/README.md). | `cd explorer && bun run dev` |
| [`analysis.py`](./analysis.py) | Exploratory analyses over the catalogs already extracted into Mongo. The open questions are in [`analysis.md`](./analysis.md). | `uv run python analysis.py` |

## Environment

Dependencies are managed with [uv](https://docs.astral.sh/uv/). The Python version is pinned in `.python-version` and exact package versions in `uv.lock`.

```sh
uv sync
uv run python -m package.module
```

## Configuration

Configuration is read from the environment and from the `.env` file at the root. The `docker-compose*.yml` files use the same variables, so development credentials are defined once and are not versioned.

To get started: copy `.env.example` to `.env` and fill in the values.

The file is always given explicitly, so as not to depend on what each tool looks for on its own:

- Python: `settings.py` loads it with `load_dotenv(dotenv_path=ENV_FILE)`, where `ENV_FILE` is the `.env` at the repository root.
- Docker: pass `--env-file`.

```sh
docker compose --env-file .env up -d
docker compose --env-file .env -f docker-compose-jena.yml up -d
```

## Documents

- [`.env.example`](./.env.example): configuration template, with the variables read by `settings.py` and docker compose.
- [`settings.py`](./settings.py): project configuration read from the environment.
- [`onto/competency_questions/`](./onto/competency_questions): the questions the knowledge base must answer, each with its SPARQL query (`.rq`) and an explanation.
- [`analysis.md`](./analysis.md): open questions about the data, gathered from the comments in `analysis.py`.
- [`tech-debt.md`](./tech-debt.md): pending technical debt.
