import { Edit3, Trash2 } from 'lucide-react';
import { formatCurrency } from '@/utils';

const statusInfo = {
  ok: { color: 'text-green-600', bg: 'bg-green-100', bar: 'bg-green-500' },
  warning: { color: 'text-yellow-600', bg: 'bg-yellow-100', bar: 'bg-yellow-500' },
  exceeded: { color: 'text-red-600', bg: 'bg-red-100', bar: 'bg-red-500' },
};

export default function BudgetCard({ budget, onEdit, onDelete }) {
  const spent = budget.spent_so_far || 0;
  const limit = budget.monthly_limit || budget.limit || 0;
  const pct = limit > 0 ? Math.round((spent / limit) * 100) : 0;
  const status = pct >= 100 ? 'exceeded' : pct >= 80 ? 'warning' : 'ok';
  const info = statusInfo[status];

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${info.bg} ${info.color}`}>{status}</span>
          <h3 className="font-semibold">{budget.category}</h3>
        </div>
        <div className="flex gap-1">
          {onEdit && (
            <button onClick={() => onEdit(budget)} className="text-gray-400 hover:text-blue-500 transition-colors" title="Edit">
              <Edit3 size={15} />
            </button>
          )}
          {onDelete && (
            <button onClick={() => onDelete(budget._id)} className="text-gray-400 hover:text-red-500 transition-colors" title="Delete">
              <Trash2 size={15} />
            </button>
          )}
        </div>
      </div>

      <div className="mb-1">
        <div className="flex justify-between text-sm mb-1">
          <span>{formatCurrency(spent)} / {formatCurrency(limit)}</span>
          <span className="font-medium">{pct}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className={`h-2 rounded-full transition-all ${info.bar}`} style={{ width: `${Math.min(pct, 100)}%` }} />
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-2">
        {budget.month || ''}
        {budget.remaining != null ? ` \u00b7 ${formatCurrency(budget.remaining)} remaining` : ''}
      </p>
    </div>
  );
}
