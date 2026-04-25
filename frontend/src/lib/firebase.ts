import { initializeApp, getApps, getApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyB2NiGZzswRM3G-fN1vtpvV_xtqVqmdBcs",
  authDomain: "veritassssss.firebaseapp.com",
  projectId: "veritassssss",
  storageBucket: "veritassssss.firebasestorage.app",
  messagingSenderId: "862742151502",
  appId: "1:862742151502:web:113bce89f4113e5ee2de1f",
  measurementId: "G-1CXXKL3ZT5"
};

// Initialize Firebase
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Analytics is only available in the browser
let analytics = null;
if (typeof window !== "undefined") {
  analytics = getAnalytics(app);
}

export { app, auth, googleProvider, analytics };
