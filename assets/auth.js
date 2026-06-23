/* ============================================
   DOCUGRAPH – Authentication Helpers
   ============================================ */

import { auth, googleProvider, microsoftProvider } from "./firebase-config.js";
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  sendPasswordResetEmail,
  sendEmailVerification,
  signOut,
  updateProfile,
  onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.13.0/firebase-auth.js";

/* ---------- Public API ---------- */
export { auth, onAuthStateChanged, signOut };

/* ---------- Sign Up (Email/Password) ---------- */
export async function signUpWithEmail(name, email, password) {
  const cred = await createUserWithEmailAndPassword(auth, email, password);
  if (name) {
    await updateProfile(cred.user, { displayName: name });
  }
  // Send verification email immediately after account creation
  await sendEmailVerification(cred.user);
  return cred.user;
}

/* ---------- Sign In (Email/Password) ---------- */
export async function signInWithEmail(email, password) {
  const cred = await signInWithEmailAndPassword(auth, email, password);
  return cred.user;
}

/* ---------- Sign In with Google ---------- */
export async function signInWithGoogle() {
  const cred = await signInWithPopup(auth, googleProvider);
  return cred.user;
}

/* ---------- Sign In with Microsoft ---------- */
export async function signInWithMicrosoft() {
  const cred = await signInWithPopup(auth, microsoftProvider);
  return cred.user;
}

/* ---------- Password Reset ---------- */
export async function sendResetEmail(email) {
  await sendPasswordResetEmail(auth, email);
}

/* ---------- Resend Verification Email ---------- */
export async function resendVerificationEmail() {
  if (!auth.currentUser) throw new Error("No user is signed in.");
  await sendEmailVerification(auth.currentUser);
}

/* ---------- Logout ---------- */
export async function logout() {
  await signOut(auth);
}

/* ---------- Translate Firebase auth error codes into friendly messages ---------- */
export function authErrorMessage(err) {
  const code = err && err.code ? err.code : "";
  const map = {
    "auth/email-already-in-use":         "An account with this email already exists.",
    "auth/invalid-email":                "That email address looks invalid.",
    "auth/operation-not-allowed":        "This sign-in method isn't enabled. Contact the admin.",
    "auth/weak-password":                "Password should be at least 6 characters.",
    "auth/user-disabled":                "This account has been disabled.",
    "auth/user-not-found":               "No account found with that email.",
    "auth/wrong-password":               "Incorrect password. Try again.",
    "auth/invalid-credential":           "Email or password is incorrect.",
    "auth/too-many-requests":            "Too many attempts. Try again in a few minutes.",
    "auth/popup-closed-by-user":         "Sign-in window was closed before completing.",
    "auth/popup-blocked":                "Browser blocked the sign-in popup. Allow popups and try again.",
    "auth/cancelled-popup-request":      "Sign-in cancelled.",
    "auth/account-exists-with-different-credential":
      "An account already exists with this email using a different sign-in method.",
    "auth/network-request-failed":       "Network error. Check your connection and try again.",
    "auth/missing-password":              "Please enter a password.",
    "auth/internal-error":                "Something went wrong. Please try again."
  };
  return map[code] || (err.message || "Authentication failed.");
}

/* ---------- Route guard helper ----------
   Call from any protected page to redirect unauthenticated users.
*/
export function requireAuth(redirectTo = "login.html") {
  return new Promise((resolve) => {
    onAuthStateChanged(auth, (user) => {
      if (!user) {
        window.location.href = redirectTo;
      } else {
        resolve(user);
      }
    });
  });
}
