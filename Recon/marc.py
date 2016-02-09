from argparse import ArgumentParser
import pymarc
import logging
import re
import sys
import constants
import normalize
from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import urllib

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def main():
    parser = ArgumentParser(usage='%(prog)s [options] data_filename')
    parser.add_argument("-f", "--format", dest="format",
                        help="Enter 1: csv, json, jsonld, mrc, nt, ttl, xml")
    parser.add_argument("-m", "--match", dest="match",
                        help="match confidence", default=80)
    parser.add_argument("-r", "--record", dest="record",
                        help="record delimiter")
    parser.add_argument("-s", "--sparql", dest="sparql",
                        help="sparql endpoint for graph generation")
    parser.add_argument("-t", "--queryType", dest="queryType",
                        help="Enter 1: PersonalName, CorporateName, Name, \
                        Topic, GeographicName, GenreForm, Title")
    parser.add_argument("-u", "--uri", dest="uri", help="resource URI")
    parser.add_argument("datafile", help="metadata file to be matched")

    args = parser.parse_args()

    #Recon Types - Personal Name
    if args.datafile and args.queryType == 'PersonalName':
        results = {}
        #Formats - MARC
        if args.format == 'mrc':
            data = open(args.datafile, 'rb')
            reader = pymarc.MARCReader(data)
            #Records - MARC
            for record in reader:
                #Generate Recon Resp that is static for all hdgs in this record
                #ID
                recordID = record['001'].data
                #Title
                try:
                    title = record['245']['a'].replace(' /', '')
                except TypeError:
                    title = None
                #Uniform Title
                try:
                    uniformTitle = record['240']['a']
                except TypeError:
                    uniformTitle = None
                #Statement of Responsibility - 2nd Affiliation?
                try:
                    stmtOfResp = record['245']['c']
                except TypeError:
                    stmtOfResp = None
                #Topics
                try:
                    topics = []
                    for topic in record.get_fields('650'):
                        topics.append(topic.format_field().replace(' -- ',
                                      '--'))
                except (TypeError):
                    topics = None
                #Iterate through headings now - first 100
                for name in record.get_fields('100'):
                    #If has something to not make a personal name, skip
                    if name['t'] or name['v'] or name['x']:
                        logging.debug('No matching for ' + name.format_field()
                                      .replace(' -- ', '--'))
                    #Otherwise, perform matching
                    else:
                        id_label = recordID + (name.format_field())
                        query = name.format_field()
                        query_norm = name['a']
                        if ", " in query_norm and name.indicator1 == 1:
                            lastname = query.split(', ', 1)[0]
                            firstname = query.split(', ', 1)[1]
                            query_inv = firstname + " " + lastname
                        else:
                            query_inv = None
                        try:
                            bdate = name['d'][:4]
                        except TypeError:
                            bdate = None
                        try:
                            ddate = name['d'].split("-", 1)[1]
                        except (TypeError, AttributeError):
                            ddate = None
                        try:
                            role = name['e']
                        except TypeError:
                            role = None
                        try:
                            role_code = name['4']
                        except TypeError:
                            role_code = None
                        try:
                            affiliation = name['u']
                        except TypeError:
                            affiliation = None
                        #start Recon Resp JSON construction
                        results[id_label] = {}
                        results[id_label]['recordID'] = recordID
                        results[id_label]['title'] = title
                        results[id_label]['uniformTitle'] = uniformTitle
                        results[id_label]['stmtOfResp'] = stmtOfResp
                        results[id_label]['topics'] = topics
                        results[id_label]['query'] = query
                        results[id_label]['query_norm'] = query_norm
                        results[id_label]['bdate'] = bdate
                        results[id_label]['ddate'] = ddate
                        results[id_label]['role'] = role
                        results[id_label]['role_code'] = role_code
                        results[id_label]['affiliation'] = affiliation
                        results[id_label]['matches'] = {}
                        lc_score = getty_score = wikidata_score = viaf_score = fast_score = 0
                        #if the heading has an ID already, match on that first
                        if name['0']:
                            field_id = name['0']
                            results[id_label]['field_id'] = field_id
                            #NAF-flavored identifiers parsed, searched
                            if re.match(constants.naf_re, field_id):
                                lcnaf = name['0'].value
                                lcnaf_uri = constants.naf_base + lcnaf
                                lc_score = 100
                                #Ask WikiData if there is match for that NAF
                                sparql = SPARQLWrapper(constants.wikidata_sparql)
                                sparql.setQuery("""
                                    PREFIX wikibase: <http://wikiba.se/ontology#>
                                    PREFIX wd: <http://www.wikidata.org/entity/>
                                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                                    SELECT ?uri ?ulan ?viaf ?fast ?prefLabel WHERE {
                                        ?uri wdt:P244 '""" + lcnaf + """' .
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
                                    wikidata_uri = (res['results']['bindings']
                                                    [0]['uri']['value'])
                                    wikidata_prefLabel = (res['results']
                                                          ['bindings'][0]
                                                          ['prefLabel']['value'])
                                    wikidata_score = 100
                                    try:
                                        ulan_uri = (constants.ulan_base +
                                                    (res['results']['bindings']
                                                     [0]['ulan']['value']))
                                        getty_score = 100
                                    except:
                                        ulan_uri = None
                                    try:
                                        viaf_uri = (constants.viaf_base +
                                                    (res['results']['bindings']
                                                     [0]['viaf']['value']))
                                        viaf_score = 100
                                    except:
                                        viaf_uri = None
                                    try:
                                        fast_uri = (constants.fast_base +
                                                    (res['results']['bindings']
                                                     [0]['fast']['value']))
                                        fast_score = 100
                                    except:
                                        fast_uri = None
                                #If no Wikidata Match for ID, leave as none for
                                #now. Will eventually have this do reg search
                                else:
                                    wikidata_uri = None
                                    wikidata_prefLabel = None
                                    ulan_uri = None
                                    viaf_uri = None
                                    fast_uri = None
                            #FAST-flavored identifiers parsed, searched
                            elif re.match(constants.fast_re, field_id):
                                fast = name['0'].value
                                fast_uri = constants.fast_base + fast
                                fast_score = 100
                                #Ask WikiData if there is match for that FAST
                                sparql = SPARQLWrapper(constants.wikidata_sparql)
                                sparql.setQuery("""
                                    PREFIX wikibase: <http://wikiba.se/ontology#>
                                    PREFIX wd: <http://www.wikidata.org/entity/>
                                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                                    SELECT ?uri ?ulan ?viaf ?naf ?prefLabel WHERE {
                                        ?uri wdt:P2163 '""" + fast + """' .
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
                                    wikidata_uri = (res['results']['bindings']
                                                    [0]['uri']['value'])
                                    wikidata_prefLabel = (res['results']
                                                          ['bindings'][0]
                                                          ['prefLabel']['value'])
                                    wikidata_score = 100
                                    try:
                                        ulan_uri = (constants.ulan_base +
                                                    (res['results']['bindings']
                                                     [0]['ulan']['value']))
                                        getty_score = 100
                                    except:
                                        ulan_uri = None
                                    try:
                                        viaf_uri = (constants.viaf_base +
                                                    (res['results']['bindings']
                                                     [0]['viaf']['value']))
                                        viaf_score = 100
                                    except:
                                        viaf_uri = None
                                    try:
                                        lcnaf_uri = (constants.naf_base +
                                                    (res['results']['bindings']
                                                     [0]['naf']['value']))
                                        lc_score = 100
                                    except:
                                        lcnaf_uri = None
                                #If no Wikidata Match for ID, leave as none for
                                #now. Will eventually have this do reg search
                                else:
                                    wikidata_uri = None
                                    wikidata_prefLabel = None
                                    ulan_uri = None
                                    viaf_uri = None
                                    lcnaf_uri = None
                            #Put results into Recon Resp JSON for $0 entries
                            wikidata0 = [wikidata_uri, wikidata_prefLabel, wikidata_score]
                            results[id_label]['matches']['wikidata'] = {wikidata0}
                            lc0 = [lcnaf_uri, lc_score]
                            results[id_label]['matches']['lc'] = {lc0}
                            getty0 = [ulan_uri, getty_score]
                            results[id_label]['matches']['getty'] = {getty0}
                            viaf0 = [viaf_uri, viaf_score]
                            results[id_label]['matches']['viaf'] = {viaf0}
                            fast0 = [fast_uri, fast_score]
                            results[id_label]['matches']['fast'] = {fast0}
                            logging.debug(results)
                        #If name does not have $0 but has $d, $q, $b, $c
                        #Then run against NAF first for id checking
                        elif name['d'] or name['q'] or name['b'] or name['c']:
                            results[id_label]['field_id'] = None
                            #Look for NAF Identifier first
                            out = []
                            query = normalize.name_alone(name)
                            url = (constants.lcnaf_suggest +
                                  urllib.parse.quote(query.encode('utf8')))
                            resp = requests.get(url)
                            results = resp.json()
                            #Ask WikiData if there is match for that NAF
                            sparql = SPARQLWrapper(constants.wikidata_sparql)
                            sparql.setQuery("""
                                PREFIX wikibase: <http://wikiba.se/ontology#>
                                PREFIX wd: <http://www.wikidata.org/entity/>
                                PREFIX wdt: <http://www.wikidata.org/prop/direct/>
                                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                                SELECT ?uri ?ulan ?viaf ?fast ?prefLabel WHERE {
                                    ?uri wdt:P244 '""" + lcnaf + """' .
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
                                wikidata_uri = (res['results']['bindings']
                                                [0]['uri']['value'])
                                wikidata_prefLabel = (res['results']
                                                      ['bindings'][0]
                                                      ['prefLabel']['value'])
                                wikidata_score = 100
                                try:
                                    ulan_uri = (constants.ulan_base +
                                                (res['results']['bindings']
                                                 [0]['ulan']['value']))
                                    getty_score = 100
                                except:
                                    ulan_uri = None
                                try:
                                    viaf_uri = (constants.viaf_base +
                                                (res['results']['bindings']
                                                 [0]['viaf']['value']))
                                    viaf_score = 100
                                except:
                                    viaf_uri = None
                                try:
                                    fast_uri = (constants.fast_base +
                                                (res['results']['bindings']
                                                 [0]['fast']['value']))
                                    fast_score = 100
                                except:
                                    fast_uri = None
                            #If no Wikidata Match for ID, leave as none for
                            #now. Will eventually have this do reg search
                            else:
                                wikidata_uri = None
                                wikidata_prefLabel = None
                                ulan_uri = None
                                viaf_uri = None
                                fast_uri = None
                            else:
                                wikidata_uri = None
                                wikidata_prefLabel = None
                                ulan_uri = None
                                viaf_uri = None
                                lcnaf_uri = None
                            #Put results into Recon Resp JSON for $0 entries
                            wikidata0 = [wikidata_uri, wikidata_prefLabel, wikidata_score]
                            results[id_label]['matches']['wikidata'] = {wikidata0}
                            lc0 = [lcnaf_uri, lc_score]
                            results[id_label]['matches']['lc'] = {lc0}
                            getty0 = [ulan_uri, getty_score]
                            results[id_label]['matches']['getty'] = {getty0}
                            viaf0 = [viaf_uri, viaf_score]
                            results[id_label]['matches']['viaf'] = {viaf0}
                            fast0 = [fast_uri, fast_score]
                            results[id_label]['matches']['fast'] = {fast0}
                            logging.debug(results)
                        #If name does not have $0 but has $d, $q, $b, $c
                        #Then run against NAF first for id checking







if __name__ == "__main__":
        main()
