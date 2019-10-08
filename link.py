from bgp_path_parser import BgpPaths
import networkx as nx
from collections import defaultdict
import numpy as np
import json
import sqlite3
from itertools import permutations


class Links(object):
    """Class for assigning link attributes."""
    def __init__(self, bgp_paths):
        if isinstance(bgp_paths, BgpPaths):
            self.bgp_paths = bgp_paths
        else:
            raise TypeError('input must be of type BgpPaths.')

        self.prob = {}
        self.rel = {}
        self.siblings = set()
        self.triplet_rel = {}
        self.prev_p2p_p2c = defaultdict(set)
        self.prev_links = defaultdict(set)
        self.nonpath = {}
        self.distance_to_tier1 = {}
        self.vp = {}
        self.colocated_ixp = defaultdict(int)
        self.colocated_facility = defaultdict(int)

    def ingest_prob(self, bootstrap_rel_file):
        """Initialize deterministic relationship probabilities and relationships
        from bootstrapping algorithms such as AS-Rank and CoreToLeaf.

        The key of self.prob dictionary is a link pair,
        and the value is a tuple (probability of the link being p2p, p2c, c2p).
        """
        with open(bootstrap_rel_file) as f:
            for line in f:
                if not line.startswith("#"):
                    AS1, AS2, rel = line.strip().split("|")
                    if rel == '0':
                        self.prob[(AS1, AS2)] = (1.0, 0.0, 0.0)
                        self.prob[(AS2, AS1)] = (1.0, 0.0, 0.0)
                        self.rel[(AS1, AS2)] = 'p2p'
                        self.rel[(AS2, AS1)] = 'p2p'
                    elif rel == '-1':
                        self.prob[(AS1, AS2)] = (0.0, 1.0, 0.0)
                        self.prob[(AS2, AS1)] = (0.0, 0.0, 1.0)
                        self.rel[(AS1, AS2)] = 'p2c'
                        self.rel[(AS2, AS1)] = 'c2p'

    def extract_siblings(self, asn_org_file):
        format_counter = 0
        org_asn = defaultdict(list)
        with open(asn_org_file) as f:
            for line in f:
                if format_counter == 2:
                    asn = line.split('|')[0]
                    org_id = line.split('|')[3]
                    org_asn[org_id].append(asn)
                if line.startswith("# format"):
                    format_counter += 1

        for k, v in org_asn.iteritems():
            sibling_perm = permutations(v, 2)
            for i in sibling_perm:
                self.siblings.add(i)

    def assign_triplet_rel(self):
        """What are the previous and next link types in each link triplet."""
        for path in (self.bgp_paths.forward_paths | self.bgp_paths.reverse_paths):
            flag = 1
            ASes = path.split("|")
            for i in range(len(ASes) - 1):
                if (ASes[i], ASes[i+1]) not in self.prob:
                    flag = 0
            if flag == 1:
                # insert a "NULL" link in front of and behind each BGP path
                link_list = ['NULL']
                for i in range(len(ASes) - 1):
                    if (ASes[i], ASes[i+1]) not in self.siblings:
                        link_list.append((ASes[i], ASes[i+1]))
                link_list.append('NULL')
                if len(link_list) != 2:
                    for i in range(1, len(link_list)-1):
                        if link_list[i] not in self.triplet_rel:
                            self.triplet_rel[link_list[i]] = []
                        prev_link = link_list[i-1]
                        next_link = link_list[i+1]
                        if prev_link == 'NULL':
                            prev_rel = 'NULL'
                        else:
                            prev_rel = self.rel[prev_link]
                        if next_link == 'NULL':
                            next_rel = 'NULL'
                        else:
                            next_rel = self.rel[next_link]
                        self.triplet_rel[link_list[i]].append((prev_rel, next_rel))

    def compute_prev_links(self):
        """Compute adjacent previous links of all the ASes."""
        for path in self.bgp_paths.forward_paths:
            ASes = path.split('|')
            for i in xrange(len(ASes) - 2):
                self.prev_links[(ASes[i+1], ASes[i+2])].add((ASes[i], ASes[i+1]))

    def compute_prev_p2p_p2c(self):
        """Compute adjacent previous p2p/p2c links of links based on current link types."""
        for link in self.prob:
            p2p, p2c, c2p = map(lambda x: np.float128(x), self.prob[link])
            if p2p > c2p or p2c > c2p:
                self.prev_p2p_p2c[link[1]].add(link)

    def assign_nonpath(self):
        """How many adjacent p2p or p2c links a link has, but none of them appear before this link on any of the paths."""
        for link in self.prob:
            if not any(i in self.prev_links[link] for i in self.prev_p2p_p2c[link[0]]):
                self.nonpath[link] = len(self.prev_p2p_p2c[link[0]])

    def assign_vp(self):
        """How many vantage points observe a link."""
        for path in self.bgp_paths.forward_paths:
            if '|' in path:
                ASes = path.split("|")
                vp = ASes[0]
                for i in range(len(ASes)-1):
                    if (ASes[i], ASes[i+1]) not in self.vp:
                        self.vp[(ASes[i], ASes[i+1])] = set()
                    self.vp[(ASes[i], ASes[i+1])].add(vp)
        for link in self.vp:
            if link in self.prob:
                self.vp[link] = len(self.vp[link])

    def assign_distance_to_tier1(self):
        """Compute link's average distance to each Tier-1 AS, and round it to a multiple of 0.1."""
        shortest_distance = defaultdict(dict)
        shortest_distance_list = defaultdict(list)
        g = nx.Graph()
        for link in self.prob:
            g.add_edge(link[0], link[1])
        tier1s = ['174', '209', '286', '701', '1239', '1299', '2828', '2914', '3257', '3320', '3356', '4436', '5511', '6453', '6461', '6762', '7018', '12956', '3549']
        for tier1_asn in tier1s:
            if tier1_asn not in g:
                tier1s.remove(tier1_asn)
            else:
                p = nx.shortest_path_length(g, source=tier1_asn)
                for k, v in p.iteritems():
                    if k not in shortest_distance or tier1_asn not in shortest_distance[k]:
                        shortest_distance[k][tier1_asn] = v
                        shortest_distance_list[k].append(v)

        for link in self.prob:
            AS1, AS2 = link
            if AS1 in shortest_distance and AS2 in shortest_distance:
                dis_AS1 = int(sum(shortest_distance_list[AS1])/float(len(shortest_distance_list[AS1]))/0.1)
                dis_AS2 = int(sum(shortest_distance_list[AS2])/float(len(shortest_distance_list[AS2]))/0.1)
                self.distance_to_tier1[link] = (dis_AS1, dis_AS2)

    def assign_colocated_ixp(self, peeringdb_file):
        """How many IXPs that two ASes are co-located in."""
        ixp_dict = {}
        # PeeringDB json dump
        if peeringdb_file.endswith('json'):
            with open(peeringdb_file) as f:
                data = json.load(f)
            for i in data['netixlan']['data']:
                AS, ixp = i['asn'], i['ixlan_id']
                if ixp not in ixp_dict:
                    ixp_dict[ixp] = [AS]
                else:
                    ixp_dict[ixp].append(AS)
        # PeeringDB sqlite dump
        elif peeringdb_file.endswith('sqlite'):
            conn = sqlite3.connect(peeringdb_file)
            c = conn.cursor()
            for row in c.execute("SELECT asn, ixlan_id FROM 'peeringdb_network_ixlan'"):
                AS, ixp = row[0], row[1]
                if ixp not in ixp_dict:
                    ixp_dict[ixp] = [AS]
                else:
                    ixp_dict[ixp].append(AS)

        for k, v in ixp_dict.iteritems():
            as_pairs = [(str(p1), str(p2)) for p1 in v for p2 in v if p1 != p2]
            for pair in as_pairs:
                self.colocated_ixp[(pair[0], pair[1])] += 1
        for link in self.prob:
            if link not in self.colocated_ixp:
                self.colocated_ixp[link] = 0

    def assign_colocated_facility(self, peeringdb_file):
        """How many peering facilities that two ASes are co-located in."""
        facility_dict = {}

        # PeeringDB json dump
        if peeringdb_file.endswith('json'):
            with open(peeringdb_file) as f:
                data = json.load(f)
            for i in data['netfac']['data']:
                AS, facility = i['local_asn'], i['fac_id']
                if facility not in facility_dict:
                    facility_dict[facility] = [AS]
                else:
                    facility_dict[facility].append(AS)
        # PeeringDB sqlite dump
        elif peeringdb_file.endswith('sqlite'):
            conn = sqlite3.connect(peeringdb_file)
            c = conn.cursor()
            for row in c.execute("SELECT local_asn, fac_id FROM 'peeringdb_network_facility'"):
                AS, facility = row[0], row[1]
                if facility not in facility_dict:
                    facility_dict[facility] = [AS]
                else:
                    facility_dict[facility].append(AS)

        for k, v in facility_dict.iteritems():
            as_pairs = [(str(p1), str(p2)) for p1 in v for p2 in v if p1 != p2]
            for pair in as_pairs:
                self.colocated_facility[(pair[0], pair[1])] += 1
        for link in self.prob:
            if link not in self.colocated_facility:
                self.colocated_facility[link] = 0

    def construct_attributes(self, asn_org_file, peeringdb_file):
        self.extract_siblings(asn_org_file)
        self.assign_triplet_rel()
        self.compute_prev_links()
        self.compute_prev_p2p_p2c()
        self.assign_nonpath()
        self.assign_vp()
        self.assign_distance_to_tier1()
        self.assign_colocated_ixp(peeringdb_file)
        self.assign_colocated_facility(peeringdb_file)
