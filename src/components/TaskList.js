// src/components/TaskList.js
import { useState } from "react";
import { CATEGORIES, CATEGORY_COLORS } from "../defaultTasks";

const STYLES = {
  input: { background: "#0a0f1e", border: "1px solid #1e293b", borderRadius: 6, padding: "7px 10px", color: "#e2e8f0", fontSize: 13, fontFamily: "system-ui, sans-serif", width: "100%", boxSizing: "border-box" },
  label: { fontSize: 12, color: "#64748b", fontFamily: "system-ui, sans-serif", marginBottom: 4, display: "block" },
  card: { background: "#111827", borderRadius: 12, padding: 20, marginBottom: 16, border: "1px solid #1e293b" },
  cardTitle: { fontSize: 11, fontFamily: "system-ui, sans-serif", letterSpacing: "1.5px", textTransform: "uppercase", color: "#4ade80", fontWeight: 700, margin: "0 0 12px" },
};

function btn(variant) {
  return {
    padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 13,
    fontFamily: "system-ui, sans-serif", fontWeight: 600,
    background: variant === "primary" ? "#4ade80" : variant === "danger" ? "#f8717122" : "#1e293b",
    color: variant === "primary" ? "#0a0f1e" : variant === "danger" ? "#f87171" : "#94a3b8",
  };
}

function pill(color) {
  return { display: "inline-block", padding: "2px 8px", borderRadius: 99, fontSize: 11, fontFamily: "system-ui, sans-serif", fontWeight: 600, background: color + "22", color };
}

