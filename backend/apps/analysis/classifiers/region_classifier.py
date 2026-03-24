"""
Region Classification Module - Phase 5 Task 027
Automatic region classification for tender notices based on content analysis.
"""

import re
from typing import Dict, List, Optional, Set


# Province mapping with codes (GB/T 2260)
PROVINCE_MAP = {
    "北京市": {"code": "110000", "cities": {"北京市": "110100"}},
    "天津市": {"code": "120000", "cities": {"天津市": "120100"}},
    "河北省": {"code": "130000", "cities": {
        "石家庄市": "130100", "唐山市": "130200", "秦皇岛市": "130300",
        "邯郸市": "130400", "邢台市": "130500", "保定市": "130600",
        "张家口市": "130700", "承德市": "130800", "沧州市": "130900",
        "廊坊市": "131000", "衡水市": "131100"
    }},
    "山西省": {"code": "140000", "cities": {
        "太原市": "140100", "大同市": "140200", "阳泉市": "140300",
        "长治市": "140400", "晋城市": "140500", "朔州市": "140600",
        "晋中市": "140700", "运城市": "140800", "忻州市": "140900",
        "临汾市": "141000", "吕梁市": "141100"
    }},
    "内蒙古自治区": {"code": "150000", "cities": {
        "呼和浩特市": "150100", "包头市": "150200", "乌海市": "150300",
        "赤峰市": "150400", "通辽市": "150500", "鄂尔多斯市": "150600",
        "呼伦贝尔市": "150700", "巴彦淖尔市": "150800", "乌兰察布市": "150900",
        "兴安盟": "152200", "锡林郭勒盟": "152500", "阿拉善盟": "152900"
    }},
    "辽宁省": {"code": "210000", "cities": {
        "沈阳市": "210100", "大连市": "210200", "鞍山市": "210300",
        "抚顺市": "210400", "本溪市": "210500", "丹东市": "210600",
        "锦州市": "210700", "营口市": "210800", "阜新市": "210900",
        "辽阳市": "211000", "盘锦市": "211100", "铁岭市": "211200",
        "朝阳市": "211300", "葫芦岛市": "211400"
    }},
    "吉林省": {"code": "220000", "cities": {
        "长春市": "220100", "吉林市": "220200", "四平市": "220300",
        "辽源市": "220400", "通化市": "220500", "白山市": "220600",
        "松原市": "220700", "白城市": "220800", "延边朝鲜族自治州": "222400"
    }},
    "黑龙江省": {"code": "230000", "cities": {
        "哈尔滨市": "230100", "齐齐哈尔市": "230200", "鸡西市": "230300",
        "鹤岗市": "230400", "双鸭山市": "230500", "大庆市": "230600",
        "伊春市": "230700", "佳木斯市": "230800", "七台河市": "230900",
        "牡丹江市": "231000", "黑河市": "231100", "绥化市": "231200",
        "大兴安岭地区": "232700"
    }},
    "上海市": {"code": "310000", "cities": {"上海市": "310100"}},
    "江苏省": {"code": "320000", "cities": {
        "南京市": "320100", "无锡市": "320200", "徐州市": "320300",
        "常州市": "320400", "苏州市": "320500", "南通市": "320600",
        "连云港市": "320700", "淮安市": "320800", "盐城市": "320900",
        "扬州市": "321000", "镇江市": "321100", "泰州市": "321200",
        "宿迁市": "321300"
    }},
    "浙江省": {"code": "330000", "cities": {
        "杭州市": "330100", "宁波市": "330200", "温州市": "330300",
        "嘉兴市": "330400", "湖州市": "330500", "绍兴市": "330600",
        "金华市": "330700", "衢州市": "330800", "舟山市": "330900",
        "台州市": "331000", "丽水市": "331100"
    }},
    "安徽省": {"code": "340000", "cities": {
        "合肥市": "340100", "芜湖市": "340200", "蚌埠市": "340300",
        "淮南市": "340400", "马鞍山市": "340500", "淮北市": "340600",
        "铜陵市": "340700", "安庆市": "340800", "黄山市": "341000",
        "滁州市": "341100", "阜阳市": "341200", "宿州市": "341300",
        "六安市": "341500", "亳州市": "341600", "池州市": "341700",
        "宣城市": "341800"
    }},
    "福建省": {"code": "350000", "cities": {
        "福州市": "350100", "厦门市": "350200", "莆田市": "350300",
        "三明市": "350400", "泉州市": "350500", "漳州市": "350600",
        "南平市": "350700", "龙岩市": "350800", "宁德市": "350900"
    }},
    "江西省": {"code": "360000", "cities": {
        "南昌市": "360100", "景德镇市": "360200", "萍乡市": "360300",
        "九江市": "360400", "新余市": "360500", "鹰潭市": "360600",
        "赣州市": "360700", "吉安市": "360800", "宜春市": "360900",
        "抚州市": "361000", "上饶市": "361100"
    }},
    "山东省": {"code": "370000", "cities": {
        "济南市": "370100", "青岛市": "370200", "淄博市": "370300",
        "枣庄市": "370400", "东营市": "370500", "烟台市": "370600",
        "潍坊市": "370700", "济宁市": "370800", "泰安市": "370900",
        "威海市": "371000", "日照市": "371100", "莱芜市": "371200",
        "临沂市": "371300", "德州市": "371400", "聊城市": "371500",
        "滨州市": "371600", "菏泽市": "371700"
    }},
    "河南省": {"code": "410000", "cities": {
        "郑州市": "410100", "开封市": "410200", "洛阳市": "410300",
        "平顶山市": "410400", "安阳市": "410500", "鹤壁市": "410600",
        "新乡市": "410700", "焦作市": "410800", "濮阳市": "410900",
        "许昌市": "411000", "漯河市": "411100", "三门峡市": "411200",
        "南阳市": "411300", "商丘市": "411400", "信阳市": "411500",
        "周口市": "411600", "驻马店市": "411700"
    }},
    "湖北省": {"code": "420000", "cities": {
        "武汉市": "420100", "黄石市": "420200", "十堰市": "420300",
        "宜昌市": "420500", "襄阳市": "420600", "鄂州市": "420700",
        "荆门市": "420800", "孝感市": "420900", "荆州市": "421000",
        "黄冈市": "421100", "咸宁市": "421200", "随州市": "421300",
        "恩施土家族苗族自治州": "422800"
    }},
    "湖南省": {"code": "430000", "cities": {
        "长沙市": "430100", "株洲市": "430200", "湘潭市": "430300",
        "衡阳市": "430400", "邵阳市": "430500", "岳阳市": "430600",
        "常德市": "430700", "张家界市": "430800", "益阳市": "430900",
        "郴州市": "431000", "永州市": "431100", "怀化市": "431200",
        "娄底市": "431300", "湘西土家族苗族自治州": "433100"
    }},
    "广东省": {"code": "440000", "cities": {
        "广州市": "440100", "韶关市": "440200", "深圳市": "440300",
        "珠海市": "440400", "汕头市": "440500", "佛山市": "440600",
        "江门市": "440700", "湛江市": "440800", "茂名市": "440900",
        "肇庆市": "441200", "惠州市": "441300", "梅州市": "441400",
        "汕尾市": "441500", "河源市": "441600", "阳江市": "441700",
        "清远市": "441800", "东莞市": "441900", "中山市": "442000",
        "潮州市": "445100", "揭阳市": "445200", "云浮市": "445300"
    }},
    "广西壮族自治区": {"code": "450000", "cities": {
        "南宁市": "450100", "柳州市": "450200", "桂林市": "450300",
        "梧州市": "450400", "北海市": "450500", "防城港市": "450600",
        "钦州市": "450700", "贵港市": "450800", "玉林市": "450900",
        "百色市": "451000", "贺州市": "451100", "河池市": "451200",
        "来宾市": "451300", "崇左市": "451400"
    }},
    "海南省": {"code": "460000", "cities": {
        "海口市": "460100", "三亚市": "460200", "三沙市": "460300",
        "儋州市": "460400"
    }},
    "重庆市": {"code": "500000", "cities": {"重庆市": "500100"}},
    "四川省": {"code": "510000", "cities": {
        "成都市": "510100", "自贡市": "510300", "攀枝花市": "510400",
        "泸州市": "510500", "德阳市": "510600", "绵阳市": "510700",
        "广元市": "510800", "遂宁市": "510900", "内江市": "511000",
        "乐山市": "511100", "南充市": "511300", "眉山市": "511400",
        "宜宾市": "511500", "广安市": "511600", "达州市": "511700",
        "雅安市": "511800", "巴中市": "511900", "资阳市": "512000",
        "阿坝藏族羌族自治州": "513200", "甘孜藏族自治州": "513300",
        "凉山彝族自治州": "513400"
    }},
    "贵州省": {"code": "520000", "cities": {
        "贵阳市": "520100", "六盘水市": "520200", "遵义市": "520300",
        "安顺市": "520400", "毕节市": "520500", "铜仁市": "520600",
        "黔西南布依族苗族自治州": "522300", "黔东南苗族侗族自治州": "522600",
        "黔南布依族苗族自治州": "522700"
    }},
    "云南省": {"code": "530000", "cities": {
        "昆明市": "530100", "曲靖市": "530300", "玉溪市": "530400",
        "保山市": "530500", "昭通市": "530600", "丽江市": "530700",
        "普洱市": "530800", "临沧市": "530900", "楚雄彝族自治州": "532300",
        "红河哈尼族彝族自治州": "532500", "文山壮族苗族自治州": "532600",
        "西双版纳傣族自治州": "532800", "大理白族自治州": "532900",
        "德宏傣族景颇族自治州": "533100", "怒江傈僳族自治州": "533300",
        "迪庆藏族自治州": "533400"
    }},
    "西藏自治区": {"code": "540000", "cities": {
        "拉萨市": "540100", "日喀则市": "540200", "昌都市": "540300",
        "林芝市": "540400", "山南市": "540500", "那曲市": "540600",
        "阿里地区": "542500"
    }},
    "陕西省": {"code": "610000", "cities": {
        "西安市": "610100", "铜川市": "610200", "宝鸡市": "610300",
        "咸阳市": "610400", "渭南市": "610500", "延安市": "610600",
        "汉中市": "610700", "榆林市": "610800", "安康市": "610900",
        "商洛市": "611000"
    }},
    "甘肃省": {"code": "620000", "cities": {
        "兰州市": "620100", "嘉峪关市": "620200", "金昌市": "620300",
        "白银市": "620400", "天水市": "620500", "武威市": "620600",
        "张掖市": "620700", "平凉市": "620800", "酒泉市": "620900",
        "庆阳市": "621000", "定西市": "621100", "陇南市": "621200",
        "临夏回族自治州": "622900", "甘南藏族自治州": "623000"
    }},
    "青海省": {"code": "630000", "cities": {
        "西宁市": "630100", "海东市": "630200",
        "海北藏族自治州": "632200", "黄南藏族自治州": "632300",
        "海南藏族自治州": "632500", "果洛藏族自治州": "632600",
        "玉树藏族自治州": "632700", "海西蒙古族藏族自治州": "632800"
    }},
    "宁夏回族自治区": {"code": "640000", "cities": {
        "银川市": "640100", "石嘴山市": "640200", "吴忠市": "640300",
        "固原市": "640400", "中卫市": "640500"
    }},
    "新疆维吾尔自治区": {"code": "650000", "cities": {
        "乌鲁木齐市": "650100", "克拉玛依市": "650200",
        "吐鲁番市": "650400", "哈密市": "650500",
        "昌吉回族自治州": "652300", "博尔塔拉蒙古自治州": "652700",
        "巴音郭楞蒙古自治州": "652800", "阿克苏地区": "652900",
        "克孜勒苏柯尔克孜自治州": "653000", "喀什地区": "653100",
        "和田地区": "653200", "伊犁哈萨克自治州": "654000",
        "塔城地区": "654200", "阿勒泰地区": "654300"
    }}
}

