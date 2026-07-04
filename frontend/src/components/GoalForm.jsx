import { useState } from 'react';
import { Target, Plus } from 'lucide-react';
import useStore from '@/store';
import { GOAL_CATEGORIES } from '@/constants';

export default function GoalForm() {
  const { createGoal } = useStore();
  const [form, setForm] = useState({ name: '', target_amount: '', category: 'General', deadline: '', monthly_contribution: '' });
  const [show, setShow] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.target_amount || !form.deadline) return;
    await createGoal({
      name: form.name,
      target_amount: parseFloat(form.target_amount),
      category: form.category,
      deadline: form.deadline,
      monthly_contribution: parseFloat(form.monthly_contribution) || 0,
    });
    setForm({ name: '', target_amount: '', category: 'General', deadline: '', monthly_contribution: '' });
    setShow(false);
  };

  if (!show) {
    return (
      <button onClick={() => setShow(true)} className="btn btn-primary flex items-center gap-2">
        <Plus size={18} /> New Goal
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="card p-6">
      <div className="flex items-center gap-2 mb-4">
        <Target size={20} className="text-primary-600" />
        <h2 className="text-lg font-semibold">Create Savings Goal</h2>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Goal Name</label>
          <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Emergency Fund" required />
        </div>
        <div>
          <label className="label">Target Amount ($)</label>
          <input type="number" step="0.01" min="1" className="input" value={form.target_amount} onChange={(e) => setForm({ ...form, target_amount: e.target.value })} placeholder="5000" required />
        </div>
        <div>
          <label className="label">Category</label>
          <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {GOAL_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Deadline</label>
          <input type="date" className="input" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })} required />
        </div>
        <div>
          <label className="label">Monthly Contribution ($)</label>
          <input type="number" step="0.01" min="0" className="input" value={form.monthly_contribution} onChange={(e) => setForm({ ...form, monthly_contribution: e.target.value })} placeholder="200" />
        </div>
      </div>
      <div className="flex gap-2 mt-4">
        <button type="submit" className="btn btn-primary">Create Goal</button>
        <button type="button" onClick={() => setShow(false)} className="btn btn-secondary">Cancel</button>
      </div>
    </form>
  );
}
