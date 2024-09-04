from lxml import etree
import typing
import xmlschema
import os
import re
from xmlschema import XsdElement
from xmlschema.validators import XsdUnion
# from xmlschema import XsdType, ElementData
from copy import copy, deepcopy

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
            rr = rr[0] if len(rr) == 1 else None
        else:
            rr = urr
        return postprocess(rr)

    def process_multi(key, postprocess=lambda x: x, remove_dup: bool = False, empty_value = None, other_value = None):
        urr = decoded.get(key)
        if urr is None:
            return []
        elif isinstance(urr, list):
            rr = urr if urr is not None else []
            rr = [handle_atom(rxx) for rxx in rr]
            if remove_dup:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx]]
            if empty_value is not None and empty_value in rr and len(rr) > 1:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != empty_value]
            if other_value is not None and len(rr) > 1 and other_value in rr:
                rr = [x for idx, x in enumerate(rr) if x not in rr[:idx] and x != other_value]
        else:
            raise BaseException
        return [postprocess(rx) for rx in rr]

    def process_institution(xx):
        dd = {tk[4:]: handle_atom(tv) for (tk, tv) in xx.items()}
        if 'institutionIdentifier' in dd and len(dd['institutionIdentifier']) > 1:
            dd['id'] = dd['institutionIdentifier'][0]
        else:
            dd['id'] = 'local:%(institutionName)s' % dd
        return dd

    return {
        "id": decoded["r3d:re3data.orgIdentifier"],
        "repositoryName": decoded["r3d:repositoryName"]['$'],
        "repositoryURL": decoded["r3d:repositoryURL"],
        "description": decoded["r3d:description"]['$'],
        "isDisciplinar": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'disciplinary']) > 0,
        "isInstitutional": len([x for x in decoded.get("r3d:type", []) if x.lower() == 'institutional']) > 0,
        "softwareNames": process_multi("r3d:software", lambda x: x['r3d:softwareName'], True, None, {'r3d:softwareName': 'other'}),
        # "softwareName": coerce_single("r3d:software", lambda x: x['r3d:softwareName'], True, None, {'r3d:softwareName': 'other'}),
        "size": coerce_single("r3d:size"),
        "subjects": [x['$'] for x in decoded.get("r3d:subject", [])],
        "keywords": decoded.get("r3d:keyword", []),
        "institutions": [process_institution(xx) for xx in decoded.get("r3d:institution", [])],
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
    schema_instance = load_schema()
    sample_data_7 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
	<r3d:repository>
		<r3d:re3data.orgIdentifier>r3d100012053</r3d:re3data.orgIdentifier>
		<r3d:repositoryName language="eng">UiT Open Research Data Dataverse</r3d:repositoryName>
				<r3d:repositoryURL>http://opendata.uit.no/</r3d:repositoryURL>
				<r3d:description language="eng">&lt;&lt;&lt;!!!&lt;&lt;&lt;    UiT Open Research Data is part of DataverseNO;  re3data:https://doi.org/10.17616/R3TV17 &gt;&gt;&gt;!!!&gt;&gt;&gt;</r3d:description>
						<r3d:size updated=""></r3d:size>
                            <r3d:endDate>2020</r3d:endDate>
            <r3d:endDate>2020</r3d:endDate>
        		
						<r3d:missionStatementURL></r3d:missionStatementURL>
												<r3d:databaseAccess>
			<r3d:databaseAccessType>open</r3d:databaseAccessType>
					</r3d:databaseAccess>
									<r3d:dataLicense>
				<r3d:dataLicenseName>CC0</r3d:dataLicenseName>
				<r3d:dataLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0/</r3d:dataLicenseURL>
			</r3d:dataLicense>
										<r3d:versioning>yes</r3d:versioning>
						<r3d:citationGuidelineURL></r3d:citationGuidelineURL>
				<r3d:enhancedPublication>unknown</r3d:enhancedPublication>
		<r3d:qualityManagement>unknown</r3d:qualityManagement>
								<r3d:remarks></r3d:remarks>
		<r3d:entryDate>2016-06-24</r3d:entryDate>
		<r3d:lastUpdate>2024-03-27</r3d:lastUpdate>
	</r3d:repository>
