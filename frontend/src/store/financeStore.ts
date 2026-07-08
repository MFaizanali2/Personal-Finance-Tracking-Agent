import { create } from 'zustand';
import { api } from '../api/client';
import type { Goal, Budget, Transaction } from '../types';

interface FinanceStore {
  // State
  currentUser: string;
  goals: Goal[];
  budgets: Budget[];
  transactions: Transaction[];
  loading: boolean;
  error: string | null;
  selectedMonth: string;

  // Goal Actions
  setGoals: (goals: Goal[]) => void;
  addGoal: (goal: Goal) => void;
  removeGoal: (goalId: string) => void;
  updateGoal: (goalId: string, updates: Partial<Goal>) => void;
  fetchGoals: () => Promise<void>;
  createGoal: (data: any) => Promise<void>;
  addGoalProgress: (goalId: string, amount: number) => Promise<void>;
  deleteGoal: (goalId: string) => Promise<void>;

  // Budget Actions
  setBudgets: (budgets: Budget[]) => void;
  addBudget: (budget: Budget) => void;
  removeBudget: (budgetId: string) => void;
  updateBudget: (budgetId: string, updates: Partial<Budget>) => void;
  fetchBudgets: (userId: string, month: string) => Promise<void>;
  createBudget: (data: any) => Promise<void>;
  addBudgetSpending: (budgetId: string, amount: number) => Promise<void>;
  deleteBudget: (budgetId: string) => Promise<void>;

  // Transaction Actions
  setTransactions: (transactions: Transaction[]) => void;
  addTransaction: (transaction: Transaction) => void;

  // UI Actions
  setCurrentUser: (userId: string) => void;
  setSelectedMonth: (month: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // Computed
  totalBudgetSpent: () => number;
  totalBudgetLimit: () => number;
  activeGoalsCount: () => number;
  completedGoalsCount: () => number;
}

export const useFinanceStore = create<FinanceStore>((set, get) => ({
  // Initial State
  currentUser: 'user1',
  goals: [],
  budgets: [],
  transactions: [],
  loading: false,
  error: null,
  selectedMonth: new Date().toISOString().slice(0, 7),

  // Goal Actions
  setGoals: (goals) => set({ goals }),

  fetchGoals: async () => {
    try {
      const data = await api.getAllGoals();
      set({ goals: data.goals || data || [] });
    } catch { /* silent */ }
  },

  createGoal: async (goalData) => {
    set({ loading: true, error: null });
    try {
      const result = await api.createGoal(goalData);
      const goal = result.goal || result;
      set((state) => ({
        goals: [...state.goals, goal],
        loading: false,
      }));
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  addGoal: (goal) => set((state) => ({
    goals: [...state.goals, goal],
  })),

  removeGoal: (goalId) => set((state) => ({
    goals: state.goals.filter((g) => g.goal_id !== goalId),
  })),

  deleteGoal: async (goalId) => {
    try {
      await api.deleteGoal(goalId);
      set((state) => ({
        goals: state.goals.filter((g) => g.goal_id !== goalId),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  addGoalProgress: async (goalId, amount) => {
    try {
      const result = await api.addGoalProgress(goalId, amount);
      set((state) => ({
        goals: state.goals.map((g) =>
          g.goal_id === goalId ? { ...g, ...(result.goal || result) } : g
        ),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  updateGoal: (goalId, updates) => set((state) => ({
    goals: state.goals.map((g) =>
      g.goal_id === goalId ? { ...g, ...updates } : g
    ),
  })),

  // Budget Actions
  setBudgets: (budgets) => set({ budgets }),

  fetchBudgets: async (userId, month) => {
    try {
      const data = await api.getUserBudgets(userId, month);
      set({ budgets: data.budgets || data || [] });
    } catch { /* silent */ }
  },

  createBudget: async (budgetData) => {
    set({ loading: true, error: null });
    try {
      const result = await api.createBudget(budgetData);
      const budget = result.budget || result;
      set((state) => ({
        budgets: [...state.budgets, budget],
        loading: false,
      }));
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },

  addBudget: (budget) => set((state) => ({
    budgets: [...state.budgets, budget],
  })),

  removeBudget: (budgetId) => set((state) => ({
    budgets: state.budgets.filter((b) => b.budget_id !== budgetId),
  })),

  deleteBudget: async (budgetId) => {
    try {
      await api.deleteBudget(budgetId);
      set((state) => ({
        budgets: state.budgets.filter((b) => b.budget_id !== budgetId),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  addBudgetSpending: async (budgetId, amount) => {
    try {
      const budget = get().budgets.find((b) => b.budget_id === budgetId);
      if (!budget) return;
      const newSpent = budget.spent_so_far + amount;
      const result = await api.updateBudget(budgetId, { spent_so_far: newSpent });
      set((state) => ({
        budgets: state.budgets.map((b) =>
          b.budget_id === budgetId ? { ...b, ...(result.budget || result), spent_so_far: newSpent } : b
        ),
      }));
    } catch (err: any) {
      set({ error: err.message });
    }
  },

  updateBudget: (budgetId, updates) => set((state) => ({
    budgets: state.budgets.map((b) =>
      b.budget_id === budgetId ? { ...b, ...updates } : b
    ),
  })),

  // Transaction Actions
  setTransactions: (transactions) => set({ transactions }),

  addTransaction: (transaction) => set((state) => ({
    transactions: [...state.transactions, transaction],
  })),

  // UI Actions
  setCurrentUser: (userId) => set({ currentUser: userId }),

  setSelectedMonth: (month) => set({ selectedMonth: month }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  // Computed Functions
  totalBudgetSpent: () => {
    return get().budgets.reduce((sum, b) => sum + b.spent_so_far, 0);
  },

  totalBudgetLimit: () => {
    return get().budgets.reduce((sum, b) => sum + b.monthly_limit, 0);
  },

  activeGoalsCount: () => {
    return get().goals.filter((g) => g.status === 'active').length;
  },

  completedGoalsCount: () => {
    return get().goals.filter((g) => g.status === 'completed').length;
  },
}));
