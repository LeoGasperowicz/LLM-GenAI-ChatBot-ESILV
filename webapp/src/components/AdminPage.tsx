import React, { useEffect, useState } from "react";
import { apiGetContacts, apiGetStats } from "../api";
import type { AdminStats, ContactEntry } from "../types";

export const AdminPage: React.FC = () => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [contacts, setContacts] = useState<ContactEntry[]>([]);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [errorStats, setErrorStats] = useState<string | null>(null);
  const [errorContacts, setErrorContacts] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      setLoadingStats(true);
      setErrorStats(null);
      try {
        const s = await apiGetStats();
        setStats(s);
      } catch (e: any) {
        setErrorStats(e?.message ?? String(e));
      } finally {
        setLoadingStats(false);
      }
    };

    const loadContacts = async () => {
      setLoadingContacts(true);
      setErrorContacts(null);
      try {
        const c = await apiGetContacts();
        setContacts(c);
      } catch (e: any) {
        setErrorContacts(e?.message ?? String(e));
      } finally {
        setLoadingContacts(false);
      }
    };

    loadStats();
    loadContacts();
  }, []);

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
      <h2 style={{ marginTop: 0 }}>🛠️ Dashboard Admin ESILV Assistant</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0,1.3fr) minmax(0,1fr)",
          gap: "1.25rem",
          alignItems: "flex-start"
        }}
      >
        {/* Stats globales */}
        <section
          style={{
            background: "white",
            borderRadius: "0.75rem",
            padding: "1rem 1.25rem",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)"
          }}
        >
          <h3 style={{ marginTop: 0 }}>📊 Statistiques globales</h3>

          {loadingStats && <p>Chargement des statistiques…</p>}
          {errorStats && <p style={{ color: "crimson" }}>Erreur : {errorStats}</p>}

          {stats && !loadingStats && !errorStats && (
            <>
              <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                <div
                  style={{
                    flex: 1,
                    background: "#eff6ff",
                    borderRadius: "0.75rem",
                    padding: "0.75rem"
                  }}
                >
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Conversations</div>
                  <div style={{ fontSize: "1.6rem", fontWeight: 600 }}>
                    {stats.total_conversations}
                  </div>
                </div>
                <div
                  style={{
                    flex: 1,
                    background: "#ecfdf3",
                    borderRadius: "0.75rem",
                    padding: "0.75rem"
                  }}
                >
                  <div style={{ fontSize: "0.8rem", color: "#6b7280" }}>Messages</div>
                  <div style={{ fontSize: "1.6rem", fontWeight: 600 }}>
                    {stats.total_messages}
                  </div>
                </div>
              </div>

              <div>
                <strong>Intents les plus fréquents :</strong>
                {Object.keys(stats.top_intents || {}).length === 0 ? (
                  <p style={{ fontSize: "0.9rem", color: "#6b7280" }}>
                    Aucun intent enregistré pour le moment.
                  </p>
                ) : (
                  <ul style={{ fontSize: "0.9rem" }}>
                    {Object.entries(stats.top_intents).map(([intent, count]) => (
                      <li key={intent}>
                        <code>{intent}</code> : {count}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </section>

        {/* Contacts / personnes à recontacter */}
        <section
          style={{
            background: "white",
            borderRadius: "0.75rem",
            padding: "1rem 1.25rem",
            boxShadow: "0 1px 4px rgba(0,0,0,0.06)"
          }}
        >
          <h3 style={{ marginTop: 0 }}>📇 Personnes à recontacter</h3>

          {loadingContacts && <p>Chargement des contacts…</p>}
          {errorContacts && <p style={{ color: "crimson" }}>Erreur : {errorContacts}</p>}

          {!loadingContacts && !errorContacts && contacts.length === 0 && (
            <p
              style={{
                background: "#eff6ff",
                borderRadius: "0.75rem",
                padding: "0.75rem",
                fontSize: "0.9rem",
                color: "#1d4ed8"
              }}
            >
              Aucune personne à recontacter pour le moment.
            </p>
          )}

          {!loadingContacts &&
            !errorContacts &&
            contacts.map((c, idx) => {
              const name = c.full_name || "Nom inconnu";
              const email = c.email || "Email inconnu";
              const phone = c.phone || "Téléphone non renseigné";
              const raw = c.raw_message || "";
              const created = c.created_at;

              let dateStr = created;
              if (created) {
                try {
                  const d = new Date(created);
                  if (!isNaN(d.getTime())) {
                    dateStr = d.toLocaleString("fr-FR");
                  }
                } catch {
                  // ignore
                }
              }

              return (
                <div
                  key={idx}
                  style={{
                    borderTop: idx === 0 ? "none" : "1px solid #e5e7eb",
                    paddingTop: idx === 0 ? 0 : "0.75rem",
                    marginTop: idx === 0 ? 0 : "0.75rem"
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: "0.1rem" }}>👤 {name}</div>
                  <div style={{ fontSize: "0.9rem" }}>
                    📧 <a href={`mailto:${email}`}>{email}</a>
                  </div>
                  <div style={{ fontSize: "0.9rem" }}>📱 {phone}</div>
                  {dateStr && (
                    <div style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: "0.1rem" }}>
                      🕒 {dateStr}
                    </div>
                  )}
                  {raw && (
                    <div
                      style={{
                        marginTop: "0.35rem",
                        fontSize: "0.9rem",
                        background: "#f9fafb",
                        borderRadius: "0.5rem",
                        padding: "0.5rem 0.6rem"
                      }}
                    >
                      <div style={{ fontWeight: 500, marginBottom: "0.15rem" }}>
                        Message initial :
                      </div>
                      <div>{raw}</div>
                    </div>
                  )}
                </div>
              );
            })}
        </section>
      </div>

      <p style={{ marginTop: "1.5rem", fontSize: "0.8rem", color: "#6b7280" }}>
        Ce dashboard consomme les endpoints <code>/api/admin/stats</code> et{" "}
        <code>/api/admin/contacts</code> du backend FastAPI.
      </p>
    </div>
  );
};
