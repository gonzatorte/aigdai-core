# Deuda técnica

## 1. CCE-1 devuelve vacío en su camino por criterios

La pregunta CCE-1 (`onto/preguntas_de_competencia/cce-1.rq`) une dos caminos: las certificaciones aplicadas al repositorio y los criterios de calidad que el repositorio satisface. El segundo camino nunca devuelve resultados, por tres motivos:

1. **`repositorio_satisface_criterio` no se puebla.** Ninguna fuente escribe esa propiedad; solo existe en la TBox (con la cadena `repositorio_satisface_criterio ∘ inv(extiende_de_criterio)`, que propagaría la satisfacción de un criterio a sus enunciados).
2. **Las certificaciones y los criterios no están enlazados.** datacite genera `certificacion/cts` (clase `certificacion`, subclase de `criterio_de_calidad`) y el poblado de criterios genera `criterio_de_calidad/cts_2022` con sus enunciados. Son individuos distintos sin relación entre sí, así que tener la certificación no conecta con sus enunciados. Además, el populator ya lo marca: `ToDo: Tengo que declarar al menos todas las certificaciones (no "other") de re3data y datacite como criterios de calidad` (`onto/populator/populate.py`).
3. **Faltan los períodos de la certificación.** Las líneas que cargarían inicio y fin están comentadas en `sources/datacite.py` y `sources/dummy.py`, y además pasan el certificado en lugar de una fecha. Sin ellas no se puede saber si una certificación está vigente.

**Decisiones pendientes:**
- Cómo enlazar certificación y criterio: `owl:sameAs` entre `certificacion/cts` y `criterio_de_calidad/cts_2022`, hacer que la certificación extienda del criterio (`extiende_de_criterio`), o que datacite apunte directamente al criterio versionado.
- De dónde sale `repositorio_satisface_criterio`: inferirlo de una certificación aplicada y vigente (regla o paso del populator), o poblarlo desde otra fuente o de forma manual.

## 2. Flujos que se eligen comentando y descomentando código

Los scripts que quedan cambian de flujo editando el código: se comenta una llamada y se descomenta otra, o se cambia un valor fijo. Conviene exponer esas opciones como parámetros de línea de comandos, con `argparse`, como ya se hizo en `populate.py` y en los extractores de datacite, re3data y fairsharing.

| Dónde | Qué se prende o apaga hoy | Opción de CLI propuesta |
|---|---|---|
| `onto/populator/ontology.py` | `onto_base_path` alterna entre `'../owl/'` y `'onto/owl/'` según desde dónde se ejecute | Resolver la ruta relativa a `__file__`, o `--owl-dir` |
| `onto/populator/populate.py` (`serialize_file`), `reasoner/*.py`, `onto/populator/utils.py` (`reason_on_memory`) | Rutas de lectura y escritura fijas: `'../owl/…'`, `'./onto/owl/…'` y una ruta absoluta a `/home/…` | `--owl-dir`, `--output` |
| `analysis.py` (`__main__`) | Qué análisis correr (`re3data_institutions`, `analysis`, `fields_of_science_analysis`, …) | `analysis <nombre>` |
| `onto/populator/utils.py` (`reason_on_memory`) | Razonador: `sync_reasoner` (HermiT) o `sync_reasoner_pellet` | `reason --reasoner hermit\|pellet` |
| `reasoner/elk_reasoner.py`, `reasoner/hermit_reasoner.py` | Classpath alternativo comentado; ontología de entrada fija | `--ontology`, `--classpath` |
| `re3data/extractor.py` (`__main__`) | Prueba con un id fijo (`r3d100000001`) | `--id` |
| `re3data/xsd_transform.py` | Esquema XSD alternativo comentado (`base_xsd_path`); el `__main__` es un test con muestras 3 a 8 comentadas | `--xsd`; pasar las muestras a tests (`pytest`) |
