"""
Tenderer Clustering Module - Phase 5 Task 029
Entity clustering for tenderer names with normalization and similarity matching.
"""

import re
import uuid
from typing import Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher
from datetime import datetime


class NameNormalizer:
    """
    Normalizer for tenderer names.

    Handles standardization of organization names including:
    - Space normalization
    - Suffix standardization
    - Character normalization
    """

    # Organization suffix mappings
    ORG_SUFFIX_MAP = {
        # Company suffixes
        "公司": "公司",
        "有限公司": "有限公司",
        "有限责任公司": "有限公司",
        "股份有限公司": "股份有限公司",
        "股份公司": "股份有限公司",
        "集团": "集团",
        "集团公司": "集团",
        "总公司": "总公司",
        "分公司": "分公司",
        # Government suffixes
        "局": "局",
        "厅": "厅",
        "部": "部",
        "委": "委",
        "办公室": "办公室",
        "中心": "中心",
        "研究所": "研究所",
        "研究院": "研究院",
        # Institution suffixes
        "医院": "医院",
        "学校": "学校",
        "大学": "大学",
        "学院": "学院",
        "幼儿园": "幼儿园",
        "小学": "小学",
        "中学": "中学",
    }

    # Common aliases for major organizations
    ORG_ALIASES = {
        "中国移动": "中国移动通信集团有限公司",
        "中国移动通信": "中国移动通信集团有限公司",
        "移动": "中国移动通信集团有限公司",
        "中国电信": "中国电信集团有限公司",
        "电信": "中国电信集团有限公司",
        "中国联通": "中国联合网络通信集团有限公司",
        "联通": "中国联合网络通信集团有限公司",
        "北大": "北京大学",
        "清华": "清华大学",
    }

    def __init__(self):
        """Initialize name normalizer."""
        self.suffix_map = self.ORG_SUFFIX_MAP
        self.aliases = self.ORG_ALIASES

    def normalize(self, name: str) -> str:
        """
        Normalize an organization name.

        Args:
            name: Raw organization name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        # Step 1: Remove extra whitespace
        name = self._remove_extra_spaces(name)

        # Step 2: Remove noise characters
        name = self._remove_noise(name)

        # Step 3: Standardize fullwidth/halfwidth characters
        name = self._standardize_chars(name)

        # Step 4: Standardize suffixes
        name = self._standardize_suffix(name)

        # Step 5: Check for aliases
        name = self._resolve_alias(name)

        return name

    def _remove_extra_spaces(self, name: str) -> str:
        """Remove extra spaces from name."""
        return " ".join(name.split())

    def _remove_noise(self, name: str) -> str:
        """Remove noise characters like parentheses content."""
        # Remove content in parentheses
        name = re.sub(r'[（(].*?[）)]', '', name)
        # Remove special characters
        name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', '', name)
        return name.strip()

    def _standardize_chars(self, name: str) -> str:
        """Standardize fullwidth/halfwidth characters."""
        # Convert fullwidth alphanumeric to halfwidth
        result = ""
        for char in name:
            code = ord(char)
            if 0xFF01 <= code <= 0xFF5E:  # Fullwidth ASCII
                result += chr(code - 0xFEE0)
            elif code == 0x3000:  # Fullwidth space
                result += " "
            else:
                result += char
        return result

    def _standardize_suffix(self, name: str) -> str:
        """Standardize organization suffixes."""
        # Sort by length (longest first) to avoid partial matches
        suffixes = sorted(self.suffix_map.keys(), key=len, reverse=True)

        for suffix in suffixes:
            if name.endswith(suffix):
                # Replace with standard form
                standard = self.suffix_map[suffix]
                if suffix != standard:
                    name = name[:-len(suffix)] + standard
                break

        return name

    def _resolve_alias(self, name: str) -> str:
        """Resolve name aliases."""
        # Check for exact alias match
        if name in self.aliases:
            return self.aliases[name]

        # Check if it contains an alias
        for alias, full_name in self.aliases.items():
            if alias in name and len(name) < len(full_name):
                return full_name

        return name

    def add_alias(self, alias: str, full_name: str):
        """Add a new alias mapping."""
        self.aliases[alias] = full_name


class SimilarityCalculator:
    """
    Calculator for string similarity metrics.

    Implements multiple similarity algorithms:
    - Levenshtein distance
    - Jaccard similarity
    - Character-based similarity
    """

    def __init__(self):
        """Initialize similarity calculator."""
        pass

    def calculate(self, name1: str, name2: str) -> float:
        """
        Calculate combined similarity score.

        Args:
            name1: First name
            name2: Second name

        Returns:
            Combined similarity score (0.0-1.0)
        """
        lev_sim = self.levenshtein_similarity(name1, name2)
        jac_sim = self.jaccard_similarity(name1, name2)
        char_sim = self.char_similarity(name1, name2)

        return self.combine_scores(lev_sim, jac_sim, char_sim)

    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate Levenshtein similarity.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # Use SequenceMatcher for edit distance
        matcher = SequenceMatcher(None, s1, s2)
        return matcher.ratio()

    def jaccard_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate Jaccard similarity based on character sets.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        set1 = set(s1)
        set2 = set(s2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def char_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate character-based similarity.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score (0.0-1.0)
        """
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # Count matching characters
        matches = sum(1 for c in s1 if c in s2)
        max_len = max(len(s1), len(s2))

        return matches / max_len if max_len > 0 else 0.0

    def combine_scores(self, *scores: float) -> float:
        """
        Combine multiple similarity scores.

        Args:
            *scores: Variable number of similarity scores

        Returns:
            Combined score (0.0-1.0)
        """
        if not scores:
            return 0.0

        # Weighted average (can be customized)
        weights = [0.4, 0.3, 0.3]  # Levenshtein, Jaccard, Char
        weighted_sum = sum(s * w for s, w in zip(scores[:3], weights))
        total_weight = sum(weights[:len(scores)])

        return weighted_sum / total_weight if total_weight > 0 else 0.0


