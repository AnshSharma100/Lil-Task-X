import { useAuth0 } from "@auth0/auth0-react";
import { Link, useNavigate } from "react-router-dom";
import Logo from "./Logo";
import "./Navbar.css";

export default function Navbar() {
  const { isAuthenticated, user, logout, isLoading } = useAuth0();
  const navigate = useNavigate();

  if (isLoading) return null;

  const handleLogout = () => {
    // Use localOnly to avoid Auth0 redirect URL configuration issues
    // This logs out locally without redirecting to Auth0
    logout({ 
      logoutParams: { 
        localOnly: true 
      } 
    });
    // Navigate to login page
    navigate("/login", { replace: true });
  };

  return (
    <nav className="navbar">
      <Link to={isAuthenticated ? "/home" : "/login"} className="navbar-logo">
        <Logo />
      </Link>
      <div className="navbar-links">
        {isAuthenticated ? (
          <>
            <Link to="/home" className="navbar-link">Home</Link>
            <div className="profile-dropdown">
              <div className="profile-trigger">
                <span className="navbar-user">
                  {user?.given_name || user?.nickname || user?.name}
                </span>
              </div>
              <div className="dropdown-menu">
                <button className="dropdown-item" onClick={handleLogout}>
                  Log out
                </button>
              </div>
            </div>
          </>
        ) : (
          <button className="navbar-button" onClick={() => navigate("/login")}>
            Log in
          </button>
        )}
      </div>
    </nav>
  );
}
