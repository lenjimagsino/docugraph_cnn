# DOCUGRAPH - Advanced Document Analysis Platform

Graph-based document layout analysis with intelligent OCR, multilingual support, and real-time processing.

## ✨ Features

- **Advanced OCR** - EasyOCR + Tesseract.js with intelligent preprocessing
- **Document Layout Analysis** - LayoutParser + Graph Neural Networks
- **Multilingual Support** - 12+ languages with semantic embeddings
- **Real Table Grids** - Automatic table detection and reconstruction with proper grid formatting
- **Shapes & Flowchart Visualization** - Automatic diagram recognition and element visualization
- **Image Inclusion in DOCX** - Preserve images and diagrams in exported documents
- **Custom Formatting Templates** - Export with customizable document styles and layouts
- **Shape & Flowchart Detection** - Automatic diagram recognition
- **User Authentication** - Firebase with Google, Microsoft, Email sign-in
- **Real-time Processing** - Async document analysis pipeline
- **Production Ready** - 24/7 backend with auto-restart

## 🚀 Quick Start

### 1. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
# Windows
backend\start_backend_windows.bat

# Linux/Mac
python backend/run_production.py
```

### 3. Open Website
```
https://docugraph.site
```

## 📋 Project Structure

```
docugraph.site/
├── index.html              # Landing page
├── login.html              # Sign in
├── signup.html             # Register
├── dashboard.html          # User dashboard
├── try.html                # Upload & analyze
├── processing.html         # Processing status
├── results.html            # Analysis results
├── assets/                 # Frontend (JS, CSS)
├── backend/                # Python Flask server
└── DOCS/                   # Documentation
```

## 🔑 Authentication Setup (Firebase)

### Setup Instructions

1. **Create Firebase Project**: https://console.firebase.google.com
2. **Add Web App**: Copy firebaseConfig
3. **Update** `assets/firebase-config.js` with your credentials
4. **Enable Sign-In Methods**: Email, Google, Microsoft in Firebase Console

For detailed setup, see [DOCS/SETUP.md](DOCS/SETUP.md)

```js
const firebaseConfig = {
  apiKey:            "AIzaSy...your-key",
  authDomain:        "docugraph.firebaseapp.com",
  projectId:         "docugraph",
  storageBucket:     "docugraph.appspot.com",
  messagingSenderId: "1234567890",
  appId:             "1:1234567890:web:abc123"
};
```

### 4. Enable sign-in providers
In Firebase Console → **Authentication** → **Sign-in method**, enable:

**a) Email/Password** — Click → toggle **Enable** → Save

**b) Google** — Click → toggle **Enable** → choose support email → Save

**c) Microsoft** — Click → toggle **Enable**
- Register an Azure AD app at https://portal.azure.com/ → App registrations → New registration
  - Name: `DOCUGRAPH`
  - Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
  - Redirect URI (Web): `https://YOUR_PROJECT.firebaseapp.com/__/auth/handler`
- Copy the **Application (client) ID** → paste in Firebase
- Generate a **Client secret** (Certificates & secrets → New client secret) → paste in Firebase
- Save

### 5. Add your domain to authorized domains
Authentication → **Settings** → **Authorized domains** → Add:
- `localhost` (already there by default)
- Your production domain (e.g. `docugraph.vercel.app`)

That's it — auth works now.

## Running locally (VS Code)

1. Open the folder in VS Code
2. Install the **Live Server** extension (Ritwick Dey)
3. Right-click `index.html` → **Open with Live Server**

> ⚠️ **Don't open via `file://`** — Firebase popups need an `http://` or `https://` origin, so you must use Live Server (or `python3 -m http.server`).

```bash
# Or use Python
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Deploying

### Vercel (recommended)
1. Push this folder to GitHub
2. Import on https://vercel.com → Framework: **Other** → Build: empty → Output: `./`
3. Add your Vercel domain to Firebase **Authorized domains**

### Firebase Hosting
```bash
npm install -g firebase-tools
firebase login
firebase init hosting   # public dir: . (this folder), single-page: No
firebase deploy
```

## File structure

```
docugraph/
├── index.html              ← Landing (public)
├── login.html              ← Sign in
├── signup.html             ← Create account
├── reset-password.html     ← Forgot password
├── verify-email.html       ← Email verification
├── dashboard.html          ← Protected — main user area
├── try.html                ← Protected — upload
├── processing.html         ← Protected — analysis
├── results.html            ← Protected — output
├── README.md
└── assets/
    ├── logo.png
    ├── style.css
    ├── main.js             ← Site-wide UI (navbar, scroll, etc.)
    ├── firebase-config.js  ← ⚠️ ADD YOUR FIREBASE KEYS HERE
    └── auth.js             ← Auth helpers (sign-in, sign-up, reset, verify, logout)
```

## Auth API reference (`assets/auth.js`)

```js
import {
  signUpWithEmail, signInWithEmail,
  signInWithGoogle, signInWithMicrosoft,
  sendResetEmail, resendVerificationEmail,
  logout, requireAuth,
  onAuthStateChanged, auth, authErrorMessage
} from "./assets/auth.js";

// Examples
await signUpWithEmail("Jane Reyes", "jane@x.com", "Pass1234!");
await signInWithGoogle();
await sendResetEmail("jane@x.com");
await logout();
```

## Customization

All colors live in CSS variables at the top of `assets/style.css`:
- `--green-700` primary brand
- `--green-500` accent
- `--green-100` soft background
- `--ink-900` body text