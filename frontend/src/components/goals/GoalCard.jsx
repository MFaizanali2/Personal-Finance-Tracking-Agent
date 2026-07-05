import { Trash2, Plus, CheckCircle, Clock } from 'lucide-react';
import { formatCurrency } from '@/utils';

const statusColors = {
  active: 'bg-green-100 text-green-700',
  completed: 'bg-blue-100 text-blue-700',
  cancelled: 'bg-red-100 text-red-700',
};

export default function GoalCard({ goal, onAddProgress, onDelete }) {
  const pct = goal.progress_pct || 0;
  const isCompleted = goal.status === 'completed';
  const remaining = Math.max(goal.target_amount - goal.current_amount, 0);
  const monthly = goal.monthly_contribution || 1;
  const monthsLeft = Math.round(remaining / monthly);

  return (
    <div className={`card p-5 ${isCompleted ? 'opacity-70' : ''}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-lg truncate">{goal.name}</h3>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${statusColors[goal.status] || 'bg-gray-100 text-gray-700'}`}>
              {goal.status}
            </span>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
            <span>{goal.category}</span>
            <span>Due {goal.deadline}</span>
          </div>
        </div>
        {onDelete && (
          <button onClick={() => onDelete(goal._id)} className="text-gray-400 hover:text-red-500 transition-colors ml-2 shrink-0" title="Delete goal">
            <Trash2 size={18} />
          </button>
        )}
      </div>

      <div className="mb-2">
        <div className="flex justify-between text-sm mb-1">
          <span>{formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}</span>
          <span className="font-medium">{pct}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div className={`h-2.5 rounded-full transition-all duration-500 ${isCompleted ? 'bg-blue-500' : 'bg-primary-500'}`}
               style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-500 mt-3">
        <div className="flex items-center gap-2">
          <Clock size={14} />
          <span>{monthsLeft} month{monthsLeft !== 1 ? 's' : ''} remaining</span>
        </div>
        {!isCompleted && onAddProgress && (
          <div className="flex gap-1">
            {[100, 200, 500].map((amt) => (
              <button key={amt} onClick={() => onAddProgress(goal._id, amt)}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-primary-100 rounded transition-colors flex items-center gap-0.5">
                <Plus size={12} />{formatCurrency(amt)}
              </button>
            ))}
          </div>
        )}
        {isCompleted && (
          <span className="flex items-center gap-1 text-xs text-blue-600 font-medium">
            <CheckCircle size={14} /> Complete
          </span>
        )}
      </div>
    </div>
  );
}
