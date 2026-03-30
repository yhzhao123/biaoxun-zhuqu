import React, { useEffect } from 'react';
import { Row, Col, Card, List, Tag, Badge, Button } from 'antd';
import {
  FileTextOutlined,
  DollarOutlined,
  RiseOutlined,
  StarOutlined,
  RightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import StatCard from '@/components/common/StatCard';
import TrendChart from '@/components/charts/TrendChart';
import { useDashboardStore } from '@/stores/dashboardStore';
import { useAppStore } from '@/stores/appStore';
import { getDashboardOverview, getHighValueOpportunities, analyzeTrends } from '@/api/analytics';
import { DashboardOverview, TrendAnalysis, Tender } from '@/types';
import dayjs from 'dayjs';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { overview, trends, highValueTenders, isLoading, setOverview, setTrends, setHighValueTenders, setLoading } = useDashboardStore();
  const addMessage = useAppStore((state) => state.addMessage);
  
  useEffect(() => {
    fetchDashboardData();
  }, []);
  
  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [overviewRes, trendsRes, opportunitiesRes] = await Promise.all([
        getDashboardOverview(),
        analyzeTrends({ analysis_type: 'time_series', start_date: dayjs().subtract(30, 'days').format('YYYY-MM-DD') }),
        getHighValueOpportunities(80, 5),
      ]);
      
      if (overviewRes.data) {
        setOverview(overviewRes.data);
      }
      if (trendsRes.data) {
        setTrends(trendsRes.data);
      }
      if (opportunitiesRes.data) {
        setHighValueTenders(opportunitiesRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const mockTrendData = [
    { period: '2024-01', count: 120, totalAmount: 5000000 },
    { period: '2024-02', count: 145, totalAmount: 6800000 },
    { period: '2024-03', count: 132, totalAmount: 5900000 },
    { period: '2024-04', count: 168, totalAmount: 8200000 },
    { period: '2024-05', count: 189, totalAmount: 9500000 },
    { period: '2024-06', count: 156, totalAmount: 7200000 },
  ];
  
  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="今日新增"
            value={overview?.todayCount || 0}
            prefix={<FileTextOutlined />}
            trend={12.5}
            loading={isLoading}
            color="blue"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="招标总数"
            value={overview?.totalCount || 0}
            prefix={<RiseOutlined />}
            trend={8.2}
            loading={isLoading}
            color="green"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="总金额"
            value={(overview?.totalAmount || 0) / 1000000}
            suffix="M"
            prefix={<DollarOutlined />}
            trend={15.3}
            loading={isLoading}
            color="orange"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="高价值商机"
            value={overview?.highValueCount || 0}
            prefix={<StarOutlined />}
            trend={-5.2}
            loading={isLoading}
            color="red"
          />
        </Col>
      </Row>
      
      {/* 趋势图和高价值商机 */}
      <Row gutter={[16, 16]} className="mt-6">
        <Col xs={24} lg={16}>
          <Card
            title="招标趋势 (近6个月)"
            extra={<Button type="link" onClick={() => navigate('/trends')}>查看更多</Button>}
          >
            <TrendChart data={trends?.timeSeries || mockTrendData} height={350} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title="高价值商机"
            extra={<Button type="link" icon={<RightOutlined />} onClick={() => navigate('/opportunity')}>全部</Button>}
          >
            <List
              dataSource={highValueTenders.slice(0, 5)}
              loading={isLoading}
              renderItem={(tender: Tender) => (
                <List.Item
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={() => navigate(`/tenders/${tender.id}`)}
                >
                  <List.Item.Meta
                    title={
                      <div className="flex items-center gap-2">
                        <span className="truncate flex-1">{tender.title}</span>
                        <Badge count={tender.opportunityScore?.totalScore || 0} style={{ backgroundColor: '#52c41a' }} />
                      </div>
                    }
                    description={
                      <div className="flex items-center gap-2 text-gray-500 text-sm">
                        <span>{tender.tenderer}</span>
                        <span>·</span>
                        <Tag color="blue">{tender.region}</Tag>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
      
      {/* 快速入口 */}
      <Row gutter={[16, 16]} className="mt-6">
        <Col xs={24}>
          <Card title="快速入口">
            <Row gutter={[16, 16]}>
              <Col xs={12} sm={6}>
                <Button type="primary" block size="large" onClick={() => navigate('/tenders')}>
                  查看招标
                </Button>
              </Col>
              <Col xs={12} sm={6}>
                <Button block size="large" onClick={() => navigate('/opportunity')}>
                  商机分析
                </Button>
              </Col>
              <Col xs={12} sm={6}>
                <Button block size="large" onClick={() => navigate('/classification')}>
                  数据分类
                </Button>
              </Col>
              <Col xs={12} sm={6}>
                <Button block size="large" onClick={() => navigate('/trends')}>
                  趋势分析
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;
