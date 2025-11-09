import { useState } from "react";
import "./AddProductModal.css";

interface AddProductModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalyze: (productData: ProductFormData) => void;
}

export interface ProductFormData {
  productName: string;
  dueDate: string;
  budget: string;
  description: string;
  employeeData: File | null;
}

export default function AddProductModal({ isOpen, onClose, onAnalyze }: AddProductModalProps) {
  const [formData, setFormData] = useState<ProductFormData>({
    productName: "",
    dueDate: "",
    budget: "",
    description: "",
    employeeData: null,
  });
  const [fileName, setFileName] = useState<string>("");

  if (!isOpen) return null;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setFormData(prev => ({ ...prev, employeeData: file }));
    setFileName(file ? file.name : "");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(formData);
    // Reset form
    setFormData({
      productName: "",
      dueDate: "",
      budget: "",
      description: "",
      employeeData: null,
    });
    setFileName("");
    onClose();
  };

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2 className="modal-title">Add New Product</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close modal">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="product-form">
          <div className="form-group">
            <label htmlFor="productName">Product Name</label>
            <input
              type="text"
              id="productName"
              name="productName"
              value={formData.productName}
              onChange={handleInputChange}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="dueDate">Due Date</label>
            <input
              type="date"
              id="dueDate"
              name="dueDate"
              value={formData.dueDate}
              onChange={handleInputChange}
              required
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="budget">Budget</label>
            <input
              type="number"
              id="budget"
              name="budget"
              value={formData.budget}
              onChange={handleInputChange}
              required
              min="0"
              step="0.01"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Budget (File Upload)</label>
            <div className="file-upload-wrapper">
              <input
                type="file"
                id="description"
                name="description"
                onChange={handleFileChange}
                required
                className="file-input"
                accept=".txt,.doc,.docx,.pdf"
              />
              <label htmlFor="description" className="file-label">
                {fileName || "Choose file..."}
              </label>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (File Upload)</label>
            <div className="file-upload-wrapper">
              <input
                type="file"
                id="description"
                name="description"
                onChange={handleFileChange}
                required
                className="file-input"
                accept=".txt,.doc,.docx,.pdf"
              />
              <label htmlFor="description" className="file-label">
                {fileName || "Choose file..."}
              </label>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="employeeData">Employee Data (File Upload)</label>
            <div className="file-upload-wrapper">
              <input
                type="file"
                id="employeeData"
                name="employeeData"
                onChange={handleFileChange}
                className="file-input"
                accept=".csv,.xlsx,.xls,.json"
              />
              <label htmlFor="employeeData" className="file-label">
                {fileName || "Choose file..."}
              </label>
            </div>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="btn-cancel">
              Cancel
            </button>
            <button type="submit" className="btn-analyze">
              Analyze
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

