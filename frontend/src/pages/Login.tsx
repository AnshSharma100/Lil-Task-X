import { useAuth0 } from "@auth0/auth0-react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

function Login() {
  const { loginWithRedirect, isAuthenticated, isLoading } = useAuth0();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/home", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (isLoading) {
    return (
      <div className="login-container">
        <div className="neon-loader"></div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-frame">
        <div className="login-content">
          <h1 className="login-title">Welcome Back</h1>
          <p className="login-subtitle">Sign in to access your dashboard</p>
          
          <button 
            className="neon-button"
            onClick={() => loginWithRedirect({
              appState: { returnTo: "/home" }
            })}
          >
            <span className="button-glow"></span>
            Log In
          </button>
        </div>
      </div>
    </div>
  );
}

export default Login;
