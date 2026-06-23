/* ============================================
   DOCUGRAPH – Firebase Configuration
   --------------------------------------------
   Replace the placeholder values below with the
   credentials from your Firebase project:
     https://console.firebase.google.com/
   → Project Settings → General → Your apps → SDK setup
   ============================================ */

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.13.0/firebase-app.js";
import {
  getAuth,
  GoogleAuthProvider,
  OAuthProvider
} from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";

// ⚠️ REPLACE THESE WITH YOUR OWN FIREBASE PROJECT CREDENTIALS
const firebaseConfig = {
  apiKey:            "AIzaSyBdLDS4oynp2uSGhMtEOVSKqpuJbJyMlwg",
  authDomain:        "docugraph-dev.firebaseapp.com",
  projectId:         "docugraph-dev",
  storageBucket:     "docugraph-dev.firebasestorage.app",
  messagingSenderId: "645736633960",
  appId:             "1:645736633960:web:c0b45783187a61d6808ddd"
};

const app  = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Providers
const googleProvider    = new GoogleAuthProvider();
const microsoftProvider = new OAuthProvider("microsoft.com");

// Tell Microsoft provider to allow any work, school, or personal account
microsoftProvider.setCustomParameters({
  prompt: "select_account",
  tenant: "common"
});

export { app, auth, googleProvider, microsoftProvider };
