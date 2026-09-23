# Preguntas de análisis

Preguntas abiertas sobre los datos, relevadas de los comentarios de [`analysis.py`](analysis.py). No son deuda técnica: son el trabajo exploratorio que queda por hacer sobre los catálogos ya extraídos. Varias viven en funciones que hoy solo tienen `pass`.

Se dividen en tres grupos: verificar la consistencia de los datos, inferir qué significado le dio cada catálogo a un concepto, y método.

## Consistencia de los datos

| Pregunta | Dónde | Notas |
|---|---|---|
| ¿Hay nombres de disciplina duplicados en `fieldOfScience`? | `fields_of_science_analysis` (L488) | El código ya detectó un caso: "agriculture, forestry, and fisheries" con coma y sin coma antes de "and". |
| ¿Cuántos repositorios declaran varias APIs, y cuántos tienen dos donde una es "other"? | `record_is_accessible` (L399) | |
| ¿Cuántos comparten las URLs entre sí? | `record_is_accessible` (L401) | |
| ¿Cuántos repositorios siguen vivos? | `record_is_still_up` (L365) | Tres vías propuestas: `endDate`, verificar el dominio contra los DNS (nslookup) y mirar publicaciones o actualizaciones recientes. La última tiene un sesgo: quien no usa DOI no queda indexado. |
| ¿Coincide el `fieldOfScience` de las colecciones con el `subject` declarado por el repositorio? | `datacite_re3data_integration_analysis` (L454) | El código deja anotado cómo comparar un caso puntual entre las colecciones `datacite` y `drepo`. |

## Significado que cada catálogo le dio a un concepto

| Pregunta | Dónde | Notas |
|---|---|---|
| ¿Qué se entiende por licencia? | `re3data_licences` (L166, L175) | Sacar los valores posibles por nombre o URL y normalizarlos. Los valores relevados quedaron en el código: `cc`, `cc0`, `apache license 2.0`, `copyrights`, `none`, entre otros. |
| ¿De dónde salió el catálogo de esquemas de metadatos, y cuánto se usa cada valor? | `re3data_metadata_standards` (L251, L252) | Parece provenir de la DCC. Falta agregar dos conteos: cuántas veces aparece cada valor y en cuántos repositorios. |
| ¿Qué tipos de identificador de organización existen además de ROR, RRID y LOCAL? | `re3data_institutions` (L321) | El comentario incluye la agregación de MongoDB que los lista. |
| ¿Qué quiere decir que un repositorio sea "accesible"? | `record_is_accessible` (L372) | La definición propuesta exige remover barreras legales, técnicas y de documentación, no solo ser abierto: APIs de integración y software conocido. |
| ¿Qué quiere decir que un repositorio sea "plural"? | `record_is_plural` (L413) | Medir la variedad de artículos agrupando por contenedores de datos comunes, para no contar varias veces las partes de un mismo estudio, o por clusters de autores poco relacionados. |
| ¿Qué quiere decir "multidisciplinar"? | `record_is_multidisciplinar` (L418) | Distingue dos casos: estudios que abordan varias disciplinas a la vez, y repositorios que alojan estudios de disciplinas distintas sin que cada estudio las mezcle. Deja abierto si una disciplina debería poder tener más de un padre, con bioinformática como ejemplo según DFG u OECD. |
| ¿Cuán disjuntos son "disciplinar" e "institucional"? | `intitutional_vs_disciplinar` (L426) | |
| ¿Los disciplinarios declaran pocas disciplinas y los institucionales muchas? | `fields_of_science_analysis_part2` (L459) | |

## Método

| Tema | Dónde | Notas |
|---|---|---|
| Matriz de covarianza entre atributos | `analysis` (L33) | La idea es detectar correlaciones, sobre todo semánticas, y usar las no semánticas para completar información faltante. |
| Puntaje de interoperabilidad entre dos repositorios | `interop_score_between` (L429) | Declarada y sin implementar; no hay comentario que defina el criterio. |
| Mapear `fieldOfScience` a Frascati/OECD | `fields_of_science_analysis` (L467) | Primero hay que obtener todos los valores posibles. |
