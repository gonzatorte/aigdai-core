ELK is an ontology reasoner that aims to support the OWL 2 EL profile.
See https://github.com/liveontologies/elk-reasoner/wiki for further information.

ELK Reasoner is Copyright (c) 2011 - 2024 
Live Ontologies Project

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

ABOUT:

This package contains a Java library for accessing ELK through 
OWL API plus all third party libraries used by ELK, except for the 
OWL API itself. The OWL API library can be obtained here:

    http://owlapi.sourceforge.net/

REQUIREMENTS:

ELK OWL API bindings are tested to work with OWL API 5.1.20. It may work 
with other versions of OWL API.

Java 8 or higher.

INSTALLATION:

To use the library make sure that Java finds elk-owlapi-library-0.6.0.jar, and
the third party libraries from the lib directory in the class path.

USAGE:

Usage instructions, including an example program demonstrating how to use ELK
through OWL API for ontology classification, can be found here:

    https://github.com/liveontologies/elk-reasoner/wiki/ELK_from_OWL_API  
    
Several example programs on how to classify an ontology and how to query the
reasoner with unnamed class expressions are included here in the folder:

	examples/src/org/semanticweb/elk/owlapi/examples