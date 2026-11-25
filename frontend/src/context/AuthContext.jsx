import { createContext, useContext, useEffect, useState } from "react";

const AuthContext = createContext(null);
const KEY = "shopvault_customer";

export function AuthProvider({ children }) {
  const [customer, setCustomer] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || "null");
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (customer) localStorage.setItem(KEY, JSON.stringify(customer));
    else localStorage.removeItem(KEY);
  }, [customer]);

  const login = (user) => setCustomer(user);
  const logout = () => setCustomer(null);

  return (
    <AuthContext.Provider value={{ customer, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
