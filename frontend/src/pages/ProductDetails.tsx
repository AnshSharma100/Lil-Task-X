import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { supabase } from "../lib/supabaseClient";
import "./ProductDetails.css";
import { fetchMessages, insertMessage, type MessageRow } from "../lib/ProductDetails";

type ChatMessage = { role: "user" | "bot"; content: string };

// Matches your `products` table
interface ProductRow {
  id: number;
  auth0_sub: string | null;
  name: string | null;
  due_date: string | null;    // YYYY-MM-DD
  budget: string | null;      // numeric comes back as string
  description: string | null;
  created_at: string;
}

function Chatbot({ productId }: { productId: number }) {
  const { user } = useAuth0();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  // Load message history
  useEffect(() => {
    (async () => {
      const { data, error } = await fetchMessages(productId);
      if (error) {
        console.error("fetchMessages error:", error);
        return;
      }
      const mapped = (data as MessageRow[]).map(m => ({ role: m.author, content: m.content }));
      setMessages(mapped);
    })();
  }, [productId]);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);

    try {
      // Save USER message
      await insertMessage(productId, "user", text, user?.sub ?? null);
      setMessages(m => [...m, { role: "user", content: text }]);

      // Call Gemini
      const apiKey = import.meta.env.VITE_GEMINI_API_KEY as string;
      const model = "gemini-2.5-flash";
      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ role: "user", parts: [{ text: `Product ID: ${productId}\n\n${text}` }] }],
            generationConfig: { temperature: 0.5, maxOutputTokens: 1024 },
          }),
        }
      );
      const body = await resp.json();
      if (!resp.ok) throw new Error(body?.error?.message ?? "Gemini request failed");

      const reply =
        body?.candidates?.[0]?.content?.parts?.map((p: any) => p?.text).filter(Boolean).join("\n") ??
        "Sorry, I didn’t catch that.";

      // Save MODEL message
      await insertMessage(productId, "bot", reply, user?.sub ?? null);
      setMessages(m => [...m, { role: "bot", content: reply }]);
    } catch (e: any) {
      const errText = `Error: ${e?.message ?? String(e)}`;
      await insertMessage(productId, "bot", errText, user?.sub ?? null);
      setMessages(m => [...m, { role: "bot", content: errText }]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chatbot">
      <div className="chat-header">✦ Ask AI ✦</div>
      <div className="chat-history">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="bubble">{m.content}</div>
          </div>
        ))}
        {loading && <div className="msg model"><div className="bubble">Thinking…</div></div>}
      </div>
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask about scope, deadlines, risks…"
          rows={2}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default function ProductDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth0();
  const productId = Number(id);

  const [product, setProduct] = useState<ProductRow | null>(null);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ name: "", due_date: "", budget: "", description: "" });

  // Load the product row
  useEffect(() => {
    if (!Number.isFinite(productId)) return;
    (async () => {
      const { data, error } = await supabase
        .from("products")
        .select("*")
        .eq("id", productId)
        .maybeSingle();

      if (error) {
        console.error("load product error:", error);
        return;
      }
      if (data) {
        const p = data as ProductRow;
        setProduct(p);
        setForm({
          name: p.name ?? "",
          due_date: p.due_date ?? "",
          budget: p.budget ?? "",
          description: p.description ?? ""
        });
      }
    })();
  }, [productId]);

  async function handleDelete() {
    if (!Number.isFinite(productId)) return;
    if (!window.confirm("Delete this product? This cannot be undone.")) return;

    // Optional owner check if you store auth0_sub on products
    let q = supabase.from("products").delete().eq("id", productId);
    if (user?.sub) q = q.eq("auth0_sub", user.sub);

    const { error } = await q;
    if (error) {
      console.error("delete product error:", error);
      alert("Failed to delete product.");
      return;
    }
    navigate("/home", { replace: true });
  }

  async function handleSave() {
    if (!Number.isFinite(productId)) return;
    setSaving(true);

    const payload = {
      name: form.name || null,
      due_date: form.due_date || null,
      budget: form.budget || null,
      description: form.description || null,
    };

    let q = supabase.from("products").update(payload).eq("id", productId);
    if (user?.sub) q = q.eq("auth0_sub", user.sub);

    const { data, error } = await q.select("*").single();
    setSaving(false);

    if (error) {
      console.error("update product error:", error);
      alert("Failed to save changes.");
      return;
    }

    const p = data as ProductRow;
    setProduct(p);
    setEditing(false);
  }

  if (!Number.isFinite(productId)) {
    return <div className="product-details-container">Invalid product id.</div>;
  }

  return (
    <div className="product-details-container">
      <div className="product-header">
        <h1>Product Details</h1>
        <div className="product-actions">
          {!editing ? (
            <>
              <button className="btn" onClick={() => setEditing(true)}>Edit</button>
              <button className="btn danger" onClick={handleDelete}>Delete</button>
            </>
          ) : (
            <>
              <button className="btn" onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save"}
              </button>
              <button
                className="btn ghost"
                onClick={() => {
                  setEditing(false);
                  if (product) {
                    setForm({
                      name: product.name ?? "",
                      due_date: product.due_date ?? "",
                      budget: product.budget ?? "",
                      description: product.description ?? ""
                    });
                  }
                }}
              >
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      {product ? (
        <>
          {!editing ? (
            <div className="product-summary">
              <p><strong>Name:</strong> {product.name || "—"}</p>
              <p><strong>Due date:</strong> {product.due_date || "—"}</p>
              <p><strong>Budget:</strong> {product.budget || "—"}</p>
              <p><strong>Description:</strong> {product.description || "—"}</p>
            </div>
          ) : (
            <div className="product-edit-form">
              <label> Name
                <input
                  value={form.name}
                  onChange={(e) => setForm(f => ({ ...f, name: e.target.value }))}
                />
              </label>
              <label> Due date
                <input
                  type="date"
                  value={form.due_date}
                  onChange={(e) => setForm(f => ({ ...f, due_date: e.target.value }))}
                />
              </label>
              <label> Budget
                <input
                  value={form.budget}
                  onChange={(e) => setForm(f => ({ ...f, budget: e.target.value }))}
                  placeholder="e.g. 10000.00"
                />
              </label>
              <label> Description
                <textarea
                  rows={4}
                  value={form.description}
                  onChange={(e) => setForm(f => ({ ...f, description: e.target.value }))}
                />
              </label>
            </div>
          )}
          <h1 className="ai-report">AI Report</h1>
          <iframe className="pdf" 
            src="https://media.geeksforgeeks.org/wp-content/cdn-uploads/20210101201653/PDF.pdf"
            width="800" 
            height="500">
          </iframe>
          <hr className="divider" />
          <Chatbot productId={productId} />
        </>
      ) : (
        <p>Loading product…</p>
      )}
    </div>
  );
}
