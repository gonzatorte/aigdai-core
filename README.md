# AIGDAI-core

./ror: contiene extractores de ror a partir de un dump de la página oficial.
./re3data: contiene extractores de re3data a partir de la API de provista por el catálogo.
./onto: 

## Configuración

La configuración se lee del entorno y del archivo `.env` de la raíz. Las mismas variables las usan los `docker-compose*.yml`, así que las credenciales de desarrollo se definen una sola vez y no se versionan.

Para empezar: copiar `.env.example` a `.env` y completar los valores.

El archivo se indica siempre de forma explícita, para no depender de lo que cada herramienta busque por su cuenta:

- Python: `settings.py` lo carga con `load_dotenv(dotenv_path=ENV_FILE)`, donde `ENV_FILE` es el `.env` de la raíz del repositorio.
- Docker: pasar `--env-file`.

```sh
docker compose --env-file .env up -d
docker compose --env-file .env -f docker-compose-jena.yml up -d
```

## Documentos

- [`.env.example`](./.env.example): plantilla de configuración, con las variables que leen `settings.py` y docker compose.
- [`settings.py`](./settings.py): configuración del proyecto leída del entorno.
- [`onto/preguntas_de_competencia/`](./onto/preguntas_de_competencia): las preguntas que la base de conocimiento debe responder, con su consulta SPARQL (`.rq`) y una explicación de cada una.
- [`analysis.md`](./analysis.md): preguntas abiertas sobre los datos, relevadas de los comentarios de `analysis.py`.
- [`tech-debt.md`](./tech-debt.md): deuda técnica pendiente.
