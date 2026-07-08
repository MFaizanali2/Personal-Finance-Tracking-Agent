import React from 'react';
import { Goal } from '../../types';
import { GoalCard } from './GoalCard';

interface GoalListProps {
  goals: Goal[];
  onAddProgress?: (goalId: string, amount: number) => void;
  onEdit?: (goal: Goal) => void;
  onDelete?: (goalId: string) => void;
  loading?: boolean;
}

export const GoalList: React.FC<GoalListProps> = ({
  goals,
  onAddProgress,
  onDelete,
  loading,
}) => {
  if (loading) {
    return <div className="text-center py-8 text-gray-500">Loading goals...</div>;
  }

  if (goals.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">No goals yet {'\ud83c\udfaf'}</p>
        <p className="text-gray-400 text-sm">Create your first financial goal to get started</p>
      </div>
    );
  }

  const sortedGoals = [...goals].sort((a, b) => {
    const priorityOrder = { high: 1, medium: 2, low: 3 };
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {sortedGoals.map((goal) => (
        <GoalCard
          key={goal.goal_id}
          goal={goal}
          onAddProgress={onAddProgress}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
