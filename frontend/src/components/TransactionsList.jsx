import { useState, useEffect } from 'react';
import { Trash2, Loader2, AlertCircle } from 'lucide-react';
import useStore from '@/store';
import { CATEGORY_COLORS, CATEGORY_LABELS } from '@/constants';
import { formatCurrency, getStatusBadgeClass, confidenceColor } from '@/utils';

const PER_PAGE = 10;

export default function TransactionsList() {
  const transactions = useStore((s) => s.transactions);
  const loading = useStore((s) => s.loading);
  const error = useStore((s) => s.error);
  const fetchAll = useStore((s) => s.fetchAllTransactions);
  const deleteTxn = useStore((s) => s.deleteTransaction);
  const fetchSummary = useStore((s) => s.fetchSummary);

  const [page, setPage] = useState(0);
  const [deleting, setDeleting] = useState(null);
  const [confirmId, setConfirmId] = useState(null);

  useEffect(() => {
    fetchAll().then(fetchSummary);
  }, []);

  const totalPages = Math.max(1, Math.ceil(transactions.length / PER_PAGE));
  const paginated = transactions.slice(page * PER_PAGE, (page + 1) * PER_PAGE);

  async function handleDelete(id) {
    setDeleting(id);
    await deleteTxn(id);
    setDeleting(null);
    setConfirmId(null);
    fetchSummary();
    if (paginated.length === 1 && page > 0) setPage((p) => p - 1);
  }

  if (loading && transactions.length === 0) {
    return (
      <div className="card flex items-center justify-center py-12">
        <Loader2 size={24} className="animate-spin text-primary-600" />
        <span className="ml-2 text-gray-500">Loading transactions...</span>
      </div>
    );
  }

  if (error && transactions.length === 0) {
    return (
      <div className="card text-center py-12">
        <AlertCircle size={32} className="mx-auto text-red-500 mb-2" />
        <p className="text-red-600 mb-3">{error}</p>
        <button onClick={() => fetchAll().then(fetchSummary)} className="btn-outline text-sm">
          Retry
        </button>
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-400 text-lg mb-1">No transactions yet</p>
        <p className="text-gray-400 text-sm">Add one using the form above</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Transactions ({transactions.length})
        </h2>
        <button onClick={() => fetchAll().then(fetchSummary)} className="btn-outline text-xs">
          Refresh
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-left text-gray-500">
              <th className="pb-2 pr-4 font-medium">Amount</th>
              <th className="pb-2 pr-4 font-medium">Category</th>
              <th className="pb-2 pr-4 font-medium hidden md:table-cell">Description</th>
              <th className="pb-2 pr-4 font-medium hidden sm:table-cell">Date</th>
              <th className="pb-2 pr-4 font-medium">Status</th>
              <th className="pb-2 pr-4 font-medium hidden lg:table-cell">Confidence</th>
              <th className="pb-2 font-medium" />
            </tr>
          </thead>
          <tbody>
            {paginated.map((txn) => (
              <tr key={txn.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <td className="py-3 pr-4 font-medium">{formatCurrency(txn.amount)}</td>
                <td className="py-3 pr-4">
                  <span style={{ color: CATEGORY_COLORS[txn.category] || '#6b7280' }}>
                    {CATEGORY_LABELS[txn.category] || txn.category}
                  </span>
                </td>
                <td className="py-3 pr-4 text-gray-600 max-w-[200px] truncate hidden md:table-cell">
                  {txn.description}
                </td>
                <td className="py-3 pr-4 text-gray-500 hidden sm:table-cell">{txn.date}</td>
                <td className="py-3 pr-4">
                  <span className={getStatusBadgeClass(txn.status)}>
                    {txn.status}
                  </span>
                </td>
                <td className="py-3 pr-4 hidden lg:table-cell">
                  <div className="flex items-center gap-2">
                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${confidenceColor(txn.agent_confidence)}`}
                        style={{ width: `${txn.agent_confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">
                      {Math.round(txn.agent_confidence * 100)}%
                    </span>
                  </div>
                </td>
                <td className="py-3 text-right">
                  {confirmId === txn.id ? (
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleDelete(txn.id)}
                        disabled={deleting === txn.id}
                        className="text-xs bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                      >
                        {deleting === txn.id ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          'Confirm'
                        )}
                      </button>
                      <button
                        onClick={() => setConfirmId(null)}
                        className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded hover:bg-gray-300"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setConfirmId(txn.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4 pt-4 border-t border-gray-100">
          <button
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
            className="btn-outline text-xs px-3 py-1"
          >
            Prev
          </button>
          <span className="text-sm text-gray-500">
            {page + 1} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
            className="btn-outline text-xs px-3 py-1"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
