import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";

const AppRoutes = () => (
  <Routes>
    <Route path="/home" element={<Home />} />
    <Route path="/" element={<Login />} />
  </Routes>
);

export default AppRoutes;