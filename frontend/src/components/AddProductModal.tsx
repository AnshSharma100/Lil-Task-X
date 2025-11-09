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

  budgetAmount?: number;
  timelineWeeks?: number;
  headcount?: number;
  scopeComplexity?: "low" | "medium" | "high";
}

type Step = "form" | "result";
type Verdict = "realistic" | "unrealistic";

type Evaluation = {
  verdict: Verdict;
  reasons: string[];
  estimates: { weeklyCost: number; totalCost: number; minWeeks: number };
};

function evaluate(form: ProductFormData): Evaluation {
  const budget = form.budgetAmount ?? 0;
  const weeks = form.timelineWeeks ?? 0;
  const people = form.headcount ?? 0;
  const complexity = form.scopeComplexity ?? "medium";

  const hourlyRate = 75;            // tweak for your org
  const hoursPerWeekPerDev = 30;    // tweak for your org

  const weeklyCost = people * hoursPerWeekPerDev * hourlyRate;

  const minWeeksByComplexity = { low: 2, medium: 6, high: 12 } as const;
  const minWeeks = minWeeksByComplexity[complexity];

  const complexityMultiplier =
    complexity === "low" ? 0.8 : complexity === "high" ? 1.4 : 1.0;

  const adjustedWeeks = Math.ceil((weeks || 0) * complexityMultiplier);
  const totalCost = weeklyCost * adjustedWeeks;

  const reasons: string[] = [];
  if (people <= 0) reasons.push("No headcount assigned.");
  if (weeks <= 0) reasons.push("Timeline is missing or zero.");
  if (budget <= 0) reasons.push("Budget is missing or zero.");
  if (weeks > 0 && weeks < minWeeks)
    reasons.push(`Timeline too short for ${complexity} scope (min ${minWeeks} weeks).`);
  if (budget > 0 && budget < totalCost)
    reasons.push(
      `Budget too low. Estimated total ${totalCost.toLocaleString(undefined, { style: "currency", currency: "USD" })} vs provided ${budget.toLocaleString(undefined, { style: "currency", currency: "USD" })}.`
    );

  return { verdict: reasons.length ? "unrealistic" : "realistic", reasons, estimates: { weeklyCost, totalCost, minWeeks } };
}


