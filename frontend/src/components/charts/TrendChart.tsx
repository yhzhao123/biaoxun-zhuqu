import React from 'react';
import ReactECharts from 'echarts-for-react';
import { TimeSeriesData } from '@/types';

interface TrendChartProps {
  data: TimeSeriesData[];
  height?: number;
}

const TrendChart: React.FC<TrendChartProps> = ({ data, height = 300 }) => {
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(d => d.period),
    },
    yAxis: [
      {
        type: 'value',
        name: '招标数量',
        position: 'left',
      },
      {
        type: 'value',
        name: '总金额(万)',
        position: 'right',
        axisLabel: {
          formatter: (value: number) => (value / 10000).toFixed(0),
        },
      },
    ],
    series: [
      {
        name: '招标数量',
        type: 'line',
        data: data.map(d => d.count),
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
            ],
          },
        },
        itemStyle: { color: '#1890ff' },
      },
      {
        name: '总金额',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => d.totalAmount),
        smooth: true,
        itemStyle: { color: '#52c41a' },
      },
    ],
  };
  
  return <ReactECharts option={option} style={{ height }} />;
};

export default TrendChart;
