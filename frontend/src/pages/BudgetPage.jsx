import BudgetSetup from '@/components/BudgetSetup';
import BudgetDashboard from '@/components/BudgetDashboard';

export default function BudgetPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Budget Management</h1>
      <div className="mb-8">
        <BudgetSetup />
      </div>
      <BudgetDashboard />
    </div>
  );
}
