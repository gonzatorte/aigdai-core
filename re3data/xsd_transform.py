from lxml import etree
import typing
import xmlschema
import os
import re
from xmlschema import XsdElement
from xmlschema.validators import XsdUnion
# from xmlschema import XsdType, ElementData
from copy import copy, deepcopy
import hashlib

class TransformError(Exception):
    def __init__(self, original_error: [Exception]):
        self.original_error = original_error


def load_schema():
    # base_xsd_path = './re3dataV2-2-lowercase-partial-lax.xsd'
    base_xsd_path = './re3dataV2-2-lowercase-partial.xsd'
    fil_path = f"{os.path.dirname(__file__)}/{base_xsd_path}"
    return xmlschema.XMLSchema(fil_path, allow="local")


# def element_hook(data_element: ElementData, xsd_element: XsdElement, xsd_type: XsdType):
#     if xsd_element.local_name == 'softwareName':
#         return ElementData(data_element.tag, data_element.text.lower(), data_element.content, data_element.attributes,
#                            data_element.xmlns)
#     if xsd_element.local_name == 'startDate':
#         return ElementData(data_element.tag, data_element.text, data_element.content, data_element.attributes,
#                            data_element.xmlns)
#     return data_element


# def value_hook(value: str | None, xsd_type: XsdType):
#     if xsd_type.local_name == 'softwareNames':
#         return value if value is None else value.lower()
#     if xsd_type.local_name == 'yesno':
#         return value if value is None else value.lower()
#     return value

DUMMY_NONE_DATE = '1990-01-01'


def validation_hook(element: etree.Element, xsd_element: XsdElement):
    if xsd_element.local_name == 'subject':
        if element.text:
            match = re.match('([0-9]+)', element.text)
            element.text = match.groups()[0]
    if xsd_element.local_name == 'softwareName':
        if element.text:
            element.text = element.text.lower()
    if xsd_element.type.local_name == 'yesno':
        if element.text:
            element.text = element.text.lower()
    if xsd_element.type.local_name == 'yesnoun':
        if element.text:
            element.text = element.text.lower()
    # if xsd_element.type.local_name == 'dateFormat':
    #     if element.text:
    #         element.text = element.text.lower()
    if xsd_element.local_name == 'size' :
        if 'updated' not in element.attrib or element.attrib['updated'] == '':
            element.attrib['updated'] = DUMMY_NONE_DATE
    return False


EMPTY_ATTRS = [
    'startDate', 'endDate', 'responsibilityStartDate', 'responsibilityEndDate', 'enhancedPublication',
    'qualityManagement', 'versioning',
    'size', 'missionStatementURL',
]

# subjectDummy = etree.Element("{http://www.re3data.org/schema/2-2}subject", nsmap={"r3d": 'http://www.re3data.org/schema/2-2'}, subjectScheme="DFG")
# subjectDummy.text = '202 Plant Sciences'
# repositoryLanguageDummy = etree.Element("{http://www.re3data.org/schema/2-2}repositoryLanguage", nsmap={"r3d": 'http://www.re3data.org/schema/2-2'})
# repositoryLanguageDummy.text = 'eng'
# providerTypeDummy = etree.Element("{http://www.re3data.org/schema/2-2}providerType", nsmap={"r3d": 'http://www.re3data.org/schema/2-2'})
# providerTypeDummy.text = 'serviceProvider'
MISSING_REQUIRED_ATTRS = {
    # 'subject': subjectDummy,
    # 'repositoryLanguage': repositoryLanguageDummy,
    # 'providerType': providerTypeDummy,
}

DUPP_ATTRS = [
    'startDate', 'endDate',
    # 'missionStatementURL', 'size', 'keyword', 'dataLicense',
    # 'subject',
    # 'contentType', 'databaseAccess', 'repositoryLanguage', 'dataUpload', 'institution',
    # 'providerType', 'versioning', 'dataAccess', 'dataUploadLicense', 'policy',
    # 'software', 'citationGuidelineURL', 'pidSystem',
    # 'aidSystem', 'enhancedPublication', 'api', 'databaseLicense',
    # 'qualityManagement',
    # 'remarks', 'metadataStandard',
    # 'entryDate',
    # 'lastUpdate',
]

