import React from 'react';
import { Card, Row, Col, Table, Badge, Progress, List, Tag } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import ReactECharts from 'echarts-for-react';
import { Tender, OpportunityScore } from '@/types';

interface OpportunityData {
  tender: Tender;
  score: OpportunityScore;
  rank: number;
}

const OpportunityPage: React.FC = () => {
  const mockData: OpportunityData[] = [
    { tender: { id: '1', title: '国家电网智能电网改造', tenderer: '国家电网', region: '北京', industry: '电力', amount: 12000000, publishDate: '2024-03-15', deadlineDate: '2024-04-15', status: 'bidding' }, score: { totalScore: 92, level: 'high', factors: { amountScore: 24, competitionScore: 22, timelineScore: 18, relevanceScore: 14, historyScore: 14 }, recommendations: ['高价值商机', '大型国企'], riskFactors: [] }, rank: 1 },
    { tender: { id: '2', title: '中国移动通信设备采购', tenderer: '中国移动', region: '上海', industry: '通信', amount: 8000000, publishDate: '2024-03-14', deadlineDate: '2024-04-14', status: 'bidding' }, score: { totalScore: 88, level: 'high', factors: { amountScore: 23, competitionScore: 20, timelineScore: 17, relevanceScore: 13, historyScore: 15 }, recommendations: ['优质客户'], riskFactors: [] }, rank: 2 },
    { tender: { id: '3', title: '某银行数据中心建设', tenderer: '某银行', region: '深圳', industry: '金融', amount: 15000000, publishDate: '2024-03-13', deadlineDate: '2024-04-13', status: 'bidding' }, score: { totalScore: 85, level: 'high', factors: { amountScore: 25, competitionScore: 18, timelineScore: 16, relevanceScore: 12, historyScore: 14 }, recommendations: ['高额项目'], riskFactors: ['竞争激烈'] }, rank: 3 },
    { tender: { id: '4', title: '政府信息化平台升级', tenderer: '某区政府', region: '广州', industry: 'IT', amount: 3000000, publishDate: '2024-03-12', deadlineDate: '2024-04-12', status: 'bidding' }, score: { totalScore: 76, level: 'medium', factors: { amountScore: 18, competitionScore: 17, timelineScore: 15, relevanceScore: 13, historyScore: 13 }, recommendations: ['政府项目'], riskFactors: [] }, rank: 4 },
  ];

  const radarOption = {
    radar: {
      indicator: [
        { name: '金额评分', max: 25 },
        { name: '竞争度评分', max: 25 },
        { name: '时间评分', max: 20 },
        { name: '相关性评分', max: 15 },
        { name: '历史评分', max: 15 },
      ],
    },
    series: [{
      type: 'radar',
      data: [
        {
          value: [22, 20, 18, 14, 15],
          name: '平均评分',
          areaStyle: { opacity: 0.3 },
        },
      ],
    }],
  };

  const columns: ColumnsType<OpportunityData> = [
    { title: '排名', dataIndex: 'rank', key: 'rank', render: (rank: number) => <Badge count={rank} style={{ backgroundColor: rank <= 3 ? '#52c41a' : '#d9d9d9' }} /> },
    { title: '标题', dataIndex: ['tender', 'title'], key: 'title', render: (text: string) => <div className="truncate max-w-xs">{text}</div> },
    { title: '招标人', dataIndex: ['tender', 'tenderer'], key: 'tenderer' },
    { title: '地区', dataIndex: ['tender', 'region'], key: 'region', render: (text: string) => <Tag color="blue">{text}</Tag> },
    { title: '金额', dataIndex: ['tender', 'amount'], key: 'amount', render: (amount: number) => `¥${(amount / 10000).toFixed(0)}万` },
    { title: '总分', dataIndex: ['score', 'totalScore'], key: 'totalScore', render: (score: number) => <Progress percent={score} size="small" status={score >= 80 ? 'success' : score >= 50 ? 'normal' : 'exception'} /> },
    { title: '等级', dataIndex: ['score', 'level'], key: 'level', render: (level: string) => <Tag color={level === 'high' ? 'success' : level === 'medium' ? 'warning' : 'error'}>{level === 'high' ? '高' : level === 'medium' ? '中' : '低'}</Tag> },
  ];

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="5维评分雷达图">
            <ReactECharts option={radarOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="TOP 10 商机排行">
            <Table dataSource={mockData} columns={columns} rowKey="rank" size="small" pagination={false} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} className="mt-4">
        <Col xs={24} lg={12}>
          <Card title="推荐建议">
            <List>
              <List.Item><Tag color="green">高价值</Tag> 优先跟进评分80分以上的项目</List.Item>
              <List.Item><Tag color="blue">重点</Tag> 关注大型国企和政府部门招标</List.Item>
              <List.Item><Tag color="orange">提醒</Tag> 注意投标截止时间安排</List.Item>
              <List.Item><Tag color="purple">策略</Tag> 评估竞争优势后再投标</List.Item>
            </List>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="风险因素">
            <List>
              <List.Item><Tag color="red">风险</Tag> 部分项目竞争激烈，需充分准备</List.Item>
              <List.Item><Tag color="orange">注意</Tag> 投标截止时间临近的项目</List.Item>
              <List.Item><Tag color="yellow">提示</Tag> 新招标人历史记录较少</List.Item>
            </List>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default OpportunityPage;
