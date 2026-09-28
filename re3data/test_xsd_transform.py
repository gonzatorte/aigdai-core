import pytest

from re3data.xsd_transform import TransformError, load_schema, refine_repository_info
from re3data.xsd_transform_samples import sample_data_8, sample_data_7, sample_data_6, sample_data_5, sample_data_4, sample_data_3, sample_data_2, sample_data_1

EXPECTED_ITEM_1 = {
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
    'size': ('13 dataverses; 3.310 datasets',),  # ToDo: The updatedAt attribute is not honored yet
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
EXPECTED_ITEM_2 = {
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
    'pidSystems': (['none'],), # ToDo: Handle this null value
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


@pytest.fixture(scope='module')
def schema_instance():
    return load_schema()


@pytest.mark.parametrize('sample_data, expected_item', [
    (sample_data_1, EXPECTED_ITEM_1),
    (sample_data_2, EXPECTED_ITEM_2),
], ids=['sample_data_1', 'sample_data_2'])
def test_refine_repository_info(schema_instance, sample_data, expected_item):
    transformed_result = refine_repository_info(schema_instance, sample_data)
    for (expected_item_k, expected_item_v) in expected_item.items():
        actual = transformed_result[expected_item_k]
        expected = expected_item_v[0]
        assert actual == expected, "Dont match '%s'. Expected %s. Actual %s" % (
            expected_item_k, repr(expected), repr(actual))


# No expected values yet: these only check that the sample can be transformed
@pytest.mark.parametrize('sample_data', [
    sample_data_3,
    sample_data_4,
    sample_data_5,
    pytest.param(sample_data_6, marks=pytest.mark.xfail(raises=TransformError, strict=True, reason='Does not validate against the strict XSD')),
    pytest.param(sample_data_7, marks=pytest.mark.xfail(raises=TransformError, strict=True, reason='Does not validate against the strict XSD')),
    sample_data_8,
], ids=['sample_data_3', 'sample_data_4', 'sample_data_5', 'sample_data_6', 'sample_data_7', 'sample_data_8'])
def test_refine_repository_info_without_expected(schema_instance, sample_data):
    refine_repository_info(schema_instance, sample_data)
