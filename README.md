FYI: Work in progress. Doesn't work as you'd expect in current form.

Notes from other documentation from project that spawned form this library will take + goals it will approach. To be rewritten/recycled for this project:

#OCLC Entity Pilot Testing

##Sample Data

###[Ecommons](https://ecommons.cornell.edu)

Ecommons OAI-PMH Simple DC Overview:

```
{http://purl.org/dc/elements/1.1/}contributor: |                         |    681/27821 |   2%
    {http://purl.org/dc/elements/1.1/}creator: |===================      |  21842/27821 |  78%
       {http://purl.org/dc/elements/1.1/}date: |=========================|  27821/27821 | 100%
{http://purl.org/dc/elements/1.1/}description: |======================   |  25203/27821 |  90%
     {http://purl.org/dc/elements/1.1/}format: |======                   |   7779/27821 |  27%
 {http://purl.org/dc/elements/1.1/}identifier: |======================== |  27820/27821 |  99%
   {http://purl.org/dc/elements/1.1/}language: |=======================  |  26490/27821 |  95%
  {http://purl.org/dc/elements/1.1/}publisher: |===============          |  17647/27821 |  63%
   {http://purl.org/dc/elements/1.1/}relation: |===                      |   4342/27821 |  15%
     {http://purl.org/dc/elements/1.1/}rights: |                         |     23/27821 |   0%
     {http://purl.org/dc/elements/1.1/}source: |                         |      1/27821 |   0%
    {http://purl.org/dc/elements/1.1/}subject: |====================     |  22519/27821 |  80%
      {http://purl.org/dc/elements/1.1/}title: |=========================|  27821/27821 | 100%
       {http://purl.org/dc/elements/1.1/}type: |=======================  |  26101/27821 |  93%
```

Field to be test reconciled with OCLC Entity Pilot: **dc:creator**

Notes:
- 15,889 unique names in 27,821 records.
- 227 unique names without commas (mix of corporate names and not inverted personal names). Most personal names are in last name, first name form.
- 27 unique names with numbers, mostly dates (1 email address, few typos). These unique names with dates are given below (numbers beside each mean how many times they appear in the ECommons data) because Jason asked about them:
  - 2005 Winter Dairy Management Series
  - Bartlett, Samuel Colcord, 1817-1898
  - Blodgett, Henry, 1825-1903
  - Boone, William Jones, 1811-1864
  - Edkins, Joseph, 1823-1905
  - Favier, Alphonse, 1837-1905
  - Ghali, Waguih, d. 1969
  - Kushwaha1, H.L.
  - Laufer, Berthold, 1874-1934
  - Legge, James, 1815-1897
  - Medhurst, Walter Henry, 1796-1857
  - Montucci, Antonio, 1762-1829
  - Mullens, Joseph, 1820-1879
  - New York State 4-H Camping Program
  - Pakenham-Walsh, William Sandford, Rev, 1868-1960
  - Parvus, 1867-1924
  - Philip, Robert, 1791-1858
  - Salisbury, Edward Elbridge, 1814-1901
  - Schereschewsky, Samuel Isaac Joseph, Bp., 1831-1906
  - Smith, Arthur Henderson, 1845-1932
  - Speer, Robert Elliott, 1867-1947
  - Stevens, William Bacon, Bp., 1815-1887
  - Taylor, James Hudson, 1832-1905
  - Wilson, Alpheus Waters, Bishop, 1834-1916
  - Winter Dairy Management 2008
  - Wylie, Alexander, 1815-1887
  - mwc34@cornell.edu, John
- some corporate names following LC heading form
- 71 unique headings have parenthesis. Many include middle names or full names in parenthesis. Some include qualifiers or role terms in parenthesis (uncertain if authority record headings qualifiers or concatenated role terms, looks to be mix of both).

**All unique values in that field with counts are in [ECommonsCreatorsUnique.txt](ECommonsCreatorsUnique.txt)**

##Matching Process

**Proposal**: Personal names (primary focus here) are best automatically matched using:

