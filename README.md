#GetUrRecon == Get Your Recon[ciliation]

##Goal
Build a library that, given a selected field in a given metadataset, can perform entity matching and related data retrieval from a set of library-focused authority and external datasets. The ability to choose a match confidence range for auto-matching as well as a method for bringing in matched related data labels or URIs into the original metadata set is in scope.

##Breaking out the Use Cases

###Reconciliation (Things to Things)
Given a URI in the descriptive metadata, bibliographic record, or RDF graph, this should find possible other URIs from external vocabularies, authorities or datasets and return that URI and preferred label. That external match is given a score, and if the score is in or above the decided match range, it should be put back in the originating metadataset. If below, the "recon objects" can be stored for later, human review and decision.

###Entity Resolution (Strings to Things)
Given a literal/string in the descriptive metadata, bibliographic record, or RDF graph, this should find possible URIs from external vocabularies, authorities or datasets and return that URI and the preferred label. The external match is given a score, and if the score is in or above the decided match range, it should be put back in the originating metadataset. If below, the "recon objects" can be stored for later, human review and decision.

###Lexicalization (Things to Strings)
Given an URI in the descriptive metadata, bibliographic record, or RDF graph, this should return possible matches with URIs and labels. The external matches are given scores, as proposed above. With that matching URI, it should be possible to retrieve other pref or alt labels as wanted.

###Metadata Normalization
Both of the above require normalization of the metadata pre and post review. This is often heavily dependent on work required outside of using this library. However, some common normalization routines that improve matching might be made into functions.

##Overview
This is the proposed game plan for this library:

1. Metadata is file stored locally or a graph available via SPARQL endpoint with supplied pattern
2. For library to work, designate:
  * the Metadata File or SPARQL endpoint with Resource Graph Pattern
  * the Row, Record or Graph definer/boundary for the resource metadata (through element name? xpath? depends on metadata format)
  * the Column, Field or Property pointing to the datapoint to be matched
  * if the datapoint is URI or literal
  * the matching type (PersonalName, CorporateName, Name, Topic, GeographicName, GenreForm, Title)
  * the matching confidence level (for determining automated matching)
3. Library generates a "recon object" which is json containing:
  * the literal or URI to be matched
  * other information from the graph or record for the chosen matching type as available (see below)
  * a record identifier or graph URI
  * the matching confidence level
4. The "recon object" is expanded according to:
  * calls made to external authorities currently supported, using either direct calls to APIs or sameAs relationships between external databases for those that support/contain them
  * the top 3 matches from each external authority supported are evaluated using the matching types are evaluated
  * a score for each is created, and the match with the highest score is added to the recon object
  * the match's URI or identifier and preferred label are returned with the score
  * the match's sameAs URIs if available from the external vocabulary
5. Have the user select a chosen recon service to use for then adding or overwriting the selected match label or URI to the original metadata file.

##Metadata Formats and Fields
It'd be best to be able to support all the possible metadata fields containing datapoints to be matched and enhanced, but this work is created with working with either literals/strings or URIs from the following metadata fields presented in either a bibliographic or descriptive metadata record or graph describing a resource:

- DC:
  - dc:contributor
  - dc:coverage
  - dc:creator
  - dc:subject
- DCTerms:
  - dcterms:contributor
  - dcterms:coverage
  - dcterms:creator
  - dcterms:rightsHolder
  - dcterms:spatial
  - dcterms:subject
- MODS:
  - mods:name/mods:namePart | mods:name[@valueURI]/mods:namePart
  - mods:genre | mods:genre[@valueURI]
  - mods:physicalDescription/mods:form | mods:physicalDescription/mods:form[@valueURI]
  - mods:subject/mods:topic | mods:subject/mods:topic[@valueURI]
  - mods:subject/mods:name/mods:namePart | mods:subject/mods:name[@valueURI]/mods:namePart
  - mods:subject/mods:geographic | mods:subject/mods:geographic[@valueURI]
  - mods:subject/mods:genre | mods:subject/mods:genre[@valueURI]
  - mods:subject/mods:titleInfo/mods:title | mods:subject/mods:titleInfo[@valueURI]/mods:title
- MARC21:
  - 100
  - 110
  - 600
  - 610
  - 650
  - 655
  - 700
  - 710

And those fields/elements can appear in records or graphs in the following formats, accessible through a local file or a SPARQL query with the supplied pattern:

- CSV
- XML
- JSON
- binary MARC
- RDF Ntriples
- RDF Turtle
- RDF JSON-LD

