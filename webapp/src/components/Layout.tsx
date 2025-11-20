import React from "react";
import { APP_TITLE } from "../config";

interface LayoutProps {
  page: "chat" | "admin";
  onChangePage: (p: "chat" | "admin") => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ page, onChangePage, children }) => {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <header
        style={{
          background: "linear-gradient(120deg,#111827,#1f2937)",
          color: "white",
          padding: "1rem 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "0 2px 8px rgba(0,0,0,0.35)"
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: "1.6rem" }}>{APP_TITLE}</h1>
          <p style={{ margin: 0, opacity: 0.8, fontSize: "0.9rem" }}>
            Assistant intelligent pour l&apos;ESILV (RAG + multi-agents)
          </p>
        </div>
        <nav style={{ display: "flex", gap: "0.5rem" }}>
          <button
            onClick={() => onChangePage("chat")}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "999px",
              border: "none",
              cursor: "pointer",
              background: page === "chat" ? "#f97316" : "#e5e7eb",
              color: page === "chat" ? "white" : "#111827",
              fontWeight: 500
            }}
          >
            💬 Chat étudiant
          </button>
          <button
            onClick={() => onChangePage("admin")}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "999px",
              border: "none",
              cursor: "pointer",
              background: page === "admin" ? "#38bdf8" : "#e5e7eb",
              color: page === "admin" ? "white" : "#111827",
              fontWeight: 500
            }}
          >
            🛠️ Admin
          </button>
        </nav>
      </header>

      {/* Body */}
      <main
        style={{
          flex: 1,
          padding: "1.5rem 2rem",
          background: "#f5f5f7"
        }}
      >
        {children}
      </main>

      {/* Footer */}
      <footer
        style={{
          textAlign: "center",
          padding: "0.75rem",
          fontSize: "0.8rem",
          color: "#6b7280"
        }}
      >
        Projet ESILV – LLM & GenAI · Backend FastAPI + Ollama/Mistral · Frontend React
      </footer>
    </div>
  );
};
