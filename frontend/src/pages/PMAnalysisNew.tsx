import { useState } from "react";
import axios from "axios";
import "./PMAnalysisNew.css";

interface AnalysisResponse {
  session_id: string;
  market_ready_description: string;
  task_assignments: Array<any>;
  cost_summary: any;
  feasibility: boolean;
  recommendations: string[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function PMAnalysisNew() {
  const [budget, setBudget] = useState("");
  const [deadline, setDeadline] = useState("");
  const [productDescription, setProductDescription] = useState("");
  
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState("");

  const handleRunAnalysis = async () => {
    if (!budget || !deadline || !productDescription) {
      setError("Please fill in all fields");
      return;
    }

    setLoading(true);
    setError("");
    setAnalysisResult(null);
    setChatMessages([]);

    try {
      const formData = new FormData();
      formData.append("deadline", deadline);
      formData.append("product_description", productDescription);
      
      // Create budget CSV with exact format expected by backend
      const budgetAmount = parseFloat(budget);
      const budgetCsvContent = `Resource,Value
Engineering Budget (USD),${budgetAmount * 0.6}
QA Budget (USD),${budgetAmount * 0.25}
Cloud Services Budget (USD),${budgetAmount * 0.1}
Licensing & Tools Budget (USD),${budgetAmount * 0.03}
Gemini API Available,False
Gemini API Monthly Cost (USD),100
Firebase Auth Monthly Cost (USD),50
Security/Compliance Budget (USD),${budgetAmount * 0.01}
Training & Upskilling Budget (USD),${budgetAmount * 0.005}
Emergency Contingency Reserve (USD),${budgetAmount * 0.005}`;
      
      // Create employees CSV with exact columns expected by backend
      const employeesCsvContent = `Name,Role,Experience_Level,Skills,Hourly_Rate_USD,Email
John Doe,Senior Frontend Engineer,Senior,"frontend,react,typescript,css",85,john@example.com
Jane Smith,Senior Backend Engineer,Senior,"backend,python,api,databases",95,jane@example.com
Bob Johnson,Mid Fullstack Engineer,Mid,"react,nodejs,typescript,databases",65,bob@example.com
Alice Williams,Senior QA Engineer,Senior,"qa,automation,selenium,testing",80,alice@example.com
Charlie Brown,Mid QA Engineer,Mid,"testing,manual,api-testing",55,charlie@example.com`;
      
      const budgetBlob = new Blob([budgetCsvContent], { type: "text/csv" });
      const employeesBlob = new Blob([employeesCsvContent], { type: "text/csv" });
      
      formData.append("budget_csv", budgetBlob, "budget.csv");
      formData.append("employees_csv", employeesBlob, "employees.csv");

      const response = await axios.post("http://localhost:8000/run-analysis", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setAnalysisResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to run analysis");
      console.error("Analysis error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendChat = async () => {
    if (!chatInput.trim() || !analysisResult?.session_id) return;

    const userMessage: ChatMessage = { role: "user", content: chatInput };
    setChatMessages((prev) => [...prev, userMessage]);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await axios.post("http://localhost:8000/chat-revise", {
        session_id: analysisResult.session_id,
        user_message: chatInput,
      });

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.data.response || "Understood. I'll update the plan accordingly.",
      };
      setChatMessages((prev) => [...prev, assistantMessage]);

      // If backend returns updated analysis, refresh it
      if (response.data.updated_analysis) {
        setAnalysisResult(response.data.updated_analysis);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Failed to process message";
      setChatMessages((prev) => [...prev, { role: "assistant", content: `Error: ${errorMsg}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!analysisResult?.session_id) return;

    try {
      const response = await axios.get(
        `http://localhost:8000/download-report/${analysisResult.session_id}`,
        { responseType: "blob" }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `pm_analysis_${analysisResult.session_id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to download PDF");
      console.error(err);
    }
  };

  return (
    <div className="pm-analysis-page">
      <div className="pm-analysis-container">
        <div className="page-header">
          <h1 className="page-title">AI Product Manager</h1>
          <p className="page-subtitle">Let AI analyze your product feasibility and generate a delivery plan</p>
        </div>

        {/* Input Form */}
        {!analysisResult && (
          <div className="input-card">
            <h2 className="card-title">Project Details</h2>
            
            {error && <div className="error-alert">{error}</div>}

            <div className="form-grid">
              <div className="form-field">
                <label className="field-label">Budget ($)</label>
                <input
                  type="number"
                  className="field-input"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="e.g., 100000"
                  disabled={loading}
                />
              </div>

              <div className="form-field">
                <label className="field-label">Deadline</label>
                <input
                  type="date"
                  className="field-input"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-field">
              <label className="field-label">Product Description</label>
              <textarea
                className="field-textarea"
                value={productDescription}
                onChange={(e) => setProductDescription(e.target.value)}
                placeholder="Describe your product vision, key features, target users, and goals..."
                rows={8}
                disabled={loading}
              />
            </div>

            <button
              className="primary-button"
              onClick={handleRunAnalysis}
              disabled={loading}
            >
              {loading ? "🔄 Analyzing..." : "🚀 Run PM Analysis"}
            </button>
          </div>
        )}

        {/* Results Section */}
        {analysisResult && (
          <>
            <div className="results-header">
              <h2 className="section-heading">Analysis Complete!</h2>
              <button className="secondary-button" onClick={() => setAnalysisResult(null)}>
                ← New Analysis
              </button>
            </div>

            {/* Feasibility Badge */}
            <div className="result-card">
              <div className="status-row">
                <span className={`status-badge ${analysisResult.feasibility ? 'feasible' : 'not-feasible'}`}>
                  {analysisResult.feasibility ? '✓ Feasible' : '⚠ Not Feasible'}
                </span>
              </div>
            </div>

            {/* Cost Summary */}
            <div className="result-card">
              <h3 className="card-subtitle">💰 Cost Summary</h3>
              <div className="cost-grid">
                <div className="cost-box">
                  <span className="cost-label">Total Cost</span>
                  <span className="cost-value">${(analysisResult.cost_summary?.total_cost || 0).toFixed(2)}</span>
                </div>
                <div className="cost-box">
                  <span className="cost-label">Developer Cost</span>
                  <span className="cost-value">${(analysisResult.cost_summary?.developer_cost || 0).toFixed(2)}</span>
                </div>
                <div className="cost-box">
                  <span className="cost-label">Tester Cost</span>
                  <span className="cost-value">${(analysisResult.cost_summary?.tester_cost || 0).toFixed(2)}</span>
                </div>
                <div className="cost-box">
                  <span className="cost-label">Available Budget</span>
                  <span className="cost-value">${(analysisResult.cost_summary?.available_budget || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* PRD */}
            <div className="result-card">
              <h3 className="card-subtitle">📋 Product Requirements Document</h3>
              <div className="prd-box">
                {analysisResult.market_ready_description}
              </div>
            </div>

            {/* Recommendations */}
            {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
              <div className="result-card">
                <h3 className="card-subtitle">💡 Recommendations</h3>
                <ul className="recommendations-list">
                  {analysisResult.recommendations.map((rec, idx) => (
                    <li key={idx} className="recommendation-item">{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tasks - Detailed Jira Format */}
            {analysisResult.task_assignments && analysisResult.task_assignments.length > 0 && (
              <div className="result-card">
                <h3 className="card-subtitle">📝 Jira Task Breakdown ({analysisResult.task_assignments.length} tasks)</h3>
                <div className="tasks-list">
                  {analysisResult.task_assignments.map((task: any, idx: number) => (
                    <div key={idx} className="jira-task-card">
                      <div className="task-header-row">
                        <span className="task-id">{task.id || `TASK-${idx + 1}`}</span>
                        <span className="sprint-tag">Sprint {task.sprint || 1}</span>
                      </div>
                      <h4 className="task-title">{task.title || task.feature || 'Task'}</h4>
                      
                      <div className="task-section">
                        <strong>📄 Description:</strong>
                        <p className="task-description">
                          {task.description || task.story || 'Implement the feature as specified in the PRD. Ensure code quality, write unit tests, and follow coding standards. Coordinate with team members for integration points.'}
                        </p>
                      </div>

                      <div className="task-section">
                        <strong>✅ Acceptance Criteria:</strong>
                        <ul className="acceptance-list">
                          <li>Feature is implemented according to specification</li>
                          <li>Unit tests achieve &gt;80% code coverage</li>
                          <li>Code passes all linting and quality checks</li>
                          <li>Integration with existing systems is tested</li>
                          <li>Documentation is updated</li>
                        </ul>
                      </div>

                      <div className="task-meta-grid">
                        <div className="meta-item">
                          <span className="meta-label">Assignee:</span>
                          <span className="meta-value">👤 {task.assignee || 'Unassigned'}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-label">Estimate:</span>
                          <span className="meta-value">⏱ {task.estimated_hours || task.hours || 0}h</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-label">Cost:</span>
                          <span className="meta-value">💵 ${(task.salary_cost || 0).toFixed(2)}</span>
                        </div>
                        <div className="meta-item">
                          <span className="meta-label">Priority:</span>
                          <span className={`priority-badge ${task.risk_level?.toLowerCase() || 'medium'}`}>
                            {task.risk_level || 'Medium'}
                          </span>
                        </div>
                      </div>

                      {task.dependencies && task.dependencies.length > 0 && (
                        <div className="task-section">
                          <strong>🔗 Dependencies:</strong>
                          <p className="dependencies">{task.dependencies.join(', ')}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Chatbot for PM Tweaks */}
            <div className="result-card chat-card">
              <h3 className="card-subtitle">💬 Tweak Budget & Make it Feasible</h3>
              <p className="chat-help-text">
                Ask the AI to adjust budget, extend timeline, or reduce scope to make the plan feasible.
              </p>
              
              <div className="chat-messages">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`chat-bubble ${msg.role}`}>
                    <div className="bubble-content">{msg.content}</div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-bubble assistant">
                    <div className="bubble-content">Thinking...</div>
                  </div>
                )}
              </div>

              <div className="chat-input-row">
                <input
                  type="text"
                  className="chat-input"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !chatLoading) handleSendChat();
                  }}
                  placeholder="e.g., 'Increase budget to $150,000' or 'Reduce scope to fit budget'"
                  disabled={chatLoading}
                />
                <button className="send-button" onClick={handleSendChat} disabled={chatLoading || !chatInput.trim()}>
                  Send
                </button>
              </div>
            </div>

            {/* Download Button */}
            <div className="download-row">
              <button className="download-button" onClick={handleDownloadReport}>
                📥 Download Full PDF Report
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