def refine_repository_info(
    schema: xmlschema.XMLSchema,
    repository_metadata_response_content: bytes,
) -> typing.Dict[str, typing.Any]:
    repository_metadata_xml = etree.fromstring(repository_metadata_response_content)
    xp = etree.ETXPath(
        '|'.join([".//{%(ns)s}" + x for x in EMPTY_ATTRS]) % {'ns': 'http://www.re3data.org/schema/2-2'},
    )
    for elem in xp(repository_metadata_xml):
        if elem.text == '' or elem.text is None:
            elem.getparent().remove(elem)
    # repository_metadata_xml_sanitized = etree.tostring(repository_metadata_xml)
    retry_attempt = 0
    errors = []
    while retry_attempt <= len(DUPP_ATTRS) + len(MISSING_REQUIRED_ATTRS) + 1:
        retry_attempt += 1
        decoded = schema.decode(
            repository_metadata_xml,
            validation='lax',
            # element_hook=element_hook,
            # value_hook=value_hook,
            validation_hook=validation_hook,
        )
        errors = decoded[1]
        if len(errors) == 0:
            break
        for error in errors:
            if isinstance(error.validator, XsdUnion) and error.validator.local_name == 'dateFormat':
                if error.reason.startswith("attribute updated="):
                    error.elem.attrib['updated'] = DUMMY_NONE_DATE
                else:
                    error.elem.text = DUMMY_NONE_DATE
            elif hasattr(error.validator, 'model') and error.validator.model == 'sequence':
                if error.validator.min_occurs == 1 and error.particle.local_name in MISSING_REQUIRED_ATTRS:
                    ee = deepcopy(MISSING_REQUIRED_ATTRS[error.particle.local_name])
                    error.invalid_child.addprevious(ee)
                    break
                elif error.validator.max_occurs == 1 and error.invalid_tag is not None and error.invalid_tag[35:] in DUPP_ATTRS:
                    error.invalid_child.getparent().remove(error.invalid_child)
                    break
    if len(errors) > 0:
        # print('\n'.join(['>>>>>>>>>>' + error.msg + etree.tostring(error.elem).decode('utf-8') + '<<<<<<<<<<' for error in errors]))
        # print('-------------\n'.join([error.msg for error in errors]))
        # print(','.join([error.invalid_tag for error in errors]))
        raise TransformError(errors)
    decoded = decoded[0]['r3d:repository'][0]

    def handle_atom(urr):
        if isinstance(urr, dict):
            return urr['$'] if '$' in urr else urr
        return urr

    def get_lang_sensible_text(urr):
        if isinstance(urr, dict):
            return {'lang': urr.get('language', None), 'text': urr['$'] if '$' in urr else urr}
        return {'lang': None, 'text': urr}

    def coerce_single(key, postprocess=lambda x: x, remove_dup: bool = False, empty_value = None, other_value = None):
        urr = decoded.get(key)
        if urr is None:
            return None
        if isinstance(urr, dict):
            rr = handle_atom(urr)
        elif isinstance(urr, list):
            rr = urr if urr is not None else []
            if remove_dup:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx]]
            if empty_value is not None and empty_value in rr and len(rr) > 1:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != empty_value]
            if other_value is not None and len(rr) > 1 and other_value in rr:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != other_value]
            # try:
            assert len(rr) <= 1
            # except AssertionError as e:
            #     raise e
            rr = rr[0] if len(rr) > 0 else None
        else:
            rr = urr
        return postprocess(rr)

    def coerce_boolean(key, true_value: str, false_value: str, null_values: [str | None]) -> bool | None:
        urr = decoded.get(key, None)
        if isinstance(urr, dict):
            urr = handle_atom(urr)
        if type(urr) is str and urr.lower() == true_value.lower():
            return True
        elif type(urr) is str and urr.lower() == false_value.lower():
            return False
        else:
            if len(list(filter(lambda null_value: urr is null_value or urr == null_value or (type(urr) is str and urr.lower() == null_value), null_values))) > 0:
                return None
        raise Exception('cannot coerce to bool %s' % (urr,))

    def process_multi(key, preprocess = None, postprocess = None, remove_dup: bool = False, empty_value = None, other_value = None):
        preprocess2 = (lambda x: x) if preprocess is None else preprocess
        postprocess2 = (lambda x: x) if postprocess is None else postprocess
        urr = decoded.get(key)
        if urr is None:
            return []
        elif isinstance(urr, list):
            rr = urr if urr is not None else []
            rr = [handle_atom(preprocess2(rxx)) for rxx in rr]
            if remove_dup:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx]]
            if empty_value is not None and empty_value in rr:
                rr = [x for x in rr if x != empty_value]
            # if callable(other_value) and any(map(other_value, rr)):
            #     rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != other_value]
            elif other_value is not None and len(rr) > 1 and other_value in rr:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != other_value]
        else:
            raise Exception('cannot process not list')
        try:
            return [postprocess2(rx) for rx in rr]
        except BaseException as e:
            raise e

    def process_institution(xx):
        dd = {tk[4:]: handle_atom(tv) for (tk, tv) in xx.items()}
        dd['institutionName'] = get_lang_sensible_text(xx.get('r3d:institutionName', None))
        dd['institutionAdditionalNames'] = [get_lang_sensible_text(xxx) for xxx in xx.get('r3d:institutionAdditionalName', [])]
        dd['institutionCountry'] = handle_atom(xx.get('r3d:institutionCountry', None))
        dd['responsibilityTypes'] = [handle_atom(xxx) for xxx in xx.get('r3d:responsibilityType', [])]
        dd['responsibilityStartDate'] = handle_atom(xx.get('r3d:responsibilityStartDate', None))
        dd['responsibilityEndDate'] = handle_atom(xx.get('r3d:responsibilityEndDate', None))
        dd['institutionURL'] = handle_atom(xx.get('r3d:institutionURL', None))
        dd['institutionContacts'] = xx.get('r3d:institutionContact', [])

        if 'institutionIdentifier' in xx and len(xx['r3d:institutionIdentifier']) >= 1:
            # ToDo: Extraer todos los identificadores
            dd['id'] = xx['institutionIdentifier'][0]
            dd['ids'] = xx['institutionIdentifier']
        else:
            local_id = hashlib.md5(dd['institutionName']['text'].encode('utf-8')).hexdigest()
            dd['id'] = 'LOCAL:%s' % (local_id, )
            dd['ids'] = [dd['id']]
        return dd

    def transform_access(x, level: str):
        # if 'r3d:databaseAccessRestriction' not in x:
        #     pass
        key_restriction = 'r3d:dataAccessRestriction'
        key_type = 'r3d:dataAccessType'
        if level == 'database':
            key_restriction = 'r3d:databaseAccessRestriction'
            key_type = 'r3d:databaseAccessType'
        elif level == 'upload':
            key_restriction = 'r3d:dataUploadRestriction'
            key_type = 'r3d:dataUploadType'
        access_restriction = [xx.lower() for xx in x.get(key_restriction, [])]
        if 'feeRequired' in access_restriction:
            pass
        return {'type': x[key_type], 'restrictions': access_restriction}

    return {
        "id": decoded["r3d:re3data.orgIdentifier"],
        # ToDo: Modelar todos los identificadores disponibles.
        #  Quitar aquellos que YA ESTAN como un identificador de la organizacion
        #   los de tipo ROR
        #  Los de tipo RRID suelen venir de a pares y son la misma cosa (SCR de servicio, y el NLX que parece ser interno).
        #   SI parecen identificar al repositorio y no a la organizacion
        #  Los de tipo FAIRSHARING si son útiles (referenciar al catalogo de fairsharing)
        #  Hay otros tipos?
        "ids": [x for x in decoded.get("r3d:repositoryIdentifier", [])],
        "repositoryName": get_lang_sensible_text(decoded["r3d:repositoryName"]),
        "additionalNames": [get_lang_sensible_text(x) for x in decoded.get("r3d:additionalName", [])],
        "repositoryURL": decoded["r3d:repositoryURL"],
        "description": get_lang_sensible_text(decoded["r3d:description"]),
        "isDisciplinar": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'disciplinary']) > 0,
        "isInstitutional": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'institutional']) > 0,
        "softwareNames": process_multi("r3d:software", None, lambda x: x['r3d:softwareName'].lower(), True, {'r3d:softwareName': 'unknown'}, {'r3d:softwareName': 'other'}),
        # "softwareName": coerce_single("r3d:software", lambda x: x['r3d:softwareName'], True, None, {'r3d:softwareName': 'other'}),
        "size": coerce_single("r3d:size"),
        "subjects": [x['$'] for x in decoded.get("r3d:subject", [])],
        "keywords": [x.lower() for x in decoded.get("r3d:keyword", [])],
        "institutions": [process_institution(xx) for xx in decoded.get("r3d:institution", [])],
        # "apis": coerce_single('r3d:api', lambda x: {'url': x['$'], 'type': x['@apiType'].lower()} if x is not None else None),
        # "apis": process_multi("r3d:api", lambda x: {'url': x['$'], 'type': x['@apiType'].lower()}, False),
        "apis": [{'url': x['$'], 'type': x['@apiType'].lower()} if x is not None else None for x in decoded.get("r3d:api", [])],
        'pidSystems': process_multi('r3d:pidSystem', lambda x: x.lower(), None, True, 'none', 'other'),
        'aidSystems': process_multi('r3d:aidSystem', lambda x: x.lower(), None, True, 'none', 'other'),
        'versioning': coerce_boolean('r3d:versioning', 'yes', 'no', [None, 'unknown']),
        'enhancedPublication': decoded.get('r3d:enhancedPublication', None),
        'qualityManagement': coerce_boolean('r3d:qualityManagement', 'yes', 'no', [None, 'unknown']),
        'citationGuidelineURL': decoded.get('r3d:citationGuidelineURL', None),
        'repositoryContact': decoded.get('r3d:repositoryContact', []),
        'certificates': [x.lower() for x in decoded.get("r3d:certificate", [])],
        'syndications': [x['@syndicationType'].lower() for x in decoded.get("r3d:syndications", [])],
        'startDate': coerce_single('r3d:startDate'),
        'endDate': coerce_single('r3d:endDate'),
        'isDataProvider': len([x for x in decoded.get("r3d:providerType", []) if x.lower() == 'dataprovider']) > 0,
        'isServiceProvider': len(
            [x for x in decoded.get("r3d:providerType", []) if x.lower() == 'serviceprovider']) > 0,
        'missionStatementURL': coerce_single('r3d:missionStatementURL'),
        'contentType': [x['$'] for x in decoded.get("r3d:contentType", [])],
        'metadataStandards': [{'name': x['r3d:metadataStandardName']['$'].lower(), 'url': x['r3d:metadataStandardURL'].lower()} for x in
                              decoded.get("r3d:metadataStandard", [])],

        # ToDo: En versiones intermedias de re3data se consideraba un tipo que podia tener esos enumerados
        # Access policy
        # Collection policy
        # Data policy
        # Metadata policy
        # Preservation policy
        # Submission policy
        # Terms of use
        # Usage policy
        # Quality policy
        'policies': [{'name': x['r3d:policyName'], 'url': x['r3d:policyURL']} for x in decoded.get("r3d:policy", [])],

        #  ToDo: normalizar licencias a los siguiente valores del nombre y descartar las otras cosas...
        #    aunque se podría desempatar usando la "other" y la url...
        #  'apache license 2.0',
        #  'bsd',
        #  'cc',
        #  'cc0',
        #  'copyrights',
        #  'none',
        #  'odc',
        #  'ogl',
        #  'oglc',
        #  'other',
        #  'public domain',
        #  'rl',
        'databaseAccess': transform_access(
            decoded.get("r3d:databaseAccess", None), 'database'
        ) if decoded.get("r3d:databaseAccess", None) is not None else None,
        'dataAccess': [
            transform_access(x, 'data')
            for x in decoded.get("r3d:dataAccess", [])
        ],
        'dataUpload': [
            transform_access(x, 'upload')
            for x in decoded.get("r3d:dataUpload", [])
        ],
        'databaseLicenses': [
            {'name': x['r3d:databaseLicenseName'], 'url': x['r3d:databaseLicenseURL']} for x in
            decoded.get("r3d:databaseLicense", [])
        ],
        'dataLicenses': [
            {'name': x['r3d:dataLicenseName'], 'url': x['r3d:dataLicenseURL']} for x in
            decoded.get("r3d:dataLicense", [])
        ],
        'dataUploadLicenses': [
            {'name': x['r3d:dataUploadLicenseName'], 'url': x['r3d:dataUploadLicenseURL']}
            for x in decoded.get("r3d:dataUploadLicense", [])
        ],
        'remarks': decoded.get('r3d:remarks', None),
        'entryDate': decoded['r3d:entryDate'],
    }


