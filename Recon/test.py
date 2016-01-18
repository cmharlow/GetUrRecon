from argparse import ArgumentParser
import requests
from lxml import etree
import constants
import json
#   1. record type assessment


class MARCmetadata:
    """Base class for binary MARC21 record."""
    def __init__(self, uri):
        self.uri = uri
        self.marcxml = etree.XML(requests.get(self.uri + ".marcxml.xml").text)


class XMLmetadata:
    """Base class for XML record."""


class JSONmetadata:
    """Base class for JSON (not LD) record."""


class RDFmetadata:
    """Base class for RDF graph."""
#   2. record feed import
#   3. field parsing
#   4. recon obj prelim creation with fields, query
#   5. recon obj expansion with calls
#   6. present results back
#   7. update records


def main():
    parser = ArgumentParser(usage='%(prog)s [options] data_filename')
    parser.add_argument("-f", "--format", dest="format",
                        help="Enter 1: csv, json, jsonld, mrc, nt, ttl, xml")
    parser.add_argument("-m", "--match", dest="match", help="match confidence",
                        default=80)
    parser.add_argument("-q", "--queryField", dest="queryField",
                        help="field to be matched")
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

    if args.datafile is not None and args.queryType == 'PersonalName':
        if args.format == 'csv':
            print('csv')
        elif args.format == 'json':
            for i in json.load(args.datafile)[args.record]:
                r = JSONRecord(json.load(args.datafile)[args.record])
                if json.load(args.datafile)[args.record][i] == args.queryField:
                    reso = r.buildReso()
                    #external calls
        elif args.format == 'jsonld':
            print('jsonld')
        elif args.format == 'mrc':
            print('mrc')
        elif args.format == 'nt':
            print('nt')
        elif args.format == 'ttl':
            print('ttl')
        elif args.format == 'xml':
            for event, elem in etree.iterparse(args.datafile):
                if elem.tag == args.record:
                    r = XMLRecord(elem)
                    for entity in elem.iter(args.queryField):
                        reso = r.buildReso()
                        #external calls

    if args.sparql is not None and args.uri is not None:
        #retrieve graph for uri from sparql endpoint
        #


if __name__ == "__main__":
    main()
