import React, { useEffect, useMemo, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { apiChat } from "../api";
import type { ConversationTurn, ChatResponse, ContextDocument } from "../types";

function getOrCreateUserId(): string {
  const key = "esilv_user_id";
  let existing = window.localStorage.getItem(key);
  if (!existing) {
    existing = uuidv4();
    window.localStorage.setItem(key, existing);
  }
  return existing;
}

export const ChatPage: React.FC = () => {
  const [userId] = useState<string>(() => getOrCreateUserId());
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const newUserTurn: ConversationTurn = {
      role: "user",
      content: text
    };
    setTurns(prev => [...prev, newUserTurn]);
    setInput("");
    setLoading(true);

    try {
      const resp: ChatResponse = await apiChat({ user_id: userId, message: text });

      const meta = {
        agent: resp.agent,
        intent: resp.intent,
        metadata: resp.metadata,
        context_documents: resp.context_documents
      };

      const assistantTurn: ConversationTurn = {
        role: "assistant",
        content: resp.reply,
        meta
      };
      setTurns(prev => [...prev, assistantTurn]);
    } catch (e: any) {
      const errTurn: ConversationTurn = {
        role: "assistant",
        content: `Erreur côté serveur : ${e?.message ?? e}`
      };
      setTurns(prev => [...prev, errTurn]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const intro = useMemo(
    () => (
      <div
        style={{
          marginBottom: "1rem",
          padding: "1rem 1.25rem",
          borderRadius: "0.75rem",
          background: "white",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)"
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: "0.5rem" }}>💬 Assistant ESILV</h2>
        <p style={{ margin: 0, fontSize: "0.9rem", color: "#4b5563" }}>
          Posez vos questions sur :
        </p>
        <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.2rem", fontSize: "0.9rem" }}>
          <li>les <strong>programmes ESILV</strong></li>
          <li>les <strong>admissions</strong></li>
          <li>les <strong>cours / spécialisations</strong></li>
          <li>ou laissez vos <strong>coordonnées</strong> pour être recontacté 🧑‍💼</li>
        </ul>
      </div>
    ),
    []
  );

  const renderSources = (docs?: ContextDocument[]) => {
    if (!docs || docs.length === 0) return null;

    return (
      <div style={{ marginTop: "0.5rem" }}>
        <strong>📚 Sources utilisées :</strong>
        <ul style={{ margin: "0.25rem 0 0", paddingLeft: "1.2rem", fontSize: "0.85rem" }}>
          {docs.map((doc, i) => {
            const source = doc.source || `Document ${i + 1}`;
            const page = doc.page;
            const url = doc.url;
            const snippet = doc.snippet || "";

            const labelPage =
              page !== undefined && page !== null && page !== "N/A" ? ` — page ${page}` : "";

            return (
              <li key={i} style={{ marginBottom: "0.25rem" }}>
                {url ? (
                  <a href={url} target="_blank" rel="noreferrer">
                    📄 {source}
                    {labelPage}
                  </a>
                ) : (
                  <>
                    📄 {source}
                    {labelPage}
                  </>
                )}
                {snippet && (
                  <div style={{ color: "#6b7280" }}>
                    {snippet.length > 250 ? snippet.slice(0, 250) + "…" : snippet}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </div>
    );
  };

  return (
    <div style={{ maxWidth: "960px", margin: "0 auto" }}>
      {intro}

      {/* Messages */}
      <div
        style={{
          maxHeight: "60vh",
          overflowY: "auto",
          paddingRight: "0.25rem",
          marginBottom: "1rem"
        }}
      >
        {turns.map((t, idx) => {
          const isUser = t.role === "user";
          const meta = t.meta || {};
          const ctxDocs: ContextDocument[] = meta.context_documents || [];

          return (
            <div
              key={idx}
              style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                marginBottom: "0.5rem"
              }}
            >
              <div
                style={{
                  maxWidth: "80%",
                  borderRadius: "0.75rem",
                  padding: "0.75rem 0.9rem",
                  background: isUser ? "#f97316" : "white",
                  color: isUser ? "white" : "#111827",
                  boxShadow: isUser ? "0 1px 3px rgba(248,113,22,0.5)" : "0 1px 4px rgba(0,0,0,0.06)",
                  fontSize: "0.95rem",
                  whiteSpace: "pre-wrap"
                }}
              >
                {t.content}

                {!isUser && renderSources(ctxDocs)}

                {!isUser && (meta.agent || meta.intent) && (
                  <details style={{ marginTop: "0.4rem", fontSize: "0.8rem", color: "#6b7280" }}>
                    <summary>🔧 Détails techniques (debug)</summary>
                    <pre
                      style={{
                        marginTop: "0.25rem",
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas",
                        whiteSpace: "pre-wrap"
                      }}
                    >
                      {JSON.stringify(meta, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Zone d'entrée */}
      <div
        style={{
          background: "white",
          borderRadius: "0.75rem",
          padding: "0.75rem",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          display: "flex",
          gap: "0.5rem",
          alignItems: "flex-end"
        }}
      >
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Posez votre question sur l'ESILV, ou indiquez que vous souhaitez être recontacté..."
          rows={2}
          style={{
            flex: 1,
            resize: "none",
            borderRadius: "0.5rem",
            border: "1px solid #d1d5db",
            padding: "0.5rem 0.75rem",
            fontFamily: "inherit",
            fontSize: "0.95rem"
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            padding: "0.55rem 1rem",
            borderRadius: "999px",
            border: "none",
            cursor: loading ? "default" : "pointer",
            background: loading ? "#e5e7eb" : "#16a34a",
            color: loading ? "#9ca3af" : "white",
            fontWeight: 500,
            whiteSpace: "nowrap"
          }}
        >
          {loading ? "..." : "Envoyer"}
        </button>
      </div>
    </div>
  );
};
