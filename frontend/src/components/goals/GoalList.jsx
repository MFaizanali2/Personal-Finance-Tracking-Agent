import { useState } from 'react';
import { Filter, Target } from 'lucide-react';
import GoalCard from './GoalCard';

export default function GoalList({ goals, onAddProgress, onDelete }) {
  const [filter, setFilter] = useState('all');

  const filtered = filter === 'all' ? goals : goals.filter((g) => g.status === filter);
  const activeCount = goals.filter((g) => g.status === 'active').length;
  const completedCount = goals.filter((g) => g.status === 'completed').length;
  const totalTarget = goals.reduce((s, g) => s + g.target_amount, 0);
  const totalSaved = goals.reduce((s, g) => s + g.current_amount, 0);

  const sortByPriority = (a, b) => {
    if (a.status === 'active' && b.status !== 'active') return -1;
    if (a.status !== 'active' && b.status === 'active') return 1;
    const aPct = a.progress_pct || 0;
    const bPct = b.progress_pct || 0;
    return aPct - bPct;
  };

  const sorted = [...filtered].sort(sortByPriority);

  const filters = ['all', 'active', 'completed'];

  return (
    <div>
      {goals.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-6">
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Total Goals</p>
            <p className="text-xl font-bold">{goals.length}</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Active</p>
            <p className="text-xl font-bold text-green-600">{activeCount}</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Target</p>
            <p className="text-xl font-bold">{formatCurrency(totalTarget)}</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Saved</p>
            <p className="text-xl font-bold text-primary-600">{formatCurrency(totalSaved)}</p>
          </div>
        </div>
      )}

      {goals.length === 0 && (
        <div className="card p-8 text-center text-gray-500">
          <Target size={48} className="mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium mb-1">No goals yet</p>
          <p className="text-sm">Create your first savings goal above to get started!</p>
        </div>
      )}

      {goals.length > 0 && (
        <>
          <div className="flex items-center gap-2 mb-4">
            <Filter size={16} className="text-gray-400" />
            {filters.map((f) => (
              <button key={f} onClick={() => setFilter(f)}
                      className={`text-xs px-3 py-1 rounded-full transition-colors ${filter === f ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
                {f === 'all' ? ` (${goals.length})` : f === 'active' ? ` (${activeCount})` : ` (${completedCount})`}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sorted.map((goal) => (
              <GoalCard key={goal._id} goal={goal} onAddProgress={onAddProgress} onDelete={onDelete} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount ?? 0);
}
