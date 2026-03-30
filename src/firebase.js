// src/firebase.js
// Firebase configuration using environment variables
// Create a .env file based on .env.example and add it to .gitenv

import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// Load environment variables
const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || '',
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN || 'time-budget-tracker.firebaseapp.com',
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || 'time-budget-tracker',
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET || 'time-budget-tracker.firebasestorage.app',
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || '309494705381',
  appId: process.env.REACT_APP_FIREBASE_APP_ID || '1:309494705381:web:91ff06e011650efcaa380c',
  measurementId: process.env.REACT_APP_FIREBASE_MEASUREMENT_ID || 'G-CZQNZQ34ME'
};

// Validate that we have the required configuration
if (!firebaseConfig.apiKey) {
  console.warn('Firebase API key not found in environment variables. Please check your .env file.');
}

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const provider = new GoogleAuthProvider();
export const db = getFirestore(app);
