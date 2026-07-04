export function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount ?? 0);
}

export function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

export function formatPercent(value) {
  if (value == null || isNaN(value)) return '0%';
  return `${Math.round(value * 100)}%`;
}

export function truncate(str, max = 50) {
  if (!str) return '';
  return str.length > max ? str.slice(0, max) + '...' : str;
}

export function confidenceColor(value) {
  if (value >= 0.7) return 'bg-green-500';
  if (value >= 0.4) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function getStatusBadgeClass(status) {
  const map = { confirmed: 'badge-green', pending: 'badge-yellow', flagged: 'badge-red' };
  return map[status] || 'badge-blue';
}
