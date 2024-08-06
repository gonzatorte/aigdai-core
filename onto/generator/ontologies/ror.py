from owlready2 import *

onto = get_ontology('http://test.org/fake-ror.owl')


def initiate():
    with onto:
        # ToDo: Extend from foaf:organization
        class Organization(Thing):
            pass

        class is_parent(ObjectProperty, TransitiveProperty):
            domain = [Organization]
            range = [Organization]

        class is_successor(ObjectProperty, TransitiveProperty):
            domain = [Organization]
            range = [Organization]

        class is_related(ObjectProperty, SymmetricProperty):
            domain = [Organization]
            range = [Organization]

        # ToDo: Puedo definir disjoint en relaciones?
        AllDisjoint([is_parent, is_related])
        AllDisjoint([is_parent, is_successor])

        class activation_status(Datatype):
            equivalent_to = [OneOf(["active", "inactive"])]

        class is_active(DataProperty, FunctionalProperty):
            domain = [Organization]
            range = [activation_status]

        class has_website(DataProperty, FunctionalProperty):
            domain = [Organization]
            # ToDo: Use foaf:homepage
            range = [str]

        class has_name(DataProperty):
            domain = [Organization]
            # ToDo: Use foaf:name
            # ToDo: Agregar que puede tener typo = acronym, alias
            #  puede también tener un argument lang
            range = [str]

        class Type(Thing):
            domain = [Organization]
            range = [activation_status]
        types = list(map(lambda x: Type, [
            'Education',
            'Healthcare',
            'Company',
            'Archive',
            'Nonprofit',
            'Government',
            'Facility',
            'Funder',
            'Other',
        ]))
        AllDifferent(types)

        class has_type(ObjectProperty, FunctionalProperty):
            domain = [Organization]
            range = [Type]

    # Education: A university or similar institution involved in providing education and educating/employing researchers
    # Healthcare: A medical care facility such as hospital or medical clinic. Excludes medical colleges/universities, which should be categorized as “Education”.
    # Company: A private for-profit corporate entity involved in conducting or sponsoring research.
    # Archive: An organization involved in stewarding research and cultural heritage materials. Includes libraries, museums, and zoos.
    # Nonprofit: A non-profit and non-governmental organization involved in conducting or funding research.
    # Government: An organization that is part of or operated by a national or regional government and that conducts or supports research.
    # Facility: A specialized facility where research takes place, such as a laboratory or telescope or dedicated research area.
    # Funder: An organization that funds research.
    # Other: Use this category for any organization that does not fit the categories above.

    # Field name	Definition	Type	Required	Value required
    # admin	Container for administrative information about the record	Object	TRUE	TRUE     --> created: "date" : "2018-11-14", "last_modified" "date" : "2024-02-21",
    # domains	The domains registered to a particular institution	Array	TRUE	FALSE
    # established	Year the organization was established (CE)	Number	TRUE	FALSE
    # links	The organization's website and Wikipedia page	Array	TRUE	FALSE
    # locations	The location of the organization	Array	TRUE	TRUE


if __name__ == '__main__':
    initiate()
    import owlready2
    owlready2.JAVA_EXE = "/usr/bin/java"
    owlready2.sync_reasoner()
    if len(list(owlready2.default_world.inconsistent_classes())) != 0:
        raise Exception('Inconsistent ontology')
