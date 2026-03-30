import React from 'react';
import ReactECharts from 'echarts-for-react';
import { RegionData } from '@/types';

interface RegionChartProps {
  data: RegionData[];
  height?: number;
}

const RegionChart: React.FC<RegionChartProps> = ({ data, height = 300 }) => {
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    series: [
      {
        name: '地区分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: data.map(d => ({ name: d.region, value: d.count })),
      },
    ],
  };
  
  return <ReactECharts option={option} style={{ height }} />;
};

export default RegionChart;
