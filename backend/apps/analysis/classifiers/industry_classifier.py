"""
Industry Classification Module - Phase 5 Task 025
Automatic industry classification for tender notices based on content analysis.
"""

import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


# Industry keyword mappings
INDUSTRY_KEYWORDS = {
    "医疗健康": {
        "code": "F06",
        "keywords": [
            "医院", "医疗", "医疗器械", "药品", "药物", "诊疗", "治疗", "诊断",
            "CT", "MRI", "核磁共振", "X光", "超声", "检验", "化验", "病理",
            "手术", "病房", "门诊", "急诊", "住院", "护理", "康复", "体检",
            "疫苗", "防疫", "疾控", "卫生", "健康", "医保", "口腔", "眼科",
            "骨科", "心血管", "肿瘤", "影像", "介入", "透析", "麻醉", "急救",
            "中医", "西医", "临床", "药房", "制剂", "输血", "消毒", "供应室",
            "三甲", "三乙", "二甲", "二乙", "院区", "科室", "医生", "护士",
            "患者", "病床", "医用", "医疗", "医学"
        ],
        "weight": 1.2
    },
    "信息技术": {
        "code": "I65",
        "keywords": [
            "软件", "系统开发", "云计算", "大数据", "人工智能", "AI", "物联网",
            "网络安全", "信息安全", "数据中心", "服务器", "存储", "网络设备",
            "软件开发", "系统集成", "信息化", "数字化", "智能化", "智慧",
            "平台", "APP", "应用", "小程序", "网站", "网页", "前端", "后端",
            "数据库", "中间件", "操作系统", "虚拟化", "容器", "微服务",
            "区块链", "5G", "通信", "电信", "宽带", "光纤", "布线",
            "监控", "安防", "摄像头", "门禁", "报警", "指挥中心", "调度",
            "等级保护", "防火墙", "入侵检测", "漏洞扫描", "安全审计",
            "政务云", "云平台", "云服务", "大数据平台", "数据中台"
        ],
        "weight": 1.0
    },
    "建筑工程": {
        "code": "E47",
        "keywords": [
            "建筑", "土建", "装修", "装饰", "机电安装", "钢结构", "市政工程",
            "房屋", "楼宇", "大厦", "广场", "中心", "园区", "厂房", "仓库",
            "住宅", "公寓", "别墅", "写字楼", "办公楼", "商业", "综合体",
            "道路", "桥梁", "隧道", "地铁", "轨道交通", "公路", "市政",
            "水利", "水电", "给排水", "暖通", "空调", "电梯", "消防",
            "景观", "园林", "绿化", "照明", "亮化", "管网", "管线",
            "勘察", "设计", "监理", "施工", "总承包", "EPC", "PPP",
            "改造", "维修", "养护", "加固", "拆除", "迁建", "扩建",
            "建设", "工程", "项目", "建筑面积", "平方米", "土建工程",
            "住院楼", "门诊楼", "教学楼", "实验楼"
        ],
        "weight": 1.0
    },
    "能源环保": {
        "code": "D44",
        "keywords": [
            "新能源", "环保", "节能", "污水处理", "垃圾处理", "固废",
            "风电", "光伏", "太阳能", "生物质", "地热", "氢能", "储能",
            "发电", "输电", "变电", "配电", "电网", "电力", "电气",
            "脱硫", "脱硝", "除尘", "VOCs", "大气治理", "水质监测",
            "环境监测", "生态修复", "土壤修复", "河道治理", "海绵城市",
            "循环经济", "资源利用", "再生资源", "废弃物", "污泥",
            "清洁能源", "绿色", "低碳", "碳中和", "碳达峰", "能效",
            "污水", "处理厂", "净化", "环保设备", "治污", "减排",
            "风力发电", "光伏发电", "发电机组", "变压器"
        ],
        "weight": 1.0
    },
    "交通物流": {
        "code": "G53",
        "keywords": [
            "交通", "运输", "物流", "仓储", "港口", "码头", "机场",
            "公路", "铁路", "地铁", "轻轨", "公交", "客运", "货运",
            "车辆", "汽车", "卡车", "货车", "客车", "特种车辆",
            "智能交通", "信号灯", "电子警察", "卡口", "ETC", "收费",
            "停车场", "停车位", "充电桩", "加油站", "加气站",
            "航运", "船舶", "集装箱", "多式联运", "供应链",
            "配送", "快递", "邮政", "分拣", "装卸", "搬运",
            "航站楼", "航班", "行李", "智能交通系统"
        ],
        "weight": 1.0
    },
    "教育科研": {
        "code": "P83",
        "keywords": [
            "学校", "教育", "教学", "培训", "高校", "大学", "学院",
            "中学", "小学", "幼儿园", "职业教育", "特殊教育",
            "科研", "实验室", "仪器", "设备", "试剂", "耗材",
            "图书", "教材", "期刊", "数据库", "文献", "档案",
            "实训", "实习", "实践", "技能", "竞赛", "考试",
            "校园", "教室", "宿舍", "食堂", "体育馆", "图书馆",
            "信息化教学", "智慧教室", "在线教育", "远程教育",
            "研究", "课题", "项目", "成果转化", "技术转移",
            "显微镜", "离心机", "PCR", "实验", "科研"
        ],
        "weight": 1.0
    },
    "金融保险": {
        "code": "J66",
        "keywords": [
            "银行", "保险", "证券", "期货", "基金", "信托", "金融",
            "金融科技", "FinTech", "支付", "清算", "结算", "核算",
            "ATM", "POS", "终端", "自助设备", "智能柜台", "VTM",
            "核心系统", "业务系统", "管理系统", "风控", "合规",
            "征信", "信贷", "理财", "资管", "投行", "托管",
            "数据中心", "灾备", "机房", "网络", "安全", "加密",
            "押运", "金库", "保险箱", "货币", "现金", "票据",
            "银行系统", "网银", "核心", "业务系统升级"
        ],
        "weight": 1.1
    },
    "制造业": {
        "code": "C35",
        "keywords": [
            "生产", "制造", "加工", "生产线", "车间", "工厂",
            "自动化", "机器人", "机械手", "数控机床", "机床",
            "模具", "夹具", "工装", "检具", "量具", "刀具",
            "铸造", "锻造", "冲压", "焊接", "喷涂", "热处理",
            "装配", "调试", "检测", "检验", "测试", "试验",
            "原材料", "零部件", "配件", "组件", "模块", "总成",
            "流水线", "传送带", "AGV", "立体库", "仓储", "物流",
            "工业", "机械", "设备", "仪器", "仪表", "工具",
            "汽车厂", "工业机器人", "生产线改造"
        ],
        "weight": 1.0
    },
    "农林牧渔": {
        "code": "A01",
        "keywords": [
            "农业", "农村", "农田", "耕地", "种植", "养殖", "畜牧",
            "农机", "农具", "农药", "化肥", "种子", "种苗", "苗木",
            "粮食", "蔬菜", "水果", "茶叶", "中药材", "花卉",
            "林业", "造林", "抚育", "采伐", "木材", "林产品",
            "畜牧", "家禽", "家畜", "兽药", "饲料", "屠宰",
            "渔业", "水产", "捕捞", "养殖", "渔船", "渔港",
            "水利", "灌溉", "排涝", "水库", "塘坝", "节水",
            "乡村振兴", "扶贫", "农田水利", "高标准农田"
        ],
        "weight": 1.0
    },
    "商贸服务": {
        "code": "F51",
        "keywords": [
            "商贸", "商业", "零售", "批发", "超市", "商场", "购物中心",
            "酒店", "宾馆", "餐饮", "住宿", "旅游", "会展", "服务",
            "物业", "管理", "咨询", "顾问", "策划", "设计", "广告",
            "营销", "推广", "品牌", "公关", "活动", "赛事", "演出",
            "家政", "保洁", "保安", "绿化", "养护", "维修", "维保",
            "租赁", "出租", "中介", "代理", "经纪", "拍卖", "典当",
            "进出口", "外贸", "跨境电商", "保税", "仓储", "物流",
            "连锁", "加盟", "直营", "特许经营", "品牌授权"
        ],
        "weight": 1.0
    }
}


