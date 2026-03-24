/**
 * Export Utilities - Phase 10 Task 056-057
 * Helper functions for data export (Excel, CSV, PDF)
 */

import type { Tender } from '../types';

/**
 * Convert tenders data to CSV format
 */
export function convertToCSV(tenders: Tender[]): string {
  if (tenders.length === 0) {
    return '';
  }

  const headers = [
    'ID',
    '标题',
    '招标人',
    '预算金额',
    '状态',
    '地区',
    '行业',
    '发布日期',
    '截止日期',
    'URL',
  ];

  const rows = tenders.map((tender) => [
    tender.id,
    `"${tender.title.replace(/"/g, '""')}"`,
    `"${(tender.tenderer || '').replace(/"/g, '""')}"`,
    tender.budget || '',
    tender.status,
    `"${(tender.region || '').replace(/"/g, '""')}"`,
    `"${(tender.industry || '').replace(/"/g, '""')}"`,
    tender.publish_date,
    tender.deadline || '',
    tender.url,
  ]);

  return [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
}

/**
 * Format budget for display
 */
export function formatBudget(budget: number | null): string {
  if (budget === null || budget === undefined) {
    return '未公开';
  }

  if (budget >= 100000000) {
    return `${(budget / 100000000).toFixed(2)}亿元`;
  } else if (budget >= 10000) {
    return `${(budget / 10000).toFixed(2)}万元`;
  } else {
    return `${budget}元`;
  }
}

/**
 * Format date for display
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN');
}

/**
 * Generate filename with timestamp
 */
export function generateFilename(prefix: string, extension: string): string {
  const timestamp = new Date().toISOString().split('T')[0];
  return `${prefix}_${timestamp}.${extension}`;
}

/**
 * Download blob as file
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Create a simple HTML table for PDF export
 */
export function createHTMLTable(tenders: Tender[]): string {
  const headers = [
    '标题',
    '招标人',
    '预算',
    '状态',
    '地区',
    '行业',
    '发布日期',
  ];

  const rows = tenders.map(
    (t) => `
    <tr>
      <td>${t.title}</td>
      <td>${t.tenderer || '-'}</td>
      <td>${formatBudget(t.budget)}</td>
      <td>${t.status}</td>
      <td>${t.region || '-'}</td>
      <td>${t.industry || '-'}</td>
      <td>${formatDate(t.publish_date)}</td>
    </tr>
  `
  );

  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        table { border-collapse: collapse; width: 100%; font-size: 12px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        h1 { text-align: center; color: #333; }
        .meta { margin: 20px 0; color: #666; font-size: 12px; }
      </style>
    </head>
    <body>
      <h1>招标信息报表</h1>
      <div class="meta">
        生成时间: ${new Date().toLocaleString('zh-CN')}
        <br>记录数量: ${tenders.length}
      </div>
      <table>
        <thead>
          <tr>${headers.map((h) => `<th>${h}</th>`).join('')}</tr>
        </thead>
        <tbody>
          ${rows.join('')}
        </tbody>
      </table>
    </body>
    </html>
  `;
}

/**
 * Validate export data
 */
export function validateExportData(data: unknown[]): boolean {
  if (!Array.isArray(data)) {
    return false;
  }
  return data.length === 0 || (typeof data[0] === 'object' && data[0] !== null);
}
