import re

#XML namespaces
ns = {'mods': 'http://www.loc.gov/mods/v3',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'oai': 'http://www.openarchives.org/OAI/2.0/',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
      'marcxml': 'http://www.loc.gov/MARC21/slim'}
OAI = '{%(oai)s}' % ns
DC = '{%(dc)s}' % ns
OAI_DC = '{%(oai_dc)s}' % ns
MARCXML = '{%(marcxml)s}' % ns

#identifier patterns
naf_re = re.compile('n\d+')
fast_re = re.compile('fst\d{8}')
lcsh_re = re.compile('sh\d+')

#search base URLs
wikidata_sparql = "https://query.wikidata.org/sparql"
lcnaf_suggest = "http://id.loc.gov/authorities/names/suggest/?q="
lcsh_suggest = "http://id.loc.gov/authorities/subjects/suggest/?q="
lc_suggest = "http://id.loc.gov/authorities/suggest/?q="
lcnaf_didyoumean = "http://id.loc.gov/authorities/names/didyoumean/?label="
lcsh_didyoumean = "http://id.loc.gov/authorities/subjects/didyoumean/?label="

#URI base URLs
naf_base = "http://id.loc.gov/authorities/names/"
ulan_base = "http://vocab.getty.edu/ulan/"
viaf_base = "http://viaf.org/viaf/"
fast_base = "http://id.worldcat.org/fast/"
cul_vivo_base = "http://vivo.cornell.edu/individual/"
