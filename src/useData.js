// src/useData.js
// All Firestore reads and writes live here.
// Data shape in Firestore:
//   users/{uid}/tasks/{taskId}   → task fields
//   users/{uid}/settings/budget  → { weeklyHours: number }

import { useState, useEffect, useCallback } from "react";
import {
  collection, doc, onSnapshot,
  addDoc, updateDoc, deleteDoc, setDoc, serverTimestamp,
} from "firebase/firestore";
import { db } from "./firebase";
import { DEFAULT_TASKS, DEFAULT_WEEKLY_HOURS } from "./defaultTasks";

export function useData(uid) {
  const [tasks, setTasks] = useState([]);
  const [weeklyBudget, setWeeklyBudgetState] = useState(DEFAULT_WEEKLY_HOURS);
  const [loading, setLoading] = useState(true);

  const tasksRef = collection(db, "users", uid, "tasks");
  const budgetRef = doc(db, "users", uid, "settings", "budget");

  // ── Real-time listeners ──────────────────────────────────────
  useEffect(() => {
    let seeded = false;

    const unsubTasks = onSnapshot(tasksRef, async (snap) => {
      if (snap.empty && !seeded) {
        // First login — seed with default tasks
        seeded = true;
        const writes = DEFAULT_TASKS.map((t) =>
          addDoc(tasksRef, { ...t, createdAt: serverTimestamp() })
        );
        await Promise.all(writes);
        return;
      }
      const loaded = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
      loaded.sort((a, b) => (a.createdAt?.seconds ?? 0) - (b.createdAt?.seconds ?? 0));
      setTasks(loaded);
      setLoading(false);
    });

    const unsubBudget = onSnapshot(budgetRef, (snap) => {
      if (snap.exists()) {
        setWeeklyBudgetState(snap.data().weeklyHours ?? DEFAULT_WEEKLY_HOURS);
      }
    });

    return () => { unsubTasks(); unsubBudget(); };
  }, [uid]); // eslint-disable-line

  // ── Task mutations ───────────────────────────────────────────
  const addTask = useCallback((task) => {
    return addDoc(tasksRef, { ...task, createdAt: serverTimestamp() });
  }, [uid]); // eslint-disable-line

  const updateTask = useCallback((id, fields) => {
    return updateDoc(doc(tasksRef, id), fields);
  }, [uid]); // eslint-disable-line

  const deleteTask = useCallback((id) => {
    return deleteDoc(doc(tasksRef, id));
  }, [uid]); // eslint-disable-line

  // ── Budget mutation ──────────────────────────────────────────
  const setWeeklyBudget = useCallback((hours) => {
    setWeeklyBudgetState(hours); // optimistic local update
    return setDoc(budgetRef, { weeklyHours: hours }, { merge: true });
  }, [uid]); // eslint-disable-line

  return { tasks, weeklyBudget, setWeeklyBudget, addTask, updateTask, deleteTask, loading };
}
