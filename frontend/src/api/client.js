const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function request(method, path, body = null) {
  const url = `${BASE_URL}${path}`;
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(url, options);

  if (method === 'DELETE') {
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Delete failed (${res.status})`);
    }
    return null;
  }

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail?.[0]?.msg || data.detail || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  health: () => request('GET', '/health'),

  addTransaction: (data) => request('POST', '/api/transactions/add', data),

  getAllTransactions: () => request('GET', '/api/transactions/all'),

  getTransaction: (id) => request('GET', `/api/transactions/${id}`),

  deleteTransaction: (id) => request('DELETE', `/api/transactions/${id}`),

  getTransactionsByCategory: (category) =>
    request('GET', `/api/transactions/category/${encodeURIComponent(category)}`),

  getTransactionsByDateRange: (start, end) =>
    request('GET', `/api/transactions/date-range?start_date=${start}&end_date=${end}`),

  searchTransactions: (q) =>
    request('GET', `/api/transactions/search?q=${encodeURIComponent(q)}`),

  getStats: () => request('GET', '/api/transactions/stats'),

  getAgentStatus: () => request('GET', '/api/agent/status'),

  resetAgent: () => request('POST', '/api/agent/reset'),

  createGoal: (data) => request('POST', '/api/goals/create', data),

  getAllGoals: () => request('GET', '/api/goals/all'),

  getActiveGoals: () => request('GET', '/api/goals/active'),

  getGoal: (id) => request('GET', `/api/goals/${id}`),

  updateGoal: (id, data) => request('PUT', `/api/goals/${id}`, data),

  deleteGoal: (id) => request('DELETE', `/api/goals/${id}`),

  getGoalProgress: () => request('GET', '/api/goals/progress/summary'),

  createGoalPlan: (goalId) => request('POST', `/api/goals/plan?goal_id=${goalId}`),

  setBudget: (data) => request('POST', '/api/budget/set', data),

  getCurrentBudget: () => request('GET', '/api/budget/current'),

  getBudgetHistory: () => request('GET', '/api/budget/history'),

  getBudgetVsActual: (month) => request('GET', `/api/budget/vs-actual${month ? `?month=${month}` : ''}`),

  suggestBudget: () => request('POST', '/api/budget/suggest'),

  getSpendingTrend: (days) => request('GET', `/api/analytics/spending-trend?days=${days || 30}`),

  getCategoryBreakdown: (month) => request('GET', `/api/analytics/category-breakdown${month ? `?month=${month}` : ''}`),

  getUnusualSpending: () => request('GET', '/api/analytics/unusual-spending'),

  getMonthlyComparison: (months) => request('GET', `/api/analytics/monthly-comparison?months=${months || 3}`),

  getCurrentAlerts: () => request('GET', '/api/alerts/current'),

  getAlertSummary: () => request('GET', '/api/alerts/summary'),

  getAlertHistory: () => request('GET', '/api/alerts/history'),

  dismissAlert: (id) => request('DELETE', `/api/alerts/${id}`),

  forecastNextMonth: () => request('GET', '/api/forecast/next-month'),

  getForecastTotal: (days) => request('GET', `/api/forecast/total?days=${days || 30}`),

  getForecastTrends: () => request('GET', '/api/forecast/trends'),

  getBudgetSuggestions: () => request('POST', '/api/forecast/budget-suggestions'),

  getBudgetMonitorThresholds: () => request('GET', '/api/budget-monitor/thresholds'),

  getBudgetMonitorRecommendations: () => request('GET', '/api/budget-monitor/recommendations'),

  createBudget: (data) => request('POST', '/api/budget/create', data),

  getUserBudgets: (userId, month) => request('GET', `/api/budget/user/${userId}${month ? '/' + month : ''}`),

  getBudget: (id) => request('GET', `/api/budget/${id}`),

  updateBudget: (id, data) => request('PUT', `/api/budget/${id}`, data),

  deleteBudget: (id) => request('DELETE', `/api/budget/${id}`),

  checkBudgetAlerts: (data) => request('POST', '/api/budget/check-alerts', data),

  monitorBudgets: (data) => request('POST', '/api/budget/monitor', data),

  addGoalProgress: (goalId, amount) => request('POST', `/api/goals/${goalId}/add-progress`, { amount }),

  analyzeGoals: (data) => request('POST', '/api/goals/analyze', data),
};
