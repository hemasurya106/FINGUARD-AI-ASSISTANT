// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "firebase/auth";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyD20rzjAukU3n2ucS7k40ieknDR9r6RpnY",
    authDomain: "pdis-bcf80.firebaseapp.com",
    projectId: "pdis-bcf80",
    storageBucket: "pdis-bcf80.firebasestorage.app",
    messagingSenderId: "762104146024",
    appId: "1:762104146024:web:bc885a1080b6e8593033dd",
    measurementId: "G-4QHY4NFTVZ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
export { auth, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut };
