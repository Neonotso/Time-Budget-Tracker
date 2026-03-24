// src/firebase.js
// ─────────────────────────────────────────────────────────────
// Replace the values below with your own Firebase project config.
// Find them at: https://console.firebase.google.com
//   → Your project → Project Settings → Your apps → Web app → Config
// ─────────────────────────────────────────────────────────────

import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyDlF0dktLWfW5PyE8A8kivXItDE-xRZ788",
  authDomain: "time-budget-tracker.firebaseapp.com",
  projectId: "time-budget-tracker",
  storageBucket: "time-budget-tracker.firebasestorage.app",
  messagingSenderId: "309494705381",
  appId: "1:309494705381:web:91ff06e011650efcaa380c",
  measurementId: "G-CZQNZQ34ME"
};

const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();
export const db = getFirestore(app);
