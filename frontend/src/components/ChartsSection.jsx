import { useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts';
import useStore from '@/store';
import { CATEGORIES, CATEGORY_COLORS } from '@/constants';

export default function ChartsSection() {
  const transactions = useStore((s) => s.transactions);

  const pieData = useMemo(() => {
    const map = {};
    transactions.forEach((t) => {
      map[t.category] = (map[t.category] || 0) + t.amount;
    });
    return CATEGORIES.filter((c) => map[c])
      .map((c) => ({ name: c, value: Math.round(map[c] * 100) / 100 }));
  }, [transactions]);

  const barData = useMemo(() => {
    const map = {};
    transactions.forEach((t) => {
      map[t.category] = (map[t.category] || 0) + t.amount;
    });
    return CATEGORIES.filter((c) => map[c])
      .map((c) => ({ category: c, amount: Math.round(map[c] * 100) / 100 }));
  }, [transactions]);

  if (transactions.length === 0) {
    return (
      <div className="card text-center py-8">
        <p className="text-gray-400">Add transactions to see charts</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Spending by Category</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={pieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
            >
              {pieData.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={CATEGORY_COLORS[entry.name] || '#6b7280'}
                />
              ))}
            </Pie>
            <Tooltip formatter={(v) => `$${v.toFixed(2)}`} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Category Spending</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="category" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => `$${v.toFixed(2)}`} />
            <Legend />
            <Bar dataKey="amount" name="Amount ($)" radius={[4, 4, 0, 0]}>
              {barData.map((entry) => (
                <Cell
                  key={entry.category}
                  fill={CATEGORY_COLORS[entry.category] || '#6b7280'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
