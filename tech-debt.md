# Technical debt

## [cce-1] Only CoreTrustSeal is linked to a quality criterion

`repositorio_satisface_criterio` is populated from the certification applications (`satisfied_criteria` in
`onto/populator/populate.py`, without validity: whether a certification is current is queried on the application), and
DataCite's "CoreTrustSeal" points to the unversioned criterion `criterio_de_calidad/cts`. CCE-1
(`onto/competency_questions/cce-1.rq`) walks `owl:sameAs` from the repository and returns results.

What is left: the other certifications (`dsa`, `wds`, `dini`, `clarin_b`, `ratswd`, `din31644`) still point to
`certificacion/<id>` and have no statements, so satisfying them propagates nothing (`CERTIFICATION_CRITERIA` in
`onto/populator/common.py`). The unversioned `cts` has no statements either: they hang from `cts_2022`. The
certifications known to be different are listed in `cts.certificaciones_distintas` and declared `owl:AllDifferent`.

**Certification periods.** CCE-1 does not use them, and the period of an application is optional: when
a source does not give it, it is not stated. They are only needed to know whether a certification is current. The lines
that would load them are commented out in `sources/datacite.py` and `sources/dummy.py`, and they pass the certificate
instead of a date.

## [commented-flows] Flows chosen by commenting and uncommenting code

The remaining scripts switch flows by editing the code: one call is commented out and another uncommented, or a hardcoded value is changed. These options should be exposed as command-line parameters with `argparse`, as was already done in `populate.py` and in the datacite, re3data and fairsharing extractors.

| Where | What is switched on or off today | Proposed CLI option |
|---|---|---|
| `onto/populator/populate.py` (`serialize_file`), `reasoner/*.py`, `onto/populator/utils.py` (`reason_on_memory`) | Read and write paths hardcoded to `onto/owl/`, relative to the repository root | `--owl-dir`, `--output` |
| `analysis.py` (`__main__`) | Which analysis to run (`re3data_institutions`, `analysis`, `fields_of_science_analysis`, …) | `analysis <name>` |
| `onto/populator/utils.py` (`reason_on_memory`) | Reasoner: `sync_reasoner` (HermiT) or `sync_reasoner_pellet` | `reason --reasoner hermit\|pellet` |
| `reasoner/elk_reasoner.py`, `reasoner/hermit_reasoner.py` | Alternative classpath commented out; hardcoded input ontology | `--ontology`, `--classpath` |
| `re3data/extractor.py` (`__main__`) | Test with a hardcoded id (`r3d100000001`) | `--id` |
| `re3data/xsd_transform.py` | Alternative XSD schema commented out (`base_xsd_path`) | `--xsd` |

## [openaire] Integrating and reconciling data with OpenAIRE

