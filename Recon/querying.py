from SPARQLWrapper import SPARQLWrapper, JSON
import constants
import urllib
import rdflib
import requests
import unidecode
from fuzzywuzzy import fuzz


def getLCprefLabel(lcuri):
    if lcuri is not None:
        try:
            graph = rdflib.Graph().parse(lcuri + ".skos.nt", format='nt')
        except urllib.error.HTTPError:
            loc_preflabel = None
        loc_labeltriple = graph.preferredLabel(rdflib.URIRef(lcuri), lang='en')
        loc_preflabel = loc_labeltriple[0][1].toPython()
        return loc_preflabel
    else:
        return None


def getFASTprefLabel(fasturi):
    if fasturi is not None:
        try:
            print(fasturi)
            graph = rdflib.Graph().parse(fasturi)
            fast_labeltriple = graph.preferredLabel(rdflib.URIRef(fasturi))
            fast_preflabel = fast_labeltriple[0][1].toPython()
            return fast_preflabel
        except urllib.error.HTTPError:
            fast_preflabel = None
            return(fast_preflabel)
            pass
    else:
        return None


def getULANprefLabel(ulanuri):
    if ulanuri is not None:
        try:
            graph = rdflib.Graph().parse(ulanuri + ".nt", format='nt')
            ulan_labeltriple = graph.preferredLabel(rdflib.URIRef(ulanuri))
            ulan_preflabel = ulan_labeltriple[0][1].toPython()
            return ulan_preflabel
        except urllib.error.HTTPError:
            ulan_preflabel = None
            return(ulan_preflabel)
            pass
    else:
        return None


def LCsuggest(query, role_code, role):
    out = {}
    label_int = query.replace(str(role_code), '').strip().replace(str(role),
                                                                  '').strip()
    label = label_int.strip('.').strip(',')
    lc_url = (constants.lcnaf_suggest + urllib.parse.quote(label))
    lc_resp = requests.get(lc_url.encode('utf8'))
    lc_results = lc_resp.json()
    if len(lc_results[1]) > 0:
        lc_prefLabel = lc_results[1][0]
        lc_uri = lc_results[3][0]
        lc = lc_uri.replace(constants.naf_base, '')
    else:
        #do further matching
        label = unidecode.unidecode(label_int.strip('.').strip(','))
        lc_url = constants.lcnaf_suggest + urllib.parse.quote(label)
        lc_resp = requests.get(lc_url.encode('utf8'))
        lc_results = lc_resp.json()
        lc_prefLabel = None
        lc_uri = None
        lc = None
        if len(lc_results[1]) > 0:
            lc_prefLabel = lc_results[1][0]
            lc_uri = lc_results[3][0]
            lc = lc_uri.replace(constants.naf_base, '')
        else:
            lc_prefLabel = None
            lc_uri = None
            lc = None
    out['lc_prefLabel'] = lc_prefLabel
    out['lc_uri'] = lc_uri
    out['lc'] = lc
    return(out)


