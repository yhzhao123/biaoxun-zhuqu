import React from 'react';
import { Card, Row, Col, Tabs, Alert, List, Tag, Statistic } from 'antd';
import ReactECharts from 'echarts-for-react';
import { RiseOutlined, FallOutlined, LineChartOutlined, PieChartOutlined, BarChartOutlined } from '@ant-design/icons';

const TrendsPage: React.FC = () => {
  const timeSeriesOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
    yAxis: { type: 'value' },
    series: [
      { name: '招标数量', type: 'line', smooth: true, data: [120, 132, 101, 134, 90, 230], itemStyle: { color: '#1890ff' } },
      { name: '中标金额', type: 'line', smooth: true, data: [220, 182, 191, 234, 290, 330], itemStyle: { color: '#52c41a' } },
    ],
  };

  const regionOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: 335, name: '北京' },
        { value: 310, name: '上海' },
        { value: 234, name: '广州' },
        { value: 135, name: '深圳' },
        { value: 148, name: '其他' },
      ],
    }],
  };

  const industryOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['通信', '电力', 'IT', '建筑', '金融', '制造'] },
    yAxis: { type: 'value' },
    series: [{
      data: [320, 280, 250, 220, 190, 150],
      type: 'bar',
      itemStyle: { color: '#1890ff' },
    }],
  };

  const amountOption = {
    tooltip: { trigger: 'item' },
    xAxis: { type: 'category', data: ['<10万', '10-50万', '50-100万', '100-500万', '500万-1000万', '>1000万'] },
    yAxis: { type: 'value' },
    series: [{
      data: [150, 230, 224, 218, 135, 147],
      type: 'bar',
      itemStyle: {
        color: (params: any) => {
          const colors = ['#ff4d4f', '#ff7a45', '#ffa940', '#73d13d', '#40a9ff', '#9254de'];
          return colors[params.dataIndex];
        },
      },
    }],
  };

  return (
    <div>
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="本月招标数" value={1128} prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} suffix="+12%" /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="本月金额" value={28456} prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} suffix="万元" /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="平均项目金额" value={25.2} prefix={<FallOutlined />} valueStyle={{ color: '#cf1322' }} suffix="万元 -5%" /></Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card><Statistic title="活跃招标人" value={156} prefix={<RiseOutlined />} valueStyle={{ color: '#3f8600' }} suffix="+8%" /></Card>
        </Col>
      </Row>

      <Card>
        <Tabs
          items={[
            {
              key: 'time',
              label: (<span><LineChartOutlined /> 时间趋势</span>),
              children: <ReactECharts option={timeSeriesOption} style={{ height: 400 }} />,
            },
            {
              key: 'region',
              label: (<span><PieChartOutlined /> 地区分布</span>),
              children: <ReactECharts option={regionOption} style={{ height: 400 }} />,
            },
            {
              key: 'industry',
              label: (<span><BarChartOutlined /> 行业热度</span>),
              children: <ReactECharts option={industryOption} style={{ height: 400 }} />,
            },
            {
              key: 'amount',
              label: (<span><PieChartOutlined /> 金额分布</span>),
              children: <ReactECharts option={amountOption} style={{ height: 400 }} />,
            },
          ]}
        />
      </Card>

      <Row gutter={[16, 16]} className="mt-4">
        <Col xs={24} lg={12}>
          <Card title="市场洞察">
            <Alert message="增长趋势" description="通信行业招标数量环比增长15%，预计下月继续增长" type="success" showIcon className="mb-2" />
            <Alert message="区域热点" description="北京、上海地区招标金额占比达60%" type="info" showIcon className="mb-2" />
            <Alert message="风险提示" description="大型项目竞争激烈，建议关注中小型项目机会" type="warning" showIcon />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="行动建议">
            <List>
              <List.Item><Tag color="blue">策略</Tag> 重点关注通信和电力行业机会</List.Item>
              <List.Item><Tag color="green">优化</Tag> 扩大北京、上海地区业务覆盖</List.Item>
              <List.Item><Tag color="orange">关注</Tag> 100-500万区间项目性价比最高</List.Item>
            </List>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TrendsPage;
