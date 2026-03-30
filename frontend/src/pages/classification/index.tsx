import React from 'react';
import { Card, Row, Col, Tree, Table, Tag, Tabs } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { FolderOutlined, EnvironmentOutlined, IndustryOutlined, BankOutlined } from '@ant-design/icons';

const ClassificationPage: React.FC = () => {
  const regionData = [
    { title: '华北', key: 'huabei', children: [{ title: '北京', key: 'beijing' }, { title: '天津', key: 'tianjin' }, { title: '河北', key: 'hebei' }] },
    { title: '华东', key: 'huadong', children: [{ title: '上海', key: 'shanghai' }, { title: '江苏', key: 'jiangsu' }, { title: '浙江', key: 'zhejiang' }] },
    { title: '华南', key: 'huanan', children: [{ title: '广东', key: 'guangdong' }, { title: '福建', key: 'fujian' }] },
  ];

  const industryColumns: ColumnsType<any> = [
    { title: '行业代码', dataIndex: 'code', key: 'code', width: 100 },
    { title: '行业名称', dataIndex: 'name', key: 'name' },
    { title: '招标数量', dataIndex: 'count', key: 'count', width: 120 },
    { title: '占比', dataIndex: 'percentage', key: 'percentage', width: 120, render: (p: number) => `${p}%` },
  ];

  const industryData = [
    { code: 'I63', name: '通信服务', count: 328, percentage: 28.5 },
    { code: 'D44', name: '电力供应', count: 256, percentage: 22.3 },
    { code: 'I65', name: '软件和信息技术', count: 198, percentage: 17.2 },
    { code: 'E50', name: '建筑业', count: 156, percentage: 13.6 },
    { code: 'J66', name: '金融业', count: 124, percentage: 10.8 },
    { code: 'C31', name: '制造业', count: 89, percentage: 7.6 },
  ];

  const amountData = [
    { range: '<10万', count: 156, level: 'small', color: 'green' },
    { range: '10-50万', count: 298, level: 'small-medium', color: 'cyan' },
    { range: '50-100万', count: 245, level: 'medium', color: 'blue' },
    { range: '100-500万', count: 312, level: 'medium-large', color: 'geekblue' },
    { range: '500-1000万', count: 178, level: 'large', color: 'purple' },
    { range: '>1000万', count: 89, level: 'extra-large', color: 'magenta' },
  ];

  const tendererData = [
    { type: '国有企业', count: 456, percentage: 39.6 },
    { type: '民营企业', count: 328, percentage: 28.5 },
    { type: '政府机关', count: 198, percentage: 17.2 },
    { type: '事业单位', count: 112, percentage: 9.7 },
    { type: '外资企业', count: 58, percentage: 5.0 },
  ];

  const tendererColumns: ColumnsType<any> = [
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '数量', dataIndex: 'count', key: 'count', width: 120 },
    { title: '占比', dataIndex: 'percentage', key: 'percentage', width: 120, render: (p: number) => <Tag color="blue">{p}%</Tag> },
  ];

  return (
    <div>
      <Tabs
        items={[
          {
            key: 'region',
            label: (<span><EnvironmentOutlined /> 地区分类</span>),
            children: (
              <Card>
                <Tree treeData={regionData} defaultExpandAll checkable />
              </Card>
            ),
          },
          {
            key: 'industry',
            label: (<span><IndustryOutlined /> 行业分类</span>),
            children: (
              <Card>
                <Table dataSource={industryData} columns={industryColumns} rowKey="code" pagination={false} />
              </Card>
            ),
          },
          {
            key: 'amount',
            label: (<span><FolderOutlined /> 金额区间</span>),
            children: (
              <Card>
                <Row gutter={[16, 16]}>
                  {amountData.map(item => (
                    <Col xs={24} sm={12} lg={8} key={item.level}>
                      <Card type="inner" title={item.range}>
                        <div className="text-2xl font-bold" style={{ color: `var(--ant-${item.color}-6)` }}>{item.count}</div>
                        <div className="text-gray-400 text-sm">个项目</div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            ),
          },
          {
            key: 'tenderer',
            label: (<span><BankOutlined /> 招标人类型</span>),
            children: (
              <Card>
                <Table dataSource={tendererData} columns={tendererColumns} rowKey="type" pagination={false} />
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default ClassificationPage;