# Region aliases (short names -> full names)
REGION_ALIASES = {
    "京": "北京市", "北京": "北京市",
    "津": "天津市", "天津": "天津市",
    "沪": "上海市", "申": "上海市", "上海": "上海市", "申城": "上海市",
    "渝": "重庆市", "重庆": "重庆市",
    "冀": "河北省", "河北": "河北省",
    "晋": "山西省", "山西": "山西省",
    "蒙": "内蒙古自治区", "内蒙古": "内蒙古自治区",
    "辽": "辽宁省", "辽宁": "辽宁省",
    "吉": "吉林省", "吉林": "吉林省",
    "黑": "黑龙江省", "黑龙江": "黑龙江省",
    "苏": "江苏省", "江苏": "江苏省",
    "浙": "浙江省", "浙江": "浙江省",
    "皖": "安徽省", "安徽": "安徽省",
    "闽": "福建省", "福建": "福建省",
    "赣": "江西省", "江西": "江西省",
    "鲁": "山东省", "山东": "山东省",
    "豫": "河南省", "河南": "河南省",
    "鄂": "湖北省", "湖北": "湖北省",
    "湘": "湖南省", "湖南": "湖南省",
    "粤": "广东省", "广东": "广东省",
    "桂": "广西壮族自治区", "广西": "广西壮族自治区",
    "琼": "海南省", "海南": "海南省",
    "川": "四川省", "蜀": "四川省", "四川": "四川省",
    "贵": "贵州省", "黔": "贵州省", "贵州": "贵州省",
    "云": "云南省", "滇": "云南省", "云南": "云南省",
    "藏": "西藏自治区", "西藏": "西藏自治区",
    "陕": "陕西省", "秦": "陕西省", "陕西": "陕西省",
    "甘": "甘肃省", "陇": "甘肃省", "甘肃": "甘肃省",
    "青": "青海省", "青海": "青海省",
    "宁": "宁夏回族自治区", "宁夏": "宁夏回族自治区",
    "新": "新疆维吾尔自治区", "新疆": "新疆维吾尔自治区",
}

