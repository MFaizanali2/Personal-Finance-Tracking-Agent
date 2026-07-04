import { NavLink } from 'react-router-dom';
import { Wallet, List, Cpu, Target, DollarSign, Bell } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: Wallet },
  { to: '/transactions', label: 'Transactions', icon: List },
  { to: '/goals', label: 'Goals', icon: Target },
  { to: '/budget', label: 'Budget', icon: DollarSign },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/agent', label: 'Agent', icon: Cpu },
];

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <NavLink to="/" className="flex items-center gap-2">
              <Wallet className="text-primary-600" size={28} />
              <span className="text-xl font-bold text-gray-900">Finance Tracker</span>
              <span className="hidden sm:inline text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">
                Agent
              </span>
            </NavLink>
            <nav className="flex items-center gap-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`
                  }
                >
                  <Icon size={18} />
                  <span className="hidden sm:inline">{label}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {children}
      </main>

      <footer className="border-t border-gray-200 bg-white py-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
          Finance Tracker Agent &mdash; Powered by ReACT Loop &amp; FastAPI
        </div>
      </footer>
    </div>
  );
}