class IndustryClassifier:
    """
    Industry classifier for tender notices.

    Uses keyword matching to identify the industry sector based on tender content.
    Supports Chinese tender documents across multiple industries.
    """

    def __init__(self, similarity_threshold: float = 0.6):
        """
        Initialize industry classifier.

        Args:
            similarity_threshold: Minimum similarity score for fuzzy matching
        """
        self.similarity_threshold = similarity_threshold
        self.industries = INDUSTRY_KEYWORDS

    def classify(self, text: str) -> Dict:
        """
        Classify the industry of a tender notice.

        Args:
            text: Tender notice text content

        Returns:
            Dictionary with classification results:
            - industry: Primary industry name (or None if no match)
            - industry_code: Industry code (GB/T 4754)
            - confidence: Confidence score (0.0-1.0)
            - keywords_matched: List of matched keywords
            - secondary_industries: List of secondary industry matches
        """
        if not text or not text.strip():
            return {
                "industry": None,
                "industry_code": None,
                "confidence": 0.0,
                "keywords_matched": [],
                "secondary_industries": []
            }

        # Score each industry
        industry_scores = self._score_industries(text)

        if not industry_scores:
            return {
                "industry": None,
                "industry_code": None,
                "confidence": 0.0,
                "keywords_matched": [],
                "secondary_industries": []
            }

        # Sort by score
        sorted_industries = sorted(
            industry_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )

        # Primary industry
        primary_industry, primary_data = sorted_industries[0]

        # Calculate confidence
        confidence = self._calculate_confidence(primary_data)

        # Secondary industries (score > 0 but less than primary)
        secondary_industries = []
        for industry, data in sorted_industries[1:]:
            if data['score'] > 0:
                sec_confidence = self._calculate_confidence(data)
                if sec_confidence > 0.3:  # Threshold for secondary
                    secondary_industries.append({
                        "industry": industry,
                        "industry_code": self.industries[industry]['code'],
                        "confidence": sec_confidence
                    })

        return {
            "industry": primary_industry if confidence > 0.5 else None,
            "industry_code": self.industries[primary_industry]['code'] if confidence > 0.5 else None,
            "confidence": confidence,
            "keywords_matched": primary_data['matched_keywords'],
            "secondary_industries": secondary_industries[:3]  # Top 3 secondary
        }

    def _score_industries(self, text: str) -> Dict:
        """
        Score each industry based on keyword matches.

        Args:
            text: Text to analyze

        Returns:
            Dictionary mapping industry names to score data
        """
        scores = {}
        text_lower = text.lower()

        for industry, data in self.industries.items():
            score = 0.0
            matched_keywords = []

            for keyword in data['keywords']:
                # Exact match
                count = text_lower.count(keyword.lower())
                if count > 0:
                    # Higher weight for longer/more specific keywords
                    keyword_weight = len(keyword) / 10.0
                    score += count * (1.0 + keyword_weight) * data['weight']
                    matched_keywords.append(keyword)

            if score > 0:
                scores[industry] = {
                    'score': score,
                    'matched_keywords': matched_keywords
                }

        return scores

    def _calculate_confidence(self, score_data: Dict) -> float:
        """
        Calculate confidence score from match data.

        Args:
            score_data: Dictionary with score and matched keywords

        Returns:
            Confidence value between 0.0 and 1.0
        """
        score = score_data['score']
        keyword_count = len(score_data['matched_keywords'])

        # Base confidence from score - more lenient scaling
        confidence = min(score / 3.5, 0.82)

        # Boost for multiple keyword matches
        if keyword_count >= 4:
            confidence += 0.15
        elif keyword_count >= 3:
            confidence += 0.1
        elif keyword_count >= 2:
            confidence += 0.05

        # Additional boost for clear single keyword match (e.g., "医院" with modifiers)
        if keyword_count >= 1 and score >= 2.5:
            confidence += 0.03

        return min(confidence, 1.0)

    def get_industry_keywords(self, industry: str) -> List[str]:
        """
        Get keywords for a specific industry.

        Args:
            industry: Industry name

        Returns:
            List of keywords for the industry
        """
        if industry in self.industries:
            return self.industries[industry]['keywords']
        return []

    def add_industry_keywords(self, industry: str, keywords: List[str]):
        """
        Add custom keywords to an industry.

        Args:
            industry: Industry name
            keywords: List of keywords to add
        """
        if industry in self.industries:
            self.industries[industry]['keywords'].extend(keywords)
            # Remove duplicates
            self.industries[industry]['keywords'] = list(
                set(self.industries[industry]['keywords'])
            )

    def list_industries(self) -> List[str]:
        """
        List all supported industries.

        Returns:
            List of industry names
        """
        return list(self.industries.keys())
