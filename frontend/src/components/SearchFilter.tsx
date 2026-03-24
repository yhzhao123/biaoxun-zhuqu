/**
 * SearchFilter component - Phase 4 Task 024-025
 * Search and filter controls for tender list
 */

import React, { useState, useCallback, useEffect } from 'react';
import type { TenderFilter } from '../../types';

interface SearchFilterProps {
  onFilterChange: (filter: TenderFilter) => void;
  initialFilter?: TenderFilter;
}

const REGIONS = ['Beijing', 'Shanghai', 'Guangdong', 'Zhejiang', 'Jiangsu', 'Other'];
const INDUSTRIES = ['IT', 'Construction', 'Healthcare', 'Education', 'Finance', 'Other'];
const STATUSES = [
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'closed', label: 'Closed' },
  { value: 'expired', label: 'Expired' },
];

export const SearchFilter: React.FC<SearchFilterProps> = ({
  onFilterChange,
  initialFilter,
}) => {
  const [filter, setFilter] = useState<TenderFilter>(initialFilter || {});
  const [searchInput, setSearchInput] = useState(initialFilter?.search || '');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setFilter((prev) => ({ ...prev, search: searchInput }));
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  // Notify parent when filter changes
  useEffect(() => {
    onFilterChange(filter);
  }, [filter, onFilterChange]);

  const handleFilterChange = useCallback((key: keyof TenderFilter, value: string | undefined) => {
    setFilter((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleClear = () => {
    setFilter({});
    setSearchInput('');
  };

  const hasActiveFilters = Object.values(filter).some((v) => v !== undefined && v !== '');

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      {/* Search input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search
        </label>
        <div className="relative">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by title, tenderer..."
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {searchInput && (
            <button
              onClick={() => setSearchInput('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Filter row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Status filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={filter.status || ''}
            onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            {STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {/* Region filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Region
          </label>
          <select
            value={filter.region || ''}
            onChange={(e) => handleFilterChange('region', e.target.value || undefined)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            {REGIONS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>

        {/* Industry filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Industry
          </label>
          <select
            value={filter.industry || ''}
            onChange={(e) => handleFilterChange('industry', e.target.value || undefined)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All</option>
            {INDUSTRIES.map((i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Budget range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Budget
          </label>
          <input
            type="number"
            value={filter.min_budget || ''}
            onChange={(e) =>
              handleFilterChange(
                'min_budget',
                e.target.value ? parseInt(e.target.value) : undefined
              )
            }
            placeholder="0"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max Budget
          </label>
          <input
            type="number"
            value={filter.max_budget || ''}
            onChange={(e) =>
              handleFilterChange(
                'max_budget',
                e.target.value ? parseInt(e.target.value) : undefined
              )
            }
            placeholder="∞"
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Date range */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Start Date
          </label>
          <input
            type="date"
            value={filter.start_date || ''}
            onChange={(e) => handleFilterChange('start_date', e.target.value || undefined)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            End Date
          </label>
          <input
            type="date"
            value={filter.end_date || ''}
            onChange={(e) => handleFilterChange('end_date', e.target.value || undefined)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Clear button */}
      {hasActiveFilters && (
        <div className="flex justify-end">
          <button
            onClick={handleClear}
            className="text-sm text-gray-600 hover:text-gray-900 underline"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchFilter;
