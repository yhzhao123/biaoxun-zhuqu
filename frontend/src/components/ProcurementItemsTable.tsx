/**
 * ProcurementItemsTable - Display procurement items in a table format
 */

import React from 'react';
import type { TenderItem } from '../types';

interface ProcurementItemsTableProps {
  items: TenderItem[];
}

export const ProcurementItemsTable: React.FC<ProcurementItemsTableProps> = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        暂无采购物品数据
      </div>
    );
  }

  const totalBudget = items.reduce((sum, item) => {
    return sum + (item.budget_total_price || 0);
  }, 0);

  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return '-';
    return num.toLocaleString();
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              序号
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              名称
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              规格型号
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              数量
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              单位
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              预算单价(元)
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              预算总价(元)
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              类别
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {items.map((item, index) => (
            <tr key={item.id} className="hover:bg-gray-50">
              <td className="px-4 py-3 text-sm text-gray-500">
                {index + 1}
              </td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                {item.name}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {item.specification || '-'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {item.quantity ?? '-'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {item.unit || '-'}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {formatNumber(item.budget_unit_price)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {formatNumber(item.budget_total_price)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {item.category || '-'}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-gray-50">
          <tr>
            <td colSpan={6} className="px-4 py-3 text-sm font-medium text-gray-900 text-right">
              预算总计:
            </td>
            <td className="px-4 py-3 text-sm font-bold text-gray-900">
              {formatNumber(totalBudget)}
            </td>
            <td></td>
          </tr>
        </tfoot>
      </table>

      {items.some(item => item.technical_requirements) && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-2">技术要求</h4>
          <ul className="space-y-1">
            {items.filter(item => item.technical_requirements).map(item => (
              <li key={item.id} className="text-sm text-gray-600">
                <span className="font-medium">{item.name}:</span> {item.technical_requirements}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ProcurementItemsTable;