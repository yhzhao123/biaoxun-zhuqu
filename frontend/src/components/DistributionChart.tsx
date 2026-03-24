/**
 * DistributionChart component - Phase 10 Task 052-053
 * Display distribution charts for region/industry statistics
 */

import React, { useEffect, useRef, useState } from 'react';

interface DistributionData {
  name: string;
  value: number;
}

interface DistributionChartProps {
  data: DistributionData[];
  loading?: boolean;
  title?: string;
  type?: 'pie' | 'bar';
  colorScheme?: 'blue' | 'green' | 'purple';
}

export const DistributionChart: React.FC<DistributionChartProps> = ({
  data,
  loading = false,
  title = '分布统计',
  type = 'pie',
  colorScheme = 'blue',
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<any>(null);
  const [echartsLib, setEchartsLib] = useState<any>(null);

  // Color schemes
  const colorSchemes = {
    blue: ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#1d4ed8', '#1e40af'],
    green: ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5', '#059669', '#047857'],
    purple: ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#ede9fe', '#7c3aed', '#6d28d9'],
  };

  useEffect(() => {
    import('echarts').then((echarts) => {
      setEchartsLib(echarts);
    });
  }, []);

  useEffect(() => {
    if (!chartRef.current || !echartsLib || loading) return;

    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    chartInstance.current = echartsLib.init(chartRef.current);

    const colors = colorSchemes[colorScheme];

    const option = type === 'pie'
      ? {
          title: {
            text: title,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'normal',
            },
          },
          tooltip: {
            trigger: 'item',
            formatter: (params: any) => {
              const percent = params.percent?.toFixed(1) || 0;
              return `<strong>${params.name}</strong><br/>数量: ${params.value}<br/>占比: ${percent}%`;
            },
          },
          legend: {
            orient: 'vertical',
            left: 'left',
            top: 'middle',
            itemWidth: 12,
            itemHeight: 12,
          },
          series: [
            {
              type: 'pie',
              radius: ['40%', '70%'],
              center: ['60%', '50%'],
              avoidLabelOverlap: true,
              itemStyle: {
                borderRadius: 8,
                borderColor: '#fff',
                borderWidth: 2,
              },
              label: {
                show: true,
                formatter: '{b}: {c}',
              },
              emphasis: {
                label: {
                  show: true,
                  fontSize: 14,
                  fontWeight: 'bold',
                },
              },
              data: data,
              color: colors,
            },
          ],
        }
      : {
          title: {
            text: title,
            left: 'center',
            textStyle: {
              fontSize: 16,
              fontWeight: 'normal',
            },
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow',
            },
            formatter: (params: any[]) => {
              const param = params[0];
              return `<strong>${param.name}</strong><br/>数量: ${param.value}`;
            },
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '10%',
            top: '15%',
            containLabel: true,
          },
          xAxis: {
            type: 'category',
            data: data.map((d) => d.name),
            axisLabel: {
              interval: 0,
              rotate: 30,
            },
          },
          yAxis: {
            type: 'value',
            name: '数量',
          },
          series: [
            {
              type: 'bar',
              data: data.map((d) => ({
                value: d.value,
                name: d.name,
              })),
              itemStyle: {
                color: {
                  type: 'linear',
                  x: 0,
                  y: 0,
                  x2: 0,
                  y2: 1,
                  colorStops: [
                    { offset: 0, color: colors[0] },
                    { offset: 1, color: colors[2] },
                  ],
                },
                borderRadius: [4, 4, 0, 0],
              },
              emphasis: {
                itemStyle: {
                  color: colors[1],
                },
              },
            },
          ],
          dataZoom: data.length > 10
            ? [
                {
                  type: 'slider',
                  show: true,
                  start: 0,
                  end: 50,
                },
              ]
            : undefined,
        };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data, echartsLib, loading, title, type, colorScheme]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
        <div className="flex justify-center items-center h-64 text-gray-500">
          暂无数据
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div ref={chartRef} className="w-full h-80" data-testid="distribution-chart" />
    </div>
  );
};

export default DistributionChart;
