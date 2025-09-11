import { AuthProvider } from './context/AuthContext';
import Home from './pages/index';
import Navigation from './components/Navigation';

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="p-4">
          <Home />
        </main>
      </div>
    </AuthProvider>
  );
}

export default App;