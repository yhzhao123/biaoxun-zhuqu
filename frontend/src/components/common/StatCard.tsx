import React from 'react';
import { Card, Statistic, Skeleton } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

interface StatCardProps {
  title: string;
  value: number | string;
  suffix?: string;
  prefix?: React.ReactNode;
  trend?: number;
  loading?: boolean;
  color?: 'blue' | 'green' | 'orange' | 'red';
}

const colorMap = {
  blue: '#1890ff',
  green: '#52c41a',
  orange: '#faad14',
  red: '#f5222d',
};

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  suffix,
  prefix,
  trend,
  loading = false,
  color = 'blue',
}) => {
  if (loading) {
    return (
      <Card>
        <Skeleton active paragraph={{ rows: 1 }} />
      </Card>
    );
  }
  
  return (
    <Card hoverable>
      <Statistic
        title={title}
        value={value}
        suffix={suffix}
        prefix={prefix}
        valueStyle={{ color: colorMap[color], fontWeight: 600 }}
      />
      {trend !== undefined && (
        <div className="mt-2 text-sm">
          {trend >= 0 ? (
            <span className="text-success">
              <ArrowUpOutlined /> {trend}%
            </span>
          ) : (
            <span className="text-error">
              <ArrowDownOutlined /> {Math.abs(trend)}%
            </span>
          )}
          <span className="text-gray-400 ml-2">较上月</span>
        </div>
      )}
    </Card>
  );
};

export default StatCard;
