from lxml import etree
import typing
import xmlschema
import os
import re
from xmlschema import XsdElement
# from xmlschema import XsdType, ElementData


class TransformError(Exception):
    def __init__(self, original_error: [Exception]):
        self.original_error = original_error


def load_schema():
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


EMPTY_ATTRS = ['startDate', 'endDate', 'responsibilityStartDate', 'responsibilityEndDate', 'enhancedPublication',
               'qualityManagement', 'versioning']


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
    decoded = schema.decode(
        repository_metadata_xml,
        validation='lax',
        # element_hook=element_hook,
        # value_hook=value_hook,
        validation_hook=validation_hook,
    )
    errors = decoded[1]
    should_retry_validation = False
    if len(errors) > 0:
        for error in errors:
            if error.validator.local_name == 'dateFormat':
                if error.reason.startswith("attribute updated="):
                    error.elem.attrib['updated'] = DUMMY_NONE_DATE
                else:
                    error.elem.text = DUMMY_NONE_DATE
                should_retry_validation = True
    if should_retry_validation:
        decoded = schema.decode(
            repository_metadata_xml,
            validation='lax',
            # element_hook=element_hook,
            # value_hook=value_hook,
            validation_hook=validation_hook,
        )
        errors = decoded[1]
    if len(errors) > 0:
        # print('\n'.join(['>>>>>>>>>>' + error.msg + etree.tostring(error.elem).decode('utf-8') + '<<<<<<<<<<' for error in errors]))
        # print('-------------\n'.join([error.msg for error in errors]))
        # print(','.join([error.invalid_tag for error in errors]))
        raise TransformError(errors)
    decoded = decoded[0]['r3d:repository'][0]

    def coerce_single(key, postprocess=lambda x: x, remove_dup: bool = False, empty_value = None):
        urr = decoded.get(key)
        if isinstance(urr, dict):
            rr = urr['$'] if '$' in urr else urr
        elif isinstance(urr, list):
            rr = urr if urr is not None else []
            if remove_dup:
                rr = list(set(rr))
            if empty_value is not None and empty_value in rr and len(rr) > 1:
                rr = set(rr)
                rr.remove(empty_value)
                rr = list(rr)
            # try:
            assert len(rr) <= 1
            # except AssertionError as e:
            #     raise e
            rr = rr[0] if len(rr) == 1 else None
        else:
            rr = urr
        return postprocess(rr)

    return {
        "id": decoded["r3d:re3data.orgIdentifier"],
        "repositoryName": decoded["r3d:repositoryName"]['$'],
        "repositoryURL": decoded["r3d:repositoryURL"],
        "description": decoded["r3d:description"]['$'],
        "isDisciplinar": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'disciplinary']) > 0,
        "isInstitutional": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'institutional']) > 0,
        # "softwareNames": [x['r3d:softwareName'] for x in decoded.get("r3d:software", [])],
        "softwareName": coerce_single("r3d:software", lambda x: x['r3d:softwareName'], True),
        "size": coerce_single("r3d:size"),
        "subjects": [x['$'] for x in decoded.get("r3d:subject", [])],
        "keywords": decoded.get("r3d:keyword", []),
        "institutions": decoded.get("r3d:institution", []),
        "apiType": coerce_single('r3d:apiType'),
        'pidSystems': decoded.get('r3d:pidSystem', []),
        'databaseAccess': decoded.get('r3d:databaseAccess', None),
        'dataAccess': decoded.get('r3d:dataAccess', []),
        'versioning': decoded.get('r3d:versioning', None),
        'enhancedPublication': decoded.get('r3d:enhancedPublication', None),
        'qualityManagement': decoded.get('r3d:qualityManagement', None),
        'citationGuidelineURL': decoded.get('r3d:citationGuidelineURL', None),
        'repositoryContact': decoded.get('r3d:repositoryContact', []),
        'certificates': decoded.get('r3d:certificate', []),
        'startDate': coerce_single('r3d:startDate'),
        'endDate': coerce_single('r3d:endDate'),
        'isDataProvider': len([x for x in decoded.get("r3d:providerType", []) if x.lower() == 'dataprovider']) > 0,
        'isServiceProvider': len(
            [x for x in decoded.get("r3d:providerType", []) if x.lower() == 'serviceprovider']) > 0,
        'missionStatementURL': coerce_single('r3d:missionStatementURL'),
        'contentType': [x['$'] for x in decoded.get("r3d:contentType", [])],
        'policies': [{'name': x['r3d:policyName'], 'url': x['r3d:policyURL']} for x in decoded.get("r3d:policy", [])],
        'metadataStandards': [{'name': x['r3d:metadataStandardName']['$'], 'url': x['r3d:metadataStandardURL']} for x in
                              decoded.get("r3d:metadataStandard", [])],
        'databaseLicense': [{'name': x['r3d:databaseLicenseName'], 'url': x['r3d:databaseLicenseURL']} for x in
                            decoded.get("r3d:databaseLicense", [])],
        'dataLicense': [{'name': x['r3d:dataLicenseName'], 'url': x['r3d:dataLicenseURL']} for x in
                        decoded.get("r3d:dataLicense", [])],
        'remarks': decoded.get('r3d:remarks', None),
        'entryDate': decoded['r3d:entryDate'],
    }


