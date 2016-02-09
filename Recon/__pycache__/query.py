from SPARQLWrapper import SPARQLWrapper, JSON
import constants


def sparqlLCid(LCid):
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?fast ?prefLabel WHERE {
            ?uri wdt:P244 '""" + LCid + """' .
            ?uri wdt:P245 ?ulan .
            ?uri wdt:P214 ?viaf .
            ?uri wdt:P2163 ?fast .
            SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
            ?uri rdfs:label ?prefLabel .
            }
        }
    """)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    #If there is WikiData match:
    if res['results']['bindings'][0]['uri']['value']:
        wikidata_uri = (res['results']['bindings'][0]['uri']['value'])
        wikidata_prefLabel = (res['results']['bindings'][0]['prefLabel']
                              ['value'])
        wikidata_score = 100
        try:
            ulan_uri = (constants.ulan_base + res['results']['bindings'][0]
                        ['ulan']['value'])
            getty_score = 100
        except:
            ulan_uri = None
        try:
            viaf_uri = (constants.viaf_base + res['results']['bindings'][0]
                        ['viaf']['value'])
            viaf_score = 100
        except:
            viaf_uri = None
        try:
            fast_uri = (constants.fast_base + res['results']['bindings'][0]
                        ['fast']['value'])
            fast_score = 100
        except:
            fast_uri = None
    else:
        wikidata_uri = wikidata_prefLabel = ulan_uri = viaf_uri = fast_uri = None
    return(wikidata_uri, wikidata_prefLabel, wikidata_score, ulan_uri,
           getty_score, viaf_uri, viaf_score, fast_uri, fast_score)


def sparqlFASTid(FASTid):
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?naf ?prefLabel WHERE {
            ?uri wdt:P2163 '""" + FASTid + """' .
            ?uri wdt:P245 ?ulan .
            ?uri wdt:P214 ?viaf .
            ?uri wdt:P244 ?naf .
            SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
            ?uri rdfs:label ?prefLabel .
            }
        }
    """)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    #If there is WikiData match:
    if res['results']['bindings'][0]['uri']['value']:
        wikidata_uri = (res['results']['bindings'][0]['uri']['value'])
        wikidata_prefLabel = (res['results']['bindings'][0]['prefLabel']
                              ['value'])
        wikidata_score = 100
        try:
            ulan_uri = (constants.ulan_base +
                        res['results']['bindings'][0]['ulan']['value'])
            getty_score = 100
        except:
            ulan_uri = None
        try:
            viaf_uri = (constants.viaf_base +
                        res['results']['bindings'][0]['viaf']['value'])
            viaf_score = 100
        except:
            viaf_uri = None
        try:
            lcnaf_uri = (constants.naf_base +
                         res['results']['bindings'][0]['naf']['value'])
            lc_score = 100
        except:
            lcnaf_uri = None
    else:
        wikidata_uri = wikidata_prefLabel = ulan_uri = viaf_uri = lcnaf_uri = None
    return(wikidata_uri, wikidata_prefLabel, wikidata_score, ulan_uri,
           getty_score, viaf_uri, viaf_score, lcnaf_uri, lc_score)
