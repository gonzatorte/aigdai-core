# Analysis questions

Open questions about the data, gathered from the comments in [`analysis.py`](analysis.py). They are not technical debt: they are the exploratory work still to be done on the catalogs already extracted. Several of them live in functions that currently contain only `pass`.

They are split into three groups: checking data consistency, inferring what meaning each catalog gave to a concept, and method.

## Data consistency

| Question | Where | Notes |
|---|---|---|
| Are there duplicate discipline names in `fieldOfScience`? | `fields_of_science_analysis` (L488) | The code already found one case: "agriculture, forestry, and fisheries" with and without a comma before "and". |
| How many repositories declare several APIs, and how many have two where one is "other"? | `record_is_accessible` (L399) | |
| How many share URLs with each other? | `record_is_accessible` (L401) | |
| How many repositories are still alive? | `record_is_still_up` (L365) | Three approaches are proposed: `endDate`, checking the domain against DNS (nslookup), and looking for recent publications or updates. The last one is biased: repositories that do not use DOIs are not indexed. |
| Does the collections' `fieldOfScience` match the `subject` declared by the repository? | `datacite_re3data_integration_analysis` (L454) | The code notes how to compare a specific case between the `datacite` and `drepo` collections. |

## Meaning each catalog gave to a concept

| Question | Where | Notes |
|---|---|---|
| What is meant by license? | `re3data_licences` (L166, L175) | Extract the possible values by name or URL and normalize them. The values found are listed in the code: `cc`, `cc0`, `apache license 2.0`, `copyrights`, `none`, among others. |
| Where did the catalog of metadata schemas come from, and how much is each value used? | `re3data_metadata_standards` (L251, L252) | It seems to come from the DCC. Two counts are missing: how many times each value appears and in how many repositories. |
| What kinds of organization identifier exist besides ROR, RRID and LOCAL? | `re3data_institutions` (L321) | The comment includes the MongoDB aggregation that lists them. |
| What does it mean for a repository to be "accessible"? | `record_is_accessible` (L372) | The proposed definition requires removing legal, technical and documentation barriers, not just being open: integration APIs and well-known software. |
| What does it mean for a repository to be "plural"? | `record_is_plural` (L413) | Measure the variety of items by grouping them by common data containers, so as not to count the parts of the same study several times, or by clusters of loosely related authors. |
| What does "multidisciplinary" mean? | `record_is_multidisciplinar` (L418) | Distinguishes two cases: studies that address several disciplines at once, and repositories that host studies from different disciplines without each study mixing them. Leaves open whether a discipline should be able to have more than one parent, with bioinformatics as an example according to DFG or OECD. |
| How disjoint are "disciplinary" and "institutional"? | `intitutional_vs_disciplinar` (L426) | |
| Do disciplinary repositories declare few disciplines and institutional ones many? | `fields_of_science_analysis_part2` (L459) | |

## Method

| Topic | Where | Notes |
|---|---|---|
| Covariance matrix between attributes | `analysis` (L33) | The idea is to detect correlations, especially semantic ones, and to use the non-semantic ones to fill in missing information. |
| Interoperability score between two repositories | `interop_score_between` (L429) | Declared but not implemented; no comment defines the criterion. |
| Map `fieldOfScience` to Frascati/OECD | `fields_of_science_analysis` (L467) | All possible values must be obtained first. |

## Research data on general-purpose platforms

Unlike the rest of this file, this topic does not come from `analysis.py`. It has two directions: data repositories hosted on general-purpose platforms (GitHub, GitLab, Google Sites…) that re3data lists, and GitHub repositories that work as data repositories without being listed in re3data.

### re3data entries on general-purpose platforms

Query on `drepo_2` (3259 entries, 2026-11-14), classifying the host of `repositoryURL` and of each `apis[].url`. Custom domains pointing to GitHub Pages or similar (CNAME or IP) were not checked.

