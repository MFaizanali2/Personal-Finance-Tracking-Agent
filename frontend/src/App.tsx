import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import Layout from '@/components/Layout';
import Toast from '@/components/Toast';
import HomePage from '@/pages/HomePage';
import TransactionsPage from '@/pages/TransactionsPage';
import AgentPage from '@/pages/AgentPage';
import GoalsPage from '@/pages/GoalsPage';
import BudgetPage from '@/pages/BudgetPage';
import AlertsPage from '@/pages/AlertsPage';

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Layout>
          <Toast />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/agent" element={<AgentPage />} />
            <Route path="/goals" element={<GoalsPage />} />
            <Route path="/budget" element={<BudgetPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