Pending work: add the [OpenAIRE Graph](https://api.openaire.eu/graph/v1/) as an additional source and reconcile its records with the ones already extracted from re3data, DataCite, FAIRsharing and ROR. OpenAIRE aggregates organizations, data sources and research products, so it is useful both to complete organization data and to cross-check which repositories are indexed and how much they publish (one of the ways proposed in `analysis.md` to tell whether a repository is still alive).

**`openaire/` is dead code, and it is kept on purpose.** It has no importers, no `__main__`, and `fetch_single_org_page` cannot run as written: `dd` is undefined and the format string has one `%s` for two arguments, so it raises `TypeError: not all arguments converted during string formatting` on the first call. What is worth keeping is the survey of the organizations API in the comments at the end of the module: the query parameters, the endpoint for looking an organization up by its ROR (`organizations?pid=https://ror.org/...`) and a sample response. That is the starting point for this work, so the module stays as a note rather than as working code.

**Pending decisions:**
- The reconciliation key. OpenAIRE exposes `pids` per organization, so ROR is the natural join with `ror/` and with the `institutionIdentifier` of re3data, but not every record has one. For repositories there is no equivalent to `r3d…`, so it needs to be decided whether to match by URL, by name or through the DOIs of their contents.
- Where the raw data lands: its own Mongo collection, following the pattern of `drepo`, `datacite` and the FAIRsharing collections.
- Which populator source consumes it (`onto/populator/sources/`), and whether it feeds organizations, repositories or both.
- Whether the two bugs above are fixed or the module is rewritten from scratch once the above is decided.

## [dfg-fos] Crosswalk between DFG and OECD Fields of Science (FOS)

Disciplines come from three taxonomies: DFG (re3data, and the hierarchy in `onto/cts.py`), OECD FOS (DataCite, as slugs such as `disciplina/animal_and_dairy_science`) and FAIRsharing's subject ontology SRAO (numeric ids such as `disciplina/1402`). `seed_disciplinas` (`sources/re3data.py`) seeds FOS from `cts.oecd_fos` (areas and fields, identified by their DataCite slug) and relates the taxonomies with SKOS mapping properties, from three tables in `datacite/`:

- `oecd_dfg_mapping.py`: 310 rows mapping DFG 2014 to OECD FOS 2007, taken from the Meaningful Data Counts project (Ninkov et al., 2022, [10.5281/zenodo.6948238](https://doi.org/10.5281/zenodo.6948238)) through a Google Sheet. The source doesn't state the relation: DFG subjects get `skos:broadMatch` and review boards `skos:closeMatch`, although some review boards are narrower than their FOS target (`111` → area 5, `102` History → 6.1), others are broader (`207` holds 4.1, 4.2 and 4.3) and a few subjects are equivalent (`31201` ↔ 1.1, `11103` ↔ 5.8).
- `oecd_dfg_derived.py`: 23 rows in the other direction, derived by us and not by the source: the FOS fields contained in a DFG node, the smallest one holding every DFG code the crosswalk maps to the field (`4.3` → `207`, `6.2` → `11`, `3.2` → `22`). Loaded as `skos:broadMatch` from the FOS field. Its header lists the 16 FOS codes left out and why.
- `srao_dfg_mapping.py`: 477 rows for 442 SRAO terms, proposed with an LLM and not reviewed by a domain expert. Each row carries its relation (`skos:exactMatch`, `broadMatch`, `narrowMatch` or `relatedMatch`). The `related` and `broader` rows, where DFG has no equivalent field, are the ones to review first. 67 rows marked "was exact" or "was narrower" were turned into `broader` because SRAO places under them terms that DFG classifies elsewhere (SRAO puts Plant Genetics, DFG 20207, under Genetics, mapped to 20105); otherwise the queries, which walk both hierarchies, drifted out of the asked discipline. Being broad terms, their repositories no longer reach DFG questions.

The discipline queries (`cci-3`, `ccn-1`, `ccn-2`) walk `es_sub_disciplina_de` together with `broadMatch`, `exactMatch` and inverse `narrowMatch`, always towards an equal or broader discipline. `closeMatch` and `relatedMatch` are left out of that `*` path: chained, they drift across fields (from 201 through 205 ↔ 1.6 to every biology subject). The review boards, mapped with `closeMatch` only, therefore don't reach FOS. DataCite's statistics are per FOS field. A question asked in DFG reaches them exactly when the DFG node contains the field (`oecd_dfg_derived.py`: 207, 11, 22…). Otherwise (111, 201) only through overlap (down from the field to a DFG subject, then up), which counts datasets outside the asked discipline: for 201 the whole of 1.6, 1.2 and 3.1. The queries don't do that.

The TBox chains `repositorio_afin_a_disciplina ∘ skos:broadMatch` and `∘ skos:exactMatch ⊑ repositorio_afin_a_disciplina` state the same, but Jena's rule reasoner does not apply property chains, so the queries keep the path.

A light review of the DFG–FOS crosswalk against `cts.py`:

- Coverage is complete at the levels that matter: all 48 review boards (3 digits) and all 209 subjects (5 digits). The 18 areas and research areas are not mapped, which is expected. Four FOS fields are never used: 1.7, 2.8, 2.10 and 4.4.
- Wrong mappings:
  - `20706` Phytomedicine → 3.1 Basic medicine. Phytomedicine is plant protection; it should be 4.1 (or 1.6).
  - `20532` Biomedical Technology and Medical Physics → 3.4 Health biotechnology. It should be 2.6 Medical engineering.
  - `111` Social Sciences → `5`, a FOS area rather than a field.
- Incomplete mappings, to review:
  - `11205` Statistics and Econometrics: only 5.2; 1.1 is missing.
  - `11206` Economic and Social History: only 5.2; 6.1 is missing.
  - `20708` Agricultural Economics and Sociology: 4.5; 5.2 and 5.4 are more precise.
  - `30602` Physics of Polymers: only 1.4; 1.3 is missing.
  - `31801` Water research: only 1.5; 2.7 is missing for water management.
  - `40705` Human Factors, Ergonomics: only 2.2; 5.1 is missing.
- Review boards inconsistent with their own subjects: in 18 of the 48, some subjects map to FOS fields the review board itself is not mapped to. The review board rows look like the main field rather than the union of what lies below:
  - `205` Medicine → 1.6, 3.1, while 21 of its subjects map to 3.2 Clinical medicine, and others to 3.3, 3.4, 3.5, 2.6 and 1.2.
  - `207` Agriculture… → 4.1; its subjects also go to 4.2, 4.3, 4.5, 3.1 and 2.11.
  - `111` → 5 (area); its subjects go to 5.4, 5.6, 5.8 and 5.9.
  - The rest: `102`, `106`, `110`, `112`, `201`, `206`, `302`, `306`, `315`, `401`, `402`, `403`, `406`, `407`, `410`.
  - The queries don't walk these rows (`closeMatch`), and subjects are leaves in DFG while FOS has only two levels, so nothing below can contradict them: with DFG and FOS only, no DFG code reaches another outside its subtree. The crosswalk is usable at the subject level and weak at the review board level.
- Some errors come from the name rather than the place in DFG: `20706` Phytomedicine sounds medical, but it sits under `207` Agriculture.
- Text errors in the table:
  - `20207` "Â Plant Genetics" (encoding).
  - `40803` "information engineerin" (truncated).
  - FOS names that vary in case or trailing spaces (1.2, 2.2, 2.9).
  - Hyphens dropped ("NonEuropean", "HighFrequency", "MetalCutting").
- Errors found in `cts.py` while comparing names:
  - Typos: "Cartogaphy" (`31502`), "Manangement" (`40105`), "Sructural" (`41004`).
  - `20610` lost "Psychiatry" from its name.
  - Commas missing in `20513` and `20709`.

**Pending decisions:**
- Whether the errors above are fixed in our copy, documenting the deviation from the published source.
- Whether DataCite's variant slugs (`biological_sciences_fos`, `chemical_science`, `veterinary_science`, `health_biotechnology`, `nano-technology`…) are linked to the canonical ones.
- How each taxonomy gets its own namespace, so that ids from different schemes cannot collide under `disciplina/<id>`.

## [catalog-relation] Missing relation between catalogs (to review soon)

The report says, in the section on repository catalogs (next to Imagen 7), that "se modelaron las conexiones entre los diferentes catálogos, permitiendo conocer qué catálogos intercambian información con otros y bajo qué condiciones". The TBox has no such relation: the only properties with `catalogo_de_repositorios` as range are `metadato_en_catalogo_emitido_por_catalogo` and its subproperty `id_de_repositorio_tiene_catalogo`. The paper does not mention it.

It is needed now for the DOI catalogs: each DOI is issued by the catalog of its prefix (`doi-10.17616`, `doi-10.25504`; see `catalogo_doi` in `onto/populator/common.py`), and nothing states that `doi-10.17616` is re3data registering its own records. Without it, a query cannot treat what a `doi-<prefix>` catalog states as coming from the catalog behind it.

**Pending decisions:**
- Names and shape. Proposal: a generic `catalogo_comparte_datos_con` (who takes data from whom, with the conditions the report mentions) and, for this case, a subproperty such as `catalogo_registra_dois_de` (`doi-10.17616` → re3data).
- Shape suggested by the user: a hierarchical, directed relation `catalogo_es_sub_catalogo_de` (e.g. `doi-10.17616` → re3data), so that an identifier issued by a catalog is, transitively, also of its parent catalogs. In OWL:
  - `catalogo_es_sub_catalogo_de`: ObjectProperty between catalogs, TransitiveObjectProperty. It cannot also be declared asymmetric or irreflexive: in OWL 2 DL those need simple properties and a transitive one is not simple, so "directed" stays a convention.
  - The inheritance as a property chain onto a new, non-functional superproperty (e.g. `metadato_reconocido_por_catalogo`): `metadato_en_catalogo_emitido_por_catalogo ⊑ X` and `metadato_en_catalogo_emitido_por_catalogo ∘ catalogo_es_sub_catalogo_de ⊑ X`. Not onto `emitido_por` or `id_de_repositorio_tiene_catalogo`: a property defined by a chain is not simple, so it could not stay functional nor keep the HasKey, and with a functional one an identifier with two catalogs would make both catalogs the same individual.
  - The key keeps using `id_de_repositorio_tiene_catalogo`, so the reconciliation does not change. The Jena rules do not apply chains; `materialize_property_chains` in `populate.py` reads them from the TBox.
- Harvesting: DataCite Commons lists re3data records (1,752 of its 2,029 records linked to re3data have no DataCite account), which is the same kind of relation between catalogs.
- Where the prefix → catalog table lives (today there are three prefixes in the data: 10.17616, 10.25504 and a malformed `100011965` from a DataCite record).
- Whether the report keeps the sentence as it is or is corrected until the relation exists.

## [hermit-sameas-bug] HermiT returns incomplete sets of equal individuals

`getSameIndividuals` of HermiT does not return the same set for every member of a group of equal individuals. On the
reconciliation subgraph of the whole graph it left out 374 to 419 pairs, and the count changed between runs (12,714
and 12,759 pairs, with the same data). It reproduces with 32 triples: a group of five records of the same repository
(`datacite-g69c8wr`, `doi-10.17616/r3k34m`, `doi-10.25504/fairsharing.m8wewa`, `fairsharing-2256`, `r3d100011173`) gets
answers of 5, 5, 4, 3 and 2 members depending on the individual asked. The reasoning itself is right:
`isEntailed(SameIndividual)` is true for the missing pairs. `precomputeInferences(SAME_INDIVIDUAL)` does not change
anything. Pellet 2.3.1 returns the five members for each of them.

Cause: `InstanceManager.initializeSameAs` builds the groups from the nodes merged in the tableau. When a merge is
certain it adds the class of `individual2` to the class of `individual1` but only repoints `individual2` to the joined
set; the other members of the absorbed class keep their old, smaller set. The nodes are walked in the order of a hash
map, which is why the result changes between runs. HermiT 1.3.8 (`reasoner/HermiT/project`) and the `master` branch of
owlcs/hermit-reasoner have the same code, and there is no issue about it in that repository.

Workaround in place: `infer_same_repositories` (`onto/populator/hermit_reasoner.py`) closes the pairs transitively
(union-find) before asserting them. It recovers the groups as long as the pairs HermiT does return connect each group,
which held for the 234 affected groups in the run that was checked, but is not guaranteed in general.

**Proposal:**
- Fix `initializeSameAs` so that every member of the absorbed class points to the joined set (about 5 lines).
- Recompile the local copy: `build.xml` targets Java 1.5, which the JDK 21 in `reasoner/jdk` no longer accepts, so it
  has to move to Java 8 (and maybe fix some error of the modern `javac`). The sources and libraries (OWL API 3.4.3) are
  in `reasoner/HermiT/project`, and `ant` is installed. Then rebuild `HermiT.jar` with its libraries and check it with
  the 32-triple case and the whole subgraph. Estimate: one or two hours.
- Report it upstream with the minimal case (a public action: ask first).

## [reasoner-benchmark] Compare Pellet, Openllet and Konclude with HermiT

HermiT does not scale on the reconciliation subgraph with the HasKey axioms (the consistency check took 2.6 s with 100
records per source, 64 s with 400, did not finish in 10 minutes with 1,600 and ran out of memory with the whole graph;
without HasKey the whole graph takes about 90 s plus 23 s for the equalities), and it has the bug above.

**Proposal:** measure on the same subgraphs (reconciliation and property chains, with and without HasKey) and on the
32-triple case:
- Pellet 2.3.1: its jars are available locally (they came with owlready2); OWL API 3, like HermiT. It returned the right
  groups on the 32-triple case. Check whether it supports HasKey.
- Openllet: the maintained continuation of Pellet, with OWL API 5 and recent Jena. It has to be downloaded and, being
  OWL API 5, run in its own process.
- Konclude: C++, parallel, strong in the ORE competitions. It runs from the command line or through OWLlink, not
  inside the JVM, so it needs files in and out.

## [coretrustseal-source] Read CoreTrustSeal certification status from a machine-readable source

Today the only evidence of a CoreTrustSeal certification is what re3data and DataCite declare, through `/api/v1` of
re3data (schema 2.2), which often says `other` where the web page shows CoreTrustSeal, and without dates. That is one of
the reasons behind [cce-1] item 3 (no certification periods). Two sources found on 14-nov-2026 would fix it:

- **DataverseNL, collection `coretrustseal`.** Since Jan-2024 every approved application is published as a dataset with a
  DOI (349 on 14-nov-2026). The title carries the expiry date, the repository name and the requirements version, e.g.
  `2027-08-08 - PURR - CoreTrustSeal Requirements 2023-2025`; the files hold the assessment. Queried with the Dataverse
  Search API: `https://dataverse.nl/api/search?q=*&subtree=coretrustseal&type=dataset`. It has no re3data or ROR id, so
  matching to repositories is by name, or through the next source.
- **re3data `/api/v40`.** Returns the certificate with `certificateName`, `certificateStartDate`, `certificateEndDate` and
  `certificateUrl` (the DataverseNL DOI), plus typed ROR, FAIRsharing and RRID ids. Example: r3d100013353 says `other`
  in v1 and CoreTrustSeal 2025-10-02 to 2028-10-01 in v40. The listing `/api/v40/repositories` answers HTTP 500 without
  `query`, so the ids would come from `/api/v1/repositories` and each record from `/api/v40/repository/{id}`.

The `certificateUrl` DOI joins both: re3data gives the repository and the dates, DataverseNL gives the requirements
version (2020-2022, 2023-2025, 2026-2028), which decides which versioned criterion applies (`cts_2022` today).

**Pending decisions:**
- Whether to move the re3data extractor to `/api/v40` (it changes the XSD used by `re3data/xsd_transform.py`) or only
  read the certificates from it.
- Whether DataverseNL becomes its own catalog (its own provenance) or only enriches the re3data record.
- How to model the requirements versions: one `criterio_de_calidad` per version (`cts_2022`, `cts_2023`, `cts_2026`),
  which ties into the pending decisions of [cce-1].

## [ftr-criteria] Base the atomised quality criteria on the FTR vocabulary (improvement)

The quality criteria (`criterios.owl`: `criterio_de_calidad`, `grupo_de_criterio`, `extiende_de_criterio`,
`evaluacion_de_repositorio`, `aplicacion_de_certificacion_a_repositorio`, `repositorio_satisface_criterio`) are an own
model. The OSTrails FAIR Testing Resource Vocabulary (FTR, https://w3id.org/ftr, v1.3.0, Nov-2026, CC BY 4.0; extends
DQV, DCAT and PROV) is becoming the shared one: FAIR-Champion, FOOPS, FAIR-Checker, the OSTrails assessment records and
the EOSC EDEN / RDA TRSP repository-attribute work use it. Aligning with it would make the criteria and evaluations
exchangeable with those tools.

Possible mapping:

| Ours | FTR |
|---|---|
| atomic `criterio_de_calidad` (a CTS requirement, a TRUST principle, a FAIR metric) | `ftr:Metric` (⊑ `dqv:Metric`), principle via `dqv:inDimension` |
| `grupo_de_criterio`, a certification or framework version (`cts_2022`) | `ftr:Benchmark` (`ftr:hasAssociatedMetric`) |
| `evaluacion_de_repositorio` against one criterion | `ftr:TestResult` with `ftr:assessmentTarget` = the repository |
| overall result of a certification | `ftr:BenchmarkScore` (⊑ `dqv:QualityMeasurement`) |

**Limits found (14-nov-2026):**
- FTR is not OWL 2 EL, not even OWL 2 DL: `ftr:supportedBy` is both object and datatype property, three domains use
  `owl:unionOf`, there is an `owl:inverseOf` and an `xsd:float` range. Importing it breaks the EL profile; the option is
  to reuse its IRIs (subclass/subproperty alignments in our TBox) without importing its axioms, or import a cleaned module.
- It targets digital objects: `ftr:Test` is a `dcat:DataService` (an API), so a CoreTrustSeal review or an ISO 16363 audit
  is not a Test; there are no classes for evidence, certifying authority or assurance level.
- No validity period for a certification (only `prov:generatedAtTime`); ours would still need start and end dates.
- No relations between criteria of different frameworks (equivalence, inclusion) nor between criteria and repository
  capabilities; `extiende_de_criterio` and the property chain stay ours.

Related: Huber, "A Semantic Web Model for Standardizing FAIR Metrics and Assessment Results", Data Science Journal 25:30
(2026), doi:10.5334/dsj-2026-030 (DQV + EARL + QMO, implemented in F-UJI, without FTR); EOSC EDEN Registry Conceptual
Model v0.1, doi:10.5281/zenodo.19096070 (Mar-2026).

## [config-population] Separate configuration population from data population

Some individuals look fixed but are configuration, not data: the discipline taxonomies and the quality criteria (with
their atomic statements and the `extiende_de_criterio` relations) are modelled as individuals, not classes, so that they
can change without changing the ontology or the code. Today both are rebuilt on every run, together with the catalogue
records: `refine_and_insert_on_rdf` always calls `seed_criterios()` and `seed_disciplinas()`
(`onto/populator/populate.py`), and the reasoning runs once over everything.

The two kinds behave differently and should be populated separately:

- **Data population** (catalogue records): runs often and its effects are local to the records it adds, so it should
  stay light, without global precomputation.
- **Configuration population** (disciplines, quality criteria): changes rarely and has global effects (the hierarchies
  feed property chains such as `isAlignedTo ∘ isSubdiscipline` and the propagation through `extiende_de_criterio`), so
  it is worth precomputing and materializing once and reusing it across data runs.

**Pending decisions:** how the precomputed configuration is stored and reused (a separate N-Triples file, a named graph
in the dataset), and what invalidates it.

## [certification-evidence] Model certifications as evidence, like catalogue metadata (improvement)

`aplicacion_de_certificacion_a_repositorio` reifies "repository R holds certification C during a period". It could
follow the same pattern as `metadato_en_catalogo` (the "identifies / describes" pattern of `CatalogMetadata`): a new
evidence entity (provisional name: certification proof holder) issued by whoever grants or reports the certification,
about a repository, pointing to the certification criterion, with its validity period and the proof (certificate URL or
document). `repositorio_satisface_criterio` would then be a summary derived from that evidence, without validity, and
the period and the source of the claim would always be queried on the evidence entity.

## [re3data-v4] Exploit the re3data 4.0 schema

The re3data metadata schema 4.0 (August 2023, `re3data/re3dataV4-0.xsd`) adds information the populator could use:

- `relatedRepository` with `relatedRepositoryType` (`predecessor`, `successor`, `dataProvider`, `serviceProvider`,
  `funding`). `dataProvider` / `serviceProvider` state who aggregates whom, which today only FAIRsharing provides
  (`shares_data_with` → `repositorio_es_cosechado_por_agregador`); `predecessor` / `successor` give succession between
  repositories.
- `institutionIdentifierType` (ROR, ISNI, VIAF, FundRef, DataCite…) next to the identifier URL, instead of a bare URI.
- `fundingInformation`, with funder names and identifiers.

Blocker: on 17-nov-2026 both API endpoints the extractor uses, `api/v1/repository/<id>` and `api/beta/repository/<id>`,
still return schema 2.2 (checked with `r3d100014283`); `api/v2` does not exist. The extractor also validates against
`re3dataV2-2-lowercase-partial.xsd` (`re3data/xsd_transform.py`). Exploiting 4.0 needs an endpoint or dump that serves it.
Note that in 4.0 `dataLicenseName` becomes free text (in 2.2 it was a coarse enumeration).

## [access-levels] Access levels and the records that get them (to consider)

Access services and openness evaluations come from FAIRsharing (`process_data_conditions` in
`onto/populator/sources/fairsharing.py`) and re3data (`process_access` in `onto/populator/sources/re3data.py`). Open
points:

- **Only data repositories get them.** `servicio_de_acceso_a_datos_tiene_repositorio` and
  `evaluacion_de_repositorio_tiene_repositorio` have range `rdd`, so the reasoner would type any record that has them as a
  data repository and inflate CCI-1. FAIRsharing records that are only a knowledgebase, and re3data records that are not
  data providers, are therefore left without access services or evaluations, although the sources describe their
  access too. To decide: widen the ranges to `repositorio`, or keep the restriction.
- **Two vocabularies.** The levels are the sources' own (`cts.niveles_de_acceso_fairsharing`,
  `cts.niveles_de_acceso_re3data`). Only `open` is shared; FAIRsharing's `controlled` and `partially open` and re3data's
  `restricted`, `embargoed` and `closed` are not aligned. FAIRsharing's access levels are ordered with
  `es_acceso_mas_amplio`; re3data's are not.
- **re3data's restrictions** (registration, fee required, institutional membership, other) are not mapped.

## [fairsharing-registries] FAIRsharing records and fields not integrated

- **Registries.** `process_registry` (`onto/populator/sources/fairsharing.py`) does nothing with Standard (about 1,900
  records: terminology artefacts, models and formats, reporting guidelines, identifier schemas, principles) or
  Collection. The TBox already has what Standard needs: the `estandar` subclasses, and `extiende_de_estandar` and
  `perfila_estandar` for the "extends" and "profiles" associations. The standards that policies recommend are typed
  `estandar` under their FAIRsharing IRI, without name or subclass.
- **Policies and organisations.** The Policy records are integrated (`process_policy`: name, URL, "recommends" to
  databases and standards, "extends" and "related_to" between policies), but not who issues them: FAIRsharing links 355
  of the 374 policies to organisations ("maintains", "funds", "associated_with", "collaborates_on"), and the TBox has no
  property from organisation to policy (the core figure's "adopts" does not exist). Without it CCA-1 cannot start from
  an institution and reach the repositories its policies recommend.
- **Fields of the database records:** `associated_tools`, `grants`, `year_creation`, `taxonomies`, `domains`. The
  validity periods written inside some certification names ("valid until 2025-02-17", "(2020-2026)") are not parsed.
- **Enumerated values.** The values of re3data, DataCite and `cts.py` are `owl:sameAs` the IRI of their FAIRsharing
  record (`https://fairsharing.org/<id>`, from `cts.fairsharing_de_enumerados`; `link_fairsharing_records` in
  `onto/populator/populate.py`). Once Standard is integrated, its individuals should use those IRIs or be the same as
  them. Values without a FAIRsharing record, or ambiguous ones, are listed in the comment of the table.
- **Licences** are reconciled by URL (`reconcile_licences`): 242 of re3data's licence URLs match a FAIRsharing licence,
  1,839 of 5,419 uses. URLs shared by two FAIRsharing licences are skipped, since those are `owl:AllDifferent`. Some
  matches are generic URLs ("creativecommons.org", "creativecommons.org/licenses") that name a family, not a licence.
