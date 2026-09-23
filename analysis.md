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