1. life dates (in OCLC Entity response, id.loc.gov, VIAF, Wikidata, ...). With exact match here and above average score for matching name strings (this needs to be firmed down as number ranges to both OCLC Entities score and other string matching possibilities)
2. Well above average score for matching name strings and one or more of the following:
  a. >90% subject matching (subjects in OCLC Entity response, original DC records, Wikidata...)
  b. >90% affiliation matching (publishers in original DC records *for this example*, 373 in id.loc.gov MARC response, 510 in VIAF, wdt:P108 in wikidata... (ISNI seems to repeat other data sources' affiliations))
  c. Matching in some way of role terms/relator codes? Need to explore further.
  d. Other?
3. Match of URI in source data (not seeing any so far in the original DC records for this example) with any/multiple of OCLC Entity SameAs URIs or identifiers from those URIs (i.e. the n12344556 from id.loc.gov URI).

This matching could occur without Entity pilot, but that provides a good starting point for exploring a number of data sources. What could help with this jumping off point:

1. Putting sameAs links in entity search response. This could help simplify somewhat this process, as well as maybe help with secondary de-duping of OCLC Entity Search responses.
2. Providing multi-index searching (being able to search name and associated dates from the beginning to get better results, matching)
3. Allowing fuzzy matching parameters to capture name labels that also have other information attached in the same field (as often happens with non-MARC metadata). Examples: names with dates, role terms, etc. Otherwise, this requires (per usual, so its not more effort than regular metadata matching and enhancement work) normalization work before running against OCLC Entity search API for decent results.

With the Results CSV provided here, the plan is to review and see if these matching points could work. Any fields with 'CUL score' in them means the script does basic levenshtein text matching of a field in the DC record and a field returned from one of the authorities/external data sources.

##Entities.py

This is built to, I hope, become the basis for a metadata entity matching python library that can work with common external library data sources - hence the preliminary work with classes (to be broken out into modules). Any feedback welcome, though its a work in progress.

##Results.csv

Guide to fields in CSV reports generated:

Each row is based on the separate dc:creator field instances to be reconciled. It is not a unique instance of every dc:creator field across the dataset as other contextual information from the record is being used for name entity matching rankings (title of work, affiliation, subjects, publication date...).

  - "record_identifier": oai record identifier for ecommons DC record. Used as way to confirm entity matching updates pathway.
  - "ecommons_entity_name": name of field to be matched. For ecommons DC records, using dc:creator, and all instances are literals/text strings. Would like to test with set also containing URIs or other identifiers next.
  - "ecommons_title": title of work described in the ecommons DC record.
  - "ecommons_title_year": The year of publication of the work taken from the Ecommons DC record. Not sure I can really use this for any meaningful entity disambiguation.
  - "ecommons_subject": Subjects from the Ecommons DC record. Stored as a list that are then matched (simply using Levenshtein matching) with subjects from the OCLC Entity Search Results topic. Highest score is stored in OCLC_result[n]_subject_CUL_score (below).
  - "ecommons_publisher": The publisher taken from the ecommons DC record. This field, for the simple DC OAI-PMH field from Ecommons seems to correlate with the academic affiliations, which makes some sense for ecommons as it is an institutional repository. Used to match against affiliations in other datasets, explained below.
  - "search_url": The OCLC Entity Search URL, stored for debugging/secondary check purposes.
  - "OCLC_result[n]_preflabel": The OCLC Entity Search Result preferred label. For this experiment, only the top 2 results are grabbed and processed.
  - "OCLC_result[n]_birthdate": The OCLC Entity Search Result birthdate. Maybe find way to match with record entity names where the life dates information has been normalized out.
  - "OCLC_result[n]_deathdate": The OCLC Entity Search Result deathdate. Same normalization/matching note as above.
  - "OCLC_result[n]_score": The OCLC Entity Search Result score.
  - "OCLC_result[n]_subject": The OCLC Entity Search Result topic field (usually/only ever 1?).
  - "OCLC_result[n]_subject_CUL_score": The levenshtein matching score of the OCLC Entity Search Result topic and the subject fields from the original ecommons DC record. All the subjects in both records are compared, and the highest result returned.
  - "OCLC_result[n]_OCLC_URI": The OCLC Entity URI for the result.
  - "OCLC_result[n]_LoC_preflabel": The Library of Congress preferred label, returned using the OCLC Entity URI, the sameAs service, then the id.loc.gov APIs and N-Triples result.
  - "OCLC_result[n]_LoC_URI": The Library of Congress URI for the entity, returned using the OCLC Entity URI. Used for retrieving the Library of Congress preferred label (above) and the LoC information below.
  - "OCLC_result[n]_LoC_birthdate": The Library of Congress birth year for the entity, taken from the MARC/XML record available via id.loc.gov. Year is returned from either the 046f or, if the 046 is not present, the 100d[:4].
  - "OCLC_result[n]_LoC_deathdate": The Library of Congress death year for the entity, taken from the MARC/XML record available via id.loc.gov. Year is returned from either the 046f or, if the 046 is not present, the 100d[-4:]
  - "OCLC_result[n]_LoC_affiliation_CUL_score": If the LoC record has a 373a, those entries are matched against the publisher field in the original ecommons DC record and the score returned. None have had 373a's yet. Possibility of doing this matching with keyword searching in 670s, seems too vague though.
  - "OCLC_result[n]_VIAF_URI": The VIAF URI for the entity, retrieved from the OCLC Entity SameAs API. Used for the calls below.
  - "OCLC_result[n]_VIAF_title_CUL_score": Via the VIAF API's resulting MARC/XML records, all the titles (510a) are matched with the title in the original ecommons dc:title, and a simple matching result returned.
  - "OCLC_result[n]_VIAF_affiliation_CUL_score": Via the VIAF API's resulting MARC/XML records, all the titles (910a) are matched with the title in the original ecommons dc:publisher, and a simple matching result returned.
  - "OCLC_result[n]_ISNI_URI": The ISNI URI for the entity retrieved via the OCLC Entity SameAs API. Not used for further matching yet, as it seems to be repeating information from other datasets.
  - "OCLC_result[n]_Wiki_URI": The Wikidata URI for the entity, retrieved via the OCLC Entity SameAs API. Used then to generate a SPARQL query for the Wikidata endpoint to retrieve other information about the entity.
  - "OCLC_result[n]_Wiki_aff_CUL_score": The Wikidata URI for the entity, retrieved via the OCLC Entity SameAs API, is used to generate a SPARQL query for the Wikidata endpoint to retrieve the employers of the entity. That is then matched against the dc:publisher field in the ecommons DC record. Not sure why scores aren't being returned at present, as the titles are. Definite case of matching lists to lists.
