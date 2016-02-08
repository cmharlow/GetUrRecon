from argparse import ArgumentParser
import pymarc
import logging
import sys

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

    if args.datafile and args.queryType == 'PersonalName':
        if args.format == 'mrc':
            data = open(args.datafile, 'rb')
            reader = pymarc.MARCReader(data)
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
                except (TypeError):
                    topics = None
                resp = {}
                resp['recordID'] = recordID
                resp['title'] = title
                resp['uniformTitle'] = uniformTitle
                resp['stmtOfResp'] = stmtOfResp
                resp['topics'] = topics
                logging.debug(resp)
                logging.debug('\n')
                for name in record.get_fields('100'):
                    if name['t'] or name['v'] or name['x']:
                        logging.debug('No matching for ' + name.format_field()
                                      .replace(' -- ', '--'))
                    elif name['0']:
                        logging.debug(name['0'].value)



if __name__ == "__main__":
        main()
