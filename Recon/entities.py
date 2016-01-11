import requests
import urllib
from lxml import etree
import rdflib
from SPARQLWrapper import SPARQLWrapper, JSON
from fuzzywuzzy import fuzz
import csv
import os
import re
from argparse import ArgumentParser

ns = {'mods': 'http://www.loc.gov/mods/v3',
      'dc': 'http://purl.org/dc/elements/1.1/',
      'oai': 'http://www.openarchives.org/OAI/2.0/',
      'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
      'marcxml': 'http://www.loc.gov/MARC21/slim'}
OAI = '{%(oai)s}' % ns
DC = '{%(dc)s}' % ns
OAI_DC = '{%(oai_dc)s}' % ns
MARCXML = '{%(marcxml)s}' % ns

wskey = os.environ['WSKEY']
search_url = ("http://experiment.worldcat.org/entity/lookup/?wskey="
              + wskey + "&q=")
sameas_url = ("http://experiment.worldcat.org/entity/lookup/.jsonld?wskey="
              + wskey + "&id=")
json_header = {'Accept': 'application/ld+json'}


class ReconException(Exception):
    """Base exception class for this review"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value)


class LoCRespMARCXML:
    """Base class for MARC21/XML Record from id.loc.gov."""
    def __init__(self, uri):
        self.uri = uri
        self.marcxml = etree.XML(requests.get(self.uri + ".marcxml.xml").text)

    def get_loc_aff(self):
        affxp = '//marcxml:datafield[@tag="373"]/marcxml:subfield[@code="a"]'
        loc_resp_373a = self.marcxml.xpath(affxp, namespaces=ns)
        out = []
        if loc_resp_373a is not None:
            for n in range(len(loc_resp_373a)):
                if loc_resp_373a[n].text:
                        out.append(loc_resp_373a[n].text.strip())
            return out
        else:
            return None

    def get_loc_bdate(self):
        rdaxp = '//marcxml:datafield[@tag="046"]/marcxml:subfield[@code="f"]'
        otherxp = '//marcxml:datafield[@tag="100"]/marcxml:subfield[@code="d"]'
        loc_resp_046f = self.marcxml.xpath(rdaxp, namespaces=ns)
        if len(loc_resp_046f) > 0:
            return loc_resp_046f[0].text[:4]
        else:
            loc_resp_100d = self.marcxml.xpath(otherxp, namespaces=ns)
            if len(loc_resp_100d) > 0:
                return loc_resp_100d[0].text[:4]
            else:
                return None

    def get_loc_ddate(self):
        rdaxp = '//marcxml:datafield[@tag="046"]/marcxml:subfield[@code="g"]'
        otherxp = '//marcxml:datafield[@tag="100"]/marcxml:subfield[@code="d"]'
        loc_046g = self.marcxml.xpath(rdaxp, namespaces=ns)
        if len(loc_046g) > 0:
            return loc_046g[0].text[:4]
        else:
            loc_100d = self.marcxml.xpath(otherxp, namespaces=ns)
            if len(loc_100d) > 0 and re.match('^\d{4}-\d{4}$',
                                              loc_100d[0].text):
                return loc_100d[0].text[-4:]
            else:
                return None


class LoCRespNT:
    def __init__(self, uri):
        self.uri = uri
        try:
            self.graph = rdflib.Graph().parse(uri + ".skos.nt", format='nt')
        except urllib.error.HTTPError:
            self.graph = None

    def get_loc_preflabel(self):
        if self.graph is not None:
            loc_labeltriple = self.graph.preferredLabel(rdflib.URIRef(self.uri)
                                                        , lang='en')
            loc_preflabel = loc_labeltriple[0][1].toPython()
            return loc_preflabel


class VIAFrespMARCXML:
    def __init__(self, uri):
        self.uri = uri
        try:
            self.viaf_mx = etree.XML(requests.get(uri + "/marc21.xml").text)
        except etree.XMLSyntaxError:
            self.viaf_mx = etree.XML('<mx:record xmlns:v="http://viaf.org/viaf/terms#" xmlns:mx="http://www.loc.gov/MARC21/slim" xmlns:srw="http://www.loc.gov/zing/srw/"></mx:record>')

    def get_viaf_title(self):
        titlexp = '//marcxml:datafield[@tag="910"]/marcxml:subfield[@code="a"]'
        viaf_resp_910a = self.viaf_mx.xpath(titlexp, namespaces=ns)
        if len(viaf_resp_910a) > 0:
            out = []
            for n in range(len(viaf_resp_910a)):
                if viaf_resp_910a[n].text:
                    out.append(viaf_resp_910a[n].text.strip())
            return out
        else:
            return None

    def get_viaf_aff(self):
        affxp = '//marcxml:datafield[@tag="510"]/marcxml:subfield[@code="a"]'
        viaf_resp_510a = self.viaf_mx.xpath(affxp, namespaces=ns)
        if len(viaf_resp_510a) > 0:
            out = []
            for n in range(len(viaf_resp_510a)):
                if viaf_resp_510a[n].text:
                    out.append(viaf_resp_510a[n].text.strip())
            return out
        else:
            return None


class WikiSPARQL:
    def __init__(self, uri):
        self.uri = uri

    def get_wiki_aff(self):
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        sparql.setQuery("""
            PREFIX wikibase: <http://wikiba.se/ontology#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

            SELECT ?inst ?instLabel WHERE {
                <""" + self.uri + """> wdt:P108 ?inst .
              SERVICE wikibase:label {
                bd:serviceParam wikibase:language "en" .
                ?inst rdfs:label ?instLabel .
              }
            }
        """)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        if len(results['results']['bindings']) > 0:
            out = []
            for n in range(len(results['results']['bindings'])):
                if results['results']['bindings'][n]['instLabel']['value']:
                    out.append(results['results']['bindings'][n]
                               ['instLabel']['value'].strip())
            return out
        else:
            return None


class OCLCSearchResp:
    def __init__(self, json):
        self.json = json

    def get_field(self, field):
        try:
            return self.json.get(field)
        except KeyError:
            return None


class OAIDCRecord:
    """Base class for Simple Dublin Core metadata record in an OAI-PMH
    Repository file."""

    def __init__(self, elem):
        self.elem = elem

    def get_record_id(self):
        try:
            record_id = self.elem.find("oai:header/oai:identifier",
                                       namespaces=ns).text
            return record_id
        except:
            raise ReconException("Record does not have a Record Identifier")

    def get_record_status(self):
        return self.elem.find("oai:header",
                              namespaces=ns).get("status", "active")

    def get_element(self, element):
        try:
            element = self.elem[1][0].find(element, namespaces=ns)
            if element.text:
                return element.text.strip()
            else:
                return None
        except IndexError:
            return None

    def get_elements(self, element):
        out = []
        try:
            elements = self.elem[1][0].findall(element, namespaces=ns)
            for element in elements:
                if element.text:
                    out.append(element.text.strip())
            if len(out) == 0:
                out = None
            return out
        except IndexError:
            return None

    def get_spec_date(self):
        try:
            return self.elem[1][0].findall(DC + 'date')[2].text[:4]
        except IndexError:
            try:
                return self.elem[1][0].find(DC + 'date').text[:4]
            except AttributeError:
                return None


def get_CUL_score(record_elems, resp_elems):
    if record_elems is None or resp_elems is None:
        return None
    elif isinstance(record_elems, str) and isinstance(resp_elems, str):
        score = str(fuzz.token_sort_ratio(record_elems, resp_elems))
        return score
    elif isinstance(record_elems, str) and not isinstance(resp_elems, str):
        scores = []
        for n in range(len(resp_elems)):
            score = str(fuzz.token_sort_ratio(record_elems, resp_elems[n]))
            scores.append(score)
        return max(scores)
    elif not isinstance(record_elems, str) and isinstance(resp_elems, str):
        scores = []
        for n in range(len(record_elems)):
            score = str(fuzz.token_sort_ratio(record_elems[n], resp_elems))
            scores.append(score)
        return max(scores)
    elif not isinstance(record_elems, str) and not isinstance(resp_elems, str):
        scores = []
        for n in range(len(record_elems)):
            for m in range(len(resp_elems)):
                score = str(fuzz.token_sort_ratio(record_elems[n],
                            resp_elems[m]))
                scores.append(score)
        if scores != []:
            return max(scores)
    else:
        return None


def main():
    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("-o", "--output", dest="output",
                        help="file to save output to", default='Results.csv')
    parser.add_argument("-n", "--normalize", dest="normalize",
                        help="normalize metadata pre-matching? (yes/no)",
                        default='no')
    parser.add_argument("datafile", help="file with creators to be matched")

    args = parser.parse_args()

    ofile = open(args.output, "w")
    writer = csv.writer(ofile, delimiter=',', quotechar='"',
                        quoting=csv.QUOTE_ALL)
    writer.writerow(["record_identifier", "ecommons_entity_name",
                    "ecommons_title", "ecommons_title_year",
                    "ecommons_subject", "ecommons_publisher", "search_url",
                    "OCLC_result1_preflabel", "OCLC_result1_birthdate",
                    "OCLC_result1_deathdate", "OCLC_result1_score",
                    "OCLC_result1_subject", "OCLC_result1_subject_CUL_score",
                    "OCLC_result1_OCLC_URI", "OCLC_result1_LoC_preflabel",
                    "OCLC_result1_LoC_URI", "OCLC_result1_LoC_birthdate",
                    "OCLC_result1_LoC_deathdate",
                    "OCLC_result1_LoC_affiliation_CUL_score",
                    "OCLC_result1_VIAF_URI",
                    "OCLC_result1_VIAF_title_CUL_score",
                    "OCLC_result1_VIAF_affiliation_CUL_score",
                    "OCLC_result1_ISNI_URI", "OCLC_result1_Wiki_URI",
                    "OCLC_result2_Wiki_affiliation_CUL_score",
                    "OCLC_result2_preflabel", "OCLC_result2_birthdate",
                    "OCLC_result2_deathdate", "OCLC_result2_score",
                    "OCLC_result2_subject", "OCLC_result2_subject_CUL_score",
                    "OCLC_result2_OCLC_URI", "OCLC_result2_LoC_preflabel",
                    "OCLC_result2_LoC_URI", "OCLC_result2_LoC_birthdate",
                    "OCLC_result2_LoC_deathdate",
                    "OCLC_result2_LoC_affiliation_CUL_score",
                    "OCLC_result2_VIAF_URI",
                    "OCLC_result2_VIAF_title_CUL_score",
                    "OCLC_result2_VIAF_affiliation_CUL_score",
                    "OCLC_result2_ISNI_URI", "OCLC_result2_Wiki_URI",
                    "OCLC_result2_Wiki_affiliation_CUL_score"])

    for event, elem in etree.iterparse(args.datafile):
        if elem.tag == OAI + "record":
            r = OAIDCRecord(elem)
            record_id = r.get_record_id()
            title = r.get_element('dc:title')
            subject = r.get_elements('dc:subject')
            publisher = r.get_elements('dc:publisher')
            titleYear = r.get_spec_date()
            for entity in elem.iter(DC + "creator"):
                if args.normalize == 'yes':
                    creator_raw = entity.text
                    if re.match('.+\d+)', creator_raw):
                        creator = re.sub(',?.?\d+\s?-{1}\d{0,}', '',
                                         entity.text)
                    else:
                        creator = entity.text
                else:
                        creator = entity.text
                query = search_url + urllib.parse.quote(entity.text)
                resp = requests.get(query).json()

                oclc_res1_label = oclc_res1_bdate = oclc_res1_ddate = oclc_res1_score = oclc_res1_subj = oclc_res1_subj_score = oclc_res1_uri = oclc_res1_loc_label = oclc_res1_loc_uri = oclc_res1_loc_byear = oclc_res1_loc_dyear = oclc_res1_loc_aff_score = oclc_res1_viaf_uri = oclc_res1_viaf_title_score = oclc_res1_viaf_aff_score = oclc_res1_isni_uri = oclc_res1_wiki_uri = oclc_res1_wiki_aff_score = oclc_res2_label = oclc_res2_bdate = oclc_res2_ddate = oclc_res2_score = oclc_res2_subj = oclc_res2_subj_score = oclc_res2_uri = oclc_res2_loc_label = oclc_res2_loc_uri = oclc_res2_loc_byear = oclc_res2_loc_dyear = oclc_res2_loc_aff_score = oclc_res2_viaf_uri = oclc_res2_viaf_title_score = oclc_res2_viaf_aff_score = oclc_res2_isni_uri = oclc_res2_wiki_uri = oclc_res2_wiki_aff_score = None

                """want to use for loop here to go through all results,
                but avoiding now for sake of variables naming issues,
                also avoiding hitting api too many times

                #for n in range(len(resp['result'])):

                processing first result"""
                if resp.get('result') != []:
                    rjson = OCLCSearchResp(resp['result'][0])
                    oclc_res1_label = rjson.get_field('defaultLabel')
                    oclc_res1_uri = rjson.get_field('uri')
                    oclc_res1_score = rjson.get_field('score')
                    oclc_res1_subj = rjson.get_field('topic')
                    oclc_res1_subj_score = get_CUL_score(subject,
                                                         oclc_res1_subj)
                    if rjson.get_field('birthDate') is not None:
                        oclc_res1_bdate = rjson.get_field('birthDate')

                    if rjson.get_field('deathDate') is not None:
                        oclc_res1_ddate = rjson.get_field('deathDate')

                    oclc_sameas_query = (sameas_url
                                         + urllib.parse.quote(oclc_res1_uri))
                    oclc_sameas = requests.get(oclc_sameas_query,
                                               headers=json_header).json()
                    for n in range(len(oclc_sameas['sameAs'])):
                        if 'id.loc.gov' in oclc_sameas['sameAs'][n]:
                            oclc_res1_loc_uri = oclc_sameas['sameAs'][n]
                            nt = LoCRespNT(oclc_res1_loc_uri)
                            oclc_res1_loc_label = nt.get_loc_preflabel()
                            mx = LoCRespMARCXML(oclc_res1_loc_uri)
                            oclc_res1_loc_byear = mx.get_loc_bdate()
                            oclc_res1_loc_dyear = mx.get_loc_ddate()
                            loc_affs = mx.get_loc_aff()
                            oclc_res1_loc_aff_score = get_CUL_score(publisher,
                                                                    loc_affs)
                        elif 'viaf.org' in oclc_sameas['sameAs'][n]:
                            oclc_res1_viaf_uri = oclc_sameas['sameAs'][n]
                            print(oclc_res1_viaf_uri)
                            viaf_mx = VIAFrespMARCXML(oclc_res1_viaf_uri)
                            viaf_titles = viaf_mx.get_viaf_title()
                            oclc_res1_viaf_title_score = get_CUL_score(title, viaf_titles)
                            viaf_affs = viaf_mx.get_viaf_aff()
                            oclc_res1_viaf_aff_score = get_CUL_score(publisher,
                                                                     viaf_affs)
                        elif 'isni.org' in oclc_sameas['sameAs'][n]:
                            oclc_res1_isni_uri = oclc_sameas['sameAs'][n]
                        elif 'wikidata.org' in oclc_sameas['sameAs'][n]:
                            oclc_res1_wiki_uri = oclc_sameas['sameAs'][n]
                            wikidata = WikiSPARQL(oclc_res1_wiki_uri)
                            wiki_affs = wikidata.get_wiki_aff()
                            oclc_res1_wiki_aff_score = get_CUL_score(publisher,
                                                                    wiki_affs)

                """Process Second Result. See above comments on
                 wanting to make this for loop, issues therein"""
                if len(resp.get('result')) > 1:
                    rjson = OCLCSearchResp(resp['result'][1])
                    oclc_res2_label = rjson.get_field('defaultLabel')
                    oclc_res2_uri = rjson.get_field('uri')
                    oclc_res2_score = rjson.get_field('score')
                    oclc_res2_subj = rjson.get_field('topic')
                    oclc_res2_subj_score = get_CUL_score(subject,
                                                         oclc_res2_subj)
                    if rjson.get_field('birthDate') is not None:
                        oclc_res2_bdate = rjson.get_field('birthDate')

                    if rjson.get_field('deathDate') is not None:
                        oclc_res2_ddate = rjson.get_field('deathDate')

                    oclc_sameas_query2 = (sameas_url +
                                          urllib.parse.quote(oclc_res2_uri))
                    oclc_sameas = requests.get(oclc_sameas_query2,
                                               headers=json_header).json()
                    for n in range(len(oclc_sameas['sameAs'])):
                        if 'id.loc.gov' in oclc_sameas['sameAs'][n]:
                            oclc_res2_loc_uri = oclc_sameas['sameAs'][n]
                            nt = LoCRespNT(oclc_res2_loc_uri)
                            oclc_res2_loc_label = nt.get_loc_preflabel()
                            mx = LoCRespMARCXML(oclc_res2_loc_uri)
                            oclc_res2_loc_byear = mx.get_loc_bdate()
                            oclc_res2_loc_dyear = mx.get_loc_ddate()
                            loc2_affs = mx.get_loc_aff()
                            oclc_res2_loc_aff_score = get_CUL_score(publisher,
                                                                    loc2_affs)
                        elif 'viaf.org' in oclc_sameas['sameAs'][n]:
                            oclc_res2_viaf_uri = oclc_sameas['sameAs'][n]
                            print(oclc_res2_viaf_uri)
                            viaf_mx = VIAFrespMARCXML(oclc_res2_viaf_uri)
                            titles = viaf_mx.get_viaf_title()
                            oclc_res2_viaf_title_score = get_CUL_score(title,
                                                                       titles)
                            viaf_affs = viaf_mx.get_viaf_aff()
                            oclc_res2_viaf_aff_score = get_CUL_score(publisher,
                                                                     viaf_affs)
                        elif 'isni.org' in oclc_sameas['sameAs'][n]:
                            oclc_res2_isni_uri = oclc_sameas['sameAs'][n]
                        elif 'wikidata.org' in oclc_sameas['sameAs'][n]:
                            oclc_res2_wiki_uri = oclc_sameas['sameAs'][n]
                            wikidata = WikiSPARQL(oclc_res2_wiki_uri)
                            wiki_affs = wikidata.get_wiki_aff()
                            oclc_res2_wiki_aff_score = get_CUL_score(publisher,
                                                                    wiki_affs)

                writer = csv.writer(ofile, delimiter=',', quotechar='"',
                                    quoting=csv.QUOTE_ALL)
                writer.writerow([record_id, creator, title, titleYear,
                                subject, publisher, query, oclc_res1_label,
                                oclc_res1_bdate, oclc_res1_ddate,
                                oclc_res1_score, oclc_res1_subj,
                                oclc_res1_subj_score, oclc_res1_uri,
                                oclc_res1_loc_label, oclc_res1_loc_uri,
                                oclc_res1_loc_byear, oclc_res1_loc_dyear,
                                oclc_res1_loc_aff_score, oclc_res1_viaf_uri,
                                oclc_res1_viaf_title_score,
                                oclc_res1_viaf_aff_score, oclc_res1_isni_uri,
                                oclc_res1_wiki_uri, oclc_res1_wiki_aff_score,
                                oclc_res2_label,
                                oclc_res2_bdate, oclc_res2_ddate,
                                oclc_res2_score, oclc_res2_subj,
                                oclc_res2_subj_score, oclc_res2_uri,
                                oclc_res2_loc_label, oclc_res2_loc_uri,
                                oclc_res2_loc_byear, oclc_res2_loc_dyear,
                                oclc_res2_loc_aff_score, oclc_res2_viaf_uri,
                                oclc_res2_viaf_title_score,
                                oclc_res2_viaf_aff_score, oclc_res2_isni_uri,
                                oclc_res2_wiki_uri, oclc_res2_wiki_aff_score])
    ofile.close()


if __name__ == "__main__":
    main()
