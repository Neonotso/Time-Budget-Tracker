// src/components/Budget.js
import { useMemo } from "react";

export default function Budget({ tasks, weeklyBudget, setWeeklyBudget }) {
  const stats = useMemo(() => {
    const weeklyLoad = tasks
      .filter(t => t.category === "Recurring" || t.category === "Work")
      .reduce((s, t) => s + Number(t.hours), 0);
    const discretionary = weeklyBudget - weeklyLoad;
    const projectsRemaining = tasks
      .filter(t => t.category !== "Recurring" && t.category !== "Work")
      .reduce((s, t) => s + Math.max(0, Number(t.hours) - Number(t.done)), 0);
    const weeksToComplete = discretionary > 0 ? projectsRemaining / discretionary : Infinity;
    return { weeklyLoad, discretionary, projectsRemaining, weeksToComplete };
  }, [tasks, weeklyBudget]);

  const weeksClamped = isFinite(stats.weeksToComplete) && stats.weeksToComplete > 0 ? Math.round(stats.weeksToComplete) : null;

  const s = {
    card: { background: "#111827", borderRadius: 12, padding: 20, marginBottom: 16, border: "1px solid #1e293b", marginTop: 16 },
    cardTitle: { fontSize: 11, fontFamily: "system-ui, sans-serif", letterSpacing: "1.5px", textTransform: "uppercase", color: "#4ade80", fontWeight: 700, margin: "0 0 12px" },
    row: { display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid #1e293b", alignItems: "center", fontFamily: "system-ui, sans-serif" },
    rowLabel: { fontSize: 14, color: "#94a3b8" },
    rowVal: (color) => ({ fontSize: 20, fontWeight: 700, color: color || "#e2e8f0" }),
    note: { fontSize: 12, color: "#475569", marginTop: 12, fontFamily: "system-ui, sans-serif", lineHeight: 1.6 },
  };

  return (
    <>
      {/* Slider */}
      <div style={s.card}>
        <p style={s.cardTitle}>Set Your Weekly Time Budget</p>
        <p style={{ fontSize: 13, color: "#64748b", fontFamily: "system-ui, sans-serif", marginTop: 0, marginBottom: 20 }}>
          How many free hours do you realistically have per week — after sleep, meals, and fixed obligations?
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <input type="range" min={1} max={60} value={weeklyBudget}
            onChange={e => setWeeklyBudget(Number(e.target.value))}
            style={{ flex: 1, accentColor: "#4ade80" }} />
          <div style={{ fontSize: 32, fontWeight: 700, color: "#f8fafc", minWidth: 70, textAlign: "right", fontFamily: "Georgia, serif" }}>
            {weeklyBudget}<span style={{ fontSize: 16, color: "#64748b" }}>h</span>
          </div>
        </div>
      </div>

      {/* Weekly breakdown */}
      <div style={{ ...s.card, marginTop: 0 }}>
        <p style={s.cardTitle}>Weekly Breakdown</p>
        <div style={s.row}>
          <span style={s.rowLabel}>Total weekly budget</span>
          <span style={s.rowVal("#4ade80")}>+{weeklyBudget.toFixed(1)}h</span>
        </div>
        <div style={s.row}>
          <span style={s.rowLabel}>Recurring + Work commitments</span>
          <span style={s.rowVal("#fb923c")}>−{stats.weeklyLoad.toFixed(1)}h</span>
        </div>
        <div style={s.row}>
          <span style={s.rowLabel}>Discretionary (for projects)</span>
          <span style={s.rowVal(stats.discretionary < 0 ? "#f87171" : "#60a5fa")}>
            {stats.discretionary >= 0 ? "+" : ""}{stats.discretionary.toFixed(1)}h
          </span>
        </div>
      </div>

      {/* Project debt */}
      <div style={{ ...s.card, marginTop: 0 }}>
        <p style={s.cardTitle}>Project Time Debt Analysis</p>
        {[
          { label: "Project hours remaining", val: `${stats.projectsRemaining.toFixed(1)}h` },
          { label: "Discretionary hours/week", val: `${stats.discretionary.toFixed(1)}h` },
          { label: "Weeks to clear at current pace", val: weeksClamped ? `~${weeksClamped} weeks` : "∞" },
          { label: "Months equivalent", val: weeksClamped ? `~${(weeksClamped / 4.3).toFixed(1)} months` : "∞" },
        ].map(row => (
          <div key={row.label} style={s.row}>
            <span style={s.rowLabel}>{row.label}</span>
            <span style={s.rowVal()}>{row.val}</span>
          </div>
        ))}
        <p style={s.note}>
          * This assumes all discretionary time goes to projects. Reality will take longer — build in margin.
          The goal isn't to clear everything instantly; it's to see clearly so you can make honest decisions about what to commit to.
        </p>
      </div>
    </>
  );
}
