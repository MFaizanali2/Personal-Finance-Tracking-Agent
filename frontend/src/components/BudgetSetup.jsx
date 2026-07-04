import { useState, useEffect } from 'react';
import { DollarSign, Save } from 'lucide-react';
import useStore from '@/store';
import { CATEGORIES } from '@/constants';

export default function BudgetSetup() {
  const { currentBudget, fetchCurrentBudget, setBudget } = useStore();
  const [budgets, setBudgets] = useState({});
  const [month, setMonth] = useState(() => new Date().toISOString().slice(0, 7));

  useEffect(() => { fetchCurrentBudget(); }, [fetchCurrentBudget]);

  useEffect(() => {
    if (currentBudget?.budget?.budgets) {
      setBudgets(currentBudget.budget.budgets);
    } else if (currentBudget?.default?.budgets) {
      setBudgets(currentBudget.default.budgets);
    } else {
      const defaults = {};
      CATEGORIES.forEach((c) => { defaults[c] = ''; });
      setBudgets(defaults);
    }
  }, [currentBudget]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const parsed = {};
    CATEGORIES.forEach((c) => { parsed[c] = parseFloat(budgets[c]) || 0; });
    await setBudget({ month, budgets: parsed });
  };

  const total = Object.values(budgets).reduce((s, v) => s + (parseFloat(v) || 0), 0);

  return (
    <form onSubmit={handleSubmit} className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <DollarSign size={20} className="text-primary-600" />
        <h2 className="text-lg font-semibold">Budget Setup</h2>
      </div>

      <div className="mb-4">
        <label className="label">Month</label>
        <input type="month" className="input max-w-xs" value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {CATEGORIES.map((cat) => (
          <div key={cat}>
            <label className="label text-sm">{cat}</label>
            <input type="number" step="0.01" min="0" className="input" value={budgets[cat] ?? ''}
              onChange={(e) => setBudgets({ ...budgets, [cat]: e.target.value })}
              placeholder="0.00" />
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
        <p className="text-lg font-semibold">Total Budget: <span className="text-primary-600">${total.toFixed(2)}</span></p>
        <button type="submit" className="btn btn-primary flex items-center gap-2">
          <Save size={18} /> Save Budget
        </button>
      </div>
    </form>
  );
}