</r3d:re3data>'''
    sample_data_6 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
    <r3d:repository>
        <r3d:re3data.orgIdentifier>r3d100011532</r3d:re3data.orgIdentifier>
        <r3d:repositoryName language="eng">ITER Database</r3d:repositoryName>
        <r3d:additionalName language="eng">International Toxicity Estimates for Risk Assessment</r3d:additionalName>
        <r3d:additionalName language="eng">formerly: TOXNET database</r3d:additionalName>
        <r3d:repositoryURL>https://iter.tera.org/db.html</r3d:repositoryURL>
        <r3d:repositoryIdentifier>RRID:SCR_008196</r3d:repositoryIdentifier>
        <r3d:repositoryIdentifier>RRID:nif-0000-21225</r3d:repositoryIdentifier>
        <r3d:description language="eng">ITER is an Internet database of human health risk values and cancer classifications for over 680 chemicals of environmental concern from multiple organizations wordwide. ITER is the only database that presents risk data in a tabular format for easy comparison, along with a synopsis explaining differences in data and a link to each organization for more information.</r3d:description>
        <r3d:repositoryContact>dourson@tera.org</r3d:repositoryContact>
        <r3d:repositoryContact>gadagbui@tera.org</r3d:repositoryContact>
        <r3d:repositoryContact>https://iter.tera.org/contact.html</r3d:repositoryContact>
        <r3d:type>disciplinary</r3d:type>
        <r3d:size updated=""></r3d:size>
        <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
        <r3d:missionStatementURL>https://tera.org/about/mission_history.html</r3d:missionStatementURL>
        <r3d:contentType contentTypeScheme="parse">Databases</r3d:contentType>
        <r3d:contentType contentTypeScheme="parse">Standard office documents</r3d:contentType>
        <r3d:providerType>serviceProvider</r3d:providerType>
        <r3d:keyword>cancer</r3d:keyword>
        <r3d:keyword>dose-response assessment</r3d:keyword>
        <r3d:keyword>environmental health</r3d:keyword>
        <r3d:keyword>hazard identification</r3d:keyword>
        <r3d:institution>
            <r3d:institutionName language="eng">International Toxicity Estimates for Risk Assessment</r3d:institutionName>
            <r3d:institutionAdditionalName language="eng">ITER</r3d:institutionAdditionalName>
            <r3d:institutionCountry>USA</r3d:institutionCountry>
            <r3d:responsibilityType>general</r3d:responsibilityType>
            <r3d:institutionType>non-profit</r3d:institutionType>
            <r3d:institutionURL>https://www.tera.org/iter/</r3d:institutionURL>
            <r3d:institutionContact>tera@tera.org</r3d:institutionContact>
        </r3d:institution>
        <r3d:institution>
            <r3d:institutionName language="eng">Toxicology Excellence for Risk Assessment</r3d:institutionName>
            <r3d:institutionAdditionalName language="eng">TERA</r3d:institutionAdditionalName>
            <r3d:institutionCountry>USA</r3d:institutionCountry>
            <r3d:responsibilityType>technical</r3d:responsibilityType>
            <r3d:institutionType>non-profit</r3d:institutionType>
            <r3d:institutionURL>https://www.tera.org/</r3d:institutionURL>
            <r3d:institutionContact>tera@tera.org</r3d:institutionContact>
        </r3d:institution>
        <r3d:policy>
            <r3d:policyName>Privacy Policy</r3d:policyName>
            <r3d:policyURL>https://www.tera.org/Website%20Privacy%20Policy.pdf</r3d:policyURL>
        </r3d:policy>
        <r3d:databaseAccess>
            <r3d:databaseAccessType>open</r3d:databaseAccessType>
        </r3d:databaseAccess>
        <r3d:dataAccess>
            <r3d:dataAccessType>open</r3d:dataAccessType>
        </r3d:dataAccess>
        <r3d:dataLicense>
            <r3d:dataLicenseName>Copyrights</r3d:dataLicenseName>
            <r3d:dataLicenseURL>https://www.tera.org</r3d:dataLicenseURL>
        </r3d:dataLicense>
        <r3d:dataUpload>
            <r3d:dataUploadType>restricted</r3d:dataUploadType>
            <r3d:dataUploadRestriction>other</r3d:dataUploadRestriction>
        </r3d:dataUpload>
        <r3d:software>
            <r3d:softwareName>MySQL</r3d:softwareName>
        </r3d:software>
        <r3d:versioning>yes</r3d:versioning>
        <r3d:pidSystem>other</r3d:pidSystem>
        <r3d:citationGuidelineURL>https://iter.tera.org/faq.html#faq10</r3d:citationGuidelineURL>
        <r3d:aidSystem>none</r3d:aidSystem>
        <r3d:enhancedPublication>yes</r3d:enhancedPublication>
        <r3d:qualityManagement>yes</r3d:qualityManagement>
        <r3d:remarks>Description: ITER contains data in support of human health risk assessments. It is compiled by Toxicology Excellence for Risk Assessment (TERA) and contains data from CDC/ATSDR, Health Canada, RIVM, U.S. EPA, IARC, NSF International and independent parties offering peer-reviewed risk values. ITER provides comparison charts of international risk assessment information and explains differences in risk values derived by different organizations.</r3d:remarks>
        <r3d:entryDate>2015-03-10</r3d:entryDate>
        <r3d:lastUpdate>2024-03-08</r3d:lastUpdate>
    </r3d:repository>
</r3d:re3data>
'''
    sample_data_5 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
  <r3d:repository>
    <r3d:re3data.orgIdentifier>r3d100000039</r3d:re3data.orgIdentifier>
    <r3d:repositoryName language="eng">Global Biodiversity Information Facility</r3d:repositoryName>
          <r3d:additionalName language="eng">Data index of the Global Biodiversity Information Facility</r3d:additionalName>
          <r3d:additionalName language="eng">GBIF.org</r3d:additionalName>
        <r3d:repositoryURL>https://www.gbif.org/</r3d:repositoryURL>
          <r3d:repositoryIdentifier>FAIRsharing_doi:10.25504/FAIRsharing.zv11j3</r3d:repositoryIdentifier>
          <r3d:repositoryIdentifier>ROR:05fjyn938</r3d:repositoryIdentifier>
          <r3d:repositoryIdentifier>RRID:SCR_005904</r3d:repositoryIdentifier>
          <r3d:repositoryIdentifier>RRID:nlx_149475</r3d:repositoryIdentifier>
        <r3d:description language="eng">GBIF is an international organisation that is working to make the world&#039;s biodiversity data accessible everywhere in the world. GBIF and its many partners work to mobilize the data, and to improve search mechanisms, data and metadata standards, web services, and the other components of an Internet-based information infrastructure for biodiversity.
