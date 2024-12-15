import asyncio
import httpx
import re

from lib import run_in_parallel

dsm_ids: list[str] = [
  # 'dsm-0-c0',
  # 'dsm-0-c1',
  # 'dsm-0-c2',
  # 'dsm-0-h1',
  # 'dsm-0-h2',
  # 'dsm-0-h3',
  # 'dsm-0-r1',
  # 'dsm-0-r2',
  # 'dsm-0-r3',
  # 'dsm-0-r4',
  # 'dsm-0-r5',
  'dsm-1-c0',
  'dsm-1-c1',
  'dsm-1-c2',
  'dsm-1-c3',
  'dsm-1-h1',
  'dsm-1-h2',
  'dsm-1-h3',
  'dsm-1-h4',
  'dsm-1-r0',
  'dsm-1-r1',
  'dsm-1-r2',
  'dsm-1-r3',
  'dsm-1-r4',
  'dsm-1-r5',
  'dsm-2-c1',
  'dsm-2-c2',
  'dsm-2-c3',
  'dsm-2-c4',
  'dsm-2-c5',
  'dsm-2-c6',
  'dsm-2-c7',
  'dsm-2-h1',
  'dsm-2-h2',
  'dsm-2-h3',
  'dsm-2-r1',
  'dsm-2-r2',
  'dsm-2-r3',
  'dsm-2-r4',
  'dsm-2-r5',
  'dsm-3-c1',
  'dsm-3-c2',
  'dsm-3-c3',
  'dsm-3-c4',
  'dsm-3-c5',
  'dsm-3-c6',
  'dsm-3-c7',
  'dsm-3-h1',
  'dsm-3-h2',
  'dsm-3-h3',
  'dsm-3-h4',
  'dsm-3-r1',
  'dsm-3-r2',
  'dsm-3-r3',
  'dsm-3-r4',
  'dsm-3-r5',
  'dsm-4-c1',
  'dsm-4-c2',
  'dsm-4-c3',
  'dsm-4-c4',
  'dsm-4-c5',
  'dsm-4-h1',
  'dsm-4-h2',
  'dsm-4-h3',
  'dsm-4-r1',
  'dsm-4-r2',
  'dsm-4-r3',
  'dsm-4-r4',
  'dsm-4-r5',
  'dsm-4-r6',
  'dsm-5-c1',
  'dsm-5-c2',
  'dsm-5-c3',
  'dsm-5-c4',
  'dsm-5-c5',
  'dsm-5-h1',
  'dsm-5-h2',
  'dsm-5-h3',
  'dsm-5-r1',
  'dsm-5-r2',
  'dsm-5-r3',
  'dsm-5-r4',
  'dsm-5-r5',
]

