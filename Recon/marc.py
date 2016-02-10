from argparse import ArgumentParser
import pymarc
import logging
import re
import sys
import constants
import querying

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def handle0(subfield0, matches):
    #NAF-flavored identifiers parsed, searched
    if re.match(constants.naf_re, subfield0):
        lcnaf = subfield0
        lcnaf_uri = constants.naf_base + lcnaf
        lc_prefLabel = querying.getLCprefLabel(lcnaf_uri)
        lc_score = 100
        #Ask WikiData if there is match for that NAF
        LCqueryout = querying.sparqlLCid(lcnaf)
        wikidata0 = ({'wikidata_uri': LCqueryout['wikidata_uri'],
                     'wikidata_prefLabel': LCqueryout['wikidata_prefLabel'],
                     'wikidata_score': LCqueryout['wikidata_score']})
        lc0 = ({'lcnaf_uri': lcnaf_uri, 'lc_prefLabel': lc_prefLabel,
               'lc_score': lc_score})
        getty0 = ({'ulan_uri': LCqueryout['ulan_uri'],
                  'ulan_prefLabel': LCqueryout['ulan_prefLabel'],
                  'getty_score': LCqueryout['getty_score']})
        fast0 = ({'fast_uri': LCqueryout['fast_uri'],
                  'fast_prefLabel': LCqueryout['fast_prefLabel'],
                  'fast_score': LCqueryout['fast_score']})
        viaf0 = ({'viaf_uri': LCqueryout['viaf_uri'],
                  'viaf_prefLabel': LCqueryout['viaf_prefLabel'],
                  'viaf_score': LCqueryout['viaf_score']})
    #FAST-flavored identifiers parsed, searched
    elif re.match(constants.fast_re, subfield0):
        fast = subfield0
        fast_uri = constants.fast_base + fast.replace('fst', '')
        fast_prefLabel = querying.getFASTprefLabel(fast_uri)
        fast_score = 100
        #Ask WikiData if there is match for that FAST
        FASTqueryout = querying.sparqlFASTid(fast)
        wikidata0 = ({'wikidata_uri': FASTqueryout['wikidata_uri'],
                     'wikidata_prefLabel': FASTqueryout['wikidata_prefLabel'],
                     'wikidata_score': FASTqueryout['wikidata_score']})
        lc0 = ({'lcnaf_uri': lcnaf_uri, 'lc_prefLabel': lc_prefLabel,
               'lc_score': lc_score})
        getty0 = ({'ulan_uri': FASTqueryout['ulan_uri'],
                  'ulan_prefLabel': FASTqueryout['ulan_prefLabel'],
                  'getty_score': FASTqueryout['getty_score']})
        fast0 = ({'fast_uri': fast_uri,
                  'fast_prefLabel': fast_prefLabel,
                  'fast_score': fast_score})
        viaf0 = ({'viaf_uri': FASTqueryout['viaf_uri'],
                  'viaf_prefLabel': FASTqueryout['viaf_prefLabel'],
                  'viaf_score': FASTqueryout['viaf_score']})
    matches['lc'] = [lc0]
    matches['wikidata'] = [wikidata0]
    matches['viaf'] = [viaf0]
    matches['getty'] = [getty0]
    matches['fast'] = [fast0]
    return(matches)
    logging.debug(matches)


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
                recordID = record['001'].data
                try:
                    title = record['245']['a'].replace(' /', '')
                except TypeError:
                    title = None
                try:
                    uniformTitle = record['240']['a']
                except TypeError:
                    uniformTitle = None
                try:
                    stmtOfResp = record['245']['c']
                except TypeError:
                    stmtOfResp = None
                try:
                    topics = []
                    for topic in record.get_fields('650'):
                        topics.append(topic.format_field().replace(' -- ',
                                      '--'))
                except TypeError:
                    topics = None
                for name in record.get_fields('100'):
                    #If has something to not make a personal name, skip
                    if not name['t'] or not name['v'] or not name['x']:
                        query = name.format_field()
                        query_norm = name['a']
                        if "," in query_norm and name.indicator1 == '1':
                            lastname = query_norm.split(', ', 1)[0]
                            firstname = query_norm.split(', ', 1)[1]
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
                        try:
                            field_id = name['0']
                        except TypeError:
                            field_id = None
                        #start Recon Resp JSON construction
                        matches = {}
                        matches['query'] = query
                        matches['recordID'] = recordID
                        lc_score = getty_score = wikidata_score = viaf_score = fast_score = 0
                        #if the heading has an ID already, match on that first
                        if field_id:
                            results = handle0(field_id, results)
                        #If name does not have $0 but has $d, $q, $b, $c
                        #Then run against NAF first for id checking
                        elif name['d'] or name['q'] or name['b'] or name['c']:
                            #Look for NAF Identifier first
                            lc_results = querying.LCsuggest(query, role_code,
                                                            role)
                            if lc_results['lc_uri']:
                                #Consider a match?
                                lc_uri = lc_results['lc_uri']
                                lc_prefLabel = lc_results['lc_prefLabel']
                                lcnaf = lc_results['lcnaf']
                                lc_score = 80 #make better later according to
                                #which subfield did matching
                                #Ask WikiData if there is match for that NAF
                                LCqueryout = querying.sparqlLCid(lcnaf)
                                wikidata0 = ({'wikidata_uri': LCqueryout['wikidata_uri'],
                                             'wikidata_prefLabel': LCqueryout['wikidata_prefLabel'],
                                             'wikidata_score': LCqueryout['wikidata_score']})
                                lc0 = ({'lcnaf_uri': lc_uri, 'lc_prefLabel': lc_prefLabel,
                                       'lc_score': lc_score})
                                getty0 = ({'ulan_uri': LCqueryout['ulan_uri'],
                                          'ulan_prefLabel': LCqueryout['ulan_prefLabel'],
                                          'getty_score': LCqueryout['getty_score']})
                                fast0 = ({'fast_uri': LCqueryout['fast_uri'],
                                          'fast_prefLabel': LCqueryout['fast_prefLabel'],
                                          'fast_score': LCqueryout['fast_score']})
                                viaf0 = ({'viaf_uri': LCqueryout['viaf_uri'],
                                          'viaf_prefLabel': LCqueryout['viaf_prefLabel'],
                                          'viaf_score': LCqueryout['viaf_score']})
                                matches['lc'] = [lc0]
                                matches['wikidata'] = [wikidata0]
                                matches['viaf'] = [viaf0]
                                matches['getty'] = [getty0]
                                matches['fast'] = [fast0]
                                matches['INVERSION'] = query_inv
                                results['matches'] = matches
                                logging.debug(results)
                            else:
                                pass
                        #If name does not have $0 but has $d, $q, $b, $c







if __name__ == "__main__":
        main()
