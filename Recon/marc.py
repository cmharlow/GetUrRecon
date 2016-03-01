import pymarc
import logging
import re
import sys
import constants
import querying

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def handle0(subfield0):
    #NAF-flavored identifiers parsed, searched
    if re.match(constants.naf_re, subfield0):
        lc = subfield0
        lc_uri = constants.naf_base + lc
        lc_prefLabel = querying.getLCprefLabel(lc_uri)
        lc_score = 100
        #Ask WikiData if there is match for that NAF
        LCqueryout = querying.sparqlLCid(lc)
        wikidata0 = LCqueryout['wikidata']
        lc0 = ({'lcnaf_uri': lc_uri, 'lc_prefLabel': lc_prefLabel,
               'lc_score': lc_score})
        getty0 = LCqueryout['getty']
        fast0 = LCqueryout['fast']
        viaf0 = LCqueryout['viaf']
    #FAST-flavored identifiers parsed, searched
    elif re.match(constants.fast_re, subfield0):
        fast = subfield0
        fast_uri = constants.fast_base + fast.replace('fst', '')
        fast_prefLabel = querying.getFASTprefLabel(fast_uri)
        fast_score = 100
        #Ask WikiData if there is match for that FAST
        FASTqueryout = querying.sparqlFASTid(fast)
        wikidata0 = FASTqueryout['wikidata']
        lc0 = FASTqueryout['lc']
        getty0 = FASTqueryout['getty']
        fast0 = ({'fast_uri': fast_uri,
                  'fast_prefLabel': fast_prefLabel,
                  'fast_score': fast_score})
        viaf0 = FASTqueryout['viaf']
    elif re.match(constants.gnd_re, subfield0):
        gnd = subfield0
        #Ask WikiData if there is match for that FAST
        GNDqueryout = querying.sparqlGNDid(gnd)
        wikidata0 = GNDqueryout['wikidata']
        lc0 = GNDqueryout['lc']
        getty0 = GNDqueryout['getty']
        fast0 = GNDqueryout['fast']
        viaf0 = GNDqueryout['viaf']
    else:
        lc0 = {}
        getty0 = {}
        fast0 = {}
        viaf0 = {}
        wikidata0 = {}
    out = {}
    out['lc'] = [lc0]
    out['wikidata'] = [wikidata0]
    out['viaf'] = [viaf0]
    out['getty'] = [getty0]
    out['fast'] = [fast0]
    return(out)
    logging.debug(out)


def processMarc(datafile, args, fields):
    response = {}
    fields = fields
    reader = pymarc.MARCReader(open(datafile, 'rb'))
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
                topics.append(topic.format_field().replace(' -- ', '--'))
        except TypeError:
            topics = None
        for field in fields:
            for name in record.get_fields(field):
                resp = dict()
                #If has something to not make a personal name, skip
                if not name['t'] and not name['v'] and not name['x']:
                    query = name.format_field()
                    query_norm = name['a'].strip('').strip(',')
                    if "," in query_norm and name.indicator1 == '1':
                        lastname = query_norm.split(', ', 1)[0]
                        firstname = query_norm.split(', ', 1)[1]
                        query_inv = firstname.strip(',') + " " + lastname
                    else:
                        query_inv = None
                    try:
                        date = name['d']
                    except TypeError:
                        date = None
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
                    resp['query'] = query
                    resp['recordID'] = recordID
                    resp['query_norm'] = query_norm
                    resp['query_inv'] = query_inv
                    resp['match_fields'] = {}
                    resp['match_fields']['title'] = title
                    resp['match_fields']['uniformTitle'] = uniformTitle
                    resp['match_fields']['stmtOfResp'] = stmtOfResp
                    resp['match_fields']['topic'] = topics
                    resp['match_fields']['bdate'] = bdate
                    resp['match_fields']['ddate'] = ddate
                    resp['match_fields']['date'] = date
                    resp['match_fields']['role'] = role
                    resp['match_fields']['role_code'] = role_code
                    resp['match_fields']['affiliation'] = affiliation
                    resp['match_fields']['field_id'] = field_id
                    resp['request_info'] = {}
                    resp['request_info']['queryType'] = args.queryType
                    resp['request_info']['match'] = args.match
                    resp['request_info']['givenFormat'] = args.format
                    resp['matches'] = {}
                    resp['matches']['lc'] = []
                    resp['matches']['viaf'] = []
                    resp['matches']['getty'] = []
                    resp['matches']['vivo'] = []
                    resp['matches']['fast'] = []
                    resp['matches']['wikidata'] = []
                    #if the heading has an ID already, match on that first
                    recon_resp = False
                    if field_id and recon_resp is False:
                        id_resp = handle0(field_id)
                        print(id_resp)
                        resp['matches']['lc'].append(id_resp['lc'])
                        resp['matches']['viaf'].append(id_resp['viaf'])
                        resp['matches']['fast'].append(id_resp['fast'])
                        resp['matches']['getty'].append(id_resp['getty'])
                        resp['matches']['wikidata'].append(id_resp['wikidata'])
                        if id_resp['wikidata'] is not None:
                            recon_resp = True

                    #If name does not have $0 but has $d, $q, $b, $c
                    #Then run against NAF first for id checking
                    if ((name['d'] or name['q'] or name['b'] or name['c']) and recon_resp is False):
                        #Look for NAF Identifier first
                        lc_results = querying.LCsuggest(query, role_code, role)
                        if lc_results['lc_uri']:
                            #Consider a match?
                            lc_uri = lc_results['lc_uri']
                            lc_prefLabel = lc_results['lc_prefLabel']
                            lc = lc_results['lc']
                            lc_score = 90 #make better later according to
                            #which subfield did matching
                            #Ask WikiData if there is match for that NAF
                            LCqueryout = querying.sparqlLCid(lc)
                            lc0 = ({'lcnaf_uri': lc_uri, 'lc_prefLabel':
                                   lc_prefLabel, 'lc_score': lc_score})
                            resp['matches']['lc'].append(lc0)
                            resp['matches']['wikidata'].append(LCqueryout['wikidata'])
                            resp['matches']['getty'].append(LCqueryout['getty'])
                            resp['matches']['fast'].append(LCqueryout['fast'])
                            resp['matches']['viaf'].append(LCqueryout['viaf'])
                            if resp['matches']['wikidata'] is not None:
                                recon_resp = True

                    if recon_resp is False:
                        #wikidata sparql query with query_inv
                        if query_inv:
                            WDqueryout = querying.sparqlWD(query_inv, resp)
                            resp['matches']['wikidata'] = WDqueryout['wikidata']
                            resp['matches']['lc'] = WDqueryout['lc']
                            resp['matches']['viaf'] = WDqueryout['viaf']
                            resp['matches']['fast'] = WDqueryout['fast']
                            resp['matches']['getty'] = WDqueryout['getty']
                        else:
                            WDqueryout = querying.sparqlWD(query_norm, resp)
                            resp['matches']['wikidata'] = WDqueryout['wikidata']
                            resp['matches']['lc'] = WDqueryout['lc']
                            resp['matches']['viaf'] = WDqueryout['viaf']
                            resp['matches']['fast'] = WDqueryout['fast']
                            resp['matches']['getty'] = WDqueryout['getty']
                response[recordID + '_' + query_norm] = resp
    return(response)
                #If name does not have $0 but has $d, $q, $b, $c
