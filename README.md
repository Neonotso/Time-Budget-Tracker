# Time Ledger

A personal time budget app — see every commitment you've made, how long it'll take,
and compare it against how much time you actually have.

Built with React + Firebase (Firestore + Auth + Hosting).

---

## Setup (one-time, ~15 minutes)

### 1. Install Node.js and Firebase CLI

If you don't have Node.js: https://nodejs.org (install the LTS version)

Then install the Firebase CLI:
```bash
npm install -g firebase-tools
```

### 2. Create a Firebase project

1. Go to https://console.firebase.google.com
2. Click **Add project** → give it a name (e.g. "time-ledger")
3. Disable Google Analytics if you don't need it → **Create project**

### 3. Enable Google Sign-In

1. In your Firebase project → **Authentication** → **Get started**
2. Click **Google** under Sign-in providers → **Enable** → Save

### 4. Enable Firestore

1. In your Firebase project → **Firestore Database** → **Create database**
2. Choose **Start in production mode** → pick a region → **Done**

### 5. Register a Web App and get your config

1. In Firebase console → **Project Settings** (gear icon) → scroll to **Your apps**
2. Click the **</>** (web) icon → give it a nickname → **Register app**
3. Copy the `firebaseConfig` object shown

### 6. Paste your config into the app

Open `src/firebase.js` and replace the placeholder values with your actual config:

```js
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abcdef",
};
```

### 7. Deploy Firestore security rules

```bash
firebase login
firebase use --add   # select your project
firebase deploy --only firestore:rules
```

### 8. Install dependencies and deploy

```bash
npm install
npm run deploy
```

That's it. Firebase will print a live URL (e.g. `your-project.web.app`) that works on any device.

---

## Local development

```bash
npm start
```

Opens at http://localhost:3000 with hot reload.

---

## File structure

```
src/
  firebase.js        ← your Firebase config (edit this)
  defaultTasks.js    ← initial task list + categories/colors
  AuthContext.js     ← Google sign-in context
  useData.js         ← all Firestore reads/writes
  App.js             ← main shell + nav
  components/
    Login.js         ← sign-in screen
    Dashboard.js     ← overview with gauge + charts
    TaskList.js      ← full task list with edit/add/delete
    Budget.js        ← weekly budget slider + analysis
```

## Customizing

- **Add/change categories**: edit `CATEGORIES` and `CATEGORY_COLORS` in `src/defaultTasks.js`
- **Change default tasks**: edit `DEFAULT_TASKS` in `src/defaultTasks.js` (only affects new users on first login)
- **Existing data**: edit tasks directly in the app — all changes sync to Firestore in real time
