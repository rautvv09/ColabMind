import { createContext, useState } from "react";

export const AuthContext = createContext();

export default function AuthProvider({ children }) {

  const [user, setUser] = useState(
    JSON.parse(localStorage.getItem("brand"))
  );

  const login = (data) => {

    localStorage.setItem("token", data.token);
    localStorage.setItem("brand", JSON.stringify(data));

    setUser(data);

  };

  const logout = () => {

    localStorage.removeItem("token");
    localStorage.removeItem("brand");

    setUser(null);

  };

  return (

    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>

  );

}