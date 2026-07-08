import React from 'react';
import { GoalCreateInput } from '../../types';
import { useForm } from 'react-hook-form';

interface GoalFormProps {
  userId: string;
  onSubmit: (data: GoalCreateInput) => void;
  loading?: boolean;
}

export const GoalForm: React.FC<GoalFormProps> = ({
  userId,
  onSubmit,
  loading = false,
}) => {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<GoalCreateInput>({
    defaultValues: {
      user_id: userId,
      goal_type: 'short_term',
      priority: 'medium',
    },
  });

  const handleFormSubmit = (data: GoalCreateInput) => {
    onSubmit(data);
    reset();
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className="bg-white rounded-lg border border-gray-200 p-6"
    >
      <h3 className="text-lg font-semibold mb-4">{'\ud83c\udfaf'} Create New Goal</h3>

      {/* Goal Name */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Goal Name *
        </label>
        <input
          type="text"
          placeholder="e.g., Emergency Fund, Vacation"
          {...register('goal_name', { required: 'Goal name is required' })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.goal_name && (
          <p className="text-red-500 text-xs mt-1">{errors.goal_name.message}</p>
        )}
      </div>

      {/* Description */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          placeholder="Why is this goal important?"
          {...register('description')}
          rows={2}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Grid: 2 columns */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Goal Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Type *
          </label>
          <select
            {...register('goal_type')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="short_term">Short Term (3-6 months)</option>
            <option value="long_term">Long Term (1+ years)</option>
          </select>
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Priority *
          </label>
          <select
            {...register('priority')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>

      {/* Grid: 2 columns */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Target Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Target Amount (PKR) *
          </label>
          <input
            type="number"
            placeholder="50000"
            {...register('target_amount', {
              required: 'Amount is required',
              min: { value: 1, message: 'Must be positive' },
            })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.target_amount && (
            <p className="text-red-500 text-xs mt-1">{errors.target_amount.message}</p>
          )}
        </div>

        {/* Deadline */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Deadline *
          </label>
          <input
            type="datetime-local"
            {...register('deadline', { required: 'Deadline is required' })}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.deadline && (
            <p className="text-red-500 text-xs mt-1">{errors.deadline.message}</p>
          )}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating...' : '\u2728 Create Goal'}
      </button>
    </form>
  );
};

export default GoalForm;