export default function AddProductModal({ isOpen, onClose, onAnalyze }: AddProductModalProps) {
  const [step, setStep] = useState<Step>("form");
  const [pmChecked, setPmChecked] = useState(false);
  const [formData, setFormData] = useState<ProductFormData>({
    productName: "",
    dueDate: "",
    budget: null,
    description: null,
    employeeData: null,
    budgetAmount: undefined,
    timelineWeeks: undefined,
    headcount: undefined,
    scopeComplexity: "medium",
  });
  const [budgetFileName, setBudgetFileName] = useState<string>("");
  const [descriptionFileName, setDescriptionFileName] = useState<string>("");
  const [employeeFileName, setEmployeeFileName] = useState<string>("");

  if (!isOpen) return null;

  const handleInputChange = (
      e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
    ) => {
      const { name, value } = e.target;
      setFormData(prev => {
        if (name === "budgetAmount" || name === "timelineWeeks" || name === "headcount") {
          return { ...prev, [name]: value === "" ? undefined : Number(value) };
        }
        return { ...prev, [name]: value };
      });
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
  setStep("result");
};

const handleSave = () => {
  onAnalyze(formData); // you already persist in Home.tsx
  // Reset
  setFormData({
    productName: "",
    dueDate: "",
    budget: null,
    description: null,
    employeeData: null,
    budgetAmount: undefined,
    timelineWeeks: undefined,
    headcount: undefined,
    scopeComplexity: "medium",
  });
  setBudgetFileName("");
  setDescriptionFileName("");
  setEmployeeFileName("");
  setPmChecked(false);
  setStep("form");
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

        {step === "form" ? (
  <form onSubmit={handleSubmit} className="product-form">
    {/* BASIC INFO */}
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

    {/* NEW STRUCTURED FIELDS */}
    <div className="grid2">
      <div className="form-group">
        <label htmlFor="budgetAmount">Budget (USD)</label>
        <input
          type="number"
          id="budgetAmount"
          name="budgetAmount"
          min={0}
          step="100"
          placeholder="e.g. 50000"
          value={formData.budgetAmount ?? ""}
          onChange={handleInputChange}
          className="form-input"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="timelineWeeks">Timeline (weeks)</label>
        <input
          type="number"
          id="timelineWeeks"
          name="timelineWeeks"
          min={1}
          step="1"
          placeholder="e.g. 8"
          value={formData.timelineWeeks ?? ""}
          onChange={handleInputChange}
          className="form-input"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="headcount">Headcount</label>
        <input
          type="number"
          id="headcount"
          name="headcount"
          min={1}
          step="1"
          placeholder="e.g. 3"
          value={formData.headcount ?? ""}
          onChange={handleInputChange}
          className="form-input"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="scopeComplexity">Scope Complexity</label>
        <select
          id="scopeComplexity"
          name="scopeComplexity"
          value={formData.scopeComplexity}
          onChange={handleInputChange}
          className="form-input"
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>

    {/* FILE UPLOADS (unchanged) */}
    <div className="form-group">
      <label htmlFor="budget">Budget (File Upload)</label>
      <div className="file-upload-wrapper">
        <input
          type="file"
          id="budget"
          name="budget"
          onChange={handleFileChange}
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
      <button type="button" onClick={onClose} className="btn-cancel">Cancel</button>
      <button type="submit" className="btn-analyze">Analyze</button>
    </div>
  </form>
) : (
  // ===== RESULT STEP =====
  (() => {
    const result = evaluate(formData);
    return (
      <div className={`resultCard ${result.verdict === "realistic" ? "ok" : "bad"}`}>
        <div className="resultHead">
          <span
            className={`status-badge ${result.verdict === "realistic" ? "ok" : "bad"}`}
            role="status"
            aria-live="polite"
          >
            {result.verdict === "realistic" ? "Realistic" : "Unrealistic"}
          </span>
          <div className="estimates">
            <div><strong>Estimated Weekly Cost:</strong> {result.estimates.weeklyCost.toLocaleString(undefined, { style: "currency", currency: "USD" })}</div>
            <div><strong>Estimated Total Cost:</strong> {result.estimates.totalCost.toLocaleString(undefined, { style: "currency", currency: "USD" })}</div>
            <div><strong>Minimum Weeks for Scope:</strong> {result.estimates.minWeeks}</div>
          </div>
        </div>

        {result.verdict === "unrealistic" ? (
          <div className="resultBody">
            <ul className="reasonList">
              {result.reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>

            <div className="changeBox">
              <h3 className="changeTitle">Change & Recalculate</h3>
              <div className="grid2">
                <label className="inlineField">
                  <span>Budget (USD)</span>
                  <input
                    type="number"
                    name="budgetAmount"
                    min={0}
                    step="100"
                    value={formData.budgetAmount ?? ""}
                    onChange={handleInputChange}
                    className="form-input"
                  />
                </label>
                <label className="inlineField">
                  <span>Timeline (weeks)</span>
                  <input
                    type="number"
                    name="timelineWeeks"
                    min={1}
                    step="1"
                    value={formData.timelineWeeks ?? ""}
                    onChange={handleInputChange}
                    className="form-input"
                  />
                </label>
                <label className="inlineField">
                  <span>Headcount</span>
                  <input
                    type="number"
                    name="headcount"
                    min={1}
                    step="1"
                    value={formData.headcount ?? ""}
                    onChange={handleInputChange}
                    className="form-input"
                  />
                </label>
                <label className="inlineField">
                  <span>Scope Complexity</span>
                  <select
                    name="scopeComplexity"
                    value={formData.scopeComplexity}
                    onChange={handleInputChange}
                    className="form-input"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </label>
              </div>

              <label className="pmCheck">
                <input
                  type="checkbox"
                  checked={pmChecked}
                  onChange={(e) => setPmChecked(e.target.checked)}
                />
                <span>I have consulted with the PM about funding/timeline changes.</span>
              </label>

              <div className="form-actions">
                <button className="btn-cancel" onClick={() => setStep("form")}>Back</button>
                <button
                  className="btn-analyze"
                  type="button"
                  disabled={!pmChecked}
                  title={!pmChecked ? "Confirm PM consultation to proceed" : ""}
                  onClick={() => {/* useMemo-like re-eval via state change; values already bound */}}
                >
                  Recalculate
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="successBox">
            <p>This plan looks feasible with the current inputs.</p>
            <div className="form-actions">
              <button className="btn-cancel" onClick={() => setStep("form")}>Edit</button>
              <button className="btn-analyze" onClick={handleSave}>Continue & Save</button>
            </div>
          </div>
        )}
      </div>
    );
  })()
)}

      </div>
    </div>
  );
}

