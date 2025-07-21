# RDA Metadata Standards Catalog integration

Integration of the RDA Metadata Standards Catalog (https://rdamsc.bath.ac.uk/) through its API (https://app.swaggerhub.com/apis-docs/alex-ball/rda-metadata-standards-catalog/2.0.0#/m/get_api2_m).

Permite conocer los crosswalks entre diferentes Metadata Schemas y provee la documentación sobre como implementar ese crosswalk.

Schemas
```commandline
{
  "description": "<p>A semantic standard developed by the Food and Agriculture Organization (FAO) of the United Nations, AgMES enables description, resource discovery, interoperability and data exchange of different types of information resources in all areas relevant to food production, nutrition and rural development.</p><p>The standard is maintained by AIMS (Agricultural Information Management Standards), and while it has been used in various application profiles, it is now deprecated for new uses and will no longer be updated.</p>",
  "keywords": [
    "http://vocabularies.unesco.org/thesaurus/concept596",
    "http://vocabularies.unesco.org/thesaurus/concept598",
    "http://vocabularies.unesco.org/thesaurus/concept1323",
    "http://vocabularies.unesco.org/thesaurus/concept2423"
  ],
  "locations": [
    {
      "type": "website",
      "url": "http://aims.fao.org/standards/agmes"
    },
    {
      "type": "document",
      "url": "http://aims.fao.org/standards/agmes/namespace-specification"
    }
  ],
  "mscid": "msc:m2",
  "relatedEntities": [
    {
      "id": "msc:m45",
      "role": "child scheme"
    },
    {
      "id": "msc:g131",
      "role": "maintainer"
    },
    {
      "id": "msc:t1",
      "role": "tool"
    },
    {
      "id": "msc:g2",
      "role": "user"
    }
  ],
  "slug": "agmes-agricultural-metadata-element-set",
  "title": "AgMES (Agricultural Metadata Element Set)",
  "uri": "https://rdamsc.bath.ac.uk/api2/m2",
  "versions": [
    {
      "issued": "2003-02-01",
      "locations": [
        {
          "type": "RDFS",
          "url": "https://web.archive.org/web/20171011092147/http://ftp.fao.org/gi/gil/gilws/aims/metadata/xml/ags.rdf"
        }
      ],
      "namespaces": [
        {
          "prefix": "agmes",
          "uri": "http://purl.org/agmes/1.1/"
        }
      ],
      "number": "1.1",
      "valid": {
        "end": "2010-11-11",
        "start": "2003-02-01"
      }
    }
  ]
}
```
