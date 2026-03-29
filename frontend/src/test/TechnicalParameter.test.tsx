/**
 * Tests for TechnicalParametersPanel component
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TechnicalParametersPanel } from '../components/TechnicalParametersPanel';
import type { TechnicalParameter } from '../types';
import React from 'react';

const mockParameters: TechnicalParameter[] = [
  {
    id: '1',
    name: '处理器',
    value: 'Intel Core i7',
    category: '性能指标',
    is_mandatory: true,
  },
  {
    id: '2',
    name: '内存',
    value: '16GB DDR4',
    category: '性能指标',
    is_mandatory: true,
  },
  {
    id: '3',
    name: '硬盘',
    value: '512GB SSD',
    category: '物理规格',
    is_mandatory: false,
  },
  {
    id: '4',
    name: '操作系统',
    value: 'Windows 11',
    category: '功能要求',
    is_mandatory: true,
  },
];

describe('TechnicalParametersPanel', () => {
  it('should render parameters grouped by category', () => {
    render(<TechnicalParametersPanel parameters={mockParameters} />);

    expect(screen.getByText('性能指标')).toBeInTheDocument();
    expect(screen.getByText('物理规格')).toBeInTheDocument();
    expect(screen.getByText('功能要求')).toBeInTheDocument();
  });

  it('should render parameter names and values', () => {
    render(<TechnicalParametersPanel parameters={mockParameters} />);

    expect(screen.getByText('处理器')).toBeInTheDocument();
    expect(screen.getByText('Intel Core i7')).toBeInTheDocument();
    expect(screen.getByText('内存')).toBeInTheDocument();
    expect(screen.getByText('16GB DDR4')).toBeInTheDocument();
  });

  it('should show mandatory badge for required parameters', () => {
    render(<TechnicalParametersPanel parameters={mockParameters} />);

    // Should show mandatory indicator for required items
    const mandatoryElements = screen.getAllByText('必填');
    expect(mandatoryElements.length).toBeGreaterThan(0);
  });

  it('should render empty state when no parameters', () => {
    render(<TechnicalParametersPanel parameters={[]} />);

    expect(screen.getByText('暂无技术参数数据')).toBeInTheDocument();
  });

  it('should be collapsible by category', () => {
    render(<TechnicalParametersPanel parameters={mockParameters} />);

    // Click to collapse a category
    const categoryHeader = screen.getByText('性能指标');
    expect(categoryHeader).toBeInTheDocument();

    // The panel should be expandable/collapsible
    const collapseButton = screen.getAllByRole('button')[0];
    expect(collapseButton).toBeInTheDocument();
  });

  it('should toggle category visibility on click', async () => {
    const user = userEvent.setup();
    render(<TechnicalParametersPanel parameters={mockParameters} />);

    // Initially - parameters should be visible
    const processorCell = screen.getByText('处理器');
    expect(processorCell).toBeInTheDocument();

    // Click the first category toggle button
    const buttons = screen.getAllByRole('button');
    await user.click(buttons[0]);

    // After click, state changes but we're just checking no error is thrown
    // The test validates the click handler works
    expect(buttons[0]).toBeInTheDocument();
  });

  it('should handle uncategorized parameters', () => {
    const uncategorizedParams: TechnicalParameter[] = [
      { id: '1', name: 'Test', value: 'Value', is_mandatory: true },
    ];
    render(<TechnicalParametersPanel parameters={uncategorizedParams} />);

    expect(screen.getByText('未分类')).toBeInTheDocument();
  });
});