| Case | Entries | Notes |
|---|---|---|
| The platform itself listed as a repository | GitHub (r3d100010375), Bitbucket (r3d100013478), SourceForge (r3d100010167), Kaggle (r3d100012705) | The first three have `isDataProvider` true, so the populator types them as `rdd`; Kaggle has `isServiceProvider` true and becomes an `agregador`. None declares a PID system. |
| Repository hosted on GitHub / GitLab / SourceForge | bii (`github.com/ISA-tools/BioInvIndex`), Pathogen Portal (a GitHub wiki), Spec Patterns, PolMine and Pitt ELI Corpus (`*.github.io`), MorpheusML (`*.gitlab.io`), Blue Obelisk (SourceForge) | Seven entries, about 0.2% of the catalog. |
| Repository on another general-purpose service | National Virtual Observatory (Google Sites, `endDate` 2015), Research Compendia (Read the Docs, `endDate` 2017), Global Land Cover Facility (a WordPress post announcing it went offline, `endDate` 2019) | All three are inactive; the URL is what was left after the shutdown. |
| API documented on a general-purpose platform | 35 on GitHub, 16 on Read the Docs, 4 on Google Docs/App Engine, 1 on Bitbucket | Mostly the documentation or client of the API, not the data. Not a hosting signal. |

`softwareNames` has 683 entries with value `other`; it was not used to classify.

### GitHub repositories that work as data repositories

Question: of the GitHub repositories holding research data, how many also have that data in a repository registered in re3data? Run on 2026-11-14/17. Only research data is of interest; general datasets (ML training sets, government open data, app reference data, hobby data) are noise.

#### Harvest

GitHub search API. Code search uses the legacy engine: it needs authentication, allows about 10 requests per minute, returns at most 1000 results per query and only searches the default branch, so queries were partitioned by file size (code) or creation date (repositories). Code search counts files, not repositories. Forks were excluded.

| Signal | Query | Files / repos | Repos harvested |
|---|---|---|---|
| `CITATION.cff` with `type: dataset` | `filename:CITATION.cff "type: dataset"` | 5976 files | 5091 |
| `.zenodo.json` with dataset | `filename:.zenodo.json "upload_type" dataset` | 2136 files | 2084 |
| DataLad | `path:.datalad filename:config` | 2816 files | 2199 (incomplete, see below) |
| Frictionless | `filename:datapackage.json` | 16832 files | 1798 |
| RO-Crate | `filename:ro-crate-metadata.json` | 22432 files | 936 |
| Topics | `topic:dataset`, `datasets`, `research-data`, `data-repository`, `datapackage` | 21390, 3839, 494, 73, 66 repos | all |

Not harvested: `topic:open-data` (mostly government and civic data), `*.dvc` (223232 files, mostly ML pipelines), `.gitattributes` with LFS (17600, noisy), schema.org JSON-LD (the legacy engine does not match phrases, 1.5M hits), `codemeta.json` (4536, describes software).

Caveats of the harvest:

- The file signals are concentrated: `mauforonda/geodatos` has 6034 of the `datapackage.json` files, `ome/ome2024-ngff-challenge-metadata` 15968 of the RO-Crate files.
- The text match is loose: `"type: dataset"` also matches files whose `type` is not `dataset`. The real `type` of `CITATION.cff` and `upload_type` of `.zenodo.json` were read afterwards.
- DataLad's `.datalad/config` is a 63-byte template, identical in every dataset, so it cannot be partitioned by size. The three largest owners (OpenNeuroDatasets, nemarDatasets, OpenNeuroDerivatives) were harvested separately; about 800 files from other owners are missing.

#### Research filter

For each of the 36038 candidate repositories, the README, `CITATION.cff`, `.zenodo.json` and the license detected by GitHub were fetched (GraphQL API). Indicators:

