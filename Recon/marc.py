from argparse import ArgumentParser
import pymarc
import logging
import re
import sys
import constants
import querying
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
                                querying.sparqlLCid(lcnaf)
                            #FAST-flavored identifiers parsed, searched
                            elif re.match(constants.fast_re, field_id):
                                fast = name['0'].value
                                fast_uri = constants.fast_base + fast
                                fast_score = 100
                                #Ask WikiData if there is match for that FAST
                                querying.sparqlFASTid(fast)
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
                            label_4 = query.replace(str(name['4']), '').strip()
                            label_e = label_4.replace(str(name['e']), '').strip()
                            label_fin = label_e.strip('.').strip(',')
                            lc_url = (constants.lcnaf_suggest +
                                      urllib.parse.quote(label_fin
                                                         .encode('utf8')))
                            print(lc_url)
                            lc_resp = requests.get(lc_url)
                            lc_results = lc_resp.json()
                            if lc_results[1][0]:
                                lc_prefLabel = lc_results[1][0]
                                lc_uri = lc_results[3][0]
                                lcnaf = lc_uri.replace(constants.naf_base, '')
                                #Ask WikiData if there is match for that NAF
                                querying.sparqlLCid(lcnaf)
                            else:
                                #do further matching
                                pass
                            wikidata0 = [wikidata_uri, wikidata_prefLabel, wikidata_score]
                            results[id_label]['matches']['wikidata'] = {wikidata0}
                            lc0 = [lcnaf_uri, lc_score, lc_prefLabel]
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
