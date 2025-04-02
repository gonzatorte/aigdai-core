

# ToDo: Más que un arbol deberia ser un DAG
capacities_tree = (['soporte'], 'capacidad_de_rdd', 'capacidad de rdd', 'capacity of data repo', [
    # ToDo: Reificar y poner otro atributo de evidencia a la relacion con soporte_para_periodo_de_embargo
    (['soporte'], 'periodo_de_embargo', 'embargo period', 'período de embargo', 'soporte_para_periodo_de_embargo_de_duracion_y = r / repositorio_soporta_periodo_de_embargo_de_duracion: repo -> natural, r repositorio_soporta_periodo_de_embargo_de_duracion y'),
    (['soporte'], 'api_para_cosecha', '', '', 'soporte_para_api_para_cosecha_tiene_api_para_cosecha_y = r / soporte_para_api_para_cosecha_tiene_api_para_cosecha: repo -> api_para_cosecha, r soporte_para_api_para_cosecha_tiene_api_para_cosecha y'),
    (['soporte'], 'exportacion_de_citas', 'cite export', 'exportación de citas', []),
    (['soporte'], 'integracion_con_red_social', 'social media integration', 'integración con red social', []),
    (['soporte'], 'servicio_de_curaduria', 'curatorial service', 'servicio de curaduría', []),
    (['soporte'], 'servicio_de_versionado', 'versioning service', 'servicio de versionado', []),
    (['soporte'], 'lenguaje_de_interfaz', 'gui language', 'lenguaje de interfaz', []), # ToDo: Subclases no se declaran explicitamente...
    # Se puede soportar declarar (en metadatos), o se puede soportar alojar... o que otra accion relativa a un repositorio? curar? adminstrar? previsualizar? cosechar? que relacion hay entre esas acciones?
    (['soporte', 'declarar'], 'caracteristica_de_cdd' 'dataset characteristic', 'caracteristica de cdd', [
        ('tipo_de_dato', '', '', []), # ToDo: Reificar
        ('formato_de_archivo', '', '', []), # ToDo: Relacion con tipo_de_dato?
        ('esquema_de_id_persistente', '', '', []), # ToDo: Reificar. ToDo: Definir todas sus subclases a partir de cada enumerado particular...
        ('esquema_de_metadatos', 'metadata schema', 'esquema de metadatos', []), # ToDo: el esquema de metadatos da mas informacion sobre el resto de las cosas
        ('licencia', '', '', []),
        ('caracteristica_de_cdd', '', '', [ # ToDo: Cual era la diferencia con soporte_para_caracteristica_de_cdd? esta se diferencia de la anterior por no ser reificada?
            ('tamanio', '', '', [
                ('tamanio_en_disco', '', '', []),
                ('cantidad_de_contenedores', '', '', []),
                ('cantidad_de_elementos', '', '', []),
            ]),
        ]),
    ]),
])

def generate(ct, parent_id, acc, visited):
    tags, idd, spa_name, eng_name, children = ct
    if 'soporte' in tags:
        # support for
        # soporte para
        # soporte_para_
        pass
    idd = f'rdd_que_provee_{idd}'
    if idd in visited:
        return
    visited.append(idd)
    acc += f'''
<Declaration>
    <Class IRI="{idd}"/>
</Declaration>
<SubClassOf>
    <Class IRI="{idd}"/>
    <Class IRI="{parent_id}"/>
</SubClassOf>
<AnnotationAssertion>
    <AnnotationProperty IRI="nombre_usual"/>
    <IRI>{idd}</IRI>
    <Literal xml:lang="en">{eng_name}</Literal>
</AnnotationAssertion>
<AnnotationAssertion>
    <AnnotationProperty IRI="nombre_usual"/>
    <IRI>{idd}</IRI>
    <Literal xml:lang="es">{spa_name}</Literal>
</AnnotationAssertion>
    '''
    if type(children) is list:
        for child in children:
            generate(child, idd, acc, visited)

generate(capacities_tree, 'owl:Thing', '', [])

# ToDo: Renombrar a "soporte para describir caracteristica"

# ToDo: Falta Regla: x soporte_para_api_para_cosecha_tiene_api_para_cosecha a ^ r repositorio_aporta_funcionalidad a -> r soporte_para_api_para_cosecha a ??
#   Sería la version directa sin evidencias

# ToDo: Falta definir todas las subclases parametricas de soporte_para_api_para_cosecha a partir de la relacion soporte_para_api_para_cosecha_tiene_api_para_cosecha
#     <Declaration>
#         <DataProperty IRI="soporte_para_api_para_cosecha_tiene_url"/>
#     </Declaration>
#     <DataPropertyDomain>
#         <DataProperty IRI="soporte_para_api_para_cosecha_tiene_url"/>
#         <Class IRI="soporte_para_api_para_cosecha"/>
#     </DataPropertyDomain>
#     <DataPropertyRange>
#         <DataProperty IRI="soporte_para_api_para_cosecha_tiene_url"/>
#         <Datatype abbreviatedIRI="xsd:string"/>
#     </DataPropertyRange>
#     <Declaration>
#         <ObjectProperty IRI="soporte_para_api_para_cosecha_tiene_api_para_cosecha"/>
#     </Declaration>
#     <ObjectPropertyDomain>
#         <ObjectProperty IRI="soporte_para_api_para_cosecha_tiene_api_para_cosecha"/>
#         <Class IRI="soporte_para_api_para_cosecha"/>
#     </ObjectPropertyDomain>
#     <ObjectPropertyRange>
#         <ObjectProperty IRI="soporte_para_api_para_cosecha_tiene_api_para_cosecha"/>
#         <Class IRI="api_para_cosecha"/>
#     </ObjectPropertyRange>
# <!--    <HasKey>-->
# <!--        <Class IRI="soporte_para_api_para_cosecha"/>-->
# <!--        <DataProperty IRI="soporte_para_api_para_cosecha_tiene_url"/>-->
# <!--    </HasKey>-->

# ToDo: Falta definir todas las subclases parametricas de soporte_para_lenguaje_de_interfaz a partir de la relacion soporte_para_lenguaje_de_interfaz_tiene_lenguaje
#     <Declaration>
#         <DataProperty IRI="soporte_para_lenguaje_de_interfaz_tiene_lenguaje"/>
#     </Declaration>
#     <DataPropertyDomain>
#         <DataProperty IRI="soporte_para_lenguaje_de_interfaz_tiene_lenguaje"/>
#         <Class IRI="soporte_para_lenguaje_de_interfaz"/>
#     </DataPropertyDomain>
#     <DataPropertyRange>
#         <DataProperty IRI="soporte_para_lenguaje_de_interfaz_tiene_lenguaje"/>
#         <Datatype abbreviatedIRI="lang:lenguaje"/>
#     </DataPropertyRange>
#     <FunctionalDataProperty>
#         <DataProperty IRI="soporte_para_lenguaje_de_interfaz_tiene_lenguaje"/>
#     </FunctionalDataProperty>