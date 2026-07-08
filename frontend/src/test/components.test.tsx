import { describe, test, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GoalCard } from '../components/goals/GoalCard';
import { BudgetCard } from '../components/budgets/BudgetCard';
import { AlertBanner } from '../components/common/AlertBanner';
import { ProgressBar } from '../components/common/ProgressBar';
import { useFinanceStore } from '../store/financeStore';
import type { Goal, Budget } from '../types';

// =============================================================================
// TEST 1: AlertBanner Component
// =============================================================================
describe('AlertBanner Component', () => {
  test('renders success alert', () => {
    render(<AlertBanner type="success" message="Test message" closeable={false} />);
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  test('renders error alert', () => {
    render(<AlertBanner type="error" message="Error occurred" closeable={false} />);
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
  });

  test('renders warning alert', () => {
    render(<AlertBanner type="warning" message="Warning message" closeable={false} />);
    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  test('close button works', () => {
    const onClose = vi.fn();
    render(<AlertBanner type="success" message="Test" closeable={true} onClose={onClose} />);
    fireEvent.click(screen.getByText('✕'));
    expect(onClose).toHaveBeenCalled();
  });
});

// =============================================================================
// TEST 2: ProgressBar Component
// =============================================================================
describe('ProgressBar Component', () => {
  test('renders progress bar with correct percentage', () => {
    render(<ProgressBar current={50} target={100} showLabel={true} />);
    expect(screen.getByText(/50% complete/)).toBeInTheDocument();
  });

  test('renders with custom percentage', () => {
    render(<ProgressBar current={0} target={100} percentage={75} showLabel={true} />);
    expect(screen.getByText(/75% complete/)).toBeInTheDocument();
  });

  test('renders correct color based on progress', () => {
    const { container } = render(<ProgressBar current={80} target={100} color="green" />);
    expect(container.querySelector('.bg-green-500')).toBeInTheDocument();
  });
});

// =============================================================================
// TEST 3: GoalCard Component
// =============================================================================
describe('GoalCard Component', () => {
  const mockGoal: Goal = {
    goal_id: 'test-1',
    user_id: 'user1',
    goal_name: 'Emergency Fund',
    goal_type: 'long_term',
    target_amount: 50000,
    current_amount: 10000,
    deadline: '2027-12-31T00:00:00',
    priority: 'high',
    status: 'active',
    progress_percentage: 20,
    created_at: '2026-01-01T00:00:00',
    updated_at: '2026-01-01T00:00:00',
  };

  test('renders goal card with correct data', () => {
    render(<GoalCard goal={mockGoal} />);
    expect(screen.getByText('Emergency Fund')).toBeInTheDocument();
    expect(screen.getByText(/20\.0%/)).toBeInTheDocument();
  });

  test('displays priority badge', () => {
    render(<GoalCard goal={mockGoal} />);
    expect(screen.getByText('high')).toBeInTheDocument();
  });

  test('shows add progress input when button clicked', () => {
    render(<GoalCard goal={mockGoal} onAddProgress={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /add progress/i }));
    expect(screen.getByRole('spinbutton')).toBeInTheDocument();
  });

  test('calls onDelete when delete button clicked', () => {
    const onDelete = vi.fn();
    render(<GoalCard goal={mockGoal} onDelete={onDelete} />);
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith('test-1');
  });
});

// =============================================================================
// TEST 4: BudgetCard Component
// =============================================================================
describe('BudgetCard Component', () => {
  const mockBudget: Budget = {
    budget_id: 'test-1',
    user_id: 'user1',
    category: 'Food',
    monthly_limit: 15000,
    spent_so_far: 12000,
    month: '2026-07',
    spent_percentage: 80,
    remaining_amount: 3000,
    status: 'warning',
    created_at: '2026-07-01T00:00:00',
    updated_at: '2026-07-01T00:00:00',
  };

  test('renders budget card with correct data', () => {
    render(<BudgetCard budget={mockBudget} />);
    expect(screen.getByText('Food')).toBeInTheDocument();
    expect(screen.getByText(/80% spent/)).toBeInTheDocument();
  });

  test('displays correct status color for warning', () => {
    const { container } = render(<BudgetCard budget={mockBudget} />);
    expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
  });

  test('shows add spending input when button clicked', () => {
    const onAddSpending = vi.fn();
    render(<BudgetCard budget={mockBudget} onAddSpending={onAddSpending} />);
    fireEvent.click(screen.getByRole('button', { name: /add spending/i }));
    expect(screen.getByRole('spinbutton')).toBeInTheDocument();
  });
});

// =============================================================================
// TEST 5: Zustand Store
// =============================================================================
describe('Zustand Store', () => {
  beforeEach(() => {
    useFinanceStore.setState({
      goals: [],
      budgets: [],
      loading: false,
      error: null,
    });
  });

  test('initializes with default state', () => {
    const store = useFinanceStore.getState();
    expect(store.goals).toEqual([]);
    expect(store.budgets).toEqual([]);
    expect(store.loading).toBe(false);
  });

  test('adds goal to store', () => {
    const store = useFinanceStore.getState();
    const testGoal: Goal = {
      goal_id: 'test-1',
      user_id: 'user1',
      goal_name: 'Test Goal',
      goal_type: 'short_term',
      target_amount: 10000,
      current_amount: 0,
      deadline: '2026-12-31T00:00:00',
      priority: 'medium',
      status: 'active',
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
    };

    store.addGoal(testGoal);
    expect(useFinanceStore.getState().goals).toHaveLength(1);
    expect(useFinanceStore.getState().goals[0].goal_name).toBe('Test Goal');
  });

  test('removes goal from store', () => {
    const store = useFinanceStore.getState();
    const testGoal: Goal = {
      goal_id: 'test-1',
      user_id: 'user1',
      goal_name: 'Test Goal',
      goal_type: 'short_term',
      target_amount: 10000,
      current_amount: 0,
      deadline: '2026-12-31T00:00:00',
      priority: 'medium',
      status: 'active',
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
    };
    store.addGoal(testGoal);
    useFinanceStore.getState().removeGoal('test-1');
    expect(useFinanceStore.getState().goals).toHaveLength(0);
  });

  test('computes activeGoalsCount correctly', () => {
    const activeGoal: Goal = {
      goal_id: 'test-1',
      user_id: 'user1',
      goal_name: 'Goal 1',
      goal_type: 'short_term',
      target_amount: 10000,
      current_amount: 0,
      deadline: '2026-12-31T00:00:00',
      priority: 'medium',
      status: 'active',
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
    };
    const completedGoal: Goal = {
      goal_id: 'test-2',
      user_id: 'user1',
      goal_name: 'Goal 2',
      goal_type: 'long_term',
      target_amount: 50000,
      current_amount: 0,
      deadline: '2027-12-31T00:00:00',
      priority: 'high',
      status: 'completed',
      created_at: '2026-01-01T00:00:00',
      updated_at: '2026-01-01T00:00:00',
    };

    useFinanceStore.getState().setGoals([activeGoal, completedGoal]);
    expect(useFinanceStore.getState().activeGoalsCount()).toBe(1);
  });
});