GBIF makes available data that are shared by hundreds of data publishers from around the world. These data are shared according to the GBIF Data Use Agreement, which includes the provision that users of any data accessed through or retrieved via the GBIF Portal will always give credit to the original data publishers.</r3d:description>
          <r3d:repositoryContact>https://www.gbif.org/contact-us</r3d:repositoryContact>
              <r3d:type>disciplinary</r3d:type>
          <r3d:type>institutional</r3d:type>
        <r3d:size updated="2024-07-30">2.980.953.577 occurence records; 106.883 datasets;</r3d:size>
                    <r3d:startDate>2001</r3d:startDate>
            <r3d:startDate>2001</r3d:startDate>
                    
          <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
              <r3d:subject subjectScheme="DFG">2 Life Sciences</r3d:subject>
          <r3d:subject subjectScheme="DFG">202 Plant Sciences</r3d:subject>
          <r3d:subject subjectScheme="DFG">20202 Plant Ecology and Ecosystem Analysis</r3d:subject>
          <r3d:subject subjectScheme="DFG">203 Zoology</r3d:subject>
          <r3d:subject subjectScheme="DFG">20303 Animal Ecology, Biodiversity and Ecosystem Research</r3d:subject>
          <r3d:subject subjectScheme="DFG">21 Biology</r3d:subject>
        <r3d:missionStatementURL>https://www.gbif.org/what-is-gbif</r3d:missionStatementURL>
          <r3d:contentType contentTypeScheme="parse">Images</r3d:contentType>
          <r3d:contentType contentTypeScheme="parse">Scientific and statistical data formats</r3d:contentType>
          <r3d:contentType contentTypeScheme="parse">Software applications</r3d:contentType>
          <r3d:contentType contentTypeScheme="parse">Structured graphics</r3d:contentType>
          <r3d:contentType contentTypeScheme="parse">Structured text</r3d:contentType>
              <r3d:providerType>dataProvider</r3d:providerType>
          <r3d:providerType>serviceProvider</r3d:providerType>
              <r3d:keyword>animal</r3d:keyword>
          <r3d:keyword>archaea</r3d:keyword>
          <r3d:keyword>bacteria</r3d:keyword>
          <r3d:keyword>biodiversity</r3d:keyword>
          <r3d:keyword>chromista</r3d:keyword>
          <r3d:keyword>fungi</r3d:keyword>
          <r3d:keyword>plant</r3d:keyword>
          <r3d:keyword>protozoa</r3d:keyword>
          <r3d:keyword>virus</r3d:keyword>
              <r3d:institution>
        <r3d:institutionName language="eng">Global Biodiversity Information Facility</r3d:institutionName>
                  <r3d:institutionAdditionalName language="eng">GBIF</r3d:institutionAdditionalName>
                <r3d:institutionCountry>DNK</r3d:institutionCountry>
                  <r3d:responsibilityType>general</r3d:responsibilityType>
                  <r3d:responsibilityType>technical</r3d:responsibilityType>
                <r3d:institutionType>non-profit</r3d:institutionType>
        <r3d:institutionURL>https://www.gbif.org/</r3d:institutionURL>
                  <r3d:institutionIdentifier>ROR:05fjyn938</r3d:institutionIdentifier>
                  <r3d:institutionIdentifier>RRID:SCR_005904</r3d:institutionIdentifier>
                          <r3d:responsibilityStartDate>2001</r3d:responsibilityStartDate>
                    
                        
        
                  <r3d:institutionContact>communication@gbif.org</r3d:institutionContact>
              </r3d:institution>
              <r3d:policy>
        <r3d:policyName>Data User Agreement</r3d:policyName>
        <r3d:policyURL>https://www.gbif.org/terms/data-user</r3d:policyURL>
      </r3d:policy>
          <r3d:policy>
        <r3d:policyName>Terms of use</r3d:policyName>
        <r3d:policyURL>https://www.gbif.org/terms</r3d:policyURL>
      </r3d:policy>
        <r3d:databaseAccess>
      <r3d:databaseAccessType>open</r3d:databaseAccessType>
          </r3d:databaseAccess>
              <r3d:dataAccess>
        <r3d:dataAccessType>open</r3d:dataAccessType>
              </r3d:dataAccess>
              <r3d:dataLicense>
        <r3d:dataLicenseName>CC</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://creativecommons.org/licenses/by-nc/4.0/</r3d:dataLicenseURL>
      </r3d:dataLicense>
          <r3d:dataLicense>
        <r3d:dataLicenseName>CC</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://creativecommons.org/licenses/by/4.0/</r3d:dataLicenseURL>
      </r3d:dataLicense>
          <r3d:dataLicense>
        <r3d:dataLicenseName>CC0</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://creativecommons.org/publicdomain/zero/1.0/</r3d:dataLicenseURL>
      </r3d:dataLicense>
          <r3d:dataLicense>
        <r3d:dataLicenseName>other</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://www.gbif.org/mou</r3d:dataLicenseURL>
      </r3d:dataLicense>
          <r3d:dataLicense>
        <r3d:dataLicenseName>other</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://www.gbif.org/terms</r3d:dataLicenseURL>
      </r3d:dataLicense>
              <r3d:dataUpload>
        <r3d:dataUploadType>restricted</r3d:dataUploadType>
                  <r3d:dataUploadRestriction>other</r3d:dataUploadRestriction>
              </r3d:dataUpload>
              <r3d:dataUploadLicense>
        <r3d:dataUploadLicenseName>Data publisher agreement</r3d:dataUploadLicenseName>
        <r3d:dataUploadLicenseURL>https://www.gbif.org/terms/data-publisher</r3d:dataUploadLicenseURL>
      </r3d:dataUploadLicense>
            <r3d:versioning>yes</r3d:versioning>
          <r3d:api apiType="REST">https://www.gbif.org/developer/summary</r3d:api>
              <r3d:pidSystem>DOI</r3d:pidSystem>
        <r3d:citationGuidelineURL>https://www.gbif.org/citation-guidelines</r3d:citationGuidelineURL>
        <r3d:enhancedPublication>unknown</r3d:enhancedPublication>
    <r3d:qualityManagement>unknown</r3d:qualityManagement>
          <r3d:certificate>WDS</r3d:certificate>
              <r3d:metadataStandard>
        <r3d:metadataStandardName metadataStandardScheme="DCC">ABCD - Access to Biological Collection Data</r3d:metadataStandardName>
        <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/abcd-access-biological-collection-data</r3d:metadataStandardURL>
      </r3d:metadataStandard>
          <r3d:metadataStandard>
        <r3d:metadataStandardName metadataStandardScheme="DCC">Darwin Core</r3d:metadataStandardName>
        <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/darwin-core</r3d:metadataStandardURL>
      </r3d:metadataStandard>
          <r3d:metadataStandard>
        <r3d:metadataStandardName metadataStandardScheme="DCC">EML - Ecological Metadata Language</r3d:metadataStandardName>
        <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/eml-ecological-metadata-language</r3d:metadataStandardURL>
      </r3d:metadataStandard>
            <r3d:remarks></r3d:remarks>
    <r3d:entryDate>2013-01-31</r3d:entryDate>
    <r3d:lastUpdate>2024-07-30</r3d:lastUpdate>
  </r3d:repository>
