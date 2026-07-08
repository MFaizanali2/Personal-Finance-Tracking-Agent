import React from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { Budget } from '../../types';

interface BudgetChartProps {
  budgets: Budget[];
  title?: string;
}

export const BudgetChart: React.FC<BudgetChartProps> = ({
  budgets,
  title = 'Spending by Category',
}) => {
  const COLORS = [
    '#3B82F6',
    '#10B981',
    '#F59E0B',
    '#EF4444',
    '#8B5CF6',
    '#EC4899',
    '#06B6D4',
    '#6366F1',
    '#F97316',
    '#14B8A6',
  ];

  const chartData = budgets.map((b) => ({
    name: b.category,
    value: parseFloat(b.spent_so_far.toFixed(2)),
  }));

  if (chartData.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
        <p className="text-gray-500">No budget data available</p>
      </div>
    );
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => `PKR ${value.toLocaleString()}`}
            contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="mt-4 p-4 bg-gray-50 rounded">
        <p className="text-sm text-gray-600">
          Total Spent: <span className="font-semibold">PKR {total.toLocaleString()}</span>
        </p>
      </div>
    </div>
  );
};
