import TransactionForm from '@/components/TransactionForm';
import SummaryDashboard from '@/components/SummaryDashboard';
import ChartsSection from '@/components/ChartsSection';

export default function HomePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">
          Add transactions and view your financial summary.
        </p>
      </div>
      <TransactionForm />
      <SummaryDashboard />
      <ChartsSection />
    </div>
  );
}
