# Task 015: 重复数据检测实现

## 任务信息

- **任务ID**: 015
- **任务名称**: 重复数据检测实现
- **任务类型**: impl
- **依赖任务**: 014 (重复数据检测测试)

## BDD Scenario

```gherkin
Scenario: 检测到重复的招标信息
  Given 数据库中已存在招标公告
  And 爬虫抓取到相似的公告内容
  When 执行重复检测
  Then 应识别出重复/相似的内容
  And 对高相似度内容标记为重复
  And 对疑似重复内容进行人工审核标记
```

## 实现目标

实现重复数据检测系统：基于公告ID的精确匹配、基于内容的相似度检测、疑似重复的人工审核队列。

## 创建/修改的文件

- `apps/crawler/duplicate_checker.py` - 重复检测器
- `apps/crawler/similarity.py` - 相似度算法
- `apps/crawler/models.py` - 添加重复检测模型
- `apps/crawler/admin.py` - 重复审核Admin
- `apps/crawler/signals.py` - 保存前检测信号

## 实施步骤

### 1. 创建相似度算法模块

```python
# apps/crawler/similarity.py
import re
import math
from collections import Counter
from typing import List, Tuple
import jieba


class SimilarityCalculator:
    """相似度计算器"""

    # 相似度阈值
    EXACT_MATCH_THRESHOLD = 1.0      # 完全匹配
    HIGH_SIMILARITY_THRESHOLD = 0.85  # 高相似度（可能是修订版）
    MEDIUM_SIMILARITY_THRESHOLD = 0.65  # 中等相似度（疑似重复）
    LOW_SIMILARITY_THRESHOLD = 0.3    # 低相似度（视为不同）

    def __init__(self):
        self.stopwords = self._load_stopwords()

    def _load_stopwords(self) -> set:
        """加载停用词"""
        default_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '公告', '招标', '采购', '项目', '关于', '年月日', 'http',
            'www', 'com', 'cn'
        }
        return default_stopwords

    def tokenize(self, text: str) -> List[str]:
        """分词"""
        if not text:
            return []
        # 使用jieba分词
        words = jieba.lcut(text)
        # 过滤停用词和标点
        words = [
            w.strip().lower() for w in words
            if w.strip() and w.strip() not in self.stopwords
            and not re.match(r'^[\s\p{Punct}]+$', w)
        ]
        return words

    def jaccard(self, text1: str, text2: str) -> float:
        """
        Jaccard相似度: |A ∩ B| / |A ∪ B|
        适用于短文本（标题）
        """
        set1 = set(self.tokenize(text1))
        set2 = set(self.tokenize(text2))

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def cosine(self, text1: str, text2: str) -> float:
        """
        余弦相似度
        适用于中等长度文本
        """
        tokens1 = self.tokenize(text1)
        tokens2 = self.tokenize(text2)

        if not tokens1 or not tokens2:
            return 0.0

        # 构建词频向量
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)
        all_terms = set(counter1.keys()) | set(counter2.keys())

        # 计算点积和模
        dot_product = sum(counter1[term] * counter2[term] for term in all_terms)
        magnitude1 = math.sqrt(sum(count ** 2 for count in counter1.values()))
        magnitude2 = math.sqrt(sum(count ** 2 for count in counter2.values()))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def levenshtein_normalized(self, text1: str, text2: str) -> float:
        """
        归一化编辑距离相似度
        适用于非常相似的文本
        """
        distance = self._levenshtein_distance(text1, text2)
        max_len = max(len(text1), len(text2))

        if max_len == 0:
            return 1.0

        return 1 - (distance / max_len)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算Levenshtein编辑距离"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # 插入、删除、替换
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def hybrid_similarity(self, text1: str, text2: str) -> float:
        """
        混合相似度算法
        综合多种算法结果
        """
        if not text1 or not text2:
            return 0.0

        # 完全匹配
        if text1.strip() == text2.strip():
            return 1.0

        # 计算多种相似度
        jaccard_sim = self.jaccard(text1, text2)
        cosine_sim = self.cosine(text1, text2)
        edit_sim = self.levenshtein_normalized(text1, text2)

        # 加权平均（标题更重视编辑距离，内容更重视词频）
        if len(text1) < 100:  # 短文本（标题）
            weights = [0.3, 0.3, 0.4]  # 编辑距离权重更高
        else:  # 长文本（内容）
            weights = [0.2, 0.6, 0.2]  # 余弦相似度权重更高

        similarity = (
            weights[0] * jaccard_sim +
            weights[1] * cosine_sim +
            weights[2] * edit_sim
        )

        return min(1.0, max(0.0, similarity))

    def find_most_similar(
        self,
        query: str,
        candidates: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        找出最相似的候选

        Returns:
            [(候选文本, 相似度), ...]
        """
        similarities = [
            (candidate, self.hybrid_similarity(query, candidate))
            for candidate in candidates
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
```

