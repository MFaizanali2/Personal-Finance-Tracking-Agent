import React from 'react';
import { Budget } from '../../types';
import { BudgetCard } from './BudgetCard';

interface BudgetListProps {
  budgets: Budget[];
  onAddSpending?: (budgetId: string, amount: number) => void;
  onEdit?: (budget: Budget) => void;
  onDelete?: (budgetId: string) => void;
  loading?: boolean;
}

export const BudgetList: React.FC<BudgetListProps> = ({
  budgets,
  onAddSpending,
  onDelete,
  loading,
}) => {
  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading budgets...</div>;
  }

  if (budgets.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No budgets yet {'\ud83d\udcb0'}</p>
        <p className="text-gray-400 text-sm">Create a budget to track spending by category</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {budgets.map((budget) => (
        <BudgetCard
          key={budget.budget_id}
          budget={budget}
          onAddSpending={onAddSpending}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
