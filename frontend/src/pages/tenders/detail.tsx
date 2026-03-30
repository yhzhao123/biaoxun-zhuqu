import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Tag, Button, Space, Row, Col, Divider, List, Badge } from 'antd';
import { ArrowLeftOutlined, StarOutlined, ShareAltOutlined } from '@ant-design/icons';
import { getTenderDetail } from '@/api/analytics';
import { Tender } from '@/types';
import dayjs from 'dayjs';

const TenderDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tender, setTender] = useState<Tender | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchTenderDetail(id);
    }
  }, [id]);

  const fetchTenderDetail = async (tenderId: string) => {
    setLoading(true);
    try {
      const response = await getTenderDetail(tenderId);
      if (response.data) {
        setTender(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch tender detail:', error);
    } finally {
      setLoading(false);
    }
  };

  const mockTender: Tender = {
    id: id || '1',
    title: '中国移动通信设备采购项目',
    tenderer: '中国移动通信集团北京有限公司',
    region: '北京市',
    industry: '通信服务',
    amount: 5000000,
    publishDate: '2024-03-15',
    deadlineDate: '2024-04-15',
    status: 'bidding',
    classification: {
      tendererCategory: { normalized: '中国移动', type: '国有企业', confidence: 0.95 },
      regionCategory: { normalized: '北京', zone: '华北', confidence: 0.98 },
      industryCategory: { normalized: '通信服务', code: 'I63', confidence: 0.92 },
      amountCategory: { range: '100-500万', level: 'medium', confidence: 0.88 },
    },
    opportunityScore: {
      totalScore: 85,
      level: 'high',
      factors: {
        amountScore: 22,
        competitionScore: 18,
        timelineScore: 16,
        relevanceScore: 14,
        historyScore: 15,
      },
      recommendations: [
        '高价值商机，建议优先跟进',
        '招标人信誉良好，国有企业',
        '项目金额较大，值得重点投入资源',
        '投标时间充裕，准备时间充足',
      ],
      riskFactors: [
        '竞争激烈，需充分准备竞争优势',
      ],
    },
  };

  const displayTender = tender || mockTender;
  const score = displayTender.opportunityScore;

  return (
    <div>
      <Card loading={loading}>
        <div className="flex items-center justify-between mb-6">
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tenders')}>
              返回列表
            </Button>
            <h1 className="text-xl font-bold m-0">{displayTender.title}</h1>
          </Space>
          <Space>
            <Button icon={<StarOutlined />}>收藏</Button>
            <Button icon={<ShareAltOutlined />}>分享</Button>
          </Space>
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            <Card title="基本信息" type="inner">
              <Descriptions column={2}>
                <Descriptions.Item label="招标人">{displayTender.tenderer}</Descriptions.Item>
                <Descriptions.Item label="地区">
                  <Tag color="blue">{displayTender.region}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="行业">
                  <Tag color="green">{displayTender.industry}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="金额">
                  <span className="text-lg font-bold text-orange-500">
                    ¥{(displayTender.amount / 10000).toFixed(2)}万
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="发布日期">
                  {dayjs(displayTender.publishDate).format('YYYY年MM月DD日')}
                </Descriptions.Item>
                <Descriptions.Item label="截止日期">
                  {dayjs(displayTender.deadlineDate).format('YYYY年MM月DD日')}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            {score && (
              <Card title="商机评分" type="inner">
                <div className="text-center mb-4">
                  <div className="text-5xl font-bold" style={{ color: score.totalScore >= 80 ? '#52c41a' : score.totalScore >= 50 ? '#faad14' : '#f5222d' }}>
                    {score.totalScore}
                  </div>
                  <div className="text-gray-500 mt-2">
                    {score.level === 'high' ? '高价值商机' : score.level === 'medium' ? '中等价值' : '低价值'}
                  </div>
                </div>
              </Card>
            )}
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default TenderDetailPage;
