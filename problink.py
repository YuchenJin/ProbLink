import argparse
from link import Links
from bgp_path_parser import BgpPaths
from feature import ProblinkFeatures
import math


def compute_class_prior(links):
    """Compute class prior probability: P(C)"""
    p2p_count, p2c_count, c2p_count = 0, 0, 0
    for link, rel in links.rel.iteritems():
        if rel == 'p2p':
            p2p_count += 1
        elif rel == 'p2c':
            p2c_count += 1
        else:
            c2p_count += 1
    sum_class = p2p_count + p2c_count + c2p_count
    return map(lambda x: float(x)/sum_class, (p2p_count, p2c_count, c2p_count))


def naive_bayes(links, features):
    """Do inference using naive bayes algorithm."""
    output_rel = open('problink_result.txt', 'w')
    inferred_link = set()
    class_prior = compute_class_prior(links)
    log_class_prior = map(lambda x: math.log10(x), class_prior)

    for link in links.prob:
        AS1, AS2 = link
        reverse_link = (AS2, AS1)

        if link in inferred_link:
            continue
        if link in links.siblings:
            output_rel.write('|'.join((AS1, AS2, '1')) + '\n')
            inferred_link.add(link)
            inferred_link.add(reverse_link)
            continue

        log_prob = log_class_prior
        # triplet feature
        if link in links.triplet_rel:
            for adjacent_links_rel in links.triplet_rel[link]:
                log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.triplet_feature[adjacent_links_rel]))
        if reverse_link in links.triplet_rel:
            for adjacent_links_rel in links.triplet_rel[reverse_link]:
                reverse_prob = features.triplet_feature[adjacent_links_rel]
                reverse_prob = (reverse_prob[0], reverse_prob[2], reverse_prob[1])
                log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), reverse_prob))

        # non-path feature
        if link in links.nonpath:
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.nonpath_feature[links.nonpath[link]]))
        if reverse_link in links.nonpath:
            reverse_prob = features.nonpath_feature[links.nonpath[reverse_link]]
            reverse_prob = (reverse_prob[0], reverse_prob[2], reverse_prob[1])
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), reverse_prob))

        # distance-to-tier1 feature
        if link in links.distance_to_tier1:
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.distance_to_tier1_feature[links.distance_to_tier1[link]]))

        # VP feature
        if link in links.vp:
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.vp_feature[links.vp[link]]))
        if reverse_link in links.vp:
            reverse_prob = features.vp_feature[links.vp[reverse_link]]
            reverse_prob = (reverse_prob[0], reverse_prob[2], reverse_prob[1])
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), reverse_prob))

        # colocated-IXP feature
        if link in links.colocated_ixp:
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.colocated_ixp_feature[links.colocated_ixp[link]]))

        # colocated-facility feature
        if link in links.colocated_facility:
            log_prob = map(lambda x, y: x + y, log_prob, map(lambda x: math.log10(x), features.colocated_facility_feature[links.colocated_facility[link]]))

        log_p2p, log_p2c, log_c2p = log_prob
        if log_p2p > log_p2c and log_p2p > log_c2p:
            output_rel.write('|'.join((AS1, AS2, '0')) + '\n')
        elif log_p2c > log_p2p and log_p2c > log_c2p:
            output_rel.write('|'.join((AS1, AS2, '-1')) + '\n')
        elif log_c2p > log_p2p and log_c2p > log_p2c:
            output_rel.write('|'.join((AS2, AS1, '-1')) + '\n')

        inferred_link.add(link)
        inferred_link.add(reverse_link)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Do problink inference.')
    parser.add_argument('-p', '--peeringdb',
                        help='PeeringDB file',
                        required=True)
    parser.add_argument('-a', '--as_org',
                        help='AS to organization mapping file',
                        required=True)
    args = parser.parse_args()
    path = BgpPaths()
    path.extract_ixp(args.peeringdb)
    path.parse_bgp_paths('sanitized_rib.txt')
    links = Links(path)
    links.ingest_prob('asrank_result.txt')
    links.construct_attributes(args.as_org, args.peeringdb)
    print('Link attributes constructed...')
    features = ProblinkFeatures(links)
    features.compute_feature_likelihoods()
    print('Feature likelihoods computed...')
    naive_bayes(links, features)
    print('Inference results are output to problink_result.txt')