</r3d:re3data>
    '''
    sample_data_4 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
  <r3d:repository>
    <r3d:re3data.orgIdentifier>r3d100000017</r3d:re3data.orgIdentifier>
    <r3d:repositoryName language="eng">RNA Abundance Database</r3d:repositoryName>
          <r3d:additionalName language="eng">RAD</r3d:additionalName>
        <r3d:repositoryURL>https://www.cbil.upenn.edu/RAD</r3d:repositoryURL>
          <r3d:repositoryIdentifier>RRID:OMICS_00869</r3d:repositoryIdentifier>
          <r3d:repositoryIdentifier>RRID:SCR_002771</r3d:repositoryIdentifier>
          <r3d:repositoryIdentifier>RRID:nif-0000-00133</r3d:repositoryIdentifier>
        <r3d:description language="eng">===  !!!!!    Due to changes in technology and funding, the RAD website is no longer available     !!!!!   ===</r3d:description>
              <r3d:type>disciplinary</r3d:type>
        <r3d:size updated=""></r3d:size>
                    <r3d:startDate>2003</r3d:startDate>
            <r3d:startDate>2003</r3d:startDate>
                            <r3d:endDate>2012</r3d:endDate>
            <r3d:endDate>2012</r3d:endDate>
            
          <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
              <r3d:subject subjectScheme="DFG">2 Life Sciences</r3d:subject>
          <r3d:subject subjectScheme="DFG">201 Basic Biological and Medical Research</r3d:subject>
          <r3d:subject subjectScheme="DFG">20105 General Genetics</r3d:subject>
          <r3d:subject subjectScheme="DFG">21 Biology</r3d:subject>
        <r3d:missionStatementURL>https://www.cbil.upenn.edu/</r3d:missionStatementURL>
          <r3d:contentType contentTypeScheme="parse">Scientific and statistical data formats</r3d:contentType>
              <r3d:providerType>dataProvider</r3d:providerType>
              <r3d:keyword>gene expression studies</r3d:keyword>
          <r3d:keyword>microarray data</r3d:keyword>
          <r3d:keyword>transcriptomics</r3d:keyword>
              <r3d:institution>
        <r3d:institutionName language="eng">University of Pennsylvania, PerelmanSchool of Medizine, Computational Biology and Informatics Laboratory</r3d:institutionName>
                  <r3d:institutionAdditionalName language="eng">CBIL</r3d:institutionAdditionalName>
                <r3d:institutionCountry>USA</r3d:institutionCountry>
                  <r3d:responsibilityType>funding</r3d:responsibilityType>
                  <r3d:responsibilityType>general</r3d:responsibilityType>
                  <r3d:responsibilityType>technical</r3d:responsibilityType>
                <r3d:institutionType>non-profit</r3d:institutionType>
        <r3d:institutionURL>https://www.cbil.upenn.edu/</r3d:institutionURL>
                                
        
                  <r3d:institutionContact>RAD@pcbi.upenn.edu</r3d:institutionContact>
              </r3d:institution>
            <r3d:databaseAccess>
      <r3d:databaseAccessType>open</r3d:databaseAccessType>
          </r3d:databaseAccess>
              <r3d:dataAccess>
        <r3d:dataAccessType>restricted</r3d:dataAccessType>
                  <r3d:dataAccessRestriction>registration</r3d:dataAccessRestriction>
              </r3d:dataAccess>
              <r3d:dataLicense>
        <r3d:dataLicenseName>other</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://www.cbil.upenn.edu/node/86</r3d:dataLicenseURL>
      </r3d:dataLicense>
              <r3d:dataUpload>
        <r3d:dataUploadType>closed</r3d:dataUploadType>
              </r3d:dataUpload>
                  <r3d:software>
        <r3d:softwareName>unknown</r3d:softwareName>
      </r3d:software>
        <r3d:versioning>no</r3d:versioning>
              <r3d:pidSystem>none</r3d:pidSystem>
        <r3d:citationGuidelineURL></r3d:citationGuidelineURL>
        <r3d:enhancedPublication>unknown</r3d:enhancedPublication>
    <r3d:qualityManagement>unknown</r3d:qualityManagement>
                <r3d:remarks>Due to changes in technology and funding, the RAD website is no longer available. RAD as a schema is still very much active and incorporated in the GUS (Genomics Unified Schema) database system used by CBIL (EuPathDB, Beta Cell Genomics) and others. The schema for RAD can be viewed along with the other GUS namespaces through our Schema Browser. //  GUS is the Genomics Unified Schema, an extensive relational database schema and associated application framework designed to store, integrate, analyze, and present functional genomics data.
Description:  (a historical description is provided below). RAD as a schema is still very much active and incorporated in the GUS (Genomics Unified Schema) database system used by CBIL (EuPathDB, Beta Cell Genomics) and others. The schema for RAD can be viewed along with the other GUS namespaces through our Schema Browser. 
RAD is a resource for gene expression studies, which stores highly curated MIAME-compliant studies (i.e. experiments) employing a variety of technologies such as filter arrays, 2-channel microarrays, Affymetrix chips, SAGE, MPSS and RT-PCR. Data are available for querying and downloading based on the MGED ontology, publications or genes. Both public and private studies (the latter viewable only by users having appropriate logins and permissions) are available from this website.
Former content: 130 Experiments; 3.942 Hybridizations; 104 Arrays; 662 Protocols; 100 Publications</r3d:remarks>
    <r3d:entryDate>2012-08-27</r3d:entryDate>
    <r3d:lastUpdate>2021-03-10</r3d:lastUpdate>
  </r3d:repository>
</r3d:re3data>
    '''
    sample_data_3 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
  <r3d:repository>
    <r3d:re3data.orgIdentifier>r3d100000015</r3d:re3data.orgIdentifier>
    <r3d:repositoryName language="eng">California Water CyberInfrastructure</r3d:repositoryName>
        <r3d:repositoryURL></r3d:repositoryURL>
        <r3d:description language="eng">&lt;&lt;&lt;!!!&lt;&lt;&lt; The repository is no longer available.  2021-01-25: no more access to California Water CyberInfrastructure  &gt;&gt;&gt;!!!&lt;&lt;&lt;</r3d:description>
              <r3d:type>disciplinary</r3d:type>
          <r3d:type>institutional</r3d:type>
        <r3d:size updated=""></r3d:size>
                            <r3d:endDate>2021-01-25</r3d:endDate>
            <r3d:endDate>2021-01-25</r3d:endDate>
            
          <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
              <r3d:subject subjectScheme="DFG">3 Natural Sciences</r3d:subject>
          <r3d:subject subjectScheme="DFG">318 Water Research</r3d:subject>
          <r3d:subject subjectScheme="DFG">34 Geosciences (including Geography)</r3d:subject>
        <r3d:missionStatementURL>https://web.archive.org/web/20161122225155/http://bwc.lbl.gov/California/</r3d:missionStatementURL>
          <r3d:contentType contentTypeScheme="parse">Networkbased data</r3d:contentType>
          <r3d:contentType contentTypeScheme="parse">Scientific and statistical data formats</r3d:contentType>
              <r3d:providerType>dataProvider</r3d:providerType>
              <r3d:keyword>water resources</r3d:keyword>
              <r3d:institution>
        <r3d:institutionName language="eng">Microsoft Research</r3d:institutionName>
                <r3d:institutionCountry>USA</r3d:institutionCountry>
                  <r3d:responsibilityType>funding</r3d:responsibilityType>
                <r3d:institutionType>commercial</r3d:institutionType>
        <r3d:institutionURL>http://research.microsoft.com/en-us/</r3d:institutionURL>
                                
        
              </r3d:institution>
          <r3d:institution>
        <r3d:institutionName language="eng">University of California, Berkeley Water Center Data Server</r3d:institutionName>
                  <r3d:institutionAdditionalName language="eng">BWC</r3d:institutionAdditionalName>
                <r3d:institutionCountry>USA</r3d:institutionCountry>
                  <r3d:responsibilityType>funding</r3d:responsibilityType>
                  <r3d:responsibilityType>general</r3d:responsibilityType>
                  <r3d:responsibilityType>technical</r3d:responsibilityType>
                <r3d:institutionType>non-profit</r3d:institutionType>
        <r3d:institutionURL>https://bwc.berkeley.edu/</r3d:institutionURL>
                                
        
              </r3d:institution>
            <r3d:databaseAccess>
      <r3d:databaseAccessType>open</r3d:databaseAccessType>
          </r3d:databaseAccess>
              <r3d:dataAccess>
        <r3d:dataAccessType>restricted</r3d:dataAccessType>
                  <r3d:dataAccessRestriction>registration</r3d:dataAccessRestriction>
              </r3d:dataAccess>
                  <r3d:dataUpload>
        <r3d:dataUploadType>closed</r3d:dataUploadType>
              </r3d:dataUpload>
                  <r3d:software>
        <r3d:softwareName>other</r3d:softwareName>
      </r3d:software>
        <r3d:versioning>no</r3d:versioning>
              <r3d:pidSystem>none</r3d:pidSystem>
        <r3d:citationGuidelineURL></r3d:citationGuidelineURL>
        <r3d:enhancedPublication>unknown</r3d:enhancedPublication>
    <r3d:qualityManagement>unknown</r3d:qualityManagement>
                <r3d:remarks>FDR offer access to data from: National Climatic Data Center; USGS Surface-Water Data for California
