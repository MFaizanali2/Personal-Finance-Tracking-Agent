import React from 'react';
import { Budget } from '../../types';
import { ProgressBar } from '../common/ProgressBar';

interface BudgetCardProps {
  budget: Budget;
  onAddSpending?: (budgetId: string, amount: number) => void;
  onEdit?: (budget: Budget) => void;
  onDelete?: (budgetId: string) => void;
}

export const BudgetCard: React.FC<BudgetCardProps> = ({
  budget,
  onAddSpending,
  onEdit,
  onDelete,
}) => {
  const [showAddSpending, setShowAddSpending] = React.useState(false);
  const [spendingAmount, setSpendingAmount] = React.useState('');

  const handleAddSpending = () => {
    const amount = parseFloat(spendingAmount);
    if (amount > 0 && onAddSpending) {
      onAddSpending(budget.budget_id, amount);
      setSpendingAmount('');
      setShowAddSpending(false);
    }
  };

  const spent_pct = budget.spent_percentage || (budget.spent_so_far / budget.monthly_limit) * 100;
  const remaining = budget.remaining_amount || budget.monthly_limit - budget.spent_so_far;

  const statusColors = {
    ok: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', emoji: '✅' },
    warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', emoji: '⚠️' },
    exceeded: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', emoji: '❌' },
  };

  const status = spent_pct >= 100 ? 'exceeded' : spent_pct >= 80 ? 'warning' : 'ok';
  const colors = statusColors[status];
  const progressColor = status === 'ok' ? 'green' : status === 'warning' ? 'yellow' : 'red';

  return (
    <div className={`rounded-lg border p-5 ${colors.bg} ${colors.border}`}>
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{colors.emoji}</span>
          <div>
            <h3 className={`font-semibold ${colors.text}`}>{budget.category}</h3>
            <p className="text-xs text-gray-500">{budget.month}</p>
          </div>
        </div>
      </div>

      {/* Progress */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className={colors.text}>PKR {budget.spent_so_far.toLocaleString()}</span>
          <span className="text-gray-600">PKR {budget.monthly_limit.toLocaleString()}</span>
        </div>
        <ProgressBar
          current={budget.spent_so_far}
          target={budget.monthly_limit}
          color={progressColor}
        />
        <p className={`text-xs mt-1 ${colors.text}`}>
          {Math.round(spent_pct)}% spent • PKR {remaining.toLocaleString()} remaining
        </p>
      </div>

      {/* Add Spending */}
      {showAddSpending && (
        <div className="bg-white rounded p-3 mb-4 flex gap-2">
          <input
            type="number"
            placeholder="Amount"
            value={spendingAmount}
            onChange={(e) => setSpendingAmount(e.target.value)}
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
          />
          <button
            onClick={handleAddSpending}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
          >
            Add
          </button>
          <button
            onClick={() => setShowAddSpending(false)}
            className="px-3 py-1 bg-gray-300 rounded text-sm"
          >
            ✕
          </button>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => setShowAddSpending(!showAddSpending)}
          className="flex-1 px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          💸 Add Spending
        </button>
        <button
          onClick={() => onEdit?.(budget)}
          className="flex-1 px-3 py-2 bg-gray-400 text-white rounded text-sm hover:bg-gray-500"
        >
          ✏️
        </button>
        <button
          onClick={() => onDelete?.(budget.budget_id)}
          className="flex-1 px-3 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600"
        >
          🗑️
        </button>
      </div>
    </div>
  );
};
