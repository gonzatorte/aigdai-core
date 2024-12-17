# Ontología para el modelado de repositorios de datos de investigación y su ecosistema

## Estructura de archivos

### Elementos del TBox (en su mayoría):
- [principles.owl](./principles.owl): Ontología que modela las relaciones entre distintos criterios de calidad de repositorios (eg: FAIR, TRUST, CoreTrustSeal, Recomendaciones del NIH, recomendaciones de PLOS, etc).
- [languajes.owl](./languajes.owl): Definición del datatype "lenguaje".
- [aigdai.owx](./aigdai.owx): Ontología principal que importa a las anteriores y los archivos XML que ahora detallo (elementos del ABox).

### Elementos del ABox:
- [commons.xml](./commons.xml): Elementos básicos (usados de manera similar a un enumerado) como formatos de archivo, tipos de archivo, esquemas de metadatos, esquema de identificadores, etc).
- [locations.xml](./locations.xml): Lista de países y regiones y sus relaciones de inclusión.
- [disciplinas.xml](./disciplinas.xml): Taxonomía de disciplinas tal como son expresadas por la DFG (taxonomía de Frascati y correspondiente crosswalk con DFG disponible pero elaborada aún).
- [organizations.xml](./organizations.xml): Una pequeña muestra de ROR de organizaciones de investigación (financiadores, universidades, institutos, etc.) y sus relaciones.
- [criterios.xml](./criterios.xml): Los elementos del ABox detallando las relaciones definidas en principles.owl, elaborado a partir de la lectura de varias de las guías y recomendaciones de diferentes fuentes.
- [instances.xml](./instances.xml): Una pequeña muestra de los datos de repositorios extraídos desde datacite y re3data y sus relaciones con las demás entidades antes mencionadas.

