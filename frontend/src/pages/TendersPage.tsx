/**
 * TendersPage - Phase 4
 * Main page for tender list with search and filter
 */

import React, { useState, useCallback } from 'react';
import { TenderList } from '../components/TenderList';
import { SearchFilter } from '../components/SearchFilter';
import type { TenderFilter } from '../types';

export const TendersPage: React.FC = () => {
  const [filter, setFilter] = useState<TenderFilter>({});

  const handleFilterChange = useCallback((newFilter: TenderFilter) => {
    setFilter(newFilter);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">招标公告</h1>
      </div>

      <SearchFilter onFilterChange={handleFilterChange} />
      <TenderList filter={filter} />
    </div>
  );
};

export default TendersPage;
