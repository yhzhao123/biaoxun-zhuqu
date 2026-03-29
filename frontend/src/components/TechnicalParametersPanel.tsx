/**
 * TechnicalParametersPanel - Display technical parameters in collapsible panels by category
 */

import React, { useState } from 'react';
import type { TechnicalParameter } from '../types';

interface TechnicalParametersPanelProps {
  parameters: TechnicalParameter[];
}

interface GroupedParameters {
  [category: string]: TechnicalParameter[];
}

export const TechnicalParametersPanel: React.FC<TechnicalParametersPanelProps> = ({ parameters }) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  if (!parameters || parameters.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        暂无技术参数数据
      </div>
    );
  }

  // Group parameters by category
  const groupedParameters: GroupedParameters = parameters.reduce((acc, param) => {
    const category = param.category || '未分类';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(param);
    return acc;
  }, {} as GroupedParameters);

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const categories = Object.keys(groupedParameters);

  return (
    <div className="space-y-4">
      {categories.map(category => {
        const isExpanded = expandedCategories.has(category) || expandedCategories.size === 0;
        const params = groupedParameters[category];

        return (
          <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => toggleCategory(category)}
              className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
            >
              <span className="font-medium text-gray-900">{category}</span>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">
                  {params.length} 项
                </span>
                <svg
                  className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </button>

            {isExpanded && (
              <div className="p-4 bg-white">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs font-medium text-gray-500 uppercase">
                      <th className="pb-2">参数名称</th>
                      <th className="pb-2">参数值</th>
                      <th className="pb-2">必填</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {params.map(param => (
                      <tr key={param.id} className="hover:bg-gray-50">
                        <td className="py-2 pr-4 text-sm font-medium text-gray-900">
                          {param.name}
                        </td>
                        <td className="py-2 pr-4 text-sm text-gray-600">
                          {param.value}
                        </td>
                        <td className="py-2">
                          {param.is_mandatory ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              必填
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              可选
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default TechnicalParametersPanel;