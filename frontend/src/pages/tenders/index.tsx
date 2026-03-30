import React, { useState, useEffect } from 'react';
import { Table, Card, Input, Select, DatePicker, Button, Tag, Space, Pagination, Badge } from 'antd';
import { SearchOutlined, FilterOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { getTenderList } from '@/api/analytics';
import { useAppStore } from '@/stores/appStore';
import { Tender, TenderFilters, PaginatedResponse } from '@/types';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;
const { Option } = Select;

const TenderListPage: React.FC = () => {
  const navigate = useNavigate();
  const { filters, setFilters, setSelectedTender } = useAppStore();
  
  const [data, setData] = useState<PaginatedResponse<Tender> | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  useEffect(() => {
    fetchTenders();
  }, [page, pageSize, filters]);
  
  const fetchTenders = async () => {
    setLoading(true);
    try {
      const response = await getTenderList(filters, page, pageSize);
      if (response.data) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch tenders:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleViewDetail = (tender: Tender) => {
    setSelectedTender(tender);
    navigate(`/tenders/${tender.id}`);
  };
  
  const statusMap = {
    pending: { text: '待开标', color: 'warning' },
    bidding: { text: '招标中', color: 'processing' },
    closed: { text: '已结束', color: 'default' },
  };
  
  const columns = [
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      render: (text: string, record: Tender) => (
        <div>
          <div className="font-medium truncate" title={text}>{text}</div>
          <div className="text-gray-400 text-sm">{record.tenderer}</div>
        </div>
      ),
    },
    {
      title: '地区',
      dataIndex: 'region',
      key: 'region',
      width: 100,
      render: (text: string) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '行业',
      dataIndex: 'industry',
      key: 'industry',
      width: 120,
      render: (text: string) => <Tag color="green">{text}</Tag>,
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: number) => (
        <span className="font-mono">
          {amount ? `¥${(amount / 10000).toFixed(2)}万` : '待定'}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Badge status={statusMap[status as keyof typeof statusMap]?.color as any} 
               text={statusMap[status as keyof typeof statusMap]?.text || status} />
      ),
    },
    {
      title: '商机评分',
      dataIndex: ['opportunityScore', 'totalScore'],
      key: 'score',
      width: 100,
      render: (score: number) => {
        if (!score) return '-';
        const color = score >= 80 ? 'success' : score >= 50 ? 'warning' : 'error';
        return <Badge count={score} style={{ backgroundColor: color === 'success' ? '#52c41a' : color === 'warning' ? '#faad14' : '#f5222d' }} />;
      },
    },
    {
      title: '发布日期',
      dataIndex: 'publishDate',
      key: 'publishDate',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: Tender) => (
        <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>
          查看
        </Button>
      ),
    },
  ];
  
  const mockData = {
    items: [
      { id: '1', title: '中国移动通信设备采购项目', tenderer: '中国移动北京公司', region: '北京', industry: '通信', amount: 5000000, status: 'bidding', publishDate: '2024-03-15', opportunityScore: { totalScore: 85 } },
      { id: '2', title: '国家电网智能电网改造', tenderer: '国家电网', region: '上海', industry: '电力', amount: 12000000, status: 'pending', publishDate: '2024-03-14', opportunityScore: { totalScore: 92 } },
      { id: '3', title: '某区政府信息化建设项目', tenderer: '某区政府', region: '广州', industry: 'IT', amount: 800000, status: 'bidding', publishDate: '2024-03-13', opportunityScore: { totalScore: 78 } },
    ],
    total: 3,
    page: 1,
    pageSize: 20,
    totalPages: 1,
  };
  
  return (
    <div>
      {/* 筛选栏 */}
      <Card className="mb-4">
        <Space wrap className="w-full">
          <Input
            placeholder="搜索标题/招标人"
            prefix={<SearchOutlined />}
            value={filters.keyword}
            onChange={(e) => setFilters({ keyword: e.target.value })}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="选择地区"
            value={filters.region}
            onChange={(value) => setFilters({ region: value })}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="北京">北京</Option>
            <Option value="上海">上海</Option>
            <Option value="广州">广州</Option>
            <Option value="深圳">深圳</Option>
          </Select>
          <Select
            placeholder="选择行业"
            value={filters.industry}
            onChange={(value) => setFilters({ industry: value })}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="通信">通信</Option>
            <Option value="电力">电力</Option>
            <Option value="IT">IT</Option>
            <Option value="建筑">建筑</Option>
          </Select>
          <Select
            placeholder="选择状态"
            value={filters.status}
            onChange={(value) => setFilters({ status: value })}
            style={{ width: 150 }}
            allowClear
          >
            <Option value="bidding">招标中</Option>
            <Option value="pending">待开标</Option>
            <Option value="closed">已结束</Option>
          </Select>
          <RangePicker
            placeholder={['开始日期', '结束日期']}
            onChange={(dates) => {
              if (dates) {
                setFilters({
                  startDate: dates[0]?.format('YYYY-MM-DD'),
                  endDate: dates[1]?.format('YYYY-MM-DD'),
                });
              }
            }}
          />
          <Button type="primary" icon={<FilterOutlined />} onClick={fetchTenders}>
            筛选
          </Button>
          <Button onClick={() => { setFilters({}); fetchTenders(); }}>
            重置
          </Button>
        </Space>
      </Card>
      
      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={data?.items || mockData.items}
          loading={loading}
          rowKey="id"
          pagination={{
            current: page,
            pageSize,
            total: data?.total || mockData.total,
            onChange: (p, ps) => {
              setPage(p);
              if (ps) setPageSize(ps);
            },
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>
    </div>
  );
};

export default TenderListPage;
