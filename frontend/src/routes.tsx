import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Login from "./pages/Login";
import ProductDetails from "./pages/ProductDetails";

const AppRoutes = () => (
  <Routes>
    <Route path="/home" element={<Home />} />
    <Route path="/" element={<Login />} />
    <Route path="/home/products/:id" element={<ProductDetails />} />
  </Routes>
);

export default AppRoutes;