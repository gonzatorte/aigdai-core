# AIGDAI-core

./ror: contiene extractores de ror a partir de un dump de la página oficial.
./re3data: contiene extractores de re3data a partir de la API de provista por el catálogo.
./onto: 

## Configuración

La configuración se lee del entorno y, si existe, del archivo `.env` de la raíz (`settings.py`). Las mismas variables las usan los `docker-compose*.yml`, así que las credenciales de desarrollo se definen una sola vez y no se versionan.

Para empezar: copiar `.env.example` a `.env` y completar los valores.

## Documentos

- [`.env.example`](./.env.example): plantilla de configuración, con las variables que leen `settings.py` y docker compose.
- [`settings.py`](./settings.py): configuración del proyecto leída del entorno.
- [`onto/preguntas_de_competencia/`](./onto/preguntas_de_competencia): las preguntas que la base de conocimiento debe responder, con su consulta SPARQL (`.rq`) y una explicación de cada una.
- [`analysis.md`](./analysis.md): preguntas abiertas sobre los datos, relevadas de los comentarios de `analysis.py`.
- [`tech-debt.md`](./tech-debt.md): deuda técnica pendiente.