##Authorities and External Databases
The chosen field will be matched with the following vocabularies and/or external datasets (to be expanded as given use cases and time):

- http://id.loc.gov/ (Library of Congress Name Authority File, Subject Headings, Genre/Form Terms, and Cultural Heritage Organizations)
- http://vocab.getty.edu/ (Getty Art and Architecture Thesaurus, Thesaurus of Geographic Names, and Union List of Artists' Names)
- http://geonames.org (Geonames geographical database)
- http://viaf.org/ (OCLC Virtual International Authority File)
- http://experimental.worldcat.org/fast/ (OCLC Faceted Application of Subject Terminology)
- https://query.wikidata.org/ (Wikidata)
- http://vivo.cornell.edu/reconcile (Cornell VIVO via their OpenRefine Endpoint)

##Matching Types and Scoring
Not all datapoints can be treated equally in matching or score generation. The various types given below are loosely defined groups of datapoints that are similar enough to share matching contexts/"algorithms", as much as they can be called that.

###PersonalName
Personal Names often share the issues of false positives (i.e. getting an accurate match for 'John Smith') and various forms of heading names ('Smith, John', 'John Smith', 'Smith, John, 1900-1980', 'John Smith (photographer)', etc.).

Preferred and alternate labels string matching is the first step, but an exact match there alone is not considered a top match for personal names. These additional matching points are used with the label matching results, where they can be parsed and retrieved:

1. life dates
2. work titles
3. role terms/job types
4. related geographic places (place of birth, place of death, place of activity)
5. affiliations
6. topical areas of interest/work/influence

The first two, if exact matches can be made, make the result considered a top match.

The rest, or partial matches of the first two, are added together to make score that qualifies the match.

###CorporateName
Corporate Names, like Personal Names, do share the issue of false positives, but to a far lesser degree (i.e. 'AT&T' versus 'AT&T Corporation'). The variation of forms remains, but again, to a far lesser degree (i.e. 'ATT', 'AT&T', 'AT&T Inc.', )

Preferred and alternate labels string matching is the first step, and an exact match there alone **is** considered a top match for corporate names. These additional matching points are used with the label matching results, where they can be parsed and retrieved:

1. corporate dates
2. work titles
3. related geographic places (place of headquarters, place of origination)
4. topical areas of interest/work/influence

###Name
Often, for non-MARC metadata, personal and corporate names are in the same field and not easily separated. So the Name type is for more generic matching of fields that could be personal or corporate names.

Preferred and alternate labels string matching is the first step, but an exact match there alone is not considered a top match for generic names. These additional matching points are used with the label matching results, where they can be parsed and retrieved:

1. dates
2. work titles
3. role terms/job types
4. related geographic places
5. affiliations
6. topical areas of interest/work/influence

###Topic
Topical headings are usually a reliable match based on labels (alternative and/or preferred) alone. Other matching points have yet to be added to this to enhance scoring, though this will need to be done for datasets that have specific subject areas (i.e. dealing with different topical foci - art history versus mathematics and their requisite topical heading sets).

The possibility of triangulating possible topic matches with the other topical headings (including classification system assignments) in a record for better matching needs to be explored.

###GeographicName
Geographic headings often have false positives due to lack of qualifiers (i.e. 'Richmond' versus 'Richmond (Virginia)'), or they have false negatives due to variation of qualifiers/headings (i.e. 'Richmond (Va.)' versus 'Richmond (Virginia)' versus 'Richmond'). This field generally requires more parsing of the metadatapoint handed over (whether literal or a URI with attached labels) for matching.

Preferred and alternate labels string matching is the first step, but an exact match there alone is not considered a top match for geographic names, dependent on the external vocabulary (id.loc.gov, VIAF, FAST matches do consider label matching as sufficient for high accuracy match; Wikidata, TGN, and Geonames, label matching alone is not considered sufficient).

These additional matching points are used with the label matching results, where they can be parsed and retrieved:

1. hierarchical levels (Country, State/Province, City)
2. default country (set by person running query for a set)
3. coordinates?

These are added together to make score that further qualifies the match.

###GenreForm
Genre or Form headings are usually a reliable match based on labels (alternative and/or preferred) alone, if the appropriate vocabulary is chosen for matching. Other matching points have yet to be added to this to enhance scoring.

These should not be conflated with item types, which are usually a much smaller subset and not requiring such granular or involved matching work.

###Title
To be explored. Could be considered frbr:work titles, uniform titles (though that usually conflates with frbr:work title), conference titles, or other.

##Recon Objects
Example of a "recon object" built out in this program:

To be written.

##Examples of Use
To be written.
