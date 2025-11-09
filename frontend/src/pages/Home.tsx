import { useState, useEffect } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import AddProductModal, { type ProductFormData } from "../components/AddProductModal";
import { Link } from "react-router-dom";
import "./Home.css";
import { supabase } from "../lib/supabaseClient";

interface ProductRow {
  id: number;
  auth0_sub: string;
  name: string;
  due_date: string;
  budget: string;
  description: string;
  created_at: string;
}

interface Product {
  id: number;
  productName: string;
  dueDate: string;
  budget: string;
  description: string;
  createdAt: string;
}


function mapRow(r: ProductRow): Product {
  return {
    id: r.id,
    productName: r.name ?? "",
    dueDate: r.due_date ?? "",
    budget: r.budget ?? "",
    description: r.description ?? "",
    createdAt: r.created_at,
  };
}

function Home() {
  const { user, isLoading } = useAuth0();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);

  useEffect(() => {
    if (!user?.sub) return;
    (async () => {
      const { data, error } = await supabase
        .from("products")
        .select("*")
        .eq("auth0_sub", user.sub)
        .order("created_at", { ascending: false });

      if (error) {
        console.error("load products error:", error);
        return;
      }
      setProducts((data ?? []).map(mapRow));
    })();
  }, [user?.sub]);

  if (isLoading) {
    return (
      <div className="home-container">
        <div className="neon-loader"></div>
      </div>
    );
  }

  const handleAnalyze = async (productData: ProductFormData) => {
    if (!user?.sub) return;

    const { data, error } = await supabase
      .from("products")
      .insert([
        {
          auth0_sub: user.sub,
          name: productData.productName ?? null,
          due_date: productData.dueDate || null,        // "YYYY-MM-DD"
          // If your modal doesn't collect a numeric budget or description text yet, pass nulls:
          budget: (productData as any).budgetAmount ?? null,
          description: (productData as any).descriptionText ?? null,
        },
      ])
      .select("*")
      .single();

    if (error) {
      console.error("insert product error:", error);
      return;
    }

    setProducts((prev) => [mapRow(data as ProductRow), ...prev]);
    setIsModalOpen(false);
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
