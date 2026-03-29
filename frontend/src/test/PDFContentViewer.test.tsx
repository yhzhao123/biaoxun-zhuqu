/**
 * Tests for PDFContentViewer component
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen, render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PDFContentViewer } from '../components/PDFContentViewer';
import React from 'react';

const mockPdfContent = `招标文件

一、项目概况
本次招标采购办公设备一批，包括台式电脑、打印机等。

二、技术要求
1. 台式电脑配置要求：
   - 处理器：Intel Core i7 或同等以上
   - 内存：16GB DDR4
   - 硬盘：512GB SSD

2. 打印机要求：
   - 类型：激光打印机
   - 支持双面打印

三、投标要求
1. 投标人具有独立法人资格
2. 具有相关产品销售资质
3. 近三年无重大违法记录`;

describe('PDFContentViewer', () => {
  it('should render PDF content', () => {
    render(<PDFContentViewer content={mockPdfContent} />);

    // The content is in a pre element, check it exists with expected text
    const preElement = document.querySelector('pre');
    expect(preElement).toBeInTheDocument();
    expect(preElement?.textContent).toContain('招标文件');
    expect(preElement?.textContent).toContain('一、项目概况');
  });

  it('should display empty state when no content', () => {
    render(<PDFContentViewer content="" />);

    expect(screen.getByText('暂无PDF内容')).toBeInTheDocument();
  });

  it('should have search functionality', async () => {
    const user = userEvent.setup();
    render(<PDFContentViewer content={mockPdfContent} />);

    const searchInput = screen.getByPlaceholderText('搜索内容...');
    expect(searchInput).toBeInTheDocument();

    await user.type(searchInput, '打印机');
    // Search should show match count - there are 3 matches in the content
    expect(screen.getByText(/找到.*3.*处匹配/)).toBeInTheDocument();
  });

  it('should display word count', () => {
    render(<PDFContentViewer content={mockPdfContent} />);

    expect(screen.getByText(/字数:/)).toBeInTheDocument();
  });

  it('should have expand/collapse toggle', () => {
    render(<PDFContentViewer content={mockPdfContent} />);

    // Should have a toggle button
    const toggleButton = screen.getByRole('button', { name: /收起|展开/ });
    expect(toggleButton).toBeInTheDocument();
  });
});