// Goal Types
export interface Goal {
  goal_id: string;
  user_id: string;
  goal_name: string;
  goal_type: 'short_term' | 'long_term';
  target_amount: number;
  current_amount: number;
  deadline: string;
  priority: 'low' | 'medium' | 'high';
  status: 'active' | 'completed' | 'abandoned';
  description?: string;
  progress_percentage?: number;
  created_at: string;
  updated_at: string;
}

export interface GoalCreateInput {
  user_id: string;
  goal_name: string;
  goal_type: 'short_term' | 'long_term';
  target_amount: number;
  deadline: string;
  priority: 'low' | 'medium' | 'high';
  description?: string;
}

// Budget Types
export interface Budget {
  budget_id: string;
  user_id: string;
  category: string;
  monthly_limit: number;
  spent_so_far: number;
  month: string;
  spent_percentage?: number;
  remaining_amount?: number;
  status?: 'ok' | 'warning' | 'exceeded';
  created_at: string;
  updated_at: string;
}

export interface BudgetCreateInput {
  user_id: string;
  category: string;
  monthly_limit: number;
  month: string;
}

// Transaction Types
export interface Transaction {
  transaction_id: string;
  user_id: string;
  amount: number;
  category: string;
  type: 'income' | 'expense';
  description: string;
  date: string;
  created_at: string;
}

// API Response Types
export interface ApiResponse<T> {
  status: string;
  data?: T;
  error?: string;
}

export interface BudgetMonitorReport {
  status: string;
  user_id: string;
  month: string;
  budget_status: any;
  alerts: {
    critical_alerts: any[];
    warning_alerts: any[];
    ok_budgets: any[];
    total_alerts: number;
  };
  spending_velocity: any;
  suggested_adjustments: any;
  report_generated: string;
}

export interface GoalAnalysisResult {
  status: string;
  user_id: string;
  spending_analysis: any;
  savings_capacity: any;
  suggested_goals: Goal[];
  action_plans: any[];
  timestamp: string;
}
