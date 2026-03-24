"""
Entity Resolver Module
Resolves entity names to existing clusters.
"""

from typing import Dict, Optional, List
from .tenderer_clusterer import TendererClusterer


class EntityResolver:
    """
    Resolver for entity disambiguation.

    Resolves ambiguous entity names to their canonical forms
    using clustering information and context.
    """

    def __init__(self, clusterer: TendererClusterer):
        """
        Initialize entity resolver.

        Args:
            clusterer: TendererClusterer instance
        """
        self.clusterer = clusterer

    def resolve(self, name: str, context: Optional[str] = None) -> Optional[Dict]:
        """
        Resolve an entity name to its canonical form.

        Args:
            name: Entity name to resolve
            context: Optional context for disambiguation

        Returns:
            Resolved entity dictionary or None
        """
        # First try exact match
        cluster = self.clusterer.find_cluster(name)
        if cluster:
            return {
                'name': name,
                'canonical_name': cluster['canonical_name'],
                'cluster_id': cluster['cluster_id'],
                'confidence': 1.0,
                'method': 'exact'
            }

        # Try similarity match
        normalized = self.clusterer.normalizer.normalize(name)
        for existing_cluster in self.clusterer.list_clusters():
            for variant in existing_cluster['variants']:
                norm_variant = self.clusterer.normalizer.normalize(variant)
                sim = self.clusterer.similarity_calc.calculate(
                    normalized, norm_variant
                )
                if sim >= self.clusterer.similarity_threshold:
                    return {
                        'name': name,
                        'canonical_name': existing_cluster['canonical_name'],
                        'cluster_id': existing_cluster['cluster_id'],
                        'confidence': sim,
                        'method': 'similarity'
                    }

        return None

    def resolve_batch(self, names: List[str]) -> List[Optional[Dict]]:
        """
        Resolve multiple entity names.

        Args:
            names: List of entity names

        Returns:
            List of resolved entity dictionaries
        """
        return [self.resolve(name) for name in names]
