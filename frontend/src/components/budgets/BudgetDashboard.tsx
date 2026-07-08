import React, { useState, useEffect } from 'react';
import { BudgetForm } from './BudgetForm';
import { BudgetList } from './BudgetList';
import { BudgetChart } from './BudgetChart';
import { AlertBanner } from '../common/AlertBanner';
import { useFinanceStore } from '../../store/financeStore';
import { useApi } from '../../hooks/useApi';
import { BudgetCreateInput } from '../../types';

export const BudgetDashboard: React.FC = () => {
  const {
    currentUser,
    budgets,
    selectedMonth,
    loading,
    error,
    setError,
    setSelectedMonth,
    setLoading,
    addBudget,
    updateBudget,
    removeBudget,
  } = useFinanceStore();

  const { budgets: budgetsApi } = useApi();

  const [monthInput, setMonthInput] = useState(selectedMonth);
  const [showAlert, setShowAlert] = React.useState(false);

  // Fetch budgets on mount / user / month change
  useEffect(() => {
    const fetchBudgets = async () => {
      setLoading(true);
      try {
        const response = await budgetsApi.getByMonth(currentUser, selectedMonth);
        if (response) {
          const budgetsData = Array.isArray(response) ? response : (response as any).budgets || [];
          (budgetsData as any[]).forEach((budget: any) => {
            const spent_pct = (budget.spent_so_far / budget.monthly_limit) * 100;
            budget.spent_percentage = spent_pct;
            addBudget(budget);
          });
        }
      } catch (err) {
        console.error('Failed to fetch budgets:', err);
        setError('Failed to load budgets');
      } finally {
        setLoading(false);
      }
    };
    fetchBudgets();
  }, [currentUser, selectedMonth]);

  const currentBudgets = budgets.filter((b) => b.month === selectedMonth);

  const totalLimit = currentBudgets.reduce((sum, b) => sum + b.monthly_limit, 0);
  const totalSpent = currentBudgets.reduce((sum, b) => sum + b.spent_so_far, 0);
  const totalRemaining = totalLimit - totalSpent;
  const totalPercentage = totalLimit > 0 ? (totalSpent / totalLimit) * 100 : 0;

  const handleMonthChange = () => {
    setSelectedMonth(monthInput);
  };

  const handleAddBudget = async (budgetData: BudgetCreateInput) => {
    setLoading(true);
    try {
      const response = await budgetsApi.create(budgetData);
      if (response) {
        const newBudget = (response as any).budget || response;
        newBudget.spent_percentage = 0;
        addBudget(newBudget);
        setShowAlert(true);
        setTimeout(() => setShowAlert(false), 3000);
      }
    } catch (err) {
      console.error('Failed to create budget:', err);
      setError('Failed to create budget');
    } finally {
      setLoading(false);
    }
  };

  const handleAddSpending = async (budgetId: string, amount: number) => {
    setLoading(true);
    try {
      const response = await budgetsApi.addSpending(budgetId, { amount });
      if (response) {
        updateBudget(budgetId, {
          spent_so_far: (response as any).new_spent_total,
          spent_percentage: (response as any).spent_percentage,
          status: (response as any).budget_status,
        });
      }
    } catch (err) {
      console.error('Failed to add spending:', err);
      setError('Failed to add spending');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBudget = async (budgetId: string) => {
    if (window.confirm('Delete this budget?')) {
      setLoading(true);
      try {
        await budgetsApi.delete(budgetId);
        removeBudget(budgetId);
      } catch (err) {
        console.error('Failed to delete budget:', err);
        setError('Failed to delete budget');
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
            message="Budget created successfully! 🎉"
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">💰 Budget Tracker</h1>
        <p className="text-gray-600">Monitor spending and stay within your limits</p>
      </div>

      {/* Month Selector */}
      <div className="flex gap-2 mb-6">
        <input
          type="month"
          value={monthInput}
          onChange={(e) => setMonthInput(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        />
        <button
          onClick={handleMonthChange}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
        >
          📅 Select Month
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Total Limit</p>
          <p className="text-2xl font-bold text-gray-900">PKR {totalLimit.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Total Spent</p>
          <p className="text-2xl font-bold text-blue-600">PKR {totalSpent.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">Remaining</p>
          <p className={`text-2xl font-bold ${totalRemaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            PKR {totalRemaining.toLocaleString()}
          </p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <p className="text-gray-600 text-sm">% Used</p>
          <p className={`text-2xl font-bold ${totalPercentage < 80 ? 'text-green-600' : totalPercentage < 100 ? 'text-yellow-600' : 'text-red-600'}`}>
            {Math.round(totalPercentage)}%
          </p>
        </div>
      </div>

      {/* Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Form & Chart */}
        <div className="lg:col-span-1 space-y-6">
          <BudgetForm
            userId={currentUser}
            defaultMonth={selectedMonth}
            onSubmit={handleAddBudget}
            loading={loading}
          />
          {currentBudgets.length > 0 && (
            <BudgetChart budgets={currentBudgets} />
          )}
        </div>

        {/* List */}
        <div className="lg:col-span-2">
          <BudgetList
            budgets={currentBudgets}
            onAddSpending={handleAddSpending}
            onDelete={handleDeleteBudget}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
};

export default BudgetDashboard;