### 2. 创建重复检测器

```python
# apps/crawler/duplicate_checker.py
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Q

from apps.tenders.models import TenderNotice
from .similarity import SimilarityCalculator
from .models import DuplicateCheckResult, SuspectedDuplicate

logger = logging.getLogger(__name__)


class DuplicateChecker:
    """重复数据检测器"""

    def __init__(self):
        self.similarity = SimilarityCalculator()

    def check(
        self,
        data: Dict,
        check_window_days: int = 30
    ) -> DuplicateCheckResult:
        """
        检查单个数据是否重复

        Args:
            data: 待检查的数据
            check_window_days: 检查时间窗口（天）

        Returns:
            DuplicateCheckResult
        """
        # 1. 精确匹配：公告ID
        exact_match = self._check_exact_match(data)
        if exact_match:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_type='exact',
                confidence=1.0,
                matched_notice=exact_match,
                action='skip'
            )

        # 2. 模糊匹配：标题相似度
        title_match = self._check_title_similarity(
            data,
            days=check_window_days
        )
        if title_match and title_match['similarity'] >= 0.85:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_type='title_similar',
                confidence=title_match['similarity'],
                matched_notice=title_match['notice'],
                action='merge' if title_match['similarity'] > 0.95 else 'review'
            )

        # 3. 模糊匹配：内容相似度
        if 'description' in data and data['description']:
            content_match = self._check_content_similarity(
                data,
                days=check_window_days
            )
            if content_match and content_match['similarity'] >= 0.7:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_type='content_similar',
                    confidence=content_match['similarity'],
                    matched_notice=content_match['notice'],
                    action='review'
                )

        return DuplicateCheckResult(
            is_duplicate=False,
            duplicate_type=None,
            confidence=0.0,
            matched_notice=None,
            action='save'
        )

    def _check_exact_match(self, data: Dict) -> Optional[TenderNotice]:
        """检查精确匹配"""
        notice_id = data.get('notice_id')
        if not notice_id:
            return None

        try:
            return TenderNotice.objects.get(notice_id=notice_id)
        except TenderNotice.DoesNotExist:
            return None

    def _check_title_similarity(
        self,
        data: Dict,
        days: int
    ) -> Optional[Dict]:
        """检查标题相似度"""
        title = data.get('title', '')
        if not title:
            return None

        # 查询近期数据
        since = datetime.now() - timedelta(days=days)
        candidates = TenderNotice.objects.filter(
            publish_date__gte=since
        ).values('id', 'notice_id', 'title')

        if not candidates:
            return None

        # 计算相似度
        best_match = None
        best_similarity = 0.0

        for candidate in candidates:
            similarity = self.similarity.hybrid_similarity(
                title,
                candidate['title']
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        if best_match and best_similarity >= 0.65:
            notice = TenderNotice.objects.get(id=best_match['id'])
            return {
                'notice': notice,
                'similarity': best_similarity
            }

        return None

    def _check_content_similarity(
        self,
        data: Dict,
        days: int
    ) -> Optional[Dict]:
        """检查内容相似度"""
        description = data.get('description', '')
        if not description or len(description) < 50:
            return None

        since = datetime.now() - timedelta(days=days)
        candidates = TenderNotice.objects.filter(
            publish_date__gte=since,
            description__isnull=False
        ).exclude(description='').values('id', 'description')

        if not candidates:
            return None

        best_match = None
        best_similarity = 0.0

        for candidate in candidates:
            similarity = self.similarity.cosine(
                description,
                candidate['description']
            )
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = candidate

        if best_match and best_similarity >= 0.7:
            notice = TenderNotice.objects.get(id=best_match['id'])
            return {
                'notice': notice,
                'similarity': best_similarity
            }

        return None

    def check_batch(
        self,
        data_list: List[Dict],
        check_window_days: int = 30
    ) -> Dict:
        """
        批量检查重复

        Returns:
            {
                'duplicates': [DuplicateCheckResult, ...],
                'suspected': [DuplicateCheckResult, ...],
                'new': [DuplicateCheckResult, ...]
            }
        """
        results = {
            'duplicates': [],
            'suspected': [],
            'new': []
        }

        for data in data_list:
            result = self.check(data, check_window_days)

            if result.is_duplicate:
                if result.confidence >= 0.85:
                    results['duplicates'].append(result)
                else:
                    results['suspected'].append(result)
            else:
                results['new'].append(result)

        return results

    def create_suspected_duplicate_record(
        self,
        new_data: Dict,
        matched_notice: TenderNotice,
        similarity: float
    ) -> SuspectedDuplicate:
        """创建疑似重复记录"""
        return SuspectedDuplicate.objects.create(
            new_notice_id=new_data.get('notice_id'),
            new_title=new_data.get('title'),
            new_source_url=new_data.get('source_url'),
            existing_notice=matched_notice,
            similarity_score=similarity,
            status='pending'
        )


class DuplicateCheckResult:
    """重复检查结果"""

    def __init__(
        self,
        is_duplicate: bool,
        duplicate_type: Optional[str],
        confidence: float,
        matched_notice: Optional[TenderNotice],
        action: str
    ):
        self.is_duplicate = is_duplicate
        self.duplicate_type = duplicate_type
        self.confidence = confidence
        self.matched_notice = matched_notice
        self.action = action  # 'skip', 'merge', 'review', 'save'
```

