import React, { useEffect } from 'react';
import { GoalForm } from './GoalForm';
import { GoalList } from './GoalList';
import { AlertBanner } from '../common/AlertBanner';
import { useFinanceStore } from '../../store/financeStore';
import { useApi } from '../../hooks/useApi';

export const GoalDashboard: React.FC = () => {
  const {
    currentUser,
    goals,
    loading,
    error,
    setError,
    activeGoalsCount,
    completedGoalsCount,
    setLoading,
    addGoal,
    updateGoal,
    removeGoal,
  } = useFinanceStore();

  const { goals: goalsApi } = useApi();

  const [showAlert, setShowAlert] = React.useState(false);

  // Fetch goals on mount
  useEffect(() => {
    const fetchGoals = async () => {
      setLoading(true);
      try {
        const response = await goalsApi.getAll(currentUser);
        if (response) {
          const goalsData = Array.isArray(response) ? response : (response as any).goals || [];
          (goalsData as any[]).forEach((goal: any) => {
            const progress = (goal.current_amount / goal.target_amount) * 100;
            goal.progress_percentage = progress;
            addGoal(goal);
          });
        }
      } catch (err) {
        console.error('Failed to fetch goals:', err);
        setError('Failed to load goals');
      } finally {
        setLoading(false);
      }
    };
    fetchGoals();
  }, [currentUser]);

  const handleAddGoal = async (goalData: any) => {
    setLoading(true);
    try {
      const response = await goalsApi.create(goalData);
      if (response) {
        const newGoal = (response as any).goal || response;
        newGoal.progress_percentage = 0;
        addGoal(newGoal);
        setShowAlert(true);
        setTimeout(() => setShowAlert(false), 3000);
      }
    } catch (err) {
      console.error('Failed to create goal:', err);
      setError('Failed to create goal');
    } finally {
      setLoading(false);
    }
  };

  const handleAddProgress = async (goalId: string, amount: number) => {
    setLoading(true);
    try {
      const response = await goalsApi.addProgress(goalId, { amount });
      if (response) {
        updateGoal(goalId, {
          current_amount: (response as any).new_progress || (response as any).goal?.current_amount,
          progress_percentage: (response as any).progress_percentage,
        });
      }
    } catch (err) {
      console.error('Failed to add progress:', err);
      setError('Failed to add progress');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    if (window.confirm('Delete this goal?')) {
      setLoading(true);
      try {
        await goalsApi.delete(goalId);
        removeGoal(goalId);
      } catch (err) {
        console.error('Failed to delete goal:', err);
        setError('Failed to delete goal');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Alert Banner */}
      {showAlert && (
        <div className="mb-4">
          <AlertBanner
            type="success"
            message="Goal created successfully! 🎉"
            onClose={() => setShowAlert(false)}
          />
        </div>
      )}

      {error && (
        <div className="mb-4">
          <AlertBanner
            type="error"
            message={error}
            onClose={() => setError(null)}
          />
        </div>
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🎯 Financial Goals</h1>
        <p className="text-gray-600">Plan and track your financial aspirations</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Total Goals</p>
          <p className="text-2xl font-bold text-gray-900">{goals.length}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Active Goals</p>
          <p className="text-2xl font-bold text-blue-600">{activeGoalsCount()}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Completed</p>
          <p className="text-2xl font-bold text-green-600">{completedGoalsCount()}</p>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form */}
        <div className="lg:col-span-1">
          <GoalForm
            userId={currentUser}
            onSubmit={handleAddGoal}
            loading={loading}
          />
        </div>

        {/* List */}
        <div className="lg:col-span-2">
          <GoalList
            goals={goals}
            onAddProgress={handleAddProgress}
            onDelete={handleDeleteGoal}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};

export default GoalDashboard;
