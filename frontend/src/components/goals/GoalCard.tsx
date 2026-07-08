import React from 'react';
import { Goal } from '../../types';
import { ProgressBar } from '../common/ProgressBar';

interface GoalCardProps {
  goal: Goal;
  onAddProgress?: (goalId: string, amount: number) => void;
  onEdit?: (goal: Goal) => void;
  onDelete?: (goalId: string) => void;
}

export const GoalCard: React.FC<GoalCardProps> = ({
  goal,
  onAddProgress,
  onDelete,
}) => {
  const [showAddProgress, setShowAddProgress] = React.useState(false);
  const [progressAmount, setProgressAmount] = React.useState('');

  const handleAddProgress = () => {
    const amount = parseFloat(progressAmount);
    if (amount > 0 && onAddProgress) {
      onAddProgress(goal.goal_id, amount);
      setProgressAmount('');
      setShowAddProgress(false);
    }
  };

  const priorityColors = {
    low: 'bg-blue-100 text-blue-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
  };

  const statusEmojis = {
    active: '\ud83c\udfaf',
    completed: '\u2705',
    abandoned: '\u274c',
  };

  const daysRemaining = Math.ceil(
    (new Date(goal.deadline).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{statusEmojis[goal.status]}</span>
            <h3 className="text-lg font-semibold text-gray-800">{goal.goal_name}</h3>
          </div>
          <p className="text-sm text-gray-500">{goal.description}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${priorityColors[goal.priority]}`}>
          {goal.priority}
        </span>
      </div>

      {/* Progress Section */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progress</span>
          <span className="font-semibold">
            PKR {goal.current_amount.toLocaleString()} / PKR {goal.target_amount.toLocaleString()}
          </span>
        </div>
        <ProgressBar current={goal.current_amount} target={goal.target_amount} />
        <p className="text-xs text-gray-500 mt-1">
          {goal.progress_percentage?.toFixed(1)}% complete
        </p>
      </div>

      {/* Timeline */}
      {goal.status === 'active' && (
        <div className="bg-gray-50 rounded p-3 mb-4 text-sm">
          <div className="flex justify-between text-gray-600">
            <span>Days Remaining:</span>
            <span className="font-semibold">{daysRemaining} days</span>
          </div>
          <div className="flex justify-between text-gray-600 mt-1">
            <span>Type:</span>
            <span className="font-semibold">{goal.goal_type.replace('_', ' ')}</span>
          </div>
        </div>
      )}

      {/* Add Progress Section */}
      {showAddProgress && goal.status === 'active' && (
        <div className="bg-blue-50 rounded p-3 mb-4 flex gap-2">
          <input
            type="number"
            placeholder="Amount to add"
            value={progressAmount}
            onChange={(e) => setProgressAmount(e.target.value)}
            className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
          />
          <button
            onClick={handleAddProgress}
            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
          >
            Add
          </button>
          <button
            onClick={() => setShowAddProgress(false)}
            className="px-3 py-1 bg-gray-300 text-gray-700 rounded text-sm"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {goal.status === 'active' && (
          <button
            onClick={() => setShowAddProgress(!showAddProgress)}
            className="flex-1 px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600"
          >
            {'\ud83d\udcb0'} Add Progress
          </button>
        )}
        <button
          onClick={() => onDelete?.(goal.goal_id)}
          className="flex-1 px-3 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600"
        >
          {'\ud83d\uddd1\ufe0f'} Delete
        </button>
      </div>
    </div>
  );
};
