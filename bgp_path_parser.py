import sys
import json
import sqlite3


class BgpPaths(object):
    """ Class for storing and sanitizing forward and reverse BGP paths """

    def __init__(self):
        self.forward_paths = set()
        self.reverse_paths = set()
        self.ixp = set()

    def extract_ixp(self, peeringdb_file):
        # PeeringDB json dump
        if peeringdb_file.endswith('json'):
            with open(peeringdb_file) as f:
                data = json.load(f)
            for i in data['net']['data']:
                if i['info_type'] == 'Route Server':
                    self.ixp.add(str(i['asn']))

        # PeeringDB sqlite dump
        elif peeringdb_file.endswith('sqlite'):
            conn = sqlite3.connect(peeringdb_file)
            c = conn.cursor()
            for row in c.execute("SELECT asn, info_type FROM 'peeringdb_network'"):
                asn, info_type = row
                if info_type == 'Route Server':
                    self.ixp.add(str(asn))
        else:
            raise TypeError('PeeringDB file must be either a json file or a sqlite file.')

        # Use IXP ASNs collected by https://github.com/vgiotsas/IxpRsCollector
        # if no route servers were included in the peeringdb file
        # if len(self.ixp) == 0:
        #     with open('RouteServerASNs_20171230.txt') as f:
        #         for line in f:
        #             if not line.startswith('#'):
        #                 self.ixp.add(line.strip())

    def parse_bgp_paths(self, rib_file):
        """ Parse BGP paths from a RIB file.

        Remove duplicated ASes, an artifact of BGP path prepending.
        Sanitize the BGP paths: remove route server ASes;
                                remove paths containing reserved ASes;
                                remove paths with AS loops.
        """
        with open(rib_file) as f:
            for line in f:
                asn_list = line.strip().split("|")
                # remove IXPs
                for asn in asn_list:
                    if asn in self.ixp:
                        asn_list.remove(asn)
                # remove prepended ASes
                asn_list = [v for i, v in enumerate(asn_list)
                            if i == 0 or v != asn_list[i-1]]
                asn_set = set(asn_list)
                # remove poisoned paths with AS loops
                if len(asn_set) == 1 or not len(asn_list) == len(asn_set):
                    continue
                else:
                    for asn in asn_list:
                        asn = int(asn)
                        # reserved ASN
                        if asn == 0 or asn == 23456 or asn >= 394240 \
                           or (61440 <= asn <= 131071) \
                           or (133120 <= asn <= 196607)\
                           or (199680 <= asn <= 262143)\
                           or (263168 <= asn <= 327679)\
                           or (328704 <= asn <= 393215):
                            break
                    else:
                        self.forward_paths.add("|".join(asn_list))
                        self.reverse_paths.add("|".join(asn_list[::-1]))
                    continue

    def output_forward_paths(self):
        f = open('sanitized_rib.txt', 'w')
        for path in self.forward_paths:
            f.write(path + '\n')
        f.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python bgp_path_parser.py <peeringdb file>')
        exit()

    path = BgpPaths()
    path.extract_ixp(sys.argv[1])
    path.parse_bgp_paths('rib.txt')
    path.output_forward_paths()
