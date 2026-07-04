import { useState } from 'react';
import { PlusCircle, Loader2 } from 'lucide-react';
import useStore from '@/store';
import { CATEGORIES } from '@/constants';

const initial = { amount: '', category: '', description: '', date: '' };

export default function TransactionForm() {
  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState({});
  const addTransaction = useStore((s) => s.addTransaction);
  const loading = useStore((s) => s.loading);

  function validate() {
    const e = {};
    const amount = parseFloat(form.amount);
    if (!form.amount || isNaN(amount) || amount <= 0) e.amount = 'Amount must be > 0';
    if (!form.category) e.category = 'Select a category';
    if (!form.description.trim()) e.description = 'Description is required';
    if (form.description.length > 200) e.description = 'Max 200 characters';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;

    try {
      await addTransaction({
        amount: parseFloat(form.amount),
        category: form.category,
        description: form.description.trim(),
        ...(form.date && { date: form.date }),
      });
      setForm(initial);
      setErrors({});
    } catch {
      // error handled by store
    }
  }

  function handleChange(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  }

  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <PlusCircle size={20} className="text-primary-600" />
        Add Transaction
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label" htmlFor="amount">Amount</label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min="0.01"
              placeholder="0.00"
              className={`input-field ${errors.amount ? 'border-red-500' : ''}`}
              value={form.amount}
              onChange={(e) => handleChange('amount', e.target.value)}
            />
            {errors.amount && <p className="text-red-600 text-xs mt-1">{errors.amount}</p>}
          </div>
          <div>
            <label className="label" htmlFor="category">Category</label>
            <select
              id="category"
              className={`input-field ${errors.category ? 'border-red-500' : ''}`}
              value={form.category}
              onChange={(e) => handleChange('category', e.target.value)}
            >
              <option value="">Select...</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            {errors.category && <p className="text-red-600 text-xs mt-1">{errors.category}</p>}
          </div>
          <div className="sm:col-span-2">
            <label className="label" htmlFor="description">Description</label>
            <input
              id="description"
              type="text"
              placeholder="What was this for?"
              className={`input-field ${errors.description ? 'border-red-500' : ''}`}
              value={form.description}
              onChange={(e) => handleChange('description', e.target.value)}
            />
            {errors.description && <p className="text-red-600 text-xs mt-1">{errors.description}</p>}
          </div>
          <div>
            <label className="label" htmlFor="date">Date</label>
            <input
              id="date"
              type="date"
              max={today}
              className="input-field"
              value={form.date}
              onChange={(e) => handleChange('date', e.target.value)}
            />
          </div>
        </div>
        <div className="flex justify-end pt-2">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <PlusCircle size={16} />}
            {loading ? 'Processing...' : 'Add Transaction'}
          </button>
        </div>
      </form>
    </div>
  );
}