!!! formerly description: Through the Microsoft eScience Project, the Berkeley Water Center is developing a Water Cyberinfrastructure prototype that can be used to investigate and eventually manage water resources. The Water Cyberinfrastructure is developing in close collaboration between IT, physical science, and California water agency leaders. The value of the Cyberinfrastructure prototype will be tested through relevant end-to-end demonstration focused on important California Basins. The study region(s) are chosen based on several criteria, including availability of the data, importance of the problem that can be tackled given the cyberinfrastructure to California, leveraging opportunity, and scientific importance of the problems to be addressed. The BWC is currently building partnerships with several water representatives, such as the USGS, Sonoma County Water Agency, the Monterey County Water Resource Agency, and the NOAA National Marine Fisheries Service. Our objective with the California Water projects is to first assemble only the most critical components needed to address relevant science questions, rather than to initially create fully developed problem solving environments or construct a grand scale solution.</r3d:remarks>
    <r3d:entryDate>2012-08-26</r3d:entryDate>
    <r3d:lastUpdate>2024-07-23</r3d:lastUpdate>
  </r3d:repository>
</r3d:re3data>
    '''
    sample_data_2 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
	<r3d:repository>
		<r3d:re3data.orgIdentifier>r3d100000002</r3d:re3data.orgIdentifier>
		<r3d:repositoryName language="eng">Access to Archival Databases</r3d:repositoryName>
        <r3d:additionalName language="eng">AAD</r3d:additionalName>
        <r3d:repositoryURL>https://aad.archives.gov/aad/</r3d:repositoryURL>
        <r3d:repositoryIdentifier>RRID:SCR_010479</r3d:repositoryIdentifier>
        <r3d:repositoryIdentifier>RRID:nlx_157752</r3d:repositoryIdentifier>
        <r3d:description language="eng">You will find in the Access to Archival Databases (AAD) resource online access to records in a small selection of historic databases preserved permanently in NARA. Out of the nearly 200,000 data files in its holdings, NARA has selected approximately 475 of them for public searching through AAD. We selected these data because the records identify specific persons, geographic areas, organizations, and dates. The records cover a wide variety of civilian and military functions and have many genealogical, social, political, and economic research uses. AAD provides: Access to over 85 million historic electronic records created by more than 30 agencies of the U.S. federal government and from collections of donated historical materials.
Both free-text and fielded searching options. The ability to retrieve, print, and download records with the specific information that you seek. Information to help you find and understand the records.</r3d:description>
        <r3d:repositoryContact>https://www.archives.gov/contact</r3d:repositoryContact>
        <r3d:type>disciplinary</r3d:type>
        <r3d:size updated=""></r3d:size>
        <r3d:startDate>1985</r3d:startDate>
        <r3d:startDate>1985</r3d:startDate>
        <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
        <r3d:repositoryLanguage>spa</r3d:repositoryLanguage>
        <r3d:subject subjectScheme="DFG">1 Humanities and Social Sciences</r3d:subject>
        <r3d:subject subjectScheme="DFG">102 History</r3d:subject>
        <r3d:subject subjectScheme="DFG">11 Humanities</r3d:subject>
        <r3d:missionStatementURL>https://www.archives.gov/publications/general-info-leaflets/1-about-archives.html</r3d:missionStatementURL>
        <r3d:contentType contentTypeScheme="parse">Images</r3d:contentType>
        <r3d:contentType contentTypeScheme="parse">Standard office documents</r3d:contentType>
        <r3d:contentType contentTypeScheme="parse">Structured text</r3d:contentType>
        <r3d:contentType contentTypeScheme="parse">other</r3d:contentType>
        <r3d:providerType>dataProvider</r3d:providerType>
        <r3d:keyword>US History</r3d:keyword>
        <r3d:institution>
            <r3d:institutionName language="eng">The U.S. National Archives and Records Administration</r3d:institutionName>
            <r3d:institutionAdditionalName language="eng">NARA</r3d:institutionAdditionalName>
            <r3d:institutionAdditionalName language="eng">National Archives</r3d:institutionAdditionalName>
            <r3d:institutionCountry>USA</r3d:institutionCountry>
            <r3d:responsibilityType>general</r3d:responsibilityType>
            <r3d:institutionType>non-profit</r3d:institutionType>
            <r3d:institutionURL>https://www.archives.gov/</r3d:institutionURL>
            <r3d:institutionIdentifier>ROR:032214n64</r3d:institutionIdentifier>
            <r3d:institutionContact>https://www.archives.gov/press/contact.html</r3d:institutionContact>
        </r3d:institution>
        <r3d:institution>
            <r3d:institutionName language="eng">The USA.gov</r3d:institutionName>
            <r3d:institutionCountry>USA</r3d:institutionCountry>
            <r3d:responsibilityType>general</r3d:responsibilityType>
            <r3d:institutionType>non-profit</r3d:institutionType>
            <r3d:institutionURL>https://www.usa.gov/</r3d:institutionURL>
            <r3d:institutionContact>https://www.usa.gov/contact-center</r3d:institutionContact>
        </r3d:institution>
        <r3d:policy>
            <r3d:policyName>Contribution Policy</r3d:policyName>
            <r3d:policyURL>https://www.archives.gov/developer#toc-contribution-policy</r3d:policyURL>
        </r3d:policy>
        <r3d:policy>
            <r3d:policyName>Freedom of Information Act - FOAI</r3d:policyName>
            <r3d:policyURL>https://www.archives.gov/foia</r3d:policyURL>
        </r3d:policy>
        <r3d:policy>
            <r3d:policyName>Privacy and Use</r3d:policyName>
            <r3d:policyURL>https://www.archives.gov/global-pages/privacy.html</r3d:policyURL>
        </r3d:policy>
        <r3d:databaseAccess>
			<r3d:databaseAccessType>open</r3d:databaseAccessType>
        </r3d:databaseAccess>
        <r3d:dataAccess>
            <r3d:dataAccessType>open</r3d:dataAccessType>
        </r3d:dataAccess>
        <r3d:dataLicense>
            <r3d:dataLicenseName>Copyrights</r3d:dataLicenseName>
            <r3d:dataLicenseURL>https://www.archives.gov/global-pages/privacy.html#copyright</r3d:dataLicenseURL>
        </r3d:dataLicense>
        <r3d:dataUpload>
            <r3d:dataUploadType>restricted</r3d:dataUploadType>
            <r3d:dataUploadRestriction>other</r3d:dataUploadRestriction>
        </r3d:dataUpload>
        <r3d:software>
            <r3d:softwareName>unknown</r3d:softwareName>
        </r3d:software>
        <r3d:versioning>no</r3d:versioning>
        <r3d:api apiType="other">https://www.archives.gov/developer#toc-application-programming-interfaces-apis-</r3d:api>
        <r3d:pidSystem>none</r3d:pidSystem>
        <r3d:citationGuidelineURL>https://aad.archives.gov/aad/help/getting-started-guide.html#cite</r3d:citationGuidelineURL>
        <r3d:enhancedPublication>unknown</r3d:enhancedPublication>
		<r3d:qualityManagement>unknown</r3d:qualityManagement>
        <r3d:remarks></r3d:remarks>
		<r3d:entryDate>2012-07-04</r3d:entryDate>
		<r3d:lastUpdate>2024-02-21</r3d:lastUpdate>
	</r3d:repository>
</r3d:re3data>
    '''
    sample_data_1 = b'''<?xml version="1.0" encoding="utf-8"?>
<!--re3data.org Schema for the Description of Research Data Repositories. Version 2.2, December 2014. doi:10.2312/re3.006-->
<r3d:re3data xmlns:r3d="http://www.re3data.org/schema/2-2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.re3data.org/schema/2-2 http://schema.re3data.org/2-2/re3dataV2-2.xsd">
  <r3d:repository>
    <r3d:re3data.orgIdentifier>r3d100000001</r3d:re3data.orgIdentifier>
    <r3d:repositoryName language="eng">Odum Institute Archive Dataverse</r3d:repositoryName>
    <r3d:repositoryURL>https://dataverse.unc.edu/dataverse/odum</r3d:repositoryURL>
    <r3d:description language="eng">The Odum Institute Archive Dataverse contains social science data curated and archived by the Odum Institute Data Archive at the University of North Carolina at Chapel Hill. Some key collections include the primary holdings of the Louis Harris Data Center, the National Network of State Polls, and other Southern-focused public opinion data.
Please note that some datasets in this collection are restricted to University of North Carolina at Chapel Hill affiliates. Access to these datasets require UNC ONYEN institutional login to the Dataverse system.</r3d:description>
    <r3d:repositoryContact>https://dataverse.unc.edu/dataverse/odum#</r3d:repositoryContact>
    <r3d:repositoryContact>odumarchive@unc.edu</r3d:repositoryContact>
    <r3d:type>disciplinary</r3d:type>
    <r3d:size updated="2023-09-19">13 dataverses; 3.310 datasets</r3d:size>
    <r3d:startDate></r3d:startDate>
    <r3d:endDate></r3d:endDate>
    <r3d:repositoryLanguage>eng</r3d:repositoryLanguage>
    <r3d:subject subjectScheme="DFG">1 Humanities and Social Sciences</r3d:subject>
    <r3d:subject subjectScheme="DFG">111 Social Sciences</r3d:subject>
    <r3d:subject subjectScheme="DFG">11104 Political Science</r3d:subject>
    <r3d:subject subjectScheme="DFG">112 Economics</r3d:subject>
    <r3d:subject subjectScheme="DFG">12 Social and Behavioural Sciences</r3d:subject>
    <r3d:missionStatementURL></r3d:missionStatementURL>
    <r3d:contentType contentTypeScheme="parse">Databases</r3d:contentType>
    <r3d:contentType contentTypeScheme="parse">Plain text</r3d:contentType>
    <r3d:contentType contentTypeScheme="parse">Scientific and statistical data formats</r3d:contentType>
    <r3d:contentType contentTypeScheme="parse">Standard office documents</r3d:contentType>
    <r3d:contentType contentTypeScheme="parse">other</r3d:contentType>
    <r3d:providerType>dataProvider</r3d:providerType>
    <r3d:keyword>FAIR</r3d:keyword>
    <r3d:keyword>Middle East</r3d:keyword>
    <r3d:keyword>crime</r3d:keyword>
    <r3d:keyword>demography</r3d:keyword>
    <r3d:keyword>economy</r3d:keyword>
    <r3d:keyword>education</r3d:keyword>
    <r3d:keyword>election</r3d:keyword>
    <r3d:keyword>environment</r3d:keyword>
    <r3d:keyword>finance</r3d:keyword>
    <r3d:keyword>health care</r3d:keyword>
    <r3d:keyword>presidents United States</r3d:keyword>
    <r3d:keyword>taxes</r3d:keyword>
    <r3d:institution>
        <r3d:institutionName language="eng">Odum Institute for Research in Social Science</r3d:institutionName>
        <r3d:institutionCountry>USA</r3d:institutionCountry>
        <r3d:responsibilityType>general</r3d:responsibilityType>
        <r3d:institutionType>non-profit</r3d:institutionType>
        <r3d:institutionURL>https://odum.unc.edu/archive/</r3d:institutionURL>
        <r3d:responsibilityStartDate></r3d:responsibilityStartDate>
        <r3d:responsibilityEndDate></r3d:responsibilityEndDate>
        <r3d:institutionContact>https://odum.unc.edu/contact/contact-form/</r3d:institutionContact>
    </r3d:institution>
    <r3d:policy>
        <r3d:policyName>Collection Development Policy</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_CollectionDevelopment_20170501.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>CoreTrustSealAssessment</r3d:policyName>
        <r3d:policyURL>https://www.coretrustseal.org/wp-content/uploads/2020/10/Odum-Institute-Data-Archive.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>Data Security Guidelines</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Guidelines_DataSecurity_20170501-1.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>Digital Preservation Policy</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_DigitalPreservation_2020200124.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>Metadata Guidelines</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Guidelines_Metadata_20170501.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>Odum Institute Data Archive Data Curation Workflow</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Pipeline_201703.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:policy>
        <r3d:policyName>UNC Dataverse terms of use</r3d:policyName>
        <r3d:policyURL>https://odum.unc.edu/files/2020/01/Policy_UNCDataverseTermsofUse_20170501.pdf</r3d:policyURL>
    </r3d:policy>
    <r3d:databaseAccess>
        <r3d:databaseAccessType>open</r3d:databaseAccessType>
    </r3d:databaseAccess>
    <r3d:databaseLicense>
        <r3d:databaseLicenseName>CC0</r3d:databaseLicenseName>
        <r3d:databaseLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:databaseLicenseURL>
    </r3d:databaseLicense>
    <r3d:dataAccess>
    <r3d:dataAccessType>embargoed</r3d:dataAccessType>
    </r3d:dataAccess>
    <r3d:dataAccess>
    <r3d:dataAccessType>open</r3d:dataAccessType>
    </r3d:dataAccess>
    <r3d:dataAccess>
    <r3d:dataAccessType>restricted</r3d:dataAccessType>
    <r3d:dataAccessRestriction>institutional membership</r3d:dataAccessRestriction>
    <r3d:dataAccessRestriction>other</r3d:dataAccessRestriction>
    </r3d:dataAccess>
    <r3d:dataLicense>
        <r3d:dataLicenseName>CC</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:dataLicenseURL>
    </r3d:dataLicense>
    <r3d:dataLicense>
        <r3d:dataLicenseName>CC0</r3d:dataLicenseName>
        <r3d:dataLicenseURL>https://creativecommons.org/share-your-work/public-domain/cc0</r3d:dataLicenseURL>
    </r3d:dataLicense>
    <r3d:dataUpload>
        <r3d:dataUploadType>restricted</r3d:dataUploadType>
        <r3d:dataUploadRestriction>institutional membership</r3d:dataUploadRestriction>
    </r3d:dataUpload>
    <r3d:software>
        <r3d:softwareName>Dataverse</r3d:softwareName>
    </r3d:software>
    <r3d:versioning></r3d:versioning>
    <r3d:pidSystem>DOI</r3d:pidSystem>
    <r3d:citationGuidelineURL></r3d:citationGuidelineURL>
    <r3d:enhancedPublication>unknown</r3d:enhancedPublication>
    <r3d:qualityManagement>yes</r3d:qualityManagement>
    <r3d:certificate>other</r3d:certificate>
    <r3d:metadataStandard>
      <r3d:metadataStandardName metadataStandardScheme="DCC">DDI - Data Documentation Initiative</r3d:metadataStandardName>
      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/ddi-data-documentation-initiative</r3d:metadataStandardURL>
    </r3d:metadataStandard>
    <r3d:metadataStandard>
      <r3d:metadataStandardName metadataStandardScheme="DCC">DataCite Metadata Schema</r3d:metadataStandardName>
      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/datacite-metadata-schema</r3d:metadataStandardURL>
    </r3d:metadataStandard>
    <r3d:metadataStandard>
      <r3d:metadataStandardName metadataStandardScheme="DCC">Dublin Core</r3d:metadataStandardName>
      <r3d:metadataStandardURL>http://www.dcc.ac.uk/resources/metadata-standards/dublin-core</r3d:metadataStandardURL>
    </r3d:metadataStandard>
    <r3d:remarks>Odum Dataverse is covered by Thomson Reuters Data Citation Index.
Odum Institute Archive Dataverse is part of UNC Dataverse</r3d:remarks>
    <r3d:entryDate>2013-06-10</r3d:entryDate>
    <r3d:lastUpdate>2023-09-19</r3d:lastUpdate>
  </r3d:repository>
</r3d:re3data>
    '''
    expected_item_1 = {
        'id': ('r3d100000001',),
        'repositoryName': ('Odum Institute Archive Dataverse',),  # ToDo: Falta honrrar el lenguaje (en varios casos)
        'repositoryURL': ('https://dataverse.unc.edu/dataverse/odum',),
        'description': (
            'The Odum Institute Archive Dataverse contains social science data curated and archived by the Odum Institute Data Archive at the University of North Carolina at Chapel Hill. Some key collections include the primary holdings of the Louis Harris Data Center, the National Network of State Polls, and other Southern-focused public opinion data.\nPlease note that some datasets in this collection are restricted to University of North Carolina at Chapel Hill affiliates. Access to these datasets require UNC ONYEN institutional login to the Dataverse system.',),
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
    sample_datas = [
        sample_data_1,
        sample_data_2,
        sample_data_3,
        sample_data_4,
        sample_data_5,
        # sample_data_6,
        # sample_data_7,
    ]
    expected_items = [expected_item_1, None, None, None, None, None, None]
    for expected_item, sample_data in zip(expected_items, sample_datas):
        transformed_result = refine_repository_info(schema_instance, sample_data)
        if expected_item is None:
            continue
        for (expected_item_k, expected_item_v) in expected_item.items():
            actual = transformed_result[expected_item_k]
            expected = expected_item_v[0]
            assert actual == expected, "Dont match '%s'. Expected %s. Actual %s" % (
                expected_item_k, repr(expected), repr(actual))
