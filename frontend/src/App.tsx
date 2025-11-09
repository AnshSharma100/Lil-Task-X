import "./App.css"
import Navbar from "./components/Navbar"
import { Routes, Route, Navigate } from "react-router-dom"
import ProtectedRoute from "./components/ProtectedRoute"
import { useAuth0 } from "@auth0/auth0-react"
import ProductDetails from "./pages/ProductDetails"
import PMAnalysisNew from "./pages/PMAnalysisNew"
import Home from "./pages/Home"
import Login from "./pages/Login"

function App() {
  const { isAuthenticated, isLoading } = useAuth0();

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="neon-loader"></div>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route 
            path="/home" 
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/" 
            element={
              isAuthenticated ? (
                <Navigate to="/home" replace />
              ) : (
                <Navigate to="/login" replace />
              )
            } 
          />
          <Route
            path="/home/products/:id"
            element={
            <ProtectedRoute>
                  <ProductDetails />
                </ProtectedRoute>
              }
            />
          <Route
            path="/pm-analysis"
            element={
              <ProtectedRoute>
                <PMAnalysisNew />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  )
}

export default App