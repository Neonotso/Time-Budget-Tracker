// src/components/Dashboard.js
import { useMemo } from "react";
import { CATEGORIES, CATEGORY_COLORS } from "../defaultTasks";

function GaugeArc({ pct, color }) {
  const r = 54, cx = 60, cy = 60;
  const clampedPct = Math.min(Math.max(pct, 0), 1);
  const x2 = cx + r * Math.cos(Math.PI + clampedPct * Math.PI);
  const y2 = cy + r * Math.sin(Math.PI + clampedPct * Math.PI);
  const largeArc = clampedPct > 0.5 ? 1 : 0;
  const pathBg = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`;
  const pathFill = clampedPct === 0 ? "" : `M ${cx - r} ${cy} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`;
  return (
    <svg width="120" height="70" viewBox="0 0 120 70">
      <path d={pathBg} fill="none" stroke="#1e293b" strokeWidth="10" strokeLinecap="round" />
      {clampedPct > 0 && <path d={pathFill} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round" />}
    </svg>
  );
}

function BarRow({ label, hours, max, color }) {
  const pct = max > 0 ? Math.min(hours / max, 1) : 0;
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94a3b8", marginBottom: 3, fontFamily: "system-ui, sans-serif" }}>
        <span>{label}</span>
        <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{hours.toFixed(1)}h</span>
      </div>
      <div style={{ height: 7, borderRadius: 99, background: "#1e293b", overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct * 100}%`, background: color, borderRadius: 99, transition: "width 0.4s ease" }} />
      </div>
    </div>
  );
}

