# Reconciliation and provenance queries

Queries about how the records of the three catalogs (re3data, FAIRsharing, DataCite) are reconciled and about
what each catalog states on the same repository. They support the camera-ready of the MTSR 2026 paper.

Run them on a dataset **without reasoner** (`with_data` in Fuseki). With `owl:sameAs` reasoning every value is
copied to every reconciled record, and it is no longer possible to tell which catalog stated what.

## How the data is modeled

- Each catalog creates its own record (`repositorio`) for a repository. The record IRI tells which catalog created
  it: `repositorio/r3d...` (re3data), `repositorio/fairsharing-<id>` (FAIRsharing), `repositorio/datacite-<uid>`
  (DataCite) and `repositorio/doi-<doi>` (DOI).
- The DOI source is the metadata fetched by DOI, today only for the re3data DOIs that DataCite lists. Each DOI is a
  record issued by the catalog of its prefix (`doi-10.17616` for re3data, `doi-10.25504` for FAIRsharing). It is not
  counted as a catalog of its own: it is the link DataCite → DOI → re3data, because the DOI states both the DOI
  (which DataCite also states) and the re3data identifier (from its URL, the re3data page).
- Records of the same repository are linked with `owl:sameAs` by `reconcile_repositories`
  (`onto/populator/populate.py`): two identifiers with the same catalog and literal identify the same repository
  (the `HasKey` of `id_de_repositorio`).
- What a catalog states about a repository is kept with its provenance as a `metadato_en_catalogo`, linked to the
  catalog (`metadato_en_catalogo_emitido_por_catalogo`) and to the record (`metadato_en_catalogo_sobre_repositorio`).
  Three kinds exist:
  - `id_de_repositorio`, through the subproperties `id_de_repositorio_tiene_catalogo` and
    `id_de_repositorio_tiene_repositorio` (the keys are defined on them). Queries that treat all the metadata alike
    reach them with `rdfs:subPropertyOf*`, since no reasoner runs.
  - `url_en_catalogo`: re3data (`repositoryURL`) and FAIRsharing (`homepage`).
  - `estado_en_catalogo`: FAIRsharing states active (`ready`) or inactive (`deprecated`); re3data only states
    inactive, when the record has an end date. Without one it states nothing. DataCite states nothing: its
    `isActive` belongs to the DOI of the re3data record, not to the repository.
- The other characteristics are direct properties of the record, without provenance (`tiene_nombre_repositorio`,
  `tiene_url_repositorio`, `repositorio_esta_activo`, ...).

## Queries

| File | What it returns |
|---|---|
| [`reconciliation_pairs.rq`](reconciliation_pairs.rq) | The reconciliation rule: pairs of records that share an identifier (same catalog and literal). Gives the same 981 pairs that the populator asserts as `owl:sameAs`. |
| [`records_by_source.rq`](records_by_source.rq) | Records per catalog and how many are reconciled with at least one other record. |
| [`reconciled_by_source_pair.rq`](reconciled_by_source_pair.rq) | For each pair of catalogs, the records of each side reconciled with the other side (`owl:sameAs`, transitively). |
| [`reconciled_all_three.rq`](reconciled_all_three.rq) | Repositories with a record in each of the three catalogs. |
| [`midrc_example.rq`](midrc_example.rq) | Worked example: everything stated about MIDRC, with and without provenance. |
| [`active_status_conflicts.rq`](active_status_conflicts.rq) | Reconciled records with opposite activity statuses. |
| [`active_status_one_sided.rq`](active_status_one_sided.rq) | Records that a catalog declares inactive while another catalog that describes them states no status. |
| [`url_conflicts.rq`](url_conflicts.rq) | Reconciled records whose catalogs declare different URLs (after normalizing scheme, `www.` and trailing slashes). |

## Running

Against Fuseki:

```sh
curl -s http://localhost:3030/with_data/query \
  --data-urlencode "query@onto/provenance_queries/midrc_example.rq" \
  -H 'Accept: text/csv'
```

## Results (population of 2026-10-21)

Full population (`--full --seeds commons,locaciones`): 2,181,855 triples including the TBox.

| Catalogs | Records | Reconciled |
|---|---|---|
| re3data | 3,259 | 975 |
| FAIRsharing | 2,385 | 977 |
| DataCite | 5,245 | 0 |

- FAIRsharing–re3data: 977 FAIRsharing records and 975 re3data records. FAIRsharing–DataCite, DataCite–re3data
  and the three together: 0. DataCite only refers to re3data through the DOI of the re3data record, which no
  other catalog uses as identifier.
- Activity status: 8 explicit conflicts, all of them FAIRsharing `ready` against an end date in re3data (e.g.
  Comparative Toxicogenomics Database, eyeGENE, NCBI Genome). 56 records are `deprecated` in FAIRsharing while
  re3data states no status (e.g. ALFRED, Histone Infobase, AgBase).
- URL: 265 reconciled pairs declare different URLs; in 103 of them the host differs too (e.g. MIDRC,
  `www.midrc.org` against `data.midrc.org`; AgBase, `agbase.msstate.edu` against `agbase.arizona.edu`). Some point
  at a wrong cross-reference: FAIRsharing 1551 (AnimalTFDB) refers to `r3d100014453`, whose URL is a UN page.
- MIDRC: FAIRsharing 4081 ("MIDRC", "Medical Imaging and Data Resource Center", `https://www.midrc.org/`, active)
  and re3data `r3d100014283` ("Medical Imaging and Data Research Center", `https://data.midrc.org/`, no status),
  reconciled through the re3data identifier that FAIRsharing cross-references.