class TendererCluster:
    """
    Represents a cluster of tenderer name variants.
    """

    def __init__(self, cluster_id: Optional[str] = None):
        """
        Initialize cluster.

        Args:
            cluster_id: Optional cluster ID
        """
        self.cluster_id = cluster_id or str(uuid.uuid4())
        self.variants: Set[str] = set()
        self.canonical_name: Optional[str] = None
        self.short_name: Optional[str] = None
        self.aliases: Set[str] = set()
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.confidence = 0.0

    def add_variant(self, name: str):
        """Add a name variant to the cluster."""
        self.variants.add(name)
        self.updated_at = datetime.now()
        self._update_canonical_name()

    def _update_canonical_name(self):
        """Update canonical name based on variants."""
        if not self.variants:
            return

        # Select longest name as canonical (most complete)
        self.canonical_name = max(self.variants, key=len)

        # Select shortest as short name
        self.short_name = min(self.variants, key=len)

        # Update aliases
        self.aliases = self.variants - {self.canonical_name}

    def to_dict(self) -> Dict:
        """Convert cluster to dictionary."""
        return {
            'cluster_id': self.cluster_id,
            'canonical_name': self.canonical_name,
            'short_name': self.short_name,
            'variants': list(self.variants),
            'aliases': list(self.aliases),
            'cluster_size': len(self.variants),
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class TendererClusterer:
    """
    Clusterer for tenderer entity names.

    Groups similar tenderer names into clusters using
    similarity algorithms and normalization.
    """

    DEFAULT_SIMILARITY_THRESHOLD = 0.75

    def __init__(self, similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD):
        """
        Initialize clusterer.

        Args:
            similarity_threshold: Minimum similarity for clustering
        """
        self.similarity_threshold = similarity_threshold
        self.normalizer = NameNormalizer()
        self.similarity_calc = SimilarityCalculator()
        self.clusters: Dict[str, TendererCluster] = {}

    def cluster(self, names: List[str]) -> List[Dict]:
        """
        Cluster a list of tenderer names.

        Args:
            names: List of tenderer names

        Returns:
            List of cluster dictionaries
        """
        if not names:
            return []

        # Normalize all names
        normalized = [(name, self.normalizer.normalize(name)) for name in names]

        # Clear existing clusters for fresh clustering
        self.clusters = {}

        # Group by normalized form (exact matches)
        normalized_groups: Dict[str, List[str]] = {}
        for original, norm in normalized:
            if norm not in normalized_groups:
                normalized_groups[norm] = []
            normalized_groups[norm].append(original)

        # Create initial clusters from exact matches
        for norm, variants in normalized_groups.items():
            cluster = TendererCluster()
            for variant in variants:
                cluster.add_variant(variant)
            cluster.confidence = 1.0  # Exact match
            self.clusters[cluster.cluster_id] = cluster

        # Merge similar clusters
        self._merge_similar_clusters()

        # Return results
        return [cluster.to_dict() for cluster in self.clusters.values()]

    def _merge_similar_clusters(self):
        """Merge clusters that are similar to each other."""
        cluster_list = list(self.clusters.values())
        merged = set()

        for i, cluster1 in enumerate(cluster_list):
            if cluster1.cluster_id in merged:
                continue

            for j, cluster2 in enumerate(cluster_list[i+1:], i+1):
                if cluster2.cluster_id in merged:
                    continue

                # Calculate similarity between clusters
                similarity = self._cluster_similarity(cluster1, cluster2)

                if similarity >= self.similarity_threshold:
                    # Merge cluster2 into cluster1
                    for variant in cluster2.variants:
                        cluster1.add_variant(variant)
                    cluster1.confidence = max(cluster1.confidence, similarity)
                    merged.add(cluster2.cluster_id)
                    del self.clusters[cluster2.cluster_id]

    def _cluster_similarity(self, cluster1: TendererCluster,
                           cluster2: TendererCluster) -> float:
        """Calculate maximum similarity between two clusters."""
        max_similarity = 0.0

        for name1 in cluster1.variants:
            norm1 = self.normalizer.normalize(name1)
            for name2 in cluster2.variants:
                norm2 = self.normalizer.normalize(name2)
                sim = self.similarity_calc.calculate(norm1, norm2)
                max_similarity = max(max_similarity, sim)

        return max_similarity

    def create_cluster(self, names: List[str]) -> str:
        """
        Create a new cluster with given names.

        Args:
            names: List of name variants

        Returns:
            Cluster ID
        """
        cluster = TendererCluster()
        for name in names:
            cluster.add_variant(name)
        cluster.confidence = 1.0
        self.clusters[cluster.cluster_id] = cluster
        return cluster.cluster_id

    def add_to_cluster(self, cluster_id: str, name: str) -> Dict:
        """
        Add a name to an existing cluster.

        Args:
            cluster_id: Cluster ID
            name: Name to add

        Returns:
            Updated cluster dictionary
        """
        if cluster_id not in self.clusters:
            raise ValueError(f"Cluster {cluster_id} not found")

        cluster = self.clusters[cluster_id]
        cluster.add_variant(name)
        return cluster.to_dict()

    def merge_clusters(self, cluster_id1: str, cluster_id2: str) -> Dict:
        """
        Merge two clusters.

        Args:
            cluster_id1: First cluster ID
            cluster_id2: Second cluster ID

        Returns:
            Merged cluster dictionary
        """
        if cluster_id1 not in self.clusters or cluster_id2 not in self.clusters:
            raise ValueError("One or both clusters not found")

        cluster1 = self.clusters[cluster_id1]
        cluster2 = self.clusters[cluster_id2]

        # Merge variants
        for variant in cluster2.variants:
            cluster1.add_variant(variant)

        # Remove cluster2
        del self.clusters[cluster_id2]

        return cluster1.to_dict()

    def find_cluster(self, name: str) -> Optional[Dict]:
        """
        Find cluster containing a name.

        Args:
            name: Name to search for

        Returns:
            Cluster dictionary or None
        """
        norm_name = self.normalizer.normalize(name)

        for cluster in self.clusters.values():
            if name in cluster.variants:
                return cluster.to_dict()

            # Check similarity
            for variant in cluster.variants:
                norm_variant = self.normalizer.normalize(variant)
                sim = self.similarity_calc.calculate(norm_name, norm_variant)
                if sim >= self.similarity_threshold:
                    return cluster.to_dict()

        return None

    def list_clusters(self) -> List[Dict]:
        """List all clusters."""
        return [cluster.to_dict() for cluster in self.clusters.values()]

    def get_cluster(self, cluster_id: str) -> Optional[Dict]:
        """Get cluster by ID."""
        if cluster_id in self.clusters:
            return self.clusters[cluster_id].to_dict()
        return None
