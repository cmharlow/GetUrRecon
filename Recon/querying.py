from SPARQLWrapper import SPARQLWrapper, JSON
import constants
import urllib
import rdflib
import requests


def getLCprefLabel(lcuri):
    try:
        graph = rdflib.Graph().parse(lcuri + ".skos.nt", format='nt')
    except urllib.error.HTTPError:
        loc_preflabel = None
    loc_labeltriple = graph.preferredLabel(rdflib.URIRef(lcuri), lang='en')
    loc_preflabel = loc_labeltriple[0][1].toPython()
    return loc_preflabel


def getFASTprefLabel(fasturi):
    try:
        graph = rdflib.Graph().parse(fasturi + "/rdf", format='xml')
        fast_labeltriple = graph.preferredLabel(rdflib.URIRef(fasturi))
        fast_preflabel = fast_labeltriple[0][1].toPython()
        return fast_preflabel
    except urllib.error.HTTPError:
        fast_preflabel = None
        return(fast_preflabel)
        pass


def LCsuggest(query, role_code, role):
    out = {}
    label_int = query.replace(str(role_code), '').strip().replace(str(role), '').strip()
    label = label_int.strip('.').strip(',').encode('utf8')
    lc_url = (constants.lcnaf_suggest + urllib.parse.quote(label))
    lc_resp = requests.get(lc_url)
    lc_results = lc_resp.json()
    if len(lc_results[1]) > 0:
        lc_prefLabel = lc_results[1][0]
        lc_uri = lc_results[3][0]
        lcnaf = lc_uri.replace(constants.naf_base, '')
        #Ask WikiData if there is match for that NAF
        sparqlLCid(lcnaf)
    else:
        #do further matching
        lc_prefLabel = None
        lc_uri = None
        lcnaf = None
    out['lc_prefLabel'] = lc_prefLabel
    out['lc_uri'] = lc_uri
    out['lcnaf'] = lcnaf
    return(out)


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
    out = {}
    #If there is WikiData match:
    if len(res['results']['bindings']) > 0:
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
        wikidata_uri = wikidata_prefLabel = wikidata_score = ulan_uri = getty_score = viaf_uri = viaf_score = fast_uri = fast_score = None
    out['wikidata_uri'] = wikidata_uri
    out['wikidata_prefLabel'] = wikidata_prefLabel
    out['wikidata_score'] = wikidata_score
    out['ulan_uri'] = ulan_uri
    out['ulan_prefLabel'] = None
    out['getty_score'] = getty_score
    out['viaf_uri'] = viaf_uri
    out['viaf_score'] = viaf_score
    out['viaf_prefLabel'] = None
    out['fast_uri'] = fast_uri
    out['fast_score'] = fast_score
    out['fast_prefLabel'] = None
    return out


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
    if len(res['results']['bindings']) > 0:
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
