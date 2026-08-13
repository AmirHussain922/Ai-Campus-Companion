import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";
import "./styles/index.css";

// Global error handler - catches EVERY error
window.addEventListener('error', (event) => {
  console.error('❌ GLOBAL ERROR:', event.error);
  console.trace();
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('❌ UNHANDLED PROMISE REJECTION:', event.reason);
  console.trace();
});

createRoot(document.getElementById("root")!).render(<App />);
