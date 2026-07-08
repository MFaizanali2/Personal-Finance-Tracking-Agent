import { useState, useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface UseApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
}

export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const request = useCallback(
    async <T,>(
      endpoint: string,
      options: UseApiOptions = { method: 'GET' }
    ): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const url = `${API_BASE_URL}${endpoint}`;
        const fetchOptions: RequestInit = {
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        };

        if (options.body) {
          fetchOptions.body = JSON.stringify(options.body);
        }

        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
          throw new Error(`API Error: ${response.statusText}`);
        }

        const data: T = await response.json();
        return data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        console.error('API Error:', errorMessage);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Goals API
  const goals = {
    create: (goalData: any) =>
      request('/goals', {
        method: 'POST',
        body: goalData,
      }),
    getAll: (userId: string) => request(`/goals/${userId}`),
    getById: (goalId: string) => request(`/goals/detail/${goalId}`),
    update: (goalId: string, updates: any) =>
      request(`/goals/${goalId}`, {
        method: 'PUT',
        body: updates,
      }),
    delete: (goalId: string) =>
      request(`/goals/${goalId}`, { method: 'DELETE' }),
    addProgress: (goalId: string, data: { amount: number }) =>
      request(`/goals/${goalId}/add-progress`, {
        method: 'POST',
        body: data,
      }),
    analyze: (userId: string, monthlyIncome: number) =>
      request('/goals/analyze', {
        method: 'POST',
        body: { user_id: userId, monthly_income: monthlyIncome },
      }),
  };

  // Budgets API
  const budgets = {
    create: (budgetData: any) =>
      request('/budgets', {
        method: 'POST',
        body: budgetData,
      }),
    getAll: (userId: string) => request(`/budgets/${userId}`),
    getByMonth: (userId: string, month: string) =>
      request(`/budgets/${userId}/${month}`),
    getById: (budgetId: string) =>
      request(`/budgets/detail/${budgetId}`),
    update: (budgetId: string, updates: any) =>
      request(`/budgets/${budgetId}`, {
        method: 'PUT',
        body: updates,
      }),
    delete: (budgetId: string) =>
      request(`/budgets/${budgetId}`, { method: 'DELETE' }),
    addSpending: (budgetId: string, data: { amount: number }) =>
      request(`/budgets/${budgetId}/add-spending`, {
        method: 'POST',
        body: data,
      }),
    checkAlerts: (userId: string, month: string) =>
      request('/budgets/check-alerts', {
        method: 'POST',
        body: { user_id: userId, month },
      }),
    monitor: (userId: string, month: string) =>
      request('/budgets/monitor', {
        method: 'POST',
        body: { user_id: userId, month },
      }),
  };

  // System API
  const system = {
    health: () => request('/health'),
    info: () => request('/info'),
  };

  return {
    loading,
    error,
    request,
    goals,
    budgets,
    system,
  };
};