export default function TaskList({ tasks, addTask, updateTask, deleteTask }) {
  const [filterCat, setFilterCat] = useState("All");
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [newTask, setNewTask] = useState({ name: "", category: "Project (Open-ended)", hours: 1, done: 0, deadline: "", notes: "" });

  const handleAdd = () => {
    if (!newTask.name.trim()) return;
    addTask({ ...newTask, hours: Number(newTask.hours), done: Number(newTask.done) });
    setNewTask({ name: "", category: "Project (Open-ended)", hours: 1, done: 0, deadline: "", notes: "" });
    setShowAdd(false);
  };

  const filtered = filterCat === "All" ? tasks : tasks.filter(t => t.category === filterCat);

  return (
    <>
      {/* Filter + Add bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, marginTop: 16, flexWrap: "wrap", gap: 8 }}>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {["All", ...CATEGORIES].map(c => (
            <button key={c} onClick={() => setFilterCat(c)} style={{
              padding: "4px 12px", borderRadius: 99, border: "none", cursor: "pointer", fontSize: 12,
              fontFamily: "system-ui, sans-serif", fontWeight: 600,
              background: filterCat === c ? (CATEGORY_COLORS[c] || "#4ade80") : "#1e293b",
              color: filterCat === c ? "#0a0f1e" : "#94a3b8",
            }}>{c}</button>
          ))}
        </div>
        <button style={btn("primary")} onClick={() => setShowAdd(v => !v)}>+ Add Task</button>
      </div>

      {/* Add form */}
      {showAdd && (
        <div style={{ ...STYLES.card, border: "1px solid #4ade8044" }}>
          <p style={STYLES.cardTitle}>New Task</p>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: 10, marginBottom: 10 }}>
            <div>
              <label style={STYLES.label}>Task Name</label>
              <input style={STYLES.input} value={newTask.name} onChange={e => setNewTask(p => ({ ...p, name: e.target.value }))} placeholder="e.g. Record Sylvia's song" />
            </div>
            <div>
              <label style={STYLES.label}>Est. Hours</label>
              <input style={STYLES.input} type="number" min={0} step={0.5} value={newTask.hours} onChange={e => setNewTask(p => ({ ...p, hours: e.target.value }))} />
            </div>
            <div>
              <label style={STYLES.label}>Hours Done</label>
              <input style={STYLES.input} type="number" min={0} step={0.5} value={newTask.done} onChange={e => setNewTask(p => ({ ...p, done: e.target.value }))} />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr", gap: 10, marginBottom: 14 }}>
            <div>
              <label style={STYLES.label}>Category</label>
              <select style={STYLES.input} value={newTask.category} onChange={e => setNewTask(p => ({ ...p, category: e.target.value }))}>
                {CATEGORIES.map(c => <option key={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label style={STYLES.label}>Deadline (optional)</label>
              <input style={STYLES.input} type="date" value={newTask.deadline} onChange={e => setNewTask(p => ({ ...p, deadline: e.target.value }))} />
            </div>
            <div>
              <label style={STYLES.label}>Notes</label>
              <input style={STYLES.input} value={newTask.notes} onChange={e => setNewTask(p => ({ ...p, notes: e.target.value }))} placeholder="Optional" />
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button style={btn("primary")} onClick={handleAdd}>Add Task</button>
            <button style={btn()} onClick={() => setShowAdd(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Task rows */}
      {filtered.map(task => {
        const rem = Math.max(0, Number(task.hours) - Number(task.done));
        const pct = Number(task.hours) > 0 ? Math.min(Number(task.done) / Number(task.hours), 1) : 0;
        const isEditing = editingId === task.id;

        return (
          <div key={task.id} style={{ background: "#111827", border: "1px solid #1e293b", borderRadius: 10, padding: "12px 14px", marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
              <div style={{ flex: 1, paddingRight: 12 }}>
                {isEditing ? (
                  <input style={{ ...STYLES.input, fontSize: 15, fontWeight: 600 }}
                    value={task.name} onChange={e => updateTask(task.id, { name: e.target.value })} />
                ) : (
                  <div style={{ fontSize: 15, fontWeight: 600, color: "#f8fafc" }}>{task.name}</div>
                )}
                <div style={{ display: "flex", gap: 8, marginTop: 4, alignItems: "center", flexWrap: "wrap" }}>
                  <span style={pill(CATEGORY_COLORS[task.category])}>{task.category}</span>
                  {task.deadline && <span style={{ fontSize: 11, color: "#94a3b8", fontFamily: "system-ui, sans-serif" }}>📅 {task.deadline}</span>}
                  {task.notes && <span style={{ fontSize: 11, color: "#64748b", fontFamily: "system-ui, sans-serif" }}>{task.notes}</span>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                <button style={btn()} onClick={() => setEditingId(isEditing ? null : task.id)}>{isEditing ? "✓ Done" : "Edit"}</button>
                <button style={btn("danger")} onClick={() => deleteTask(task.id)}>✕</button>
              </div>
            </div>

            {isEditing ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 8, marginTop: 8 }}>
                <div>
                  <label style={STYLES.label}>Est. Hours</label>
                  <input style={STYLES.input} type="number" min={0} step={0.5} value={task.hours}
                    onChange={e => updateTask(task.id, { hours: Number(e.target.value) })} />
                </div>
                <div>
                  <label style={STYLES.label}>Hours Done</label>
                  <input style={STYLES.input} type="number" min={0} step={0.5} value={task.done}
                    onChange={e => updateTask(task.id, { done: Number(e.target.value) })} />
                </div>
                <div>
                  <label style={STYLES.label}>Category</label>
                  <select style={STYLES.input} value={task.category}
                    onChange={e => updateTask(task.id, { category: e.target.value })}>
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label style={STYLES.label}>Deadline</label>
                  <input style={STYLES.input} type="date" value={task.deadline || ""}
                    onChange={e => updateTask(task.id, { deadline: e.target.value })} />
                </div>
                <div style={{ gridColumn: "1 / -1" }}>
                  <label style={STYLES.label}>Notes</label>
                  <input style={STYLES.input} value={task.notes || ""}
                    onChange={e => updateTask(task.id, { notes: e.target.value })} placeholder="Optional notes" />
                </div>
              </div>
            ) : (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#64748b", fontFamily: "system-ui, sans-serif", marginBottom: 4 }}>
                  <span>{(pct * 100).toFixed(0)}% done</span>
                  <span><strong style={{ color: "#e2e8f0" }}>{rem.toFixed(1)}h</strong> remaining of {Number(task.hours).toFixed(1)}h</span>
                </div>
                <div style={{ height: 6, borderRadius: 99, background: "#1e293b", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${pct * 100}%`, background: CATEGORY_COLORS[task.category], borderRadius: 99, transition: "width 0.3s ease" }} />
                </div>
              </div>
            )}
          </div>
        );
      })}

      {filtered.length === 0 && (
        <div style={{ textAlign: "center", color: "#64748b", fontFamily: "system-ui, sans-serif", padding: 40 }}>
          No tasks in this category yet.
        </div>
      )}
    </>
  );
}
