import { useState } from 'react';
import { Calendar, DollarSign } from 'lucide-react';
import BudgetCard from './BudgetCard';

export default function BudgetList({ budgets, month, onMonthChange, onEdit, onDelete }) {
  const totalLimit = budgets.reduce((s, b) => s + (b.monthly_limit || b.limit || 0), 0);
  const totalSpent = budgets.reduce((s, b) => s + (b.spent_so_far || 0), 0);
  const pct = totalLimit > 0 ? Math.round((totalSpent / totalLimit) * 100) : 0;

  const sorted = [...budgets].sort((a, b) => {
    const pctA = (a.spent_so_far || 0) / (a.monthly_limit || a.limit || 1);
    const pctB = (b.spent_so_far || 0) / (b.monthly_limit || b.limit || 1);
    return pctB - pctA;
  });

  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <Calendar size={16} className="text-gray-400" />
        <input type="month" className="input max-w-[180px]" value={month}
               onChange={(e) => onMonthChange?.(e.target.value)} />
      </div>

      {budgets.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Total Budget</p>
            <p className="text-xl font-bold">{formatCurrency(totalLimit)}</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Total Spent</p>
            <p className="text-xl font-bold">{formatCurrency(totalSpent)}</p>
          </div>
          <div className="card p-3 text-center">
            <p className="text-xs text-gray-500">Utilization</p>
            <p className={`text-xl font-bold ${pct >= 100 ? 'text-red-600' : pct >= 80 ? 'text-yellow-600' : 'text-green-600'}`}>{pct}%</p>
          </div>
        </div>
      )}

      {budgets.length === 0 && (
        <div className="card p-8 text-center text-gray-500">
          <DollarSign size={48} className="mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium mb-1">No budgets set</p>
          <p className="text-sm">Create a budget to start tracking your spending limits.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sorted.map((budget) => (
          <BudgetCard key={budget._id} budget={budget} onEdit={onEdit} onDelete={onDelete} />
        ))}
      </div>
    </div>
  );
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount ?? 0);
}
