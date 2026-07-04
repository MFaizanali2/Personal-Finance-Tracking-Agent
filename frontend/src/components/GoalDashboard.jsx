import { useEffect, useState } from 'react';
import { Target, TrendingUp, CheckCircle } from 'lucide-react';
import useStore from '@/store';
import GoalList from './GoalList';

export default function GoalDashboard() {
  const { goals, fetchGoals, updateGoal, deleteGoal } = useStore();
  const [summary, setSummary] = useState(null);

  useEffect(() => { fetchGoals(); }, [fetchGoals]);

  useEffect(() => {
    if (goals.length > 0) {
      const active = goals.filter((g) => g.status === 'active');
      const completed = goals.filter((g) => g.status === 'completed');
      const totalTarget = goals.reduce((s, g) => s + g.target_amount, 0);
      const totalSaved = goals.reduce((s, g) => s + g.current_amount, 0);
      const overallPct = totalTarget > 0 ? Math.round((totalSaved / totalTarget) * 100) : 0;
      setSummary({ active: active.length, completed: completed.length, totalTarget, totalSaved, overallPct });
    } else {
      setSummary(null);
    }
  }, [goals]);

  const handleAddProgress = async (goalId, amount) => {
    try {
      const { default: store } = await import('@/store');
      const { api } = await import('@/api/client');
      const result = await api.addGoalProgress(goalId, amount);
      const state = store.getState();
      state.fetchGoals();
    } catch {
      await updateGoal(goalId, { current_amount: amount });
    }
  };

  return (
    <div>
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="card p-4 flex items-center gap-3">
            <Target size={24} className="text-primary-600" />
            <div>
              <p className="text-sm text-gray-500">Active Goals</p>
              <p className="text-2xl font-bold">{summary.active}</p>
            </div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <CheckCircle size={24} className="text-green-600" />
            <div>
              <p className="text-sm text-gray-500">Completed</p>
              <p className="text-2xl font-bold">{summary.completed}</p>
            </div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <TrendingUp size={24} className="text-blue-600" />
            <div>
              <p className="text-sm text-gray-500">Overall Progress</p>
              <p className="text-2xl font-bold">{summary.overallPct}%</p>
            </div>
          </div>
          <div className="card p-4 flex items-center gap-3">
            <Target size={24} className="text-purple-600" />
            <div>
              <p className="text-sm text-gray-500">Total Saved</p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalSaved)}</p>
            </div>
          </div>
        </div>
      )}

      <GoalList goals={goals} onAddProgress={handleAddProgress} onDelete={deleteGoal} />
    </div>
  );
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount ?? 0);
}
