'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Calendar, Loader2 } from 'lucide-react';
import { resumeApi } from '@/lib/api/client';

type AggregationType = 'daily' | 'weekly' | 'monthly' | 'yearly';

interface ChartData {
  date: string;
  count: number;
}

export function ResumeStatisticsChart() {
  const [aggregation, setAggregation] = useState<AggregationType>('weekly');
  const [chartData, setChartData] = useState<ChartData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [totalResumes, setTotalResumes] = useState(0);

  useEffect(() => {
    fetchStatistics();
  }, [aggregation]);

  const fetchStatistics = async () => {
    try {
      setIsLoading(true);
      const response = await resumeApi.getStatistics(aggregation);
      
      // Transform the data for recharts
      const data = response.data.map((item: any) => ({
        date: formatDate(item.date, aggregation),
        count: item.count
      }));
      
      setChartData(data);
      setTotalResumes(response.total_count);
    } catch (error) {
      console.error('Failed to fetch resume statistics:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string, type: AggregationType): string => {
    const date = new Date(dateStr);
    
    switch (type) {
      case 'daily':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      case 'weekly':
        return `Week of ${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
      case 'monthly':
        return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      case 'yearly':
        return date.getFullYear().toString();
      default:
        return dateStr;
    }
  };

  const aggregationOptions: { value: AggregationType; label: string }[] = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'yearly', label: 'Yearly' }
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <Calendar className="mr-2 h-5 w-5" />
            Resume Upload Trends
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Total resumes: {totalResumes}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {aggregationOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setAggregation(option.value)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                aggregation === option.value
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="h-64 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400">No data available for the selected period</p>
        </div>
      ) : (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis 
                dataKey="date" 
                className="text-xs"
                tick={{ fill: 'currentColor' }}
                angle={aggregation === 'daily' && chartData.length > 7 ? -45 : 0}
                textAnchor={aggregation === 'daily' && chartData.length > 7 ? 'end' : 'middle'}
                height={aggregation === 'daily' && chartData.length > 7 ? 80 : 40}
              />
              <YAxis 
                className="text-xs"
                tick={{ fill: 'currentColor' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--tooltip-bg)',
                  border: '1px solid var(--tooltip-border)',
                  borderRadius: '6px'
                }}
                labelStyle={{ color: 'var(--tooltip-text)' }}
              />
              <Legend />
              <Bar 
                dataKey="count" 
                fill="#4F46E5" 
                name="Resumes Added"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}