if __name__ == '__main__':
    schema_instance = load_schema()
    from re3data.xsd_transform_samples import sample_data_8, sample_data_7, sample_data_6, sample_data_5, sample_data_4, sample_data_3, sample_data_2, sample_data_1
    expected_item_1 = {
        'id': ('r3d100000001',),
        'repositoryName': ({'text': 'Odum Institute Archive Dataverse', 'lang': 'eng'},),
        'additionalNames': ([],),
        'repositoryURL': ('https://dataverse.unc.edu/dataverse/odum',),
        'description': (
            {'text': 'The Odum Institute Archive Dataverse contains social science data curated and archived by the Odum Institute Data Archive at the University of North Carolina at Chapel Hill. Some key collections include the primary holdings of the Louis Harris Data Center, the National Network of State Polls, and other Southern-focused public opinion data.\nPlease note that some datasets in this collection are restricted to University of North Carolina at Chapel Hill affiliates. Access to these datasets require UNC ONYEN institutional login to the Dataverse system.', 'lang': 'eng'},),
        'repositoryContact': (['https://dataverse.unc.edu/dataverse/odum#', 'odumarchive@unc.edu'],),
        'isDisciplinar': (True,),
        'isInstitutional': (False,),
        'softwareNames': (['dataverse'],),
        # 'softwareName': ('dataverse',),
        'size': ('13 dataverses; 3.310 datasets',),  # ToDo: Falta honrrar el atributo updatedAt
        'startDate': (None,),
        'endDate': (None,),
        'subjects': (
            ['1', '111', '11104', '112',
             '12'],),
        'keywords': ([
                         'fair',
                         'middle east',
                         'crime',
                         'demography',
                         'economy',
                         'education',
                         'election',
                         'environment',
                         'finance',
                         'health care',
                         'presidents united states',
                         'taxes',
                     ],),
        'isDataProvider': (True,),
        'isServiceProvider': (False,),
        'missionStatementURL': (None,),
        'contentType': ([
                            'Databases',
                            'Plain text',
                            'Scientific and statistical data formats',
                            'Standard office documents',
                            'other',
                        ],),
        # 'institutions': ([
        #                      {
        #                          'institutionName': 'Odum Institute for Research in Social Science',
        #                          'institutionCountry': 'USA',
        #                          'responsibilityType': 'general',
        #                          'institutionType': 'non-profit',
        #                          'institutionURL': 'https://odum.unc.edu/archive/',
        #                          'responsibilityStartDate': None,
        #                          'responsibilityEndDate': None,
        #                          'institutionContact': 'https://odum.unc.edu/contact/contact-form/',
        #                      }
        #                  ],),
        'policies': ([
                         {'name': 'Collection Development Policy',
                          'url': 'https://odum.unc.edu/files/2020/01/Policy_CollectionDevelopment_20170501.pdf'},
                         {'name': 'CoreTrustSealAssessment',
                          'url': 'https://www.coretrustseal.org/wp-content/uploads/2020/10/Odum-Institute-Data-Archive.pdf'},
                         {'name': 'Data Security Guidelines',
                          'url': 'https://odum.unc.edu/files/2020/01/Guidelines_DataSecurity_20170501-1.pdf'},
                         {'name': 'Digital Preservation Policy',
                          'url': 'https://odum.unc.edu/files/2020/01/Policy_DigitalPreservation_2020200124.pdf'},
                         {'name': 'Metadata Guidelines',
                          'url': 'https://odum.unc.edu/files/2020/01/Guidelines_Metadata_20170501.pdf'},
                         {'name': 'Odum Institute Data Archive Data Curation Workflow',
                          'url': 'https://odum.unc.edu/files/2020/01/Pipeline_201703.pdf'},
                         {'name': 'UNC Dataverse terms of use',
                          'url': 'https://odum.unc.edu/files/2020/01/Policy_UNCDataverseTermsofUse_20170501.pdf'},
                     ],),
        'api': (None,),
        'metadataStandards': ([{'name': 'ddi - data documentation initiative', 'url': 'http://www.dcc.ac.uk/resources/metadata-standards/ddi-data-documentation-initiative'}, {'name': 'datacite metadata schema', 'url': 'http://www.dcc.ac.uk/resources/metadata-standards/datacite-metadata-schema'}, {'name': 'dublin core', 'url': 'http://www.dcc.ac.uk/resources/metadata-standards/dublin-core'}],),
        'pidSystems': (['DOI'],),
        # 'databaseAccess': ('open',),
        'databaseLicense': ([{
            'name': 'CC0', 'url': 'https://creativecommons.org/share-your-work/public-domain/cc0',
        }],),
        # 'dataAccess': (
        #     ['embargoed', 'open', {'type': 'restricted', 'restrictions': ['institutional membership', 'other']}],),
        'dataLicense': ([{
            'name': 'CC', 'url': 'https://creativecommons.org/share-your-work/public-domain/cc0',
        },
                            {
                                'name': 'CC0', 'url': 'https://creativecommons.org/share-your-work/public-domain/cc0',
                            }
                        ],),
        # 'dataUpload': ({
        #                    'type': 'restricted', 'restriction': 'institutional membership',
        #                },),
        'versioning': (None,),
        'qualityManagement': (True,),
        'certificates': (['other'],),
        'citationGuidelineURL': (None,),
        'enhancedPublication': ('unknown',),
        'remarks': (
            'Odum Dataverse is covered by Thomson Reuters Data Citation Index.\nOdum Institute Archive Dataverse is part of UNC Dataverse',),
        'entryDate': ('2013-06-10',),
    }
    expected_item_2 = {
        'id': ('r3d100000002',),
        'repositoryName': ({'text': 'Access to Archival Databases', 'lang': 'eng'},),
        'additionalNames': ([{'text': 'AAD', 'lang': 'eng'}],),
        'repositoryURL': ('https://aad.archives.gov/aad/',),
        'description': (
            {'text': ''''You will find in the Access to Archival Databases (AAD) resource online access to records in a small selection of historic databases preserved permanently in NARA. Out of the nearly 200,000 data files in its holdings, NARA has selected approximately 475 of them for public searching through AAD. We selected these data because the records identify specific persons, geographic areas, organizations, and dates. The records cover a wide variety of civilian and military functions and have many genealogical, social, political, and economic research uses. AAD provides: Access to over 85 million historic electronic records created by more than 30 agencies of the U.S. federal government and from collections of donated historical materials.
Both free-text and fielded searching options. The ability to retrieve, print, and download records with the specific information that you seek. Information to help you find and understand the records.''', 'lang': 'eng'},),
        'repositoryContact': (['https://www.archives.gov/contact'],),
        'isDisciplinar': (True,),
        'isInstitutional': (False,),
        'softwareNames': (['unknown'],),
        # 'softwareName': ('dataverse',),
        'size': (None,),
        'startDate': ('1985',),
        'endDate': (None,),
        'subjects': (
            ['1', '102', '11'],),
        'keywords': (['us history'],),
        'isDataProvider': (True,),
        'isServiceProvider': (False,),
        'missionStatementURL': ('https://www.archives.gov/publications/general-info-leaflets/1-about-archives.html',),
        'contentType': (['Images', 'Standard office documents', 'Structured text', 'other'],),
        # 'institutions': ([
        #                      {
        #                          'institutionName': 'Odum Institute for Research in Social Science',
        #                          'institutionCountry': 'USA',
        #                          'responsibilityType': 'general',
        #                          'institutionType': 'non-profit',
        #                          'institutionURL': 'https://odum.unc.edu/archive/',
        #                          'responsibilityStartDate': None,
        #                          'responsibilityEndDate': None,
        #                          'institutionContact': 'https://odum.unc.edu/contact/contact-form/',
        #                      }
        #                  ],),
        'policies': ([{'name': 'Contribution Policy', 'url': 'https://www.archives.gov/developer#toc-contribution-policy'}, {'name': 'Freedom of Information Act - FOAI', 'url': 'https://www.archives.gov/foia'}, {'name': 'Privacy and Use', 'url': 'https://www.archives.gov/global-pages/privacy.html'}],),
        'api': ({'url': 'https://www.archives.gov/developer#toc-application-programming-interfaces-apis-', 'type': 'other'},),
        'metadataStandards': ([],),
        'pidSystems': (['none'],), # ToDo: Manejar este valor nulo
        # 'databaseAccess': ('open',),
        'databaseLicense': ([],),
        # 'dataAccess': (
        #     ['embargoed', 'open', {'type': 'restricted', 'restrictions': ['institutional membership', 'other']}],),
        'dataLicense': ([{'name': 'Copyrights', 'url': 'https://www.archives.gov/global-pages/privacy.html#copyright'}],),
        # 'dataUpload': ({
        #                    'type': 'restricted', 'restriction': 'institutional membership',
        #                },),
        'versioning': (False,),
        'qualityManagement': (None,),
        'certificates': ([],),
        'citationGuidelineURL': ('https://aad.archives.gov/aad/help/getting-started-guide.html#cite',),
        'enhancedPublication': ('unknown',),
        'remarks': (None,),
        'entryDate': ('2012-07-04',),
    }
    sample_datas = [
        (sample_data_1, expected_item_1),
        (sample_data_2, expected_item_2),
        # (sample_data_3, None),
        # (sample_data_4, None),
        # (sample_data_5, None),
        # (sample_data_6, None),
        # (sample_data_7, None),
        # (sample_data_8, None),
    ]
    for sample_data, expected_item in sample_datas:
        transformed_result = refine_repository_info(schema_instance, sample_data)
        if expected_item is None:
            continue
        for (expected_item_k, expected_item_v) in expected_item.items():
            actual = transformed_result[expected_item_k]
            expected = expected_item_v[0]
            assert actual == expected, "Dont match '%s'. Expected %s. Actual %s" % (
                expected_item_k, repr(expected), repr(actual))