export default function Dashboard({ tasks, weeklyBudget }) {
  const stats = useMemo(() => {
    const totalHours = tasks.reduce((s, t) => s + Number(t.hours), 0);
    const doneHours = tasks.reduce((s, t) => s + Number(t.done), 0);
    const remaining = totalHours - doneHours;
    const weeklyLoad = tasks
      .filter(t => t.category === "Recurring" || t.category === "Work")
      .reduce((s, t) => s + Number(t.hours), 0);
    const discretionary = weeklyBudget - weeklyLoad;
    const projectsRemaining = tasks
      .filter(t => t.category !== "Recurring" && t.category !== "Work")
      .reduce((s, t) => s + Math.max(0, Number(t.hours) - Number(t.done)), 0);
    const weeksToComplete = discretionary > 0 ? projectsRemaining / discretionary : Infinity;
    const byCategory = {};
    CATEGORIES.forEach(c => {
      byCategory[c] = tasks.filter(t => t.category === c).reduce((s, t) => s + Math.max(0, Number(t.hours) - Number(t.done)), 0);
    });
    return { totalHours, doneHours, remaining, weeklyLoad, discretionary, weeksToComplete, byCategory, projectsRemaining };
  }, [tasks, weeklyBudget]);

  const debtPct = weeklyBudget > 0 ? Math.min(stats.remaining / (weeklyBudget * 52), 1) : 1;
  const debtColor = debtPct < 0.4 ? "#4ade80" : debtPct < 0.7 ? "#fbbf24" : "#f87171";
  const weeksClamped = isFinite(stats.weeksToComplete) && stats.weeksToComplete > 0 ? Math.round(stats.weeksToComplete) : null;

  const s = {
    card: { background: "#111827", borderRadius: 12, padding: 20, marginBottom: 16, border: "1px solid #1e293b" },
    cardTitle: { fontSize: 11, fontFamily: "system-ui, sans-serif", letterSpacing: "1.5px", textTransform: "uppercase", color: "#4ade80", fontWeight: 700, marginBottom: 12, margin: "0 0 12px" },
    statNum: { fontSize: 32, fontWeight: 700, color: "#f8fafc", lineHeight: 1, fontFamily: "Georgia, serif" },
    statLabel: { fontSize: 12, color: "#64748b", fontFamily: "system-ui, sans-serif", marginTop: 4 },
    grid3: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 },
    pill: (color) => ({ display: "inline-block", padding: "2px 8px", borderRadius: 99, fontSize: 11, fontFamily: "system-ui, sans-serif", fontWeight: 600, background: color + "22", color }),
  };

  return (
    <>
      {/* Gauge */}
      <div style={{ ...s.card, textAlign: "center", paddingTop: 24 }}>
        <p style={s.cardTitle}>Time Debt Gauge</p>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: -8 }}>
          <GaugeArc pct={debtPct} color={debtColor} />
        </div>
        <div style={{ ...s.statNum, color: debtColor, fontSize: 40 }}>
          {stats.remaining.toFixed(0)}<span style={{ fontSize: 18, color: "#64748b" }}>h</span>
        </div>
        <div style={{ ...s.statLabel, fontSize: 13 }}>hours of committed work remaining</div>
        {weeksClamped ? (
          <div style={{ marginTop: 12, fontSize: 13, color: "#94a3b8", fontFamily: "system-ui, sans-serif" }}>
            At your current pace →{" "}
            <span style={{ color: debtColor, fontWeight: 700 }}>~{weeksClamped} weeks</span> to clear non-recurring work
            {" "}(~{(weeksClamped / 4.3).toFixed(1)} months)
          </div>
        ) : (
          <div style={{ marginTop: 12, fontSize: 13, color: "#f87171", fontFamily: "system-ui, sans-serif" }}>
            ⚠️ Recurring + Work commitments already exceed your weekly budget.
          </div>
        )}
      </div>

      {/* Key numbers */}
      <div style={s.grid3}>
        <div style={s.card}>
          <p style={s.cardTitle}>Weekly Budget</p>
          <div style={s.statNum}>{weeklyBudget}<span style={{ fontSize: 16, color: "#64748b" }}>h</span></div>
          <div style={s.statLabel}>free hours/week</div>
        </div>
        <div style={s.card}>
          <p style={{ ...s.cardTitle, color: "#fb923c" }}>Weekly Load</p>
          <div style={{ ...s.statNum, color: "#fb923c" }}>{stats.weeklyLoad.toFixed(1)}<span style={{ fontSize: 16, color: "#64748b" }}>h</span></div>
          <div style={s.statLabel}>recurring + work</div>
        </div>
        <div style={s.card}>
          <p style={{ ...s.cardTitle, color: "#60a5fa" }}>Discretionary</p>
          <div style={{ ...s.statNum, color: stats.discretionary < 0 ? "#f87171" : "#60a5fa" }}>
            {stats.discretionary.toFixed(1)}<span style={{ fontSize: 16, color: "#64748b" }}>h</span>
          </div>
          <div style={s.statLabel}>left for projects/week</div>
        </div>
      </div>

      {/* By category */}
      <div style={s.card}>
        <p style={s.cardTitle}>Hours Remaining by Category</p>
        {CATEGORIES.map(c => (
          <BarRow key={c} label={c} hours={stats.byCategory[c] || 0} max={stats.remaining || 1} color={CATEGORY_COLORS[c]} />
        ))}
      </div>

      {/* Top commitments */}
      <div style={s.card}>
        <p style={s.cardTitle}>Biggest Commitments</p>
        {[...tasks]
          .sort((a, b) => (Number(b.hours) - Number(b.done)) - (Number(a.hours) - Number(a.done)))
          .slice(0, 7)
          .map(t => {
            const rem = Math.max(0, Number(t.hours) - Number(t.done));
            return (
              <div key={t.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderBottom: "1px solid #1e293b" }}>
                <div>
                  <div style={{ fontSize: 14, color: "#e2e8f0", marginBottom: 3 }}>{t.name}</div>
                  <span style={s.pill(CATEGORY_COLORS[t.category])}>{t.category}</span>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: "#f8fafc" }}>{rem.toFixed(0)}h</div>
                  <div style={{ fontSize: 11, color: "#64748b", fontFamily: "system-ui, sans-serif" }}>remaining</div>
                </div>
              </div>
            );
          })}
      </div>
    </>
  );
}
