import { createContext, useContext, useState } from 'react';
import { toast } from 'react-toastify';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [apiKey] = useState(process.env.REACT_APP_API_KEY);
  const [loading, setLoading] = useState(false);

  const handleError = (error) => {
    toast.error(error.message || 'API request failed');
    throw error;
  };

  const authFetch = async (url, options = {}) => {
    setLoading(true);
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'X-API-Key': apiKey
        }
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ apiKey, authFetch, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};