if __name__ == '__main__':
    schemaInstance = load_schema()
    sampleData = (b'<?xml version="1.0" encoding="utf-8"?>'
                  b'<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->'
                  b'<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">'
                  b'  <r3d:repository>'
                  b'    <r3d:re3data.orgIdentifier>r3d100000001</r3d:re3data.orgIdentifier>'
                  b'    <r3d:repositoryName language="eng">Odum Institute Archive Dataverse</r3d:repositoryName>'
                  b'    <r3d:repositoryURL>https://dataverse.unc.edu/dataverse/odum</r3d:repositoryURL>'
                  b'    <r3d:description language="eng">The Odum Institute Archive Dataverse contains social science data curated and archived by the Odum Institute Data Archive at the University of North Carolina at Chapel Hill. Some key collections include the primary holdings of the Louis Harris Data Center, the National Network of State Polls, and other Southern-focused public opinion data.\r\nPlease note that some datasets in this collection are restricted to University of North Carolina at Chapel Hill affiliates. Access to these datasets require UNC ONYEN institutional login to the Dataverse system.</r3d:description>'
                  b'    <r3d:repositoryContact>https://dataverse.unc.edu/dataverse/odum#</r3d:repositoryContact>'
                  b'    <r3d:repositoryContact>odumarchive@unc.edu</r3d:repositoryContact>'
                  b'    <r3d:type>disciplinary</r3d:type>'
                  b'    <r3d:size updated="2023-09-19">13 dataverses; 3.310 datasets</r3d:size>'
                  b'    <r3d:startDate></r3d:startDate>'
                  b'    <r3d:endDate></r3d:endDate>'
                  b'    <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>'
                  b'    <r3d:subject subjectScheme="DFG">1 Humanities and Social Sciences</r3d:subject>'
                  b'    <r3d:subject subjectScheme="DFG">111 Social Sciences</r3d:subject>'
                  b'    <r3d:subject subjectScheme="DFG">11104 Political Science</r3d:subject>'
                  b'    <r3d:subject subjectScheme="DFG">112 Economics</r3d:subject>'
                  b'    <r3d:subject subjectScheme="DFG">12 Social and Behavioural Sciences</r3d:subject>'
                  b'    <r3d:missionStatementURL></r3d:missionStatementURL>'
                  b'    <r3d:contentType contentTypeScheme="parse">Databases</r3d:contentType>'
                  b'    <r3d:contentType contentTypeScheme="parse">Plain text</r3d:contentType>'
                  b'    <r3d:contentType contentTypeScheme="parse">Scientific and statistical data formats</r3d:contentType>'
                  b'    <r3d:contentType contentTypeScheme="parse">Standard office documents</r3d:contentType>'
                  b'    <r3d:contentType contentTypeScheme="parse">other</r3d:contentType>'
                  b'    <r3d:providerType>dataProvider</r3d:providerType>'
                  b'    <r3d:keyword>FAIR</r3d:keyword>'
                  b'    <r3d:keyword>Middle East</r3d:keyword>'
                  b'    <r3d:keyword>crime</r3d:keyword>'
                  b'    <r3d:keyword>demography</r3d:keyword>'
                  b'    <r3d:keyword>economy</r3d:keyword>'
                  b'    <r3d:keyword>education</r3d:keyword>'
                  b'    <r3d:keyword>election</r3d:keyword>'
                  b'    <r3d:keyword>environment</r3d:keyword>'
                  b'    <r3d:keyword>finance</r3d:keyword>'
                  b'    <r3d:keyword>health care</r3d:keyword>'
                  b'    <r3d:keyword>presidents United States</r3d:keyword>'
                  b'    <r3d:keyword>taxes</r3d:keyword>'
                  b'    <r3d:institution>'
                  b'        <r3d:institutionName language="eng">Odum Institute for Research in Social Science</r3d:institutionName>'
                  b'        <r3d:institutionCountry>USA</r3d:institutionCountry>'
                  b'        <r3d:responsibilityType>general</r3d:responsibilityType>'
                  b'        <r3d:institutionType>non-profit</r3d:institutionType>'
                  b'        <r3d:institutionURL>https://odum.unc.edu/archive/</r3d:institutionURL>'
                  b'        <r3d:responsibilityStartDate></r3d:responsibilityStartDate>'
                  b'        <r3d:responsibilityEndDate></r3d:responsibilityEndDate>'
                  b'        <r3d:institutionContact>https://odum.unc.edu/contact/contact-form/</r3d:institutionContact>'
                  b'    </r3d:institution>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>Collection Development Policy</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_CollectionDevelopment_20170501.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>CoreTrustSealAssessment</r3d:policyName>'
                  b'        <r3d:policyURL>https://www.coretrustseal.org/wp-content/uploads/2020/10/Odum-Institute-Data-Archive.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>Data Security Guidelines</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Guidelines_DataSecurity_20170501-1.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>Digital Preservation Policy</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_DigitalPreservation_2020200124.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>Metadata Guidelines</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Guidelines_Metadata_20170501.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>Odum Institute Data Archive Data Curation Workflow</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Pipeline_201703.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:policy>'
                  b'        <r3d:policyName>UNC Dataverse terms of use</r3d:policyName>'
                  b'        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_UNCDataverseTermsofUse_20170501.pdf</r3d:policyURL>'
                  b'    </r3d:policy>'
                  b'    <r3d:databaseAccess>'
                  b'        <r3d:databaseAccessType>open</r3d:databaseAccessType>'
                  b'    </r3d:databaseAccess>'
                  b'    <r3d:databaseLicense>'
                  b'        <r3d:databaseLicenseName>CC0</r3d:databaseLicenseName>'
                  b'        <r3d:databaseLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:databaseLicenseURL>'
                  b'    </r3d:databaseLicense>'
                  b'    <r3d:dataAccess>'
                  b'    <r3d:dataAccessType>embargoed</r3d:dataAccessType>'
                  b'    </r3d:dataAccess>'
                  b'    <r3d:dataAccess>'
                  b'    <r3d:dataAccessType>open</r3d:dataAccessType>'
                  b'    </r3d:dataAccess>'
                  b'    <r3d:dataAccess>'
                  b'    <r3d:dataAccessType>restricted</r3d:dataAccessType>'
                  b'    <r3d:dataAccessRestriction>institutional membership</r3d:dataAccessRestriction>'
                  b'    <r3d:dataAccessRestriction>other</r3d:dataAccessRestriction>'
                  b'    </r3d:dataAccess>'
                  b'    <r3d:dataLicense>'
                  b'        <r3d:dataLicenseName>CC</r3d:dataLicenseName>'
                  b'        <r3d:dataLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:dataLicenseURL>'
                  b'    </r3d:dataLicense>'
                  b'    <r3d:dataLicense>'
                  b'        <r3d:dataLicenseName>CC0</r3d:dataLicenseName>'
                  b'        <r3d:dataLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:dataLicenseURL>'
                  b'    </r3d:dataLicense>'
                  b'    <r3d:dataUpload>'
                  b'        <r3d:dataUploadType>restricted</r3d:dataUploadType>'
                  b'        <r3d:dataUploadRestriction>institutional membership</r3d:dataUploadRestriction>'
                  b'    </r3d:dataUpload>'
                  b'    <r3d:software>'
                  b'        <r3d:softwareName>Dataverse</r3d:softwareName>'
                  b'    </r3d:software>'
                  b'    <r3d:versioning></r3d:versioning>'
                  b'    <r3d:pidSystem>DOI</r3d:pidSystem>'
                  b'    <r3d:citationGuidelineURL></r3d:citationGuidelineURL>'
                  b'    <r3d:enhancedPublication>unknown</r3d:enhancedPublication>'
                  b'    <r3d:qualityManagement>yes</r3d:qualityManagement>'
                  b'    <r3d:certificate>other</r3d:certificate>'
                  b'    <r3d:metadataStandard>'
                  b'      <r3d:metadataStandardName metadataStandardScheme="DCC">DDI - Data Documentation Initiative</r3d:metadataStandardName>'
                  b'      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/ddi-data-documentation-initiative</r3d:metadataStandardURL>'
                  b'    </r3d:metadataStandard>'
                  b'    <r3d:metadataStandard>'
                  b'      <r3d:metadataStandardName metadataStandardScheme="DCC">DataCite Metadata Schema</r3d:metadataStandardName>'
                  b'      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/datacite-metadata-schema</r3d:metadataStandardURL>'
                  b'    </r3d:metadataStandard>'
                  b'    <r3d:metadataStandard>'
                  b'      <r3d:metadataStandardName metadataStandardScheme="DCC">Dublin Core</r3d:metadataStandardName>'
                  b'      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/dublin-core</r3d:metadataStandardURL>'
                  b'    </r3d:metadataStandard>'
                  b'    <r3d:remarks>Odum Dataverse is covered by Thomson Reuters Data Citation Index.\r\nOdum Institute Archive Dataverse is part of UNC Dataverse</r3d:remarks>'
                  b'    <r3d:entryDate>2013-06-10</r3d:entryDate>'
                  b'    <r3d:lastUpdate>2023-09-19</r3d:lastUpdate>'
                  b'  </r3d:repository>'
                  b'</r3d:re3data>')
    transformed_result = refine_repository_info(schemaInstance, sampleData)
    expected_items = {
        'id': ('r3d100000001',),
        'repositoryName': ('Odum Institute Archive Dataverse',),  # ToDo: Falta honrrar el lenguaje (en varios casos)
        'repositoryURL': ('https://dataverse.unc.edu/dataverse/odum',),
        'description': (
            'The Odum Institute Archive Dataverse contains social science data curated and archived by the Odum Institute Data Archive at the University of North Carolina at Chapel Hill. Some key collections include the primary holdings of the Louis Harris Data Center, the National Network of State Polls, and other Southern-focused public opinion data.\nPlease note that some datasets in this collection are restricted to University of North Carolina at Chapel Hill affiliates. Access to these datasets require UNC ONYEN institutional login to the Dataverse system.',),
        'repositoryContact': (['https://dataverse.unc.edu/dataverse/odum#', 'odumarchive@unc.edu'],),
        'isDisciplinar': (True,),
        'isInstitutional': (False,),
        'softwareNames': (['dataverse'],),
        'size': ('13 dataverses; 3.310 datasets',),  # ToDo: Falta honrrar el atributo updatedAt
        'startDate': (None,),
        'endDate': (None,),
        'subjects': (
            ['1 Humanities and Social Sciences', '111 Social Sciences', '11104 Political Science', '112 Economics',
             '12 Social and Behavioural Sciences'],),
        'keywords': ([
                         'FAIR',
                         'Middle East',
                         'crime',
                         'demography',
                         'economy',
                         'education',
                         'election',
                         'environment',
                         'finance',
                         'health care',
                         'presidents United States',
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
        'metadataStandards': ([
                                  {'name': 'DDI - Data Documentation Initiative',
                                   'url': 'http://www.dcc.ac.uk/resources/metadata-standards/ddi-data-documentation-initiative', },
                                  {'name': 'DataCite Metadata Schema',
                                   'url': 'http://www.dcc.ac.uk/resources/metadata-standards/datacite-metadata-schema', },
                                  {'name': 'Dublin Core',
                                   'url': 'http://www.dcc.ac.uk/resources/metadata-standards/dublin-core', },
                              ],),
        'apiType': (None,),
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
        'qualityManagement': ('yes',),
        'certificates': (['other'],),
        'citationGuidelineURL': (None,),
        'enhancedPublication': ('unknown',),
        'remarks': (
            'Odum Dataverse is covered by Thomson Reuters Data Citation Index.\nOdum Institute Archive Dataverse is part of UNC Dataverse',),
        'entryDate': ('2013-06-10',),
    }
    for (expected_item_k, expected_item_v) in expected_items.items():
        actual = transformed_result[expected_item_k]
        expected = expected_item_v[0]
        assert actual == expected, "Dont match '%s'. Expected %s. Actual %s" % (
            expected_item_k, repr(expected), repr(actual))
