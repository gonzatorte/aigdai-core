# AIGDAI-core

./ror: extractors for ROR, working from a dump of the official site.
./re3data: extractors for re3data, working from the API provided by the catalog.
./onto: 

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
