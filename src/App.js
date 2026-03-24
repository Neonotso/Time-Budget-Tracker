// src/App.js
import { useState } from "react";
import { useAuth } from "./AuthContext";
import { useData } from "./useData";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import TaskList from "./components/TaskList";
import Budget from "./components/Budget";

export default function App() {
  const { user, logout } = useAuth();
  const [view, setView] = useState("dashboard");

  const { tasks, weeklyBudget, setWeeklyBudget, addTask, updateTask, deleteTask, loading } = useData(user?.uid ?? "anon");

  // ── Not logged in ────────────────────────────────────────────
  if (!user && user !== undefined) return <Login />;

  // ── Loading ──────────────────────────────────────────────────
  if (user === undefined || loading) {
    return (
      <div style={{ minHeight: "100vh", background: "#0a0f1e", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: "#4ade80", fontFamily: "Georgia, serif", fontSize: 18 }}>Loading your time ledger…</div>
      </div>
    );
  }

  const navBtn = (v, label) => ({
    padding: "8px 16px", border: "none", borderRadius: "6px 6px 0 0", cursor: "pointer",
    fontSize: 13, fontFamily: "system-ui, sans-serif", fontWeight: 600, letterSpacing: "0.3px",
    background: view === v ? "#1e293b" : "transparent",
    color: view === v ? "#f8fafc" : "#64748b",
    borderBottom: view === v ? "2px solid #4ade80" : "2px solid transparent",
  });

  return (
    <div style={{ minHeight: "100vh", background: "#0a0f1e", color: "#e2e8f0", fontFamily: "Georgia, serif", paddingBottom: 60 }}>
      {/* Header */}
      <div style={{ padding: "28px 28px 0", borderBottom: "1px solid #1e293b", marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: "#f8fafc", margin: 0 }}>Time Ledger</h1>
            <p style={{ fontSize: 13, color: "#64748b", marginTop: 4, fontFamily: "system-ui, sans-serif" }}>
              Your commitment budget
            </p>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <img src={user.photoURL} alt="" style={{ width: 32, height: 32, borderRadius: "50%" }} />
            <button onClick={logout} style={{
              background: "none", border: "1px solid #1e293b", borderRadius: 6, color: "#64748b",
              fontSize: 12, padding: "5px 10px", cursor: "pointer", fontFamily: "system-ui, sans-serif"
            }}>Sign out</button>
          </div>
        </div>
        <div style={{ display: "flex", gap: 4, marginTop: 20 }}>
          <button style={navBtn("dashboard")} onClick={() => setView("dashboard")}>📊 Overview</button>
          <button style={navBtn("tasks")} onClick={() => setView("tasks")}>📋 All Tasks</button>
          <button style={navBtn("budget")} onClick={() => setView("budget")}>⏱ Budget</button>
        </div>
      </div>

      {/* Content */}
      <div style={{ padding: "0 24px" }}>
        {view === "dashboard" && <Dashboard tasks={tasks} weeklyBudget={weeklyBudget} />}
        {view === "tasks" && <TaskList tasks={tasks} addTask={addTask} updateTask={updateTask} deleteTask={deleteTask} />}
        {view === "budget" && <Budget tasks={tasks} weeklyBudget={weeklyBudget} setWeeklyBudget={setWeeklyBudget} />}
      </div>
    </div>
  );
}