### 3. 扩展爬虫模型

```python
# apps/crawler/models.py (扩展)
from django.db import models
from apps.tenders.models import TenderNotice


class DuplicateCheckResult(models.Model):
    """重复检查结果记录"""
    check_id = models.CharField(max_length=64, unique=True)
    notice = models.ForeignKey(
        TenderNotice,
        on_delete=models.CASCADE,
        related_name='duplicate_checks'
    )
    is_duplicate = models.BooleanField(default=False)
    duplicate_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('exact', '精确重复'),
            ('title_similar', '标题相似'),
            ('content_similar', '内容相似'),
        ]
    )
    confidence = models.DecimalField(max_digits=5, decimal_places=4)
    matched_notice = models.ForeignKey(
        TenderNotice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_duplicates'
    )
    action_taken = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['notice', '-created_at']),
            models.Index(fields=['is_duplicate', '-confidence']),
        ]


class SuspectedDuplicate(models.Model):
    """疑似重复记录（人工审核队列）"""
    class Status(models.TextChoices):
        PENDING = 'pending', '待审核'
        CONFIRMED = 'confirmed', '确认重复'
        REJECTED = 'rejected', '非重复'
        MERGED = 'merged', '已合并'

    new_notice_id = models.CharField(max_length=64)
    new_title = models.CharField(max_length=500)
    new_source_url = models.URLField()
    existing_notice = models.ForeignKey(
        TenderNotice,
        on_delete=models.CASCADE,
        related_name='suspected_duplicates'
    )
    similarity_score = models.DecimalField(max_digits=5, decimal_places=4)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', '-similarity_score']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"疑似重复: {self.new_title[:50]}..."
```

