import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import useStore from '@/store';
import { formatCurrency } from '@/utils';
import { CATEGORY_COLORS, BUDGET_STATUS_COLORS } from '@/constants';

export default function BudgetTracking() {
  const { fetchBudgetThresholds, budgetThresholds, fetchBudgetRecommendations, budgetRecommendations } = useStore();
  const [vsActual, setVsActual] = useState(null);
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));

  useEffect(() => {
    fetchBudgetThresholds();
    fetchBudgetRecommendations();
    loadVsActual();
  }, [fetchBudgetThresholds, fetchBudgetRecommendations, month]);

  const loadVsActual = async () => {
    const { default: store } = await import('@/store');
    const data = await store.getState().fetchBudgetVsActual(month);
    setVsActual(data);
  };

  const pieData = vsActual?.categories?.map((c) => ({
    name: c.category, value: c.actual,
  })) || [];

  const barData = vsActual?.categories?.map((c) => ({
    name: c.category, Budget: c.budget, Actual: c.actual,
  })) || [];

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <h2 className="text-lg font-semibold">Budget Tracking</h2>
        <input type="month" className="input max-w-[180px]" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      {vsActual && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="card p-4">
            <p className="text-sm text-gray-500">Total Budget</p>
            <p className="text-2xl font-bold">{formatCurrency(vsActual.total_budget)}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">Total Spent</p>
            <p className="text-2xl font-bold">{formatCurrency(vsActual.total_actual)}</p>
          </div>
          <div className="card p-4">
            <p className="text-sm text-gray-500">Remaining</p>
            <p className="text-2xl font-bold">{formatCurrency(vsActual.total_budget - vsActual.total_actual)}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card p-4">
          <h3 className="font-semibold mb-3">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart><Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
              {pieData.map((e) => <Cell key={e.name} fill={CATEGORY_COLORS[e.name] || '#6b7280'} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3">Budget vs Actual</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis /><Tooltip /><Legend />
              <Bar dataKey="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Actual" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><AlertTriangle size={18} className="text-yellow-500" /> Budget Thresholds</h3>
          {budgetThresholds.length === 0 && <p className="text-sm text-gray-500">Set a budget to see thresholds</p>}
          <div className="space-y-2">
            {budgetThresholds.map((t) => (
              <div key={t.category} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div>
                  <p className="font-medium text-sm">{t.category}</p>
                  <p className="text-xs text-gray-500">{t.percentage}% used</p>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${BUDGET_STATUS_COLORS[t.status] || 'bg-gray-500'}`} />
                  <span className={`text-xs font-medium ${t.status === 'over' ? 'text-red-600' : t.status === 'warning' ? 'text-yellow-600' : 'text-green-600'}`}>{t.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2"><TrendingUp size={18} className="text-blue-500" /> Recommendations</h3>
          {budgetRecommendations.length === 0 && <p className="text-sm text-gray-500">Set a budget to see recommendations</p>}
          <div className="space-y-2">
            {budgetRecommendations.map((r, i) => (
              <div key={i} className={`p-3 rounded border-l-4 ${r.severity === 'critical' ? 'border-red-400 bg-red-50' : r.severity === 'warning' ? 'border-yellow-400 bg-yellow-50' : 'border-blue-400 bg-blue-50'}`}>
                <p className="text-sm font-medium">{r.message}</p>
                {r.suggestion && <p className="text-xs text-gray-600 mt-1">{r.suggestion}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
