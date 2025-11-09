import { useState } from "react";
import { useParams } from "react-router-dom";
import "./ProductDetails.css";

type ChatMessage = { role: "user" | "model"; content: string };

function Chatbot({ productId }: { productId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "model", content: "Hi! Ask me anything about this product’s plan, budget, or timeline." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      // Option A (client-only demo): direct REST call to Gemini
      // NOTE: Exposes your API key in the browser — use only for quick testing!
      const apiKey = import.meta.env.VITE_GEMINI_API_KEY as string;
      const model = "gemini-2.5-flash"; // or gemini-1.5-pro

      const resp = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [
              // you can prepend a system-style instruction by adding another part here
              { role: "user", parts: [{ text: `Product ID: ${productId}\n\nUser: ${text}` }] },
            ],
            generationConfig: {
              temperature: 0.5,
              maxOutputTokens: 1024,
            },
          }),
        }
      );

      const data = await resp.json();

      if (!resp.ok) {
        // Log the actual error from the API to your browser console
        console.error("API Error Response:", data);
        // Throw an error to be caught by the 'catch' block
        throw new Error(data?.error?.message ?? "API request failed");
      }

      const reply =
        data?.candidates?.[0]?.content?.parts?.map((p: any) => p.text).join("\n") ??
        "Sorry, I didn’t catch that.";

      setMessages((m) => [...m, { role: "model", content: reply }]);
    } catch (e: any) {
      setMessages((m) => [...m, { role: "model", content: `Error: ${e?.message ?? e}` }]);
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

function ProductDetails() {
    const { id } = useParams();

    return (
        <div className="product-details-container">
            <h1>Product Details</h1>
            <p>Details for product with ID: {id}</p>

            <Chatbot productId={id ?? "unknown"} />
        </div>
    )
}

export default ProductDetails;