full_dsm = [
  ('dsm-lvl-1', 'This is a **data-related** requirement. The Dataset is assigned a unique identifier such that it can be referenced unambiguously.', 'Content and Context', 'Dataset', 'F1. (Meta)data are assigned a globally unique and persistent identifier', ['dsm-1-r2'], ['RDA-F1-02D', 'FsF-F1-01D']),
  ('dsm-lvl-1', 'This is a **metadata-related** requirement. Metadata should include summary information about the study or project that the Data Object is related to. This is basic contextual-metadata that will allow minimum levels of human interpretation of the data being shared.', 'Content and Context', 'Project', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', [], []),
  ('dsm-lvl-1', 'This is a **metadata-related** requirement. Metadata should include the Dataset Identifier it is describing AND descriptive information about the Dataset as a whole to enable Search-ability and Findability of Data (e.g., name, description, keywords).', 'Content and Context', 'Dataset', 'F3. Metadata clearly and explicitly include the identifier of the data they describe, R1. Meta(data) are richly described with a plurality of accurate and relevant attributes.', [], ['RDA-F3-01M', 'RDA-F2-01M', 'F2F-F2-01M', 'FsF-F3-01M']),
  ('dsm-lvl-1', 'This is a **metadata-related** requirement. Metadata should include Both access level and conditions  necessary  to potentially gain access to the data', 'Content and Context', 'Dataset', 'A1. (Meta)data are retrievable by their identifier using a standardised communications protocol', [], ['RDA-A1-01M', 'FsF-A1-01M']),
  ('dsm-lvl-1', 'The hosting environment stores for each data object a related metadata record, which enables findability. At this basic level of maturity, there is no restriction on the persistence model for the metadata records as long as the representation for data exchange is offered in accordance to a standard generic metadata schema (DSM-1-R4) ', 'Hosting Environment', '', 'A1. (Meta)data are retrievable by their identifier using a standardised communications protocol', ['dsm-1-r4'], ['RDA-F1-01M', 'RDA-F1-01D']),
  ('dsm-lvl-1', 'This indicator focuses on the resolvability and persistence of the Identifier, which needs to be guaranteed by the hosting environment.', 'Hosting Environment', '', 'A1. (Meta)data are retrievable by their identifier using a standardised communications protocol', [], ['RDA-A1-03M', 'RDA-A1-03D', 'FsF-F1-02D']),
  ('dsm-lvl-1', 'Standardised protocol implementation facilitates access of the data and metadata such as HTTP, FTP (e.g. simple links for download).', 'Hosting Environment', '', 'A1.1 The protocol is open, free, and universally implementable.', [], ['RDA-A1.1-01D']),
  ('dsm-lvl-1', 'This capability is enabled by the Metadata Hosting Environment storing and indexing the metadata that is included in the Dataset Descriptor (F+MM-1.H2). As a gained benefit, the hosting environment should be able to offer simple keyword search against their locally defined metadata schema to enable basic human led discoverability of the associated datasets.', 'Hosting Environment', '', 'F4. (Meta)data are registered or indexed in a searchable resource', [], []),
  ('dsm-lvl-1', 'The Metadata describing the dataset description is conformed as an object that can be identified and it is called a Dataset Descriptor.', 'Metadata Representation', 'Dataset', 'F1. (Meta)data are assigned a globally unique and persistent identifier', [], ['RDA-F1-01M']),
  ('dsm-lvl-1', 'The Dataset Descriptor of the dataset includes metadata that describes the context in which the dataset was produced within.', 'Data Representation', 'Dataset', 'F2. Data are described with rich metadata', [], ['RDA-F2-01M']),
  ('dsm-lvl-1', "This is a pre-requisite requirement to *define* the *unit* of data that is the subject-matter of the FAIRification process. This requirement requires the data managers to consider the form and the representation of data into [Datasets](https://fairplus.github.io/Data-Maturity/docs/Glossary/#dataset) that are designed and purposed for sharing and re-use by users unfamiliar with the data. Once defined, a Dataset should be assigned an identifier as indicated by [DSM-1-C0](https://fairplus.github.io/Data-Maturity/docs/Indicators/#DSM-1-C0), which then makes it an Identifiable Dataset. <br><br> What this requirement is trying to advice against are decisions to FAIRify data stored in databases according to a defined schema without defining the 'data exchange unit' that is meant for sharing and re-use. ", 'Data Representation', 'Dataset', 'Foundational Principle', [], []),
  ('dsm-lvl-1', 'The Dataset Descriptor includes what are considered the essential elements to describe the data.', 'Metadata Representation', 'Dataset', 'R1.3. (Meta)data meet domain-relevant community standards', [], ['RDA-R1.3-01M', 'FsF-R1.3-01M']),
  ('dsm-lvl-1', 'This is a **format-related** requirement that focuses on machine-readability aspect of the metadata. This is a pre-requisite requirement to having the metadata indexed and searchable in a hosting resource [DSM-1-H4](https://github.com/FAIRplus/Data-Maturity/blob/master/docs/_indicators/DSM-1-H4.md).', 'Metadata Format', 'Dataset', 'F4. (Meta)data are registered or indexed in a searchable resource', [], ['RDA-F4-01M', 'RDA-I1-01M', 'FsF-I1-01M']),
  ('dsm-lvl-1', 'This is a **format-related** requirement that focuses on machine-readability aspect of the data. This is a pre-requisite requirement to having the data indexed and searchable in a hosting resource [DSM-1-H4](https://github.com/FAIRplus/Data-Maturity/blob/master/docs/_indicators/DSM-1-H4.md).', 'Data Format', 'Dataset', 'F4. (Meta)data are registered or indexed in a searchable resource', [], ['RDA-I1-01D', 'FsF-R1.3-02D']),
  ('dsm-lvl-2', "This is a **metadata-related requirement** focusing on context and domain description. This is an entry level requirement to describe the 'Domain' of the data, which at this level might not be fully represented by either the hosting environment or an adopted standard (level 3). The Metadata Record should include information that can help a researcher understand the data context, especially in relation to the overall project or study design that this dataset belongs to as well as the entities that are represented by the dataset content. ", 'Content and Context', 'Dataset', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', [], ['RDA-R1-01M', 'FsF-R1-01MD']),
  ('dsm-lvl-2', "This is a **data-related requirement** that is a pre-requisite for the 'accuracy' of metadata that FAIR principle (R1) refers to. This requirement is borrowed from one of the key Tidy Data Principles, which states that each column/field should be a **single** variable. This prevents the often seen scenario in structured data whereby a single column header might carry values for more than one variable. For example, 'temperature_screening', 'temperature_followup', each column implicitly carries the value for a **visit** variable and a value for an observation **temperature** in this case. This indicator therefore requires the data manager to split these variables into two fields: One per variable that is a field for **temperature** and a field for **visit**. This is a pre-requisite to DSM-2-C5 and DSM-2-C6 since each Dataset Field is expected to control its terms and create a local dictionary. Unless individual concepts are reported per Dataset Field it will not be possible to find suitable terms that can later be standardised for level 3. ", 'Content and Context', 'Dataset Fields', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', ['dsm-2-c5', 'dsm-2-c6'], []),
  ('dsm-lvl-2', 'The Dataset(s) includes Reference Fields that allows the joining of other datasets that might or not be part of the same project.', 'Content and Context', 'Dataset Fields', '', [], []),
  ('dsm-lvl-2', "This is a **data-related requirement** that focuses on the consistency of a Dataset's textual content. This is also related to the 'accuracy' and overall consistency of data content within and across multiple related project datasets. Level 2 content standardisation is not required to comply with standard terminologies or ontologies. However, to achieve Level 2 content standardisation, textual values reported in text-based Dataset Fields are expected to be consistently reported using locally defined terms. These local terms are defined in a local Data Dictionary that ought to be reported as well as part of the content-related metadata (DSM-2-C6). ", 'Content and Context', 'Dataset Field Values', 'F2. Data are described with rich metadata, R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', ['dsm-2-c6'], []),
  ('dsm-lvl-2', 'The Reference Fields that allow you to join Datasets are included in the Dataset Descriptor (metadata).', 'Content and Context', 'Dataset Level', '', ['dsm-2-c3'], []),
  ('dsm-lvl-2', "This is a **metadata-related requirement** focusing on the Dataset's structure. This is a requirement to include structural metadata into the Dataset's Metadata Record irrespective of how this information is represented (DSM-2-R1). Dataset-Field metadata include 'field name', 'description', 'data type' ", 'Content and Context', 'Dataset Field', 'F2. Data are described with rich metadata, R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', ['dsm-2-r1'], ['RDA-F2-01M', 'FsF-R1-01MD']),
  ('dsm-lvl-2', 'This is a **metadata-related requirement**. This indicator is related to F+MM-2.C5, which requires that textual data values used within and across related datasets should consistently reported using locally defined terms or values. In case of using numeric values instead of textual values, a data dictionary is needed to map these values and allow users to interpret the data. Therefore, a data dictionary that associated each Dataset Field with its associated list of permissible terms or values and their meanings should also be made available. This could either be represented inside the Metadata Record itself if the metadata schema allows (DSM-2-R3), or otherwise represented separately.', 'Content and Context', 'Dataset Field Values', 'F2. Data are described with rich metadata, R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', ['dsm-2-r3'], []),
  ('dsm-lvl-2', 'This is a **data-storage related requirement.** In order to provide a basic level of contextual browsing or searching capabilities, the data hosting environment/resource should offer a common data model albeit being a locally defined one or project-specific one, against which all hosted datasets can be navigated and explored against.', 'Hosting Environment', '', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', [], []),
  ('dsm-lvl-2', "This is a **metadata-retrieval-related** requirement. The metadata hosting environment (which could be the same or different from the data hosting environment) should offer the capability to retrieve the Dataset's Metadata Record using API technologies like REST, RPC or GRAPHQL. ", 'Hosting Environment', '', 'A1. (Meta)data are retrievable by their identifier using a standardised communications protocol', [], ['RDA-A1.1-01M', 'FsF-A1-02M']),
  ('dsm-lvl-2', "This capability provides enhanced contextual interpretation of multiple related datasets when they are commonly linked to a study or a project. This capability is enabled by the hosting environment's capitalising on contextual metadata and dataset structural metadata made available at this level of maturity and established by dsm-22c, dsm24c and dsm-26c.", 'Hosting Environment', '', 'F4. (Meta)data are registered or indexed in a searchable resource', ['dsm-22c, dsm-24c, dsm-26c'], []),
  ('dsm-lvl-2', "This is a **metadata-related requirement** focusing on the representation of the reported **Contextual Metadata** (DSM-2-C2). For level 2, having a human interpretable representation suffices to pass this requirement. This can be a visual diagram, or textual documentation that can be available from the hosting environment's documentation pages.  ", 'Metadata Representation', 'Project', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', [], ['RDA-R1.3-01M', 'FsF-R1.3-01M']),
  ('dsm-lvl-2', 'This is a **data-modelling related requirement**. More specifically, this indicator focuses on the data model used to describe the structure of the Dataset which is the form that data is modelled against for the purpose of being utilized for FAIR sharing and re-use (DSM-2-C1). At Level 2, this model is simply a set of defined Dataset Types or Names and their respective Dataset Fields to be used consistently by all project related Datasets. <br> <br> This is often represented in the form of pre-defined templates that data owners define for their project data or made available by the data hosting environment to be used for importing and exporting the FAIRified Datasets. This is to guarantee a minimum level of consistency amongst similarly reported datasets, which directly affects the **storage** capability of the hosting environment. This consistency will enable the hosting environment to store and index multiple datasets against this locally defined dataset model and hence offer better searching and discovery capabilities.', 'Data Representation', 'Dataset', 'R1. Meta(data) are richly described with a plurality of accurate and relevant attributes', [], []),
  ('dsm-lvl-2', 'This is a **metadata-modelling requirement** focusing on the representation of the Dataset Field level and Field Value level metadata required by DSM-2-C4 and DSM-2-C6. This indicator requires that the chosen standard metadata schema used to describe the Dataset should be amenable to represent structural metadata about the Dataset. Each Dataset Field will have a name, description, data type ...etc. Value related metadata may include reference to local dictionary of controlled terms used in each field. Examples of generic metadata schemas supporting field-level metadata are DATS and BioSchemas Dataset.', 'Metadata Representation', 'Dataset', '', [], ['RDA-R1.3-02M']),
  ('dsm-lvl-2', '', 'Metadata Format', 'Dataset', '', [], []),
  ('dsm-lvl-2', 'This is a **data-related formatting requirement**. The exchange format used to share the Dataset(s) should be readable by machines. This is not a requirement to use semantic representations, this is a simple requirement to use standard formats (e.g. CSV, JSON, XML or similar) for data exchanged via the relevant API (DSM-2-H2).', 'Data Format', 'Dataset', 'I1. (Meta)data use a formal, accessible, shared, and broadly applicable language for knowledge representation.', ['dsm-2-h2'], ['RDA-I1-02D']),
  ('dsm-lvl-3', 'This is a **metadata-related requirement** focusing on standardisation of context and domain representation. Minimum information standards are sets of guidelines and formats for reporting data derived by specific high-throughput methods. Their purpose is to ensure the data generated by these methods can be easily verified, analysed and interpreted by the wider scientific community', 'Content and Context', 'Project/Study', 'R1.3. (Meta)data meet domain-relevant community standards', [], ['RDA-R1.3-01M', 'FsF-R1.3-01M']),
  ('dsm-lvl-3', 'This is a **data-related requirement** focusing on standardisation of the type and definition of Dataset(s) that should be reported for a given subject-area or a study type. Minimum information standards are sets of guidelines and formats for reporting data derived by specific high-throughput methods. Their purpose is to ensure the data generated by these methods can be easily verified, analysed and interpreted by the wider scientific community', 'Content and Context', 'Dataset', 'R1.3. (Meta)data meet domain-relevant community standards', [], ['RDA-R1.3-01D']),
  ('dsm-lvl-3', '', 'Content and Context', 'Dataset', 'R1.1. (Meta)data are released with a clear and accessible data usage license', [], ['RDA-R1.1-01M', 'RDA-R1.1-02M', 'FsF-R1.1-01M']),
  ('dsm-lvl-3', 'This is a **data-related requirement** focusing on the standardisation of the terminologies used within and across related Datasets. This indicator focuses on the set of data values for a given dataset field. To promote interoperability and enable the hosting environment to carry out cross-study queries, dataset textual field values should be standardised against community-standard controlled terminology or ontologies.', 'Content and Context', 'Dataset Field Values', 'I2. (Meta)data use vocabularies that follow FAIR principles, R1.3. (Meta)data meet domain-relevant community standards', [], ['RDA-I2-01D']),
  ('dsm-lvl-3', 'This is a **metadata-related requirement** related to F+MM-3.C4. Dataset Field Values are expected to use standard terminology that are defined and described by other external resources. This indicator requires that for each term used a reference to its external definition is included in either the dataset itself (e.g. as a separate related field) or in a metadata record as specified by the Dataset Exchange Model if applicable.', 'Content and Context', 'Dataset Field Values', 'I2. (Meta)data use vocabularies that follow FAIR principles, I3. (Meta)data include qualified references to other (meta)data', [], ['RDA-I3-01M', 'RDA-I3-01D']),
  ('dsm-lvl-3', '', 'Content and Context', 'Dataset', '', [], []),
  ('dsm-lvl-3', '', 'Content and Context', 'Dataset', '', [], []),
  ('dsm-lvl-3', '', 'Hosting Environment related requirements', '', '', [], []),
  ('dsm-lvl-3', 'This indicator is about the resolution of the identifier that identifies the dataset. The hosting environment should assign a persistent identifier to the dataset and associate it with a formally defined retrieval/resolution mechanism for dataset access and retrieval.', 'Hosting Environment related requirements', '', 'F1. (Meta)data are assigned a globally unique and persistent identifier.', [], ['RDA-F1-01D', 'RDA-A1-03D', 'FsF-F1-02D']),
  ('dsm-lvl-3', 'This indicator requires the hosting environment to offer enhanced data discovery capabilities. This can be achieved by linking multiple related datasets through an implementation of a common domain model (DSM-3-R1), which allows users to search and find contextually-related datasets. Datasets at this level are expected to use annotated and described standardised Dataset Fields (DSM-3-R2) and their content to use standardised value terms and concepts (DSM-3-C2). The hosting resource should therefore capitalise on these rich annotations and allow users to search across datasets for concepts and standard terms in their content through the use of ontology-related query expansions.', 'Hosting Environment related requirements', '', 'F1. (Meta)data are assigned a globally unique and persistent identifier', [], []),
  ('dsm-lvl-3', 'This indicator requires the hosting resource to provide a more granular approach to data accessibility. A dataset level authorisation capability would allow data owners to define user-access rights per dataset rather than on a project or study based level.', 'Hosting Environment related requirements', '', 'A1.2 The protocol allows for an authentication and authorisation procedure, where necessary.', [], ['RDA-A1.2-01D']),
  ('dsm-lvl-3', '', 'Metadata Representation', 'Dataset', '', [], []),
  ('dsm-lvl-3', '', 'Data Representation', 'Dataset-level', '', [], []),
  ('dsm-lvl-3', '', 'Data Representation', 'Dataset-level', '', [], ['RDA-R1.3-01D']),
  ('dsm-lvl-3', '', 'Data Format', 'Dataset-level', '', [], []),
  ('dsm-lvl-3', '', 'Data Format', 'Dataset-level', '', [], []),
  ('dsm-lvl-4', 'When dataset(s) are typed semantically, means that the data is structured and represented in a logical way. It adds a basic meaning to the data and the relationships that lie between them, for data consisteny and easy maintenance.', 'Content-related requirements', 'Dataset', 'I1. (Meta)data use a formal, accessible, shared, and broadly applicable language for knowledge representation.', [], []),
  ('dsm-lvl-4', 'When dataset(s) are typed semantically, means that the data is structured and represented in a logical way. It adds a basic meaning to the data and the relationships that lie between them, for data consisteny and easy maintenance.', 'Content-related requirements', 'Dataset Fields', 'I1. (Meta)data use a formal, accessible, shared, and broadly applicable language for knowledge representation.', [], []),
  ('dsm-lvl-4', '', 'Content-related requirements', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-4', '', 'Content-related requirements', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-4', '', 'Content-related requirements', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-4', '', 'Hosting Environment', 'Search Capability', '', [], []),
  ('dsm-lvl-4', '', 'Hosting Environment', 'Semantic Querying Capability', '', [], []),
  ('dsm-lvl-4', '', 'Hosting Environment', 'Search Capability', '', [], []),
  ('dsm-lvl-4', '', 'Metadata representation', 'Dataset', '', [], []),
  ('dsm-lvl-4', '', 'Data representation', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-4', '', 'License representation', 'Dataset', '', [], []),
  ('dsm-lvl-4', '', 'License representation', 'Dataset', '', [], []),
  ('dsm-lvl-4', '', 'License representation', 'Dataset', '', [], []),
  ('dsm-lvl-4', '', 'License representation', 'Dataset', '', [], []),
  ('dsm-lvl-5', '', 'Content and Context', 'Dataset Fields', '', [], []),
  ('dsm-lvl-5', '', 'Content and Context', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-5', '', 'Content and Context', 'Dataset', '', [], ['RDA-R1.2-01M', 'FsF-R1.1-01M']),
  ('dsm-lvl-5', '', 'Content and Context', 'Dataset', '', [], []),
  ('dsm-lvl-5', '', 'Content and Context', 'Dataset', '', [], []),
  ('dsm-lvl-5', '', 'Hosting Environment', '', '', [], []),
  ('dsm-lvl-5', '', 'Hosting Environment', '', '', [], []),
  ('dsm-lvl-5', '', 'Hosting Environment', '', '', [], []),
  ('dsm-lvl-5', '', 'Data Representation', 'Dataset Fields', '', [], []),
  ('dsm-lvl-5', '', 'Data Representation', 'Dataset Field Values', '', [], []),
  ('dsm-lvl-5', '', 'Data Representation', 'Dataset Field Values', '', [], []),
]

maturity_level_re = re.compile('.*\n\| Maturity Level \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
description_re = re.compile('.*\n\| Description \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
category_re = re.compile('.*\n\| Category \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
granularity_level_re = re.compile('.*\n\| Granularity Level \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
related_fair_principle_re = re.compile('.*\n\| Related FAIR Principle \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
related_dsm_indicator_re = re.compile('.*\n\| Related DSM Indicator \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)
cross_reference_fair_indicators_re = re.compile('.*\n\| (?:(?:Cross-reference)|(?:Cross-ref)) FAIR indicators \|([^|]*)\|', re.DOTALL | re.MULTILINE | re.IGNORECASE)

if __name__ == '__main__':
  async def run():
    async with httpx.AsyncClient() as http_client:
      async def fetch_single_doi_local(b: str):
        response = await http_client.get(
          'https://raw.githubusercontent.com/FAIRplus/Data-Maturity/refs/heads/master/docs/_indicators/%s.md' % (
            b.upper(),), timeout=20)
        if response.status_code == 404:
          raise Exception()
        rr = response.text
        # maturity_level = maturity_level_re.match(rr)
        description = description_re.match(rr)
        category = category_re.match(rr)
        granularity_level = granularity_level_re.match(rr)
        related_fair_principle = related_fair_principle_re.match(rr)
        related_dsm_indicator = related_dsm_indicator_re.match(rr)
        cross_reference_fair_indicators = cross_reference_fair_indicators_re.match(rr)
        return (
          # maturity_level.groups()[0] if maturity_level is not None else None,
          description.groups()[0] if description is not None else None,
          category.groups()[0] if category is not None else None,
          # granularity_level.groups()[0] if granularity_level is not None else '',
          related_fair_principle.groups()[0] if related_fair_principle is not None else None,
          related_dsm_indicator.groups()[0] if related_dsm_indicator is not None else '',
          cross_reference_fair_indicators.groups()[0] if cross_reference_fair_indicators is not None else None,
        )
      full_data = []
      async for (cc, idd) in run_in_parallel(fetch_single_doi_local, dsm_ids, 20, 2):
        full_data.append(cc)
      print(full_data)
  asyncio.run(run())
