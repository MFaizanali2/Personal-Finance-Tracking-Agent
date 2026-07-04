import { create } from 'zustand';
import { api } from '@/api/client';

const useStore = create((set, get) => ({
  transactions: [],
  loading: false,
  error: null,
  summary: null,
  agentStatus: null,
  toast: null,
  goals: [],
  budgets: [],
  currentBudget: null,
  alerts: [],
  alertSummary: null,
  budgetThresholds: [],
  budgetRecommendations: [],

  clearError: () => set({ error: null }),

  clearToast: () => set({ toast: null }),

  showToast: (message, type = 'success') => {
    set({ toast: { message, type } });
    setTimeout(() => set({ toast: null }), 4000);
  },

  addTransaction: async (data) => {
    set({ loading: true, error: null });
    try {
      const result = await api.addTransaction(data);
      const { transactions } = get();
      set({ transactions: [result, ...transactions], loading: false });
      get().showToast('Transaction added successfully', 'success');
      return result;
    } catch (err) {
      set({ error: err.message, loading: false });
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  fetchAllTransactions: async () => {
    set({ loading: true, error: null });
    try {
      const data = await api.getAllTransactions();
      set({ transactions: data, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  deleteTransaction: async (id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteTransaction(id);
      const { transactions } = get();
      set({ transactions: transactions.filter((t) => t.id !== id), loading: false });
      get().showToast('Transaction deleted', 'success');
    } catch (err) {
      set({ error: err.message, loading: false });
      get().showToast(err.message, 'error');
    }
  },

  fetchSummary: async () => {
    try {
      const transactions = get().transactions;
      if (transactions.length === 0) { set({ summary: null }); return; }
      const totalAmount = transactions.reduce((s, t) => s + t.amount, 0);
      const byCategory = transactions.reduce((acc, t) => {
        acc[t.category] = (acc[t.category] || 0) + t.amount; return acc;
      }, {});
      const statusCounts = transactions.reduce((acc, t) => {
        acc[t.status] = (acc[t.status] || 0) + 1; return acc;
      }, { confirmed: 0, pending: 0, flagged: 0 });
      set({
        summary: {
          totalAmount, count: transactions.length,
          average: transactions.length > 0 ? totalAmount / transactions.length : 0,
          byCategory, ...statusCounts,
        },
      });
    } catch { /* silent */ }
  },

  fetchAgentStatus: async () => {
    try {
      const data = await api.getAgentStatus();
      set({ agentStatus: data });
    } catch { /* silent */ }
  },

  createGoal: async (data) => {
    set({ loading: true, error: null });
    try {
      const result = await api.createGoal(data);
      const { goals } = get();
      set({ goals: [result, ...goals], loading: false });
      get().showToast('Goal created!', 'success');
      return result;
    } catch (err) {
      set({ error: err.message, loading: false });
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  fetchGoals: async () => {
    try {
      const data = await api.getAllGoals();
      set({ goals: data });
    } catch { /* silent */ }
  },

  updateGoal: async (id, data) => {
    try {
      const result = await api.updateGoal(id, data);
      const { goals } = get();
      set({ goals: goals.map((g) => (g._id === id ? result : g)) });
      get().showToast('Goal updated', 'success');
      return result;
    } catch (err) {
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  deleteGoal: async (id) => {
    try {
      await api.deleteGoal(id);
      const { goals } = get();
      set({ goals: goals.filter((g) => g._id !== id) });
      get().showToast('Goal deleted', 'success');
    } catch (err) {
      get().showToast(err.message, 'error');
    }
  },

  setBudget: async (data) => {
    try {
      const result = await api.setBudget(data);
      set({ currentBudget: result.budget });
      get().showToast('Budget saved', 'success');
      return result;
    } catch (err) {
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  fetchCurrentBudget: async () => {
    try {
      const data = await api.getCurrentBudget();
      set({ currentBudget: data });
    } catch { /* silent */ }
  },

  fetchBudgetVsActual: async (month) => {
    try {
      const data = await api.getBudgetVsActual(month);
      return data;
    } catch { return null; }
  },

  fetchAlerts: async () => {
    try {
      const data = await api.getCurrentAlerts();
      set({ alerts: data.alerts || [] });
    } catch { /* silent */ }
  },

  fetchAlertSummary: async () => {
    try {
      const data = await api.getAlertSummary();
      set({ alertSummary: data });
    } catch { /* silent */ }
  },

  dismissAlert: async (id) => {
    try {
      await api.dismissAlert(id);
      const { alerts } = get();
      set({ alerts: alerts.filter((a) => a._id !== id) });
    } catch { /* silent */ }
  },

  fetchBudgetThresholds: async () => {
    try {
      const data = await api.getBudgetMonitorThresholds();
      set({ budgetThresholds: data.thresholds || [] });
    } catch { /* silent */ }
  },

  fetchBudgetRecommendations: async () => {
    try {
      const data = await api.getBudgetMonitorRecommendations();
      set({ budgetRecommendations: data.recommendations || [] });
    } catch { /* silent */ }
  },

  fetchUserBudgets: async (userId, month) => {
    try {
      const data = await api.getUserBudgets(userId, month);
      set({ budgets: data.budgets || [] });
    } catch { /* silent */ }
  },

  createBudgetItem: async (data) => {
    set({ loading: true, error: null });
    try {
      const result = await api.createBudget(data);
      const { budgets } = get();
      set({ budgets: [...budgets, result.budget], loading: false });
      get().showToast('Budget created', 'success');
      return result;
    } catch (err) {
      set({ error: err.message, loading: false });
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  updateBudgetItem: async (id, data) => {
    try {
      const result = await api.updateBudget(id, data);
      const { budgets } = get();
      set({ budgets: budgets.map((b) => (b._id === id ? result.budget : b)) });
      get().showToast('Budget updated', 'success');
      return result;
    } catch (err) {
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  deleteBudgetItem: async (id) => {
    try {
      await api.deleteBudget(id);
      const { budgets } = get();
      set({ budgets: budgets.filter((b) => b._id !== id) });
      get().showToast('Budget deleted', 'success');
    } catch (err) {
      get().showToast(err.message, 'error');
    }
  },

  checkBudgetAlerts: async (userId) => {
    try {
      const data = await api.checkBudgetAlerts({ user_id: userId });
      set({ alerts: data.alerts || [] });
      return data;
    } catch { return { alerts: [] }; }
  },

  monitorBudgets: async (userId) => {
    try {
      const data = await api.monitorBudgets({ user_id: userId });
      return data;
    } catch { return null; }
  },

  addGoalProgress: async (goalId, amount) => {
    try {
      const result = await api.addGoalProgress(goalId, amount);
      const { goals } = get();
      set({ goals: goals.map((g) => (g._id === goalId ? { ...g, ...result } : g)) });
      return result;
    } catch (err) {
      get().showToast(err.message, 'error');
      throw err;
    }
  },

  analyzeGoals: async (data) => {
    try {
      return await api.analyzeGoals(data);
    } catch { return null; }
  },
}));

export default useStore;