def sparqlWD(label, resp):
    print('HITTING LABEL: ' + label)
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?fast ?bdate ?ddate ?role WHERE {
            ?uri ?label """ + '"' + unidecode.unidecode(label) + '"' + """ .
            OPTIONAL { ?uri wdt:P245 ?ulan . }
            OPTIONAL { ?uri wdt:P214 ?viaf . }
            OPTIONAL { ?uri wdt:P2163 ?fast . }
            OPTIONAL { ?uri wdt:P569 ?bdate . }
            OPTIONAL { ?uri wdt:P570 ?ddate . }
            OPTIONAL { ?uri wdt:P106 ?roleuri . }
            OPTIONAL { ?roleuri rdfs:label ?role . }
            FILTER NOT EXISTS { ?uri a wikibase:BestRank . }
        } LIMIT 10
    """)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    print(res)
    out = {}
    #If there is WikiData match:
    if len(res['results']['bindings']) > 0:
        out['wikidata'] = []
        out['getty'] = []
        out['viaf'] = []
        out['lc'] = []
        out['fast'] = []
        for n in range(len(res['results']['bindings'])):
            wikidata_uri = (res['results']['bindings'][n]['uri']['value'])
            wikidata_prefLabel = label
            try:
                wikidata_role = res['results']['bindings'][n]['role']['value']
                wikidata_score = 10
            except:
                wikidata_role = None
                wikidata_score = 0
            try:
                wikidata_bdate = (res['results']['bindings'][n]['bdate']
                                  ['value'][:4])
            except:
                wikidata_bdate = None
            try:
                wikidata_ddate = (res['results']['bindings'][n]['ddate']
                                  ['value'][:4])
            except:
                wikidata_ddate = None

            if (resp['match_fields']['bdate'] == wikidata_bdate) or (resp['match_fields']['ddate'] == wikidata_ddate):
                wikidata_score = 80
            elif resp['match_fields']['role'] == wikidata_role:
                wikidata_score = 70
            elif resp['match_fields']['role'] and fuzz.ratio(resp['match_fields']['role'], wikidata_role) > 60:
                wikidata_score = 60
            else:
                wikidata_score = 50

            try:
                ulan_uri = (constants.ulan_base + res['results']['bindings'][n]
                            ['ulan']['value'])
                getty_score = wikidata_uri
            except:
                ulan_uri = None
                getty_score = 0
            try:
                viaf_uri = (constants.viaf_base + res['results']['bindings'][n]
                            ['viaf']['value'])
                viaf_score = wikidata_score
            except:
                viaf_uri = None
                viaf_score = 0
            try:
                lc_uri = (constants.lc_base + res['results']['bindings'][n]
                          ['lc']['value'])
                lc_score = wikidata_score
            except:
                lc_uri = None
                lc_score = 0
            try:
                fast_uri = (constants.fast_base + res['results']['bindings'][n]
                            ['fast']['value'])
                fast_score = wikidata_score
            except:
                fast_uri = None
                fast_score = 0
            wikidata0 = {}
            wikidata0['wikidata_uri'] = wikidata_uri
            wikidata0['wikidata_prefLabel'] = wikidata_prefLabel
            wikidata0['wikidata_score'] = wikidata_score
            out['wikidata'].append(wikidata0)
            getty0 = {}
            getty0['ulan_uri'] = ulan_uri
            getty0['ulan_prefLabel'] = getULANprefLabel(ulan_uri)
            getty0['getty_score'] = getty_score
            out['getty'].append(getty0)
            viaf0 = {}
            viaf0['viaf_uri'] = viaf_uri
            viaf0['viaf_score'] = viaf_score
            viaf0['viaf_prefLabel'] = None
            out['viaf'].append(viaf0)
            lc0 = {}
            lc0['lc_uri'] = lc_uri
            lc0['lc'] = lc_score
            lc0['lc_prefLabel'] = getLCprefLabel(lc_uri)
            out['lc'].append(lc0)
            fast0 = {}
            fast0['fast_uri'] = fast_uri
            fast0['fast_score'] = fast_score
            fast0['fast_prefLabel'] = getFASTprefLabel(fast_uri)
            out['fast'].append(fast0)
        return out
    else:
        out['wikidata'] = []
        out['getty'] = []
        out['viaf'] = []
        out['fast'] = []
        out['lc'] = []
        return out


def sparqlLCid(LCid):
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?fast ?prefLabel WHERE {
            ?uri wdt:P244 '""" + LCid + """' .
            OPTIONAL { ?uri wdt:P245 ?ulan . }
            OPTIONAL { ?uri wdt:P214 ?viaf . }
            OPTIONAL { ?uri wdt:P2163 ?fast . }
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
            getty_score = 0
        try:
            viaf_uri = (constants.viaf_base + res['results']['bindings'][0]
                        ['viaf']['value'])
            viaf_score = 100
        except:
            viaf_uri = None
            viaf_score = 0
        try:
            fast_uri = (constants.fast_base + res['results']['bindings'][0]
                        ['fast']['value'])
            fast_score = 100
        except:
            fast_uri = None
            fast_score = 0
    else:
        wikidata_uri = wikidata_prefLabel = ulan_uri = viaf_uri = fast_uri = None
        getty_score = viaf_score = fast_score = wikidata_score = 0
    out['wikidata'] = {}
    out['wikidata']['wikidata_uri'] = wikidata_uri
    out['wikidata']['wikidata_prefLabel'] = wikidata_prefLabel
    out['wikidata']['wikidata_score'] = wikidata_score
    out['getty'] = {}
    out['getty']['ulan_uri'] = ulan_uri
    out['getty']['ulan_prefLabel'] = getULANprefLabel(ulan_uri)
    out['getty']['getty_score'] = getty_score
    out['viaf'] = {}
    out['viaf']['viaf_uri'] = viaf_uri
    out['viaf']['viaf_score'] = viaf_score
    out['viaf']['viaf_prefLabel'] = None
    out['fast'] = {}
    out['fast']['fast_uri'] = fast_uri
    out['fast']['fast_score'] = fast_score
    out['fast']['fast_prefLabel'] = getFASTprefLabel(fast_uri)
    return out


def sparqlGNDid(GNDid):
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?fast ?prefLabel ?naf WHERE {
            ?uri wdt:p227 '""" + GNDid.replace('(DE-588)', '').replace('-', '') + """'
            OPTIONAL { ?uri wdt:P244 ?naf . }
            OPTIONAL { ?uri wdt:P245 ?ulan . }
            OPTIONAL { ?uri wdt:P214 ?viaf . }
            OPTIONAL { ?uri wdt:P2163 ?fast . }
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
            lc_uri = (constants.naf_base + res['results']['bindings'][0]
                      ['lc']['value'])
            lc_score = 100
        except:
            lc_uri = None
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
        wikidata_uri = wikidata_prefLabel = ulan_uri = viaf_uri = lc_uri = fast_uri = None
        getty_score = viaf_score = fast_score = wikidata_score = lc_score = 0
    out['wikidata'] = {}
    out['wikidata']['wikidata_uri'] = wikidata_uri
    out['wikidata']['wikidata_prefLabel'] = wikidata_prefLabel
    out['wikidata']['wikidata_score'] = wikidata_score
    out['getty'] = {}
    out['getty']['ulan_uri'] = ulan_uri
    out['getty']['ulan_prefLabel'] = getULANprefLabel(ulan_uri)
    out['getty']['getty_score'] = getty_score
    out['viaf'] = {}
    out['viaf']['viaf_uri'] = viaf_uri
    out['viaf']['viaf_score'] = viaf_score
    out['viaf']['viaf_prefLabel'] = None
    out['fast'] = {}
    out['fast']['fast_uri'] = fast_uri
    out['fast']['fast_score'] = fast_score
    out['fast']['fast_prefLabel'] = getFASTprefLabel(fast_uri)
    out['lc'] = {}
    out['lc']['lc_uri'] = lc_uri
    out['lc']['lc_score'] = lc_score
    out['lc']['lc_prefLabel'] = getLCprefLabel(lc_uri)
    return out


def sparqlFASTid(FASTid):
    FASTid = FASTid.lstrip('(OCoLC)fst').lstrip('0')
    print('SPARQL Query id: ' + FASTid)
    sparql = SPARQLWrapper(constants.wikidata_sparql)
    sparql.setQuery("""
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?uri ?ulan ?viaf ?naf ?prefLabel WHERE {
            ?uri wdt:P2163 '""" + FASTid + """' .
            OPTIONAL { ?uri wdt:P245 ?ulan . }
            OPTIONAL { ?uri wdt:P214 ?viaf . }
            OPTIONAL { ?uri wdt:P244 ?naf . }
            SERVICE wikibase:label {
            bd:serviceParam wikibase:language "en" .
            ?uri rdfs:label ?prefLabel .
            }
        }
    """)
    sparql.setReturnFormat(JSON)
    res = sparql.query().convert()
    print(res)
    out = {}
    print(res)
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
            getty_score = None
        try:
            viaf_uri = (constants.viaf_base +
                        res['results']['bindings'][0]['viaf']['value'])
            viaf_score = 100
        except:
            viaf_uri = None
            viaf_score = 0
        try:
            lc_uri = (constants.naf_base +
                      res['results']['bindings'][0]['naf']['value'])
            lc_score = 100
        except:
            lc_uri = None
            lc_score = 0
    else:
        wikidata_uri = wikidata_prefLabel = ulan_uri = viaf_uri = lc_uri = None
        wikidata_score = getty_score = viaf_score = lc_score = 0
    out['wikidata'] = {}
    out['wikidata']['wikidata_uri'] = wikidata_uri
    out['wikidata']['wikidata_prefLabel'] = wikidata_prefLabel
    out['wikidata']['wikidata_score'] = wikidata_score
    out['getty'] = {}
    out['getty']['ulan_uri'] = ulan_uri
    out['getty']['ulan_prefLabel'] = None
    out['getty']['getty_score'] = getty_score
    out['viaf'] = {}
    out['viaf']['viaf_uri'] = viaf_uri
    out['viaf']['viaf_score'] = viaf_score
    out['viaf']['viaf_prefLabel'] = None
    out['lc'] = {}
    out['lc']['lc_uri'] = lc_uri
    out['lc']['lc_score'] = lc_score
    out['lc']['lc_prefLabel'] = None
    return out
