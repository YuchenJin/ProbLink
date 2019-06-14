from collections import defaultdict
from link import Links
import pickle


class ProblinkFeatures(object):
    """Class for computing feature likelihoods given BGP paths
       and currently inferred link types."""
    def __init__(self, links):
        if isinstance(links, Links):
            self.links = links
        else:
            raise TypeError('input must be of type Links.')
        self.triplet_feature = defaultdict(lambda: [0.0, 0.0, 0.0])
        self.nonpath_feature = defaultdict(lambda: [0.0, 0.0, 0.0])
        self.distance_to_tier1_feature = defaultdict(lambda: [0.0, 0.0, 0.0])
        self.vp_feature = defaultdict(lambda: [0.0, 0.0, 0.0])
        self.colocated_ixp_feature = defaultdict(lambda: [0.0, 0.0, 0.0])
        self.colocated_facility_feature = defaultdict(lambda: [0.0, 0.0, 0.0])

    def _compute_likelihood(self, link_feature, feature_likelihood, is_triplet_feature=False):
        """Compute feature likelihood: probability of feature given link type P(f|C)."""
        count_class = [0.0, 0.0, 0.0]
        for k, v in link_feature.iteritems():
            if k in self.links.prob:
                if is_triplet_feature:
                    for adjacent_links_rel in v:
                        feature_likelihood[adjacent_links_rel] = [x + y for x, y in zip(feature_likelihood[adjacent_links_rel], self.links.prob[k])]
                        count_class = map(lambda x, y: x + y, self.links.prob[k], count_class)
                else:
                    feature_likelihood[v] = [x + y for x, y in zip(feature_likelihood[v], self.links.prob[k])]
                    count_class = map(lambda x, y: x + y, self.links.prob[k], count_class)

        for i in feature_likelihood:
            # Laplace smoothing
            feature_likelihood[i] = [(x+1)/(y+len(feature_likelihood)) for x, y in zip(feature_likelihood[i], count_class)]

    def compute_feature_likelihoods(self):
        """Compute likelihoods of all the features"""
        self._compute_likelihood(self.links.triplet_rel, self.triplet_feature, True)
        self._compute_likelihood(self.links.nonpath, self.nonpath_feature)
        self._compute_likelihood(self.links.distance_to_tier1, self.distance_to_tier1_feature)
        self._compute_likelihood(self.links.vp, self.vp_feature)
        self._compute_likelihood(self.links.colocated_ixp, self.colocated_ixp_feature)
        self._compute_likelihood(self.links.colocated_facility, self.colocated_facility_feature)

    def dump_feature(self, save_filename, feature):
        fileObject = open(save_filename, 'w')
        pickle.dump(feature, fileObject)
        fileObject.close()
