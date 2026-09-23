# Technical debt

## 1. CCE-1 returns nothing on its criteria path

The CCE-1 question (`onto/preguntas_de_competencia/cce-1.rq`) joins two paths: the certifications applied to the repository and the quality criteria the repository satisfies. The second path never returns results, for three reasons:

1. **`repositorio_satisface_criterio` is not populated.** No source writes that property; it only exists in the TBox (with the chain `repositorio_satisface_criterio ∘ inv(extiende_de_criterio)`, which would propagate the satisfaction of a criterion to its statements).
2. **Certifications and criteria are not linked.** datacite generates `certificacion/cts` (class `certificacion`, a subclass of `criterio_de_calidad`) and the criteria population generates `criterio_de_calidad/cts_2022` with its statements. They are distinct individuals with no relation between them, so having the certification does not connect to its statements. The populator already flags this: `ToDo: I have to declare at least all the certifications (not "other") from re3data and datacite as quality criteria` (`onto/populator/populate.py`).
3. **The certification periods are missing.** The lines that would load the start and end are commented out in `sources/datacite.py` and `sources/dummy.py`, and they also pass the certificate instead of a date. Without them there is no way to know whether a certification is current.

**Pending decisions:**
- How to link certification and criterion: `owl:sameAs` between `certificacion/cts` and `criterio_de_calidad/cts_2022`, make the certification extend the criterion (`extiende_de_criterio`), or have datacite point directly to the versioned criterion.
- Where `repositorio_satisface_criterio` comes from: infer it from an applied, current certification (a rule or a populator step), or populate it from another source or manually.

## 2. Flows chosen by commenting and uncommenting code

The remaining scripts switch flows by editing the code: one call is commented out and another uncommented, or a hardcoded value is changed. These options should be exposed as command-line parameters with `argparse`, as was already done in `populate.py` and in the datacite, re3data and fairsharing extractors.

| Where | What is switched on or off today | Proposed CLI option |
|---|---|---|
| `onto/populator/ontology.py` | `onto_base_path` alternates between `'../owl/'` and `'onto/owl/'` depending on where it is run from | Resolve the path relative to `__file__`, or `--owl-dir` |
| `onto/populator/populate.py` (`serialize_file`), `reasoner/*.py`, `onto/populator/utils.py` (`reason_on_memory`) | Hardcoded read and write paths: `'../owl/…'`, `'./onto/owl/…'` and an absolute path under `/home/…` | `--owl-dir`, `--output` |
| `analysis.py` (`__main__`) | Which analysis to run (`re3data_institutions`, `analysis`, `fields_of_science_analysis`, …) | `analysis <name>` |
| `onto/populator/utils.py` (`reason_on_memory`) | Reasoner: `sync_reasoner` (HermiT) or `sync_reasoner_pellet` | `reason --reasoner hermit\|pellet` |
| `reasoner/elk_reasoner.py`, `reasoner/hermit_reasoner.py` | Alternative classpath commented out; hardcoded input ontology | `--ontology`, `--classpath` |
| `re3data/extractor.py` (`__main__`) | Test with a hardcoded id (`r3d100000001`) | `--id` |
| `re3data/xsd_transform.py` | Alternative XSD schema commented out (`base_xsd_path`); the `__main__` is a test with samples 3 to 8 commented out | `--xsd`; move the samples to tests (`pytest`) |
