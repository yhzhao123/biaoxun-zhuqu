import React from 'react';
import { Card, List, Badge, Button, Space, Tag, Empty } from 'antd';
import { BellOutlined, CheckCircleOutlined, DeleteOutlined, SoundOutlined } from '@ant-design/icons';
import { useAppStore } from '@/stores/appStore';
import { RealtimeMessage } from '@/types';
import dayjs from 'dayjs';

const RealtimePage: React.FC = () => {
  const { messages, markMessageAsRead, clearMessages } = useAppStore();

  const mockMessages: RealtimeMessage[] = [
    { id: '1', type: 'new_tender', title: '新招标提醒', content: '发现新招标：中国移动通信设备采购项目，金额500万', timestamp: dayjs().subtract(5, 'minutes').toISOString(), read: false },
    { id: '2', type: 'high_value', title: '高价值商机', content: '国家电网智能电网改造项目商机评分达到92分', timestamp: dayjs().subtract(30, 'minutes').toISOString(), read: false },
    { id: '3', type: 'deadline_warning', title: '截止提醒', content: '某政府信息化项目即将截止，还剩2天', timestamp: dayjs().subtract(2, 'hours').toISOString(), read: true },
    { id: '4', type: 'system', title: '系统通知', content: '数据更新完成，共同步120条招标信息', timestamp: dayjs().subtract(1, 'day').toISOString(), read: true },
  ];

  const displayMessages = messages.length > 0 ? messages : mockMessages;

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'new_tender': return <Badge color="blue"><BellOutlined /></Badge>;
      case 'high_value': return <Badge color="green"><CheckCircleOutlined /></Badge>;
      case 'deadline_warning': return <Badge color="orange"><SoundOutlined /></Badge>;
      default: return <Badge color="gray"><BellOutlined /></Badge>;
    }
  };

  const getMessageTag = (type: string) => {
    switch (type) {
      case 'new_tender': return <Tag color="blue">新招标</Tag>;
      case 'high_value': return <Tag color="green">高价值</Tag>;
      case 'deadline_warning': return <Tag color="orange">截止提醒</Tag>;
      default: return <Tag>系统</Tag>;
    }
  };

  return (
    <div>
      <Card
        title={<Space><BellOutlined /> 实时消息</Space>}
        extra={
          <Space>
            <Button onClick={() => clearMessages()} icon={<DeleteOutlined />}>清空消息</Button>
          </Space>
        }
      >
        <List
          dataSource={displayMessages}
          renderItem={(item) => (
            <List.Item
              key={item.id}
              className={!item.read ? 'bg-blue-50' : ''}
              actions={[
                !item.read && <Button type="link" size="small" onClick={() => markMessageAsRead(item.id)}>标记已读</Button>
              ]}
            >
              <List.Item.Meta
                avatar={getMessageIcon(item.type)}
                title={
                  <Space>
                    <span className={!item.read ? 'font-bold' : ''}>{item.title}</span>
                    {getMessageTag(item.type)}
                    {!item.read && <Badge dot />}
                  </Space>
                }
                description={
                  <div>
                    <div>{item.content}</div>
                    <div className="text-gray-400 text-sm mt-1">{dayjs(item.timestamp).format('YYYY-MM-DD HH:mm:ss')}</div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default RealtimePage;
