import { useState } from 'react';
import { Plus, DollarSign, X } from 'lucide-react';
import { CATEGORIES } from '@/constants';
import useStore from '@/store';

export default function BudgetForm() {
  const { setBudget } = useStore();
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ category: 'Food', monthly_limit: '', month: new Date().toISOString().slice(0, 7) });

  if (!show) {
    return (
      <button onClick={() => setShow(true)} className="btn btn-primary flex items-center gap-2">
        <Plus size={18} /> New Budget
      </button>
    );
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.monthly_limit || parseFloat(form.monthly_limit) <= 0) return;
    try {
      const { default: store } = await import('@/store');
      const { api } = await import('@/api/client');
      await api.createBudget({
        category: form.category,
        monthly_limit: parseFloat(form.monthly_limit),
        month: form.month,
      });
      store.getState().showToast('Budget created!', 'success');
      setForm({ category: 'Food', monthly_limit: '', month: new Date().toISOString().slice(0, 7) });
      setShow(false);
    } catch (err) {
      console.error('Budget create failed:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="card p-6 relative">
      <button type="button" onClick={() => setShow(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
        <X size={18} />
      </button>
      <div className="flex items-center gap-2 mb-4">
        <DollarSign size={20} className="text-primary-600" />
        <h2 className="text-lg font-semibold">Create Budget</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className="label">Category</label>
          <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Monthly Limit ($)</label>
          <input type="number" step="0.01" min="1" className="input" value={form.monthly_limit}
                 onChange={(e) => setForm({ ...form, monthly_limit: e.target.value })} placeholder="500" required />
        </div>
        <div>
          <label className="label">Month</label>
          <input type="month" className="input" value={form.month} onChange={(e) => setForm({ ...form, month: e.target.value })} />
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <button type="submit" className="btn btn-primary">Create Budget</button>
        <button type="button" onClick={() => setShow(false)} className="btn btn-secondary">Cancel</button>
      </div>
    </form>
  );
}
