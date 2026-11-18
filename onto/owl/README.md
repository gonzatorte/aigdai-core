# Ontology for modeling research data repositories and their ecosystem

## File structure

### TBox elements (mostly):
- [criterios.owl](./criterios.owl): Ontology that models the relations between different repository quality criteria (e.g.: FAIR, TRUST, CoreTrustSeal, NIH recommendations, PLOS recommendations, etc.).
- [lenguajes.owl](./lenguajes.owl): Definition of the "lenguaje" (language) datatype.
- [aigdai.owx](./aigdai.owx): Main ontology, which imports the previous ones and the XML files detailed below (ABox elements).

### ABox elements:
The ABox (commons, locations, disciplines, ROR organizations, quality criteria and repositories) is built by the populator and written to an N-Triples file together with the TBox, to load into Fuseki (see [Populating Fuseki](../README.md#populating-fuseki)).
- [disciplinas.xml](./disciplinas.xml): Taxonomy of disciplines as expressed by the DFG (the Frascati taxonomy and the corresponding crosswalk with DFG are available but not yet elaborated). An earlier output of the populator, kept because aigdai.owx imports it; it is no longer regenerated.

## Conceptual model

ToDo:
    Talk about the 3 worlds?
        Research process
        body of disciplinary knowledge
        agents and technological resources
    Talk about the different levels of abstraction and directions of expansion considered:
        the catalogs (more or less fixed entities).
        the agents and resources (relational info about objects that are tangible or natural to research processes).
        their characteristics or attributes (over which criteria are defined, concepts that abstract characteristics of repositories).
    
    Talk about the vision of a community for preserving content:
        Contents (resources, inert objects)
        Communities (agents, e.g.: organizations)
        Metrics? (+ policies, + quality criteria, etc.)
        Repositories (the link between both, the arrow)
    
    Talk about the ontology's ability to associate different lenses or layers with the same elements of reality?
        e.g.: the same organization can be a consumer of services in one context and a service provider in another
    Talk about the dilemma of defining a new entity versus attributing new characteristics to an existing entity...
        Is there a pattern called role-attribution?
        Instances should not have an identity that is artificial to the model itself, but a value and identity understandable by the end user.

### Main concepts and narrative:
- repositorio: Repositories usually host different types of research outputs (should this narrative also be part of the model's annotations?)
- resultado_de_investigacion: 
- articulo: 
- cdd (mnemonic for Colección De Datos, data collection): 
- criterio_de_calidad: 

Attach the semantic model (drawio diagram):

## Testing and usage guide

Tested with https://github.com/protegeproject/rdf-library with Protégé V5
