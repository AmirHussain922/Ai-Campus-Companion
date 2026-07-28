import { RouterProvider } from 'react-router';
import { router } from './routes.tsx';
import { useEffect } from 'react';
import { useStore } from './store';
import ErrorBoundary from './components/ErrorBoundary';

export default function App() {
  const login = useStore(state => state.login);
  const authToken = useStore(state => state.authToken);
  
  useEffect(() => {
    // Only auto-login for demo if demo mode is enabled and there's no existing session
    // Check for VITE_DEMO_MODE environment variable (defaults to false for security)
    const isDemoMode = ((import.meta as any).env?.VITE_DEMO_MODE ?? 'false') === 'true';
    
    if (isDemoMode && !authToken) {
      login('User', 'user@example.com');
    }
  }, [login, authToken]);

  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  );
}