| Indicator | Rule | Repos |
|---|---|---|
| Declared as data | `CITATION.cff` `type: dataset`, `.zenodo.json` `upload_type: dataset`, or a DataLad dataset | 8707 |
| Own DOI | A DOI from the README or from the top-level `doi`/`identifiers` of `CITATION.cff` (not `preferred-citation` nor `references`) whose DataCite record has the repository as `url` or related identifier. DOIs of other agencies (Crossref: mostly articles) do not count. | 2829 |
| ORCID | In the README, `CITATION.cff` or `.zenodo.json` | 2858 |
| Data license | CC, ODbL, PDDL or ODC-By | 2614 |
| Publication link | arXiv, bioRxiv, medRxiv, PsyArXiv, OSF Preprints or SSRN in the README. It is a citation to another work, so it is reported separately. | 2420 |

The own-DOI check only sees DOIs mentioned in the repository: a repository archived in Zenodo whose README does not show the DOI is missed (e.g. many `lexibank` and `cldf-datasets` repositories). Querying DataCite per repository (about 5 s each) was not viable for 36000 candidates. Unfilled template DOIs (`zenodo.xxxxxxx`) are frequent.

#### Data in a re3data repository

Path: DOI → DataCite client → the client's re3data DOI (`10.17616/R3...`) → re3data id → `drepo_2`. GitHub, Bitbucket, SourceForge and Kaggle are excluded as targets, since they are themselves in re3data.

- Confirmed: the own DOI belongs to a re3data repository.
- Mirror: the repository belongs to OpenNeuroDatasets or OpenNeuroDerivatives (OpenNeuro, r3d100010924) or nemarDatasets (NEMAR, r3d100013945). NEMAR's DOIs are registered by the "UC San Diego" DataCite client, which has no re3data id.
- Possible: the README cites a DataCite DOI of type Dataset in a re3data repository that does not point back to the repository. It may be the same data or other data.
- Neither: no link to a re3data repository was found.

| Research criterion | Repos | Confirmed | Mirror | Possible | Neither |
|---|---|---|---|---|---|
| At least one indicator (own DOI, ORCID, data license) | 6445 | 2295 (35.6%) | 543 (8.4%) | 545 (8.5%) | 3062 (47.5%) |
| Same, or a publication link | 8477 | 2295 (27.1%) | 574 (6.8%) | 662 (7.8%) | 4946 (58.3%) |
| Declared as data, or an indicator | 11321 | 2295 (20.3%) | 1809 (16.0%) | 795 (7.0%) | 6422 (56.7%) |
| Same, or a publication link | 13115 | 2295 (17.5%) | 1809 (13.8%) | 902 (6.9%) | 8109 (61.8%) |

Declaring the type is a weak signal: it includes, for instance, 557 domain-name lists from `UniqueDomains` with `CITATION.cff` `type: dataset`. A data license alone is also weak: it admits benchmarks and rankings that are not research.

Confirmed cases are almost all Zenodo (2286 of 2295), through its GitHub integration; then figshare (6), Illinois Data Bank, 4TU.ResearchData, GigaDB, Mendeley Data and ReDATA. Possible cases: Zenodo, figshare, Harvard Dataverse, Mendeley Data, Dryad.

By source. "With indicator" uses the first criterion; confirmed, mirror and possible are counted over the third one (declared as data, or an indicator). A repository can come from several sources.

| Source | Repos | With indicator | Confirmed | Mirror | Possible |
|---|---|---|---|---|---|
| `CITATION.cff` dataset | 5091 | 2537 | 1073 | 1 | 388 |
| `.zenodo.json` dataset | 2084 | 1444 | 772 | 0 | 232 |
| DataLad | 2199 | 566 | 6 | 543 | 4 |
| `datapackage.json` | 1798 | 125 | 34 | 0 | 3 |
| RO-Crate | 936 | 226 | 162 | 0 | 3 |
| `topic:dataset` | 21386 | 1964 | 555 | 0 | 322 |
| `topic:datasets` | 3828 | 246 | 55 | 0 | 28 |
| `topic:research-data` | 494 | 125 | 44 | 0 | 14 |
| `topic:data-repository` | 73 | 14 | 6 | 0 | 1 |
| `topic:datapackage` | 66 | 15 | 4 | 0 | 0 |