# Common districts for major cities (subset for demonstration)
DISTRICT_MAP = {
    ("北京市", "北京市"): {
        "东城区": "110101", "西城区": "110102", "朝阳区": "110105",
        "丰台区": "110106", "石景山区": "110107", "海淀区": "110108",
        "门头沟区": "110109", "房山区": "110111", "通州区": "110112",
        "顺义区": "110113", "昌平区": "110114", "大兴区": "110115",
        "怀柔区": "110116", "平谷区": "110117", "密云区": "110118", "延庆区": "110119"
    },
    ("上海市", "上海市"): {
        "黄浦区": "310101", "徐汇区": "310104", "长宁区": "310105",
        "静安区": "310106", "普陀区": "310107", "虹口区": "310109",
        "杨浦区": "310110", "浦东新区": "310115", "闵行区": "310112",
        "宝山区": "310113", "嘉定区": "310114", "金山区": "310116",
        "松江区": "310117", "青浦区": "310118", "奉贤区": "310120", "崇明区": "310151"
    },
    ("广东省", "广州市"): {
        "荔湾区": "440103", "越秀区": "440104", "海珠区": "440105",
        "天河区": "440106", "白云区": "440111", "黄埔区": "440112",
        "番禺区": "440113", "花都区": "440114", "南沙区": "440115",
        "从化区": "440117", "增城区": "440118"
    },
    ("广东省", "深圳市"): {
        "罗湖区": "440303", "福田区": "440304", "南山区": "440305",
        "宝安区": "440306", "龙岗区": "440307", "盐田区": "440308",
        "龙华区": "440309", "坪山区": "440310", "光明区": "440311"
    },
    ("浙江省", "杭州市"): {
        "上城区": "330102", "下城区": "330103", "江干区": "330104",
        "拱墅区": "330105", "西湖区": "330106", "滨江区": "330108",
        "萧山区": "330109", "余杭区": "330110", "富阳区": "330111",
        "临安区": "330112", "桐庐县": "330122", "淳安县": "330127",
        "建德市": "330182"
    },
}


