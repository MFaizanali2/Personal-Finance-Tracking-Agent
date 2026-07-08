import React from 'react';
import { BudgetCreateInput } from '../../types';
import { useForm } from 'react-hook-form';

interface BudgetFormProps {
  userId: string;
  defaultMonth?: string;
  onSubmit: (data: BudgetCreateInput) => void;
  loading?: boolean;
}

const CATEGORIES = [
  'Food',
  'Transport',
  'Entertainment',
  'Utilities',
  'Healthcare',
  'Education',
  'Shopping',
  'Dining',
  'Travel',
  'Other',
];

export const BudgetForm: React.FC<BudgetFormProps> = ({
  userId,
  defaultMonth,
  onSubmit,
  loading = false,
}) => {
  const currentMonth = defaultMonth || new Date().toISOString().slice(0, 7);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<BudgetCreateInput>({
    defaultValues: {
      user_id: userId,
      month: currentMonth,
      category: 'Food',
    },
  });

  const handleFormSubmit = (data: BudgetCreateInput) => {
    onSubmit(data);
    reset();
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className="bg-white rounded-lg border border-gray-200 p-6"
    >
      <h3 className="text-lg font-semibold mb-4">{'\ud83d\udcb0'} New Budget</h3>

      {/* Category */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Category *
        </label>
        <select
          {...register('category', { required: 'Category is required' })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
        {errors.category && (
          <p className="text-red-500 text-xs mt-1">{errors.category.message}</p>
        )}
      </div>

      {/* Monthly Limit */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Monthly Limit (PKR) *
        </label>
        <input
          type="number"
          placeholder="15000"
          {...register('monthly_limit', {
            required: 'Limit is required',
            min: { value: 1, message: 'Must be positive' },
          })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {errors.monthly_limit && (
          <p className="text-red-500 text-xs mt-1">{errors.monthly_limit.message}</p>
        )}
      </div>

      {/* Month */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Month
        </label>
        <input
          type="month"
          {...register('month')}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
      >
        {loading ? 'Creating...' : '\u2728 Create Budget'}
      </button>
    </form>
  );
};