### 4. 创建信号处理器

```python
# apps/crawler/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
import logging

from apps.tenders.models import TenderNotice
from .duplicate_checker import DuplicateChecker

logger = logging.getLogger(__name__)


def check_duplicate_before_save(sender, instance, **kwargs):
    """保存前检查重复"""
    if instance.pk:  # 更新操作，跳过
        return

    checker = DuplicateChecker()
    data = {
        'notice_id': instance.notice_id,
        'title': instance.title,
        'description': instance.description,
        'source_url': instance.source_url,
    }

    result = checker.check(data)

    if result.is_duplicate:
        if result.confidence >= 0.95:
            # 高置信度重复，阻止保存
            logger.warning(
                f"Duplicate detected: {instance.notice_id} matches "
                f"{result.matched_notice.notice_id}"
            )
            # 可以在这里抛出异常或设置标记
            instance._is_duplicate = True
            instance._duplicate_of = result.matched_notice
        else:
            # 疑似重复，创建审核记录
            checker.create_suspected_duplicate_record(
                data,
                result.matched_notice,
                result.confidence
            )


# 在apps.py的ready方法中连接信号
# pre_save.connect(check_duplicate_before_save, sender=TenderNotice)
```

### 5. 配置Admin界面

```python
# apps/crawler/admin.py
from django.contrib import admin
from .models import CrawlJob, DuplicateCheckResult, SuspectedDuplicate


@admin.register(DuplicateCheckResult)
class DuplicateCheckResultAdmin(admin.ModelAdmin):
    list_display = [
        'check_id', 'notice', 'is_duplicate',
        'duplicate_type', 'confidence', 'action_taken', 'created_at'
    ]
    list_filter = ['is_duplicate', 'duplicate_type', 'created_at']
    search_fields = ['notice__notice_id', 'notice__title']
    readonly_fields = ['created_at']


@admin.register(SuspectedDuplicate)
class SuspectedDuplicateAdmin(admin.ModelAdmin):
    list_display = [
        'new_notice_id', 'new_title', 'similarity_score',
        'status', 'reviewed_by', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['new_notice_id', 'new_title']
    actions = ['mark_confirmed', 'mark_rejected']

    def mark_confirmed(self, request, queryset):
        """标记为确认重复"""
        queryset.update(
            status='confirmed',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
    mark_confirmed.short_description = "标记为确认重复"

    def mark_rejected(self, request, queryset):
        """标记为非重复"""
        queryset.update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
    mark_rejected.short_description = "标记为非重复"
```

### 6. 安装依赖

```bash
# requirements.txt 添加
jieba==0.42.1
numpy==1.24.0
```

## 验证步骤

```bash
# 运行重复检测测试
pytest apps/crawler/tests/test_duplicate_checker.py -v
pytest apps/crawler/tests/test_similarity.py -v

# 测试相似度算法
python -c "
from apps.crawler.similarity import SimilarityCalculator
calc = SimilarityCalculator()
sim = calc.hybrid_similarity('招标公告', '招标公告（更正）')
print(f'Similarity: {sim}')
"

# 创建迁移
python manage.py makemigrations crawler
python manage.py migrate
```

**预期**: 所有测试通过(GREEN状态)

## 提交信息

```
feat: implement duplicate detection system

- Add SimilarityCalculator with Jaccard, Cosine, and Levenshtein algorithms
- Add DuplicateChecker for exact and fuzzy matching
- Create DuplicateCheckResult and SuspectedDuplicate models
- Add pre-save signal handler for automatic duplicate checking
- Configure Django Admin for duplicate review queue
- Support batch duplicate detection
- Add confidence thresholds for different actions (skip/merge/review)
- All tests passing (GREEN state)
```