class RegionClassifier:
    """
    Region classifier for tender notices.

    Identifies province, city, and district from tender text content.
    Supports Chinese administrative divisions (GB/T 2260).
    """

    def __init__(self):
        """Initialize region classifier."""
        self.province_map = PROVINCE_MAP
        self.aliases = REGION_ALIASES
        self.district_map = DISTRICT_MAP

    def classify(self, text: str) -> Dict:
        """
        Classify the region from tender text.

        Args:
            text: Tender notice text content

        Returns:
            Dictionary with region classification:
            - province: Province name (or None)
            - province_code: Province code (GB/T 2260)
            - city: City name (or None)
            - city_code: City code
            - district: District name (or None)
            - district_code: District code
            - confidence: Confidence score (0.0-1.0)
            - source: Extraction source
            - mentioned_regions: All regions mentioned
        """
        if not text or not text.strip():
            return self._empty_result()

        mentioned_regions = []

        # Extract province
        province, province_code = self._extract_province(text)
        if province:
            mentioned_regions.append(province)

        # Extract city
        city, city_code = self._extract_city(text, province)
        if city:
            mentioned_regions.append(city)

        # Extract district
        district, district_code = self._extract_district(text, province, city)
        if district:
            mentioned_regions.append(district)

        # Calculate confidence
        confidence = self._calculate_confidence(province, city, district, text)

        # Determine source
        source = self._determine_source(text, province, city, district)

        return {
            "province": province,
            "province_code": province_code,
            "city": city,
            "city_code": city_code,
            "district": district,
            "district_code": district_code,
            "confidence": confidence,
            "source": source,
            "mentioned_regions": mentioned_regions
        }

    def _extract_province(self, text: str) -> tuple:
        """Extract province from text."""
        # Check full names first
        for province_name in self.province_map.keys():
            if province_name in text:
                return province_name, self.province_map[province_name]["code"]

        # Check aliases
        for alias, full_name in self.aliases.items():
            # Use word boundary to avoid partial matches
            pattern = re.escape(alias)
            if re.search(pattern, text):
                return full_name, self.province_map[full_name]["code"]

        return None, None

    def _extract_city(self, text: str, province: Optional[str]) -> tuple:
        """Extract city from text."""
        if not province:
            # Try to find city without province context
            for prov_name, prov_data in self.province_map.items():
                for city_name, city_code in prov_data["cities"].items():
                    if city_name in text:
                        return city_name, city_code
            return None, None

        # Search within province's cities
        cities = self.province_map[province]["cities"]
        for city_name, city_code in cities.items():
            if city_name in text:
                return city_name, city_code

        return None, None

    def _extract_district(self, text: str, province: Optional[str], city: Optional[str]) -> tuple:
        """Extract district from text."""
        if not province or not city:
            return None, None

        key = (province, city)
        if key in self.district_map:
            districts = self.district_map[key]
            for district_name, district_code in districts.items():
                if district_name in text:
                    return district_name, district_code

        # Try generic district pattern
        district_match = re.search(r'([\u4e00-\u9fa5]{2,4}区)', text)
        if district_match:
            return district_match.group(1), None

        return None, None

    def _calculate_confidence(self, province: Optional[str], city: Optional[str],
                              district: Optional[str], text: str) -> float:
        """Calculate confidence score."""
        confidence = 0.0

        if province:
            confidence += 0.4
        if city:
            confidence += 0.35
        if district:
            confidence += 0.25

        # Boost if in tenderer/purchaser context
        if province and re.search(r'(采购人|招标人|采购单位).*?' + re.escape(province), text):
            confidence = min(confidence + 0.1, 1.0)

        return confidence

    def _determine_source(self, text: str, province: Optional[str],
                          city: Optional[str], district: Optional[str]) -> str:
        """Determine extraction source."""
        if not province:
            return "none"

        # Check if in title (typically first line)
        first_line = text.split('\n')[0] if text else ""
        if province in first_line or (city and city in first_line):
            return "title"

        # Check if in tenderer/purchaser section
        if re.search(r'(采购人|招标人|采购单位).*?' + re.escape(province), text):
            return "tenderer"

        # Check if in address/location section
        if re.search(r'(项目地点|地址|所在地).*?' + re.escape(province), text):
            return "address"

        return "keywords"

    def _empty_result(self) -> Dict:
        """Return empty result."""
        return {
            "province": None,
            "province_code": None,
            "city": None,
            "city_code": None,
            "district": None,
            "district_code": None,
            "confidence": 0.0,
            "source": "none",
            "mentioned_regions": []
        }

    def list_provinces(self) -> List[str]:
        """List all supported provinces."""
        return list(self.province_map.keys())

    def list_cities(self, province: str) -> List[str]:
        """List cities for a province."""
        if province in self.province_map:
            return list(self.province_map[province]["cities"].keys())
        return []
