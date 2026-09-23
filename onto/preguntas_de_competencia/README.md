# Preguntas de competencia

Preguntas que la base de conocimiento debe poder responder, tomadas de la sección 4.6 del informe. Cada una tiene su consulta SPARQL en un archivo `.rq` de esta carpeta.

Se agrupan según el requisito que atienden (ver sección 3.1 del informe):

- **CCI**: información general y contextual del repositorio.
- **CCA**: apoyo institucional.
- **CCE**: evaluación de calidad.
- **CCN**: interoperabilidad.

Los valores fijos de cada consulta (tipo de dato, disciplina, institución, repositorio o criterio) son ejemplos; se cambian en el bloque `VALUES` o en el IRI correspondiente.

## Ejecución

Contra el endpoint de Fuseki (ver `docker-compose-jena.yml`):

```sh
curl -s http://localhost:3030/<dataset>/query \
  --data-urlencode "query@onto/preguntas_de_competencia/cci-1.rq" \
  -H 'Accept: text/csv'
```

Con rdflib, sobre un grafo cargado en memoria: `graph.query(open('cci-1.rq').read())`.

## Información general y contextual

### CCI-1: ¿Qué repositorios permiten publicar datos? — [`cci-1.rq`](cci-1.rq)
Lista los repositorios de datos de investigación (clase `rdd`) con su nombre. En DL equivale a verificar la pertenencia a la clase `dai:rdd`.

### CCI-2: ¿Qué repositorios son adecuados para cierto tipo de datos? — [`cci-2.rq`](cci-2.rq)
Combina dos fuentes: los tipos de contenido que el repositorio declara aceptar (`repositorio_acepta_tipo_de_contenido`) y las estadísticas por tipo de dato de sus contenidos. Incluye los subtipos del tipo buscado (`skos:broaderTransitive*`) y, de las estadísticas, usa solo la más reciente de cada repositorio.

### CCI-3: ¿Qué repositorios son afines a cierta disciplina dada? — [`cci-3.rq`](cci-3.rq)
Igual que CCI-2, pero con disciplinas: afinidad declarada (`repositorio_afin_a_disciplina`) o estadísticas por disciplina, incluyendo las subdisciplinas (`es_sub_disciplina_de*`). El ejemplo usa DFG 111 (Social Sciences).

### CCI-4: ¿Qué repositorio, actualmente activo, brinda servicios de curaduría, control de acceso o soporte técnico?, ¿bajo qué términos? — [`cci-4.rq`](cci-4.rq)
Para repositorios activos, devuelve los servicios de acceso a datos (con su nivel de acceso), las evaluaciones de curaduría (con su nivel) y la documentación general, junto con la URL donde consultar los términos. Los términos concretos deben revisarse manualmente en esa documentación.

### CCI-5: ¿Qué políticas y estándares adoptados por un repositorio impulsan la apertura de sus datos alojados? — [`cci-5.rq`](cci-5.rq)
Repositorios que permiten licencias abiertas (CC0 o CC-BY, por nombre), con sus certificaciones vigentes y las políticas que declaran. "Vigente" usa la cota superior del fin del período (`_hasta >= NOW()`), es decir, que puede seguir vigente.

## Apoyo institucional

### CCA-1: ¿Cuáles son los repositorios que cumplen las políticas de determinada institución? — [`cca-1.rq`](cca-1.rq)
Parte de una institución (ejemplo: Udelar, ROR `030bbe882`), recorre sus organizaciones dependientes (`es_organizacion_antecesora*`), se queda con las activas y devuelve los repositorios con los que mantienen una relación vigente, junto con las políticas del repositorio.

## Evaluación de calidad

### CCE-1: ¿Qué certificaciones son compatibles o aplicables a este repositorio particular? — [`cce-1.rq`](cce-1.rq)
Une dos caminos: las certificaciones aplicadas al repositorio y los criterios de mayor nivel que contienen enunciados que el repositorio satisface. Hoy devuelve vacío en el segundo camino (ver `tech-debt.md`).

### CCE-2: ¿Qué características concretas debe tener un repositorio para cumplir una determinada certificación o principio? — [`cce-2.rq`](cce-2.rq)
Devuelve los enunciados atómicos (hojas) que extienden, directa o indirectamente, un criterio de calidad; el ejemplo usa FAIR. Incluye la descripción de cada enunciado.

## Interoperabilidad

### CCN-1: ¿Qué repositorios están indexados por agregadores de una disciplina específica? — [`ccn-1.rq`](ccn-1.rq)
Repositorios cosechados, directa o transitivamente, por agregadores afines a la disciplina (ejemplo: DFG 201) o a sus subdisciplinas.

### CCN-2: ¿Qué repositorios podrían estar indexados por agregadores de una disciplina específica? — [`ccn-2.rq`](ccn-2.rq)
Repositorios aún no cosechados por un agregador de la disciplina, pero compatibles con él: comparten software, o soportan un protocolo de cosecha o de métricas que el agregador consume (o una extensión de ese protocolo). Devuelve los elementos en común para evaluar el grado de compatibilidad.
