import TransactionsList from '@/components/TransactionsList';

export default function TransactionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
        <p className="text-sm text-gray-500 mt-1">
          View, search, and manage all your transactions.
        </p>
      </div>
      <TransactionsList />
    </div>
  );
}
