/**
 * TrendChart component - Phase 10 Task 052-053
 * Display tender trend charts using ECharts
 */

import React, { useEffect, useRef, useState } from 'react';
import type { ECharts } from 'echarts';

interface TrendData {
  date: string;
  count: number;
  budget?: number;
}

interface TrendChartProps {
  data: TrendData[];
  loading?: boolean;
  title?: string;
  type?: 'count' | 'budget' | 'both';
}

export const TrendChart: React.FC<TrendChartProps> = ({
  data,
  loading = false,
  title = '招标趋势',
  type = 'both',
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<ECharts | null>(null);
  const [echartsLib, setEchartsLib] = useState<any>(null);

  // Load ECharts dynamically
  useEffect(() => {
    import('echarts').then((echarts) => {
      setEchartsLib(echarts);
    });
  }, []);

  // Initialize chart
  useEffect(() => {
    if (!chartRef.current || !echartsLib || loading) return;

    // Dispose existing chart
    if (chartInstance.current) {
      chartInstance.current.dispose();
    }

    // Create new chart
    chartInstance.current = echartsLib.init(chartRef.current);

    const option = {
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
          type: 'cross',
        },
        formatter: (params: any[]) => {
          const date = params[0]?.axisValue;
          let html = `<strong>${date}</strong><br/>`;
          params.forEach((param) => {
            const value = param.seriesName === '预算金额'
              ? `¥${(param.value / 10000).toFixed(1)}万`
              : param.value;
            html += `${param.marker} ${param.seriesName}: ${value}<br/>`;
          });
          return html;
        },
      },
      legend: {
        data: type === 'both'
          ? ['招标数量', '预算金额']
          : type === 'count'
            ? ['招标数量']
            : ['预算金额'],
        bottom: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.map((d) => d.date),
        axisLabel: {
          rotate: 45,
          interval: Math.floor(data.length / 10),
        },
      },
      yAxis: [
        {
          type: 'value',
          name: '数量',
          position: 'left',
          show: type === 'count' || type === 'both',
          axisLabel: {
            formatter: '{value}',
          },
        },
        {
          type: 'value',
          name: '金额(万)',
          position: 'right',
          show: type === 'budget' || type === 'both',
          axisLabel: {
            formatter: (value: number) => `¥${(value / 10000).toFixed(0)}`,
          },
        },
      ],
      series: [
        ...(type === 'count' || type === 'both'
          ? [
              {
                name: '招标数量',
                type: 'line',
                data: data.map((d) => d.count),
                smooth: true,
                itemStyle: {
                  color: '#3b82f6',
                },
                areaStyle: {
                  color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [
                      { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                      { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
                    ],
                  },
                },
              },
            ]
          : []),
        ...(type === 'budget' || type === 'both'
          ? [
              {
                name: '预算金额',
                type: 'line',
                yAxisIndex: 1,
                data: data.map((d) => d.budget || 0),
                smooth: true,
                itemStyle: {
                  color: '#10b981',
                },
                lineStyle: {
                  type: 'dashed',
                },
              },
            ]
          : []),
      ],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
        {
          start: 0,
          end: 100,
        },
      ],
    };

    chartInstance.current.setOption(option);

    // Handle resize
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data, echartsLib, loading, title, type]);

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
      <div ref={chartRef} className="w-full h-80" data-testid="echarts-container" />
    </div>
  );
};

export default TrendChart;
