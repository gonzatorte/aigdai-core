import xmlschema
import os
print('__file__', __file__)


def generate_attribute_list():
    base_xsd_path = './re3dataV2-2-original.xsd'
    fil_path = f"{os.path.dirname(__file__)}/{base_xsd_path}"
    print('absolute_path', fil_path)
    schema = xmlschema.XMLSchema(fil_path, allow="local")


    # { descr: , name: , enums: [{desc, value}], child: , presence: array | noEmptyArray | optional | required, type: number | string | enum }
    def to_attr_extractor(attr, elem):
        # attr.annotation
        if attr.type.__class__ is xmlschema.validators.elements.XsdElement:
            # if (attr.type.content.model === 'sequence'):
            #     childs = list(attr.type.content)
            elem['children'] = {}
            for chattr in attr:
                elem[attr.local_name] = {}
                to_attr_extractor(chattr, elem[attr.local_name])
        elif attr.type.local_name == 'yesno':
            elem[attr.local_name] = lambda vv: vv == 'yes'
        elif attr.type.local_name == 'yesnoun':
            elem[attr.local_name] = lambda vv: None if vv == 'unknown' else True if vv == 'yes' else False
        elif attr.type.local_name == 'dateFormat':
            elem[attr.local_name] = attr
        elif attr.type.__class__ is xmlschema.validators.simple_types.XsdAtomicRestriction:
            if attr.type.validion.max_length:
                pass
            else:
                enums = []
                if attr.type.validators[0].__class__ is xmlschema.validators.facets.XsdEnumerationFacets:
                    for (idx, value) in enumerate(attr.type.validators[0].enumeration):
                        enumOfIdx = attr.type.validators[0].get_annotation(idx)
                        enums.append((value, enumOfIdx))
                # ToDo: Check given value belongs to enum
                elem[attr.local_name] = attr

        # elif attr.type.__class__ is xmlschema.validators.simple_types.XsdUnion:
        #     list(attr.type.iter_components())
        else:
            raise ValueError()

        if not attr.occurs:
            raise ValueError()
        elif attr.occurs[0] is None:
            if attr.occurs[1] == 0:
                raise ValueError()
            elif attr.occurs[1] == 1:
                raise ValueError()
            elif attr.occurs[1] is None:
                raise ValueError()
            else:
                raise ValueError()
        elif attr.occurs[0] == 1:
            if attr.occurs[1] == 0:
                raise ValueError()
            elif attr.occurs[1] == 1:
                return elem
            elif attr.occurs[1] is None:
                return {
                    'first': elem,
                    'rest': [elem],
                }
            else:
                raise ValueError()
        elif attr.occurs[0] == 0:
            if attr.occurs[1] == 0:
                return None
            elif attr.occurs[1] == 1:
                # ToDo: Ojo con los string vacios y etc
                return elem or None
            elif attr.occurs[1] is None:
                # ToDo: un array potencialmente vacio
                return []
            else:
                raise ValueError()
        else:
            raise ValueError()

    elems = []
    for attr in schema[0]:
        elem = {}
        to_attr_extractor(attr, elem)
        elems.append(elem)

    schema.to_dict('https://www.re3data.org/api/beta/repository/r3d100000001')
