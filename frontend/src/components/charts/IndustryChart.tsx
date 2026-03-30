import React from 'react';
import ReactECharts from 'echarts-for-react';
import { IndustryData } from '@/types';

interface IndustryChartProps {
  data: IndustryData[];
  height?: number;
}

const IndustryChart: React.FC<IndustryChartProps> = ({ data, height = 300 }) => {
  const sortedData = [...data].sort((a, b) => b.count - a.count).slice(0, 10);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
    },
    yAxis: {
      type: 'category',
      data: sortedData.map(d => d.industry).reverse(),
    },
    series: [
      {
        name: '招标数量',
        type: 'bar',
        data: sortedData.map(d => d.count).reverse(),
        itemStyle: {
          color: new (window as any).echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' },
          ]),
        },
      },
    ],
  };
  
  return <ReactECharts option={option} style={{ height }} />;
};

export default IndustryChart;
