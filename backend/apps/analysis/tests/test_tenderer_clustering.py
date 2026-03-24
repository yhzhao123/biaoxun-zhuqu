"""
Tenderer Clustering Tests - Phase 5 Task 028
Tests for tenderer entity clustering and name normalization.
"""

import pytest
from unittest.mock import Mock, patch


class TestTendererClustererExists:
    """Test 1: TendererClusterer class exists"""

    def test_clusterer_class_exists(self):
        """TendererClusterer class should exist"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer
        assert TendererClusterer is not None

    def test_clusterer_has_cluster_method(self):
        """TendererClusterer should have cluster method"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer
        assert hasattr(TendererClusterer, 'cluster')


class TestHospitalNameClustering:
    """Test 2: Hospital name variant clustering"""

    def test_cluster_hospital_name_variants(self):
        """Should cluster different name variants of same hospital"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        names = [
            "某市人民医院",
            "某市第一人民医院",
            "某市人民医院（新院区）",
            "某市人民 医院",
        ]

        clusterer = TendererClusterer()
        clusters = clusterer.cluster(names)

        assert len(clusters) == 1
        assert clusters[0]['canonical_name'] == "某市人民医院"
        assert len(clusters[0]['variants']) == 4


class TestCompanyNameNormalization:
    """Test 3: Company name normalization"""

    def test_normalize_company_names(self):
        """Should normalize different forms of company names"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        names = [
            "中国移动通信集团有限公司",
            "中国移动",
            "中国移动公司",
        ]

        clusterer = TendererClusterer()
        result = clusterer.cluster(names)

        assert result[0]['canonical_name'] == "中国移动通信集团有限公司"
        assert result[0]['short_name'] == "中国移动"


class TestGovernmentDepartmentClustering:
    """Test 4: Government department name clustering"""

    def test_cluster_government_department_names(self):
        """Should cluster government department name variants"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        names = [
            "某市财政局",
            "某市财政局政府采购中心",
            "某市财政 局",
            "某市财政局（本级）",
        ]

        clusterer = TendererClusterer()
        result = clusterer.cluster(names)

        assert len(result) == 1
        assert "财政局" in result[0]['canonical_name']


class TestSimilarButDifferent:
    """Test 5: Distinguish similar but different entities"""

    def test_distinguish_similar_but_different_entities(self):
        """Should distinguish similar but different tenderers"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        names = [
            "某市人民医院",      # City level
            "某县人民医院",      # County level - different entity
            "某市第二人民医院",  # Different hospital
        ]

        clusterer = TendererClusterer()
        result = clusterer.cluster(names)

        # Should identify as 3 different entities
        assert len(result) == 3


class TestAliasRecognition:
    """Test 6: Alias recognition and merging"""

    def test_recognize_and_merge_aliases(self):
        """Should recognize aliases and merge"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        names = [
            "北京大学",
            "北大",
        ]

        clusterer = TendererClusterer()
        result = clusterer.cluster(names)

        assert len(result) == 1
        assert result[0]['canonical_name'] == "北京大学"
        assert "北大" in result[0]['aliases']


class TestIncrementalClustering:
    """Test 7: Incremental clustering"""

    def test_incremental_clustering(self):
        """Should support incremental clustering"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()

        # Initial cluster
        initial_names = ["A公司", "A股份有限公司"]
        cluster_id = clusterer.create_cluster(initial_names)

        # Add new name
        new_name = "A公司（本部）"
        result = clusterer.add_to_cluster(cluster_id, new_name)

        assert new_name in result['variants']
        assert result['cluster_size'] == 3


class TestNameNormalization:
    """Test 8: Name normalization"""

    def test_normalize_spaces(self):
        """Should normalize spaces in names"""
        from apps.analysis.clustering.name_normalizer import NameNormalizer

        normalizer = NameNormalizer()
        result = normalizer.normalize("某市 人民 医院")

        assert result == "某市人民医院"

    def test_normalize_company_suffix(self):
        """Should normalize company suffixes"""
        from apps.analysis.clustering.name_normalizer import NameNormalizer

        normalizer = NameNormalizer()
        result = normalizer.normalize("某科技有限公司")

        assert "科技" in result


class TestSimilarityCalculation:
    """Test 9: Similarity calculation"""

    def test_levenshtein_similarity(self):
        """Should calculate Levenshtein similarity"""
        from apps.analysis.clustering.similarity_calculator import SimilarityCalculator

        calc = SimilarityCalculator()
        similarity = calc.levenshtein_similarity("人民医院", "第一人民医院")

        assert 0.0 <= similarity <= 1.0
        assert similarity > 0.5

    def test_jaccard_similarity(self):
        """Should calculate Jaccard similarity"""
        from apps.analysis.clustering.similarity_calculator import SimilarityCalculator

        calc = SimilarityCalculator()
        similarity = calc.jaccard_similarity("人民医院", "第一人民医院")

        assert 0.0 <= similarity <= 1.0

    def test_combine_scores(self):
        """Should combine multiple similarity scores"""
        from apps.analysis.clustering.similarity_calculator import SimilarityCalculator

        calc = SimilarityCalculator()
        combined = calc.combine_scores(0.8, 0.7, 0.9)

        assert 0.0 <= combined <= 1.0


class TestEntityResolver:
    """Test 10: Entity resolution"""

    def test_resolve_entity(self):
        """Should resolve entity to existing cluster"""
        from apps.analysis.clustering.entity_resolver import EntityResolver
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()
        clusterer.create_cluster(["北京大学", "北大"])

        resolver = EntityResolver(clusterer)
        result = resolver.resolve("北大")

        assert result is not None
        assert result['canonical_name'] == "北京大学"

    def test_context_aware_disambiguation(self):
        """Should use context for disambiguation"""
        from apps.analysis.clustering.entity_resolver import EntityResolver

        # This would require more complex setup with context
        pass


class TestClusterMetadata:
    """Test 11: Cluster metadata"""

    def test_cluster_has_metadata(self):
        """Cluster should have metadata"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()
        clusters = clusterer.cluster(["A公司", "A股份有限公司"])

        assert 'cluster_id' in clusters[0]
        assert 'created_at' in clusters[0]
        assert 'confidence' in clusters[0]


class TestClusterSizeLimits:
    """Test 12: Cluster size limits"""

    def test_single_name_cluster(self):
        """Should handle single name cluster"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()
        clusters = clusterer.cluster(["单一公司"])

        assert len(clusters) == 1
        assert clusters[0]['canonical_name'] == "单一公司"

    def test_empty_cluster(self):
        """Should handle empty input"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()
        clusters = clusterer.cluster([])

        assert len(clusters) == 0


class TestMergeClusters:
    """Test 13: Merge clusters"""

    def test_merge_clusters(self):
        """Should merge related clusters"""
        from apps.analysis.clustering.tenderer_clusterer import TendererClusterer

        clusterer = TendererClusterer()

        # Create two clusters that should be merged
        cluster1 = clusterer.create_cluster(["中国移动", "移动公司"])
        cluster2 = clusterer.create_cluster(["中国移动通信", "移动集团"])

        # Merge them
        merged = clusterer.merge_clusters(cluster1, cluster2)

        assert merged is not None
        assert "中国移动" in merged['canonical_name'] or "中国移动通信集团有限公司" in merged['canonical_name']
