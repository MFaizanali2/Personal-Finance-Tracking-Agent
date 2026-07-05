import { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react';
import { formatCurrency } from '@/utils';
import { CATEGORY_COLORS, BUDGET_STATUS_COLORS } from '@/constants';
import BudgetList from './BudgetList';
import BudgetForm from './BudgetForm';
import useStore from '@/store';

export default function BudgetDashboard() {
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));
  const [vsActual, setVsActual] = useState(null);
  const [budgetList, setBudgetList] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const store = useStore();

  const loadData = async () => {
    try {
      const { default: store } = await import('@/store');
      const { api } = await import('@/api/client');

      const [vsResult, budgetResult, alertResult] = await Promise.all([
        api.getBudgetVsActual(month).catch(() => null),
        api.getUserBudgets('default', month).catch(() => null),
        api.checkBudgetAlerts({ user_id: 'default' }).catch(() => null),
      ]);
      setVsActual(vsResult);
      setBudgetList(budgetResult?.budgets || []);
      setAlerts(alertResult?.alerts || []);
    } catch { /* silent */ }
  };

  useEffect(() => { loadData(); }, [month]);

  const pieData = vsActual?.categories?.map((c) => ({
    name: c.category, value: c.actual,
  })) || [];

  const barData = vsActual?.categories?.map((c) => ({
    name: c.category, Budget: c.budget, Actual: c.actual,
  })) || [];

  const handleEdit = (budget) => {
    /* future: inline edit modal */
  };

  const handleDelete = async (budgetId) => {
    try {
      const { api } = await import('@/api/client');
      await api.deleteBudget(budgetId);
      loadData();
    } catch { /* silent */ }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h2 className="text-xl font-semibold">Budget Overview</h2>
        <BudgetForm />
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
            <p className={`text-2xl font-bold ${(vsActual.total_budget - vsActual.total_actual) < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatCurrency(vsActual.total_budget - vsActual.total_actual)}
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="card p-4">
          <h3 className="font-semibold mb-3">Spending by Category</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90}
                   label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {pieData.map((e) => <Cell key={e.name} fill={CATEGORY_COLORS[e.name] || '#6b7280'} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3">Budget vs Actual</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Budget" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Actual" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-4 mb-6">
        <h3 className="font-semibold mb-3 flex items-center gap-2">
          <TrendingUp size={18} className="text-blue-500" /> Budget Limits
        </h3>
        <BudgetList budgets={budgetList} month={month} onMonthChange={setMonth}
                    onEdit={handleEdit} onDelete={handleDelete} />
      </div>

      {alerts.length > 0 && (
        <div className="card p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle size={18} className="text-yellow-500" /> Alerts ({alerts.length})
          </h3>
          <div className="space-y-2">
            {alerts.map((a, i) => (
              <div key={i} className={`flex items-center justify-between p-3 rounded border-l-4 ${
                a.severity === 'critical' ? 'border-red-400 bg-red-50' :
                a.severity === 'warning' ? 'border-yellow-400 bg-yellow-50' : 'border-blue-400 bg-blue-50'
              }`}>
                <div>
                  <p className="text-sm font-medium">{a.message}</p>
                  <p className="text-xs text-gray-500">{a.category} - {a.percentage}% used</p>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  a.severity === 'critical' ? 'bg-red-100 text-red-700' :
                  a.severity === 'warning' ? 'bg-yellow-100 text-yellow-700' : 'bg-blue-100 text-blue-700'
                }`}>{a.severity}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
