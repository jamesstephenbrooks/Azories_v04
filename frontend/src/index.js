import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Suppress ResizeObserver loop error (benign browser warning)
// This occurs when ResizeObserver cannot deliver all notifications in a single animation frame
const resizeObserverErr = window.onerror;
window.onerror = (message, ...args) => {
  if (message && message.includes('ResizeObserver loop')) {
    return true; // Suppress the error
  }
  return resizeObserverErr ? resizeObserverErr(message, ...args) : false;
};

// Also handle unhandled promise rejections for ResizeObserver
window.addEventListener('error', (event) => {
  if (event.message && event.message.includes('ResizeObserver loop')) {
    event.stopImmediatePropagation();
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
