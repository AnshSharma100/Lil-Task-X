import { useState } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import AddProductModal, { type ProductFormData } from "../components/AddProductModal";
import { Link } from "react-router-dom";
import "./Home.css";

interface Product {
  id: string;
  productName: string;
  dueDate: string;
  budget: string;
  description: string;
  createdAt: string;
}

function Home() {
  const { user, isLoading } = useAuth0();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);

  if (isLoading) {
    return (
      <div className="home-container">
        <div className="neon-loader"></div>
      </div>
    );
  }

  const handleAnalyze = (productData: ProductFormData) => {
    // Create new product from form data
    const newProduct: Product = {
      id: Date.now().toString(),
      productName: productData.productName,
      dueDate: productData.dueDate,
      // store file names for budget and description so the UI can show them
      budget: productData.budget ? productData.budget.name : "",
      description: productData.description ? productData.description.name : "",
      createdAt: new Date().toISOString(),
    };

    // Add product to list
    setProducts(prev => [...prev, newProduct]);

    // Here you would typically send the data to your backend for analysis
    console.log("Analyzing product:", productData);
    // TODO: Implement actual analysis logic
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="home-container">
      <div className="home-content">
        <div className="welcome-frame">
          <h1 className="welcome-title">
            Welcome, <span className="neon-text">{user?.given_name || user?.nickname || user?.name || "User"}</span>
          </h1>
          <p className="welcome-subtitle">You're now logged in to Lil Task X</p>
        </div>

        <div className="products-section">
          <div className="products-header">
            <h2 className="section-title">Products</h2>
            <button 
              className="add-product-btn"
              onClick={() => setIsModalOpen(true)}
            >
              + Add Product
            </button>
          </div>

          {products.length === 0 ? (
            <div className="empty-state">
              <p className="empty-text">No products yet. Click "Add Product" to get started.</p>
            </div>
          ) : (
            <div className="products-grid">
              {products.map((product) => (
                <div key={product.id} className="product-card">
                  <div className="product-card-glow"></div>
                  <h3 className="product-name">{product.productName}</h3>
                  <div className="product-details">
                    <div className="product-detail-item">
                      <span className="detail-label">Due Date:</span>
                      <span className="detail-value">{formatDate(product.dueDate)}</span>
                    </div>
                    <div className="product-detail-item">
                      <span className="detail-label">Budget:</span>
                      <span className="detail-value">{product.budget || "(no budget file)"}</span>
                    </div>
                    <div className="product-detail-item">
                      <span className="detail-label">Description:</span>
                      <span className="detail-value">{product.description}</span>
                    </div>
                  </div>
                  <button className="view-details-button">
                  <Link to={`/home/products/${product.id}`} className="view-details-btn">
                    View Details
                  </Link>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <AddProductModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAnalyze={handleAnalyze}
      />
    </div>
  );
}

export default Home;
