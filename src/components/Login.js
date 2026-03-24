// src/components/Login.js
import { useAuth } from "../AuthContext";

export default function Login() {
  const { login } = useAuth();

  const s = {
    page: {
      minHeight: "100vh", background: "#0a0f1e", display: "flex",
      alignItems: "center", justifyContent: "center", fontFamily: "Georgia, serif",
    },
    card: {
      background: "#111827", border: "1px solid #1e293b", borderRadius: 16,
      padding: "48px 40px", maxWidth: 400, width: "90%", textAlign: "center",
    },
    title: { fontSize: 28, fontWeight: 700, color: "#f8fafc", margin: "0 0 8px" },
    sub: { fontSize: 14, color: "#64748b", margin: "0 0 36px", fontFamily: "system-ui, sans-serif", lineHeight: 1.6 },
    btn: {
      display: "flex", alignItems: "center", justifyContent: "center", gap: 12,
      width: "100%", padding: "13px 0", borderRadius: 8, border: "none",
      background: "#4ade80", color: "#0a0f1e", fontSize: 15, fontWeight: 700,
      fontFamily: "system-ui, sans-serif", cursor: "pointer", letterSpacing: "0.2px",
    },
    accent: { color: "#4ade80" },
  };

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={{ fontSize: 40, marginBottom: 16 }}>⏱</div>
        <h1 style={s.title}>Time <span style={s.accent}>Ledger</span></h1>
        <p style={s.sub}>
          See every commitment you've made, how long it will take,
          and how much time you actually have.
        </p>
        <button style={s.btn} onClick={login}>
          <svg width="20" height="20" viewBox="0 0 48 48">
            <path fill="#FFC107" d="M43.6 20H24v8h11.3C33.7 33.1 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.7 1.1 7.8 2.9l5.7-5.7C34.1 6.5 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20c11 0 19.7-8 19.7-20 0-1.3-.1-2.7-.1-4z"/>
            <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.5 16 19 13 24 13c3 0 5.7 1.1 7.8 2.9l5.7-5.7C34.1 6.5 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
            <path fill="#4CAF50" d="M24 44c5.2 0 9.9-1.9 13.5-5l-6.2-5.2C29.4 35.5 26.8 36 24 36c-5.2 0-9.6-3-11.3-7.2L6 33.8C9.4 39.6 16.2 44 24 44z"/>
            <path fill="#1976D2" d="M43.6 20H24v8h11.3c-.9 2.5-2.6 4.6-4.8 6l6.2 5.2C40.4 35.6 44 30.2 44 24c0-1.3-.1-2.7-.4-4z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  );
}
