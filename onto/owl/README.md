# Ontología para el modelado de repositorios de datos de investigación y su ecosistema

## Estructura de archivos

### Elementos del TBox (en su mayoría):
- [criterios.owl](./criterios.owl): Ontología que modela las relaciones entre distintos criterios de calidad de repositorios (eg: FAIR, TRUST, CoreTrustSeal, Recomendaciones del NIH, recomendaciones de PLOS, etc).
- [lenguajes.owl](./lenguajes.owl): Definición del datatype "lenguaje".
- [aigdai.owx](./aigdai.owx): Ontología principal que importa a las anteriores y los archivos XML que ahora detallo (elementos del ABox).

### Elementos del ABox:
- [commons.xml](./commons.xml): Elementos básicos (usados de manera similar a un enumerado) como formatos de archivo, tipos de archivo, esquemas de metadatos, esquema de identificadores, etc).
- [localizaciones.xml](./localizaciones.xml): Lista de países y regiones y sus relaciones de inclusión.
- [disciplinas.xml](./disciplinas.xml): Taxonomía de disciplinas tal como son expresadas por la DFG (taxonomía de Frascati y correspondiente crosswalk con DFG disponible pero elaborada aún).
- [organizaciones.xml](./organizaciones.xml): Una pequeña muestra de ROR de organizaciones de investigación (financiadores, universidades, institutos, etc.) y sus relaciones.
- [criterios.xml](./criterios.xml): Los elementos del ABox detallando las relaciones definidas en criterios.owl, elaborado a partir de la lectura de varias de las guías y recomendaciones de diferentes fuentes.
- [repositorios.xml](./repositorios.xml): Una pequeña muestra de los datos de repositorios extraídos desde datacite y re3data y sus relaciones con las demás entidades antes mencionadas.

## Modelo conceptual

Hablar de los 3 mundos?
    Proceso de investigación
    corpus de conocimiento disciplinar
    agentes y recursos tecnológicos
Hablar de los distintos niveles de abstracción y dirección de expansión considerados:
    los catálogos (entidades más o menos fijas).
    de los agentes y recursos (info relacional sobre objetos tangibles o naturales para los procesos de investigación).
    de las características o atributos de los mismos (sobre los que se definen criterios, conceptos que abstraen caracteristicas de los repositorios).

Hablar de la visión de una comunidad por preservar contenidos:
    Contenidos (recursos, objetos inertes)
    Comunidades (agentes, eg: organizaciones)
    Métricas? (+ politicas, + criterios de calidad, etc)
    Repositorios (nexo entre ambos, la flecha)

Hablar de la capacidad de la ontología de asociar diferentes lentes o capas a los mismos elementos de la realidad?
    eg: una misma organización puede ser un consumidor de servicios en un contexto, en otro un prestador de servicio
Hablar del dilema de definir una entidad nueva o de atribuir nuevas características a una entidad existente...
    Hay un patron llamado role-attribution?
    Las instancias deberían tener una identidad no artificial del propio modelo, sino que un valor e identidad comprensible para el usuario final.

### Conceptos principales y narrativa:
- repositorio: Los repositorios suelen alojar diferentes tipos de resultados de investigación (esta narrativa tb debería ser parte de anotaciones del modelo?)
- resultado_de_investigacion: 
- articulo: 
- cdd (mnemónico de Colección De Datos): 
- criterio_de_calidad: 

Adjuntar modelo semántico (diagrama de drawio):

## Pruebas y guía de uso

Probado con https://github.com/protegeproject/rdf-library con Protégé V5




Tiene que haber funcionalidaes de repositorios que son:
    - ObjectProperties (cuando el domain es un objeto)
    - DataProperties (cuando el domain no es un objeto)
    - Clases (cuando se precisa reificar pues la clase es una relación ternaria que incluye ademas una evidencia de esa relacion (eg: URL de la API que dice es compatible))
        - Aca hay que declarar tambien (por reglas?) la version más sencilla (Object Property o Data Property) que se desprende de la relacion reificada


