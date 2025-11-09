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
  budget: File | null;
  description: File | null;
  employeeData: File | null;
}

export default function AddProductModal({ isOpen, onClose, onAnalyze }: AddProductModalProps) {
  const [formData, setFormData] = useState<ProductFormData>({
    productName: "",
    dueDate: "",
    budget: null,
    description: null,
    employeeData: null,
  });
  const [budgetFileName, setBudgetFileName] = useState<string>("");
  const [descriptionFileName, setDescriptionFileName] = useState<string>("");
  const [employeeFileName, setEmployeeFileName] = useState<string>("");

  if (!isOpen) return null;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    const { name } = e.target;

    if (name === "budget") {
      setFormData(prev => ({ ...prev, budget: file }));
      setBudgetFileName(file ? file.name : "");
    } else if (name === "description") {
      setFormData(prev => ({ ...prev, description: file }));
      setDescriptionFileName(file ? file.name : "");
    } else if (name === "employeeData") {
      setFormData(prev => ({ ...prev, employeeData: file }));
      setEmployeeFileName(file ? file.name : "");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAnalyze(formData);
    // Reset form
    setFormData({
      productName: "",
      dueDate: "",
      budget: null,
      description: null,
      employeeData: null,
    });
    setBudgetFileName("");
    setDescriptionFileName("");
    setEmployeeFileName("");
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
            <label htmlFor="budget">Budget (File Upload)</label>
            <div className="file-upload-wrapper">
              <input
                type="file"
                id="budget"
                name="budget"
                onChange={handleFileChange}
                required
                className="file-input"
                accept=".csv,.xlsx,.xls,.pdf"
              />
              <label htmlFor="budget" className="file-label">
                {budgetFileName || "Choose budget file..."}
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
                {descriptionFileName || "Choose description file..."}
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
                {employeeFileName || "Choose employee data file..."}
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

