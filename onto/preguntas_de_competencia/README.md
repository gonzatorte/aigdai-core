# Competency questions

Questions the knowledge base must be able to answer, taken from section 4.6 of the report. Each one has its SPARQL query in a `.rq` file in this folder.

They are grouped by the requirement they address (see section 3.1 of the report):

- **CCI**: general and contextual information about the repository.
- **CCA**: institutional support.
- **CCE**: quality assessment.
- **CCN**: interoperability.

The fixed values in each query (data type, discipline, institution, repository or criterion) are examples; change them in the `VALUES` block or in the corresponding IRI.

## Running

Against the Fuseki endpoint (see `docker-compose-jena.yml`):

```sh
curl -s http://localhost:3030/<dataset>/query \
  --data-urlencode "query@onto/preguntas_de_competencia/cci-1.rq" \
  -H 'Accept: text/csv'
```

With rdflib, over a graph loaded in memory: `graph.query(open('cci-1.rq').read())`.

## General and contextual information

### CCI-1: Which repositories allow publishing data? — [`cci-1.rq`](cci-1.rq)
Lists the research data repositories (class `rdd`) with their name. In DL it amounts to checking membership in the class `dai:rdd`.

### CCI-2: Which repositories are suitable for a certain type of data? — [`cci-2.rq`](cci-2.rq)
Combines two sources: the content types the repository declares it accepts (`repositorio_acepta_tipo_de_contenido`) and the per-data-type statistics of its contents. Includes the subtypes of the requested type (`skos:broaderTransitive*`) and, from the statistics, uses only the most recent one for each repository.

### CCI-3: Which repositories are related to a given discipline? — [`cci-3.rq`](cci-3.rq)
Same as CCI-2, but with disciplines: declared affinity (`repositorio_afin_a_disciplina`) or per-discipline statistics, including subdisciplines (`es_sub_disciplina_de*`). The example uses DFG 111 (Social Sciences).

### CCI-4: Which currently active repository provides curation, access control or technical support services, and under what terms? — [`cci-4.rq`](cci-4.rq)
For active repositories, returns the data access services (with their access level), the curation assessments (with their level) and the general documentation, along with the URL where the terms can be consulted. The actual terms must be reviewed manually in that documentation.

### CCI-5: Which policies and standards adopted by a repository promote the openness of the data it hosts? — [`cci-5.rq`](cci-5.rq)
Repositories that allow open licenses (CC0 or CC-BY, by name), with their current certifications and the policies they declare. "Current" uses the upper bound of the end of the period (`_hasta >= NOW()`), that is, it may still be current.

## Institutional support

### CCA-1: Which repositories comply with the policies of a given institution? — [`cca-1.rq`](cca-1.rq)
Starts from an institution (example: Udelar, ROR `030bbe882`), walks its dependent organizations (`es_organizacion_antecesora*`), keeps the active ones and returns the repositories they have a current relation with, along with the repository's policies.

## Quality assessment

### CCE-1: Which certifications are compatible with or applicable to this particular repository? — [`cce-1.rq`](cce-1.rq)
Joins two paths: the certifications applied to the repository and the higher-level criteria containing statements the repository satisfies. It currently returns nothing on the second path (see `tech-debt.md`).

### CCE-2: What concrete characteristics must a repository have to comply with a given certification or principle? — [`cce-2.rq`](cce-2.rq)
Returns the atomic statements (leaves) that extend a quality criterion, directly or indirectly; the example uses FAIR. Includes the description of each statement.

## Interoperability

### CCN-1: Which repositories are indexed by aggregators of a specific discipline? — [`ccn-1.rq`](ccn-1.rq)
Repositories harvested, directly or transitively, by aggregators related to the discipline (example: DFG 201) or to its subdisciplines.

### CCN-2: Which repositories could be indexed by aggregators of a specific discipline? — [`ccn-2.rq`](ccn-2.rq)
Repositories not yet harvested by an aggregator of the discipline, but compatible with it: they share software, or support a harvesting or metrics protocol that the aggregator consumes (or an extension of that protocol). Returns the elements in common so the degree of compatibility can be assessed.
