/**
 * Tests for ProcurementItemsTable component
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import { ProcurementItemsTable } from '../components/ProcurementItemsTable';
import type { TenderItem } from '../types';
import React from 'react';

const mockItems: TenderItem[] = [
  {
    id: '1',
    name: '办公电脑',
    specification: 'Intel i7/16GB/512GB SSD',
    quantity: 10,
    unit: '台',
    budget_unit_price: 5000,
    budget_total_price: 50000,
    category: '办公设备',
    technical_requirements: '三年质保',
  },
  {
    id: '2',
    name: '打印机',
    specification: '激光打印/黑白',
    quantity: 5,
    unit: '台',
    budget_unit_price: 2000,
    budget_total_price: 10000,
    category: '办公设备',
  },
];

describe('ProcurementItemsTable', () => {
  it('should render table headers correctly', () => {
    render(<ProcurementItemsTable items={mockItems} />);

    expect(screen.getByText('序号')).toBeInTheDocument();
    expect(screen.getByText('名称')).toBeInTheDocument();
    expect(screen.getByText('规格型号')).toBeInTheDocument();
    expect(screen.getByText('数量')).toBeInTheDocument();
    expect(screen.getByText('单位')).toBeInTheDocument();
    expect(screen.getByText('预算单价(元)')).toBeInTheDocument();
    expect(screen.getByText('预算总价(元)')).toBeInTheDocument();
  });

  it('should render procurement items data', () => {
    render(<ProcurementItemsTable items={mockItems} />);

    expect(screen.getByText('办公电脑')).toBeInTheDocument();
    expect(screen.getByText('Intel i7/16GB/512GB SSD')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('5,000')).toBeInTheDocument();
    expect(screen.getByText('50,000')).toBeInTheDocument();
  });

  it('should render empty state when no items', () => {
    render(<ProcurementItemsTable items={[]} />);

    expect(screen.getByText('暂无采购物品数据')).toBeInTheDocument();
  });

  it('should render category and technical requirements', () => {
    render(<ProcurementItemsTable items={mockItems} />);

    // Check category is in table
    expect(screen.getAllByText('办公设备').length).toBeGreaterThan(0);
    expect(screen.getByText('三年质保')).toBeInTheDocument();
  });

  it('should display total budget at bottom', () => {
    render(<ProcurementItemsTable items={mockItems} />);

    expect(screen.getByText(/预算总计:/)).toBeInTheDocument();
    expect(screen.getByText('60,000')).toBeInTheDocument();
  });
});