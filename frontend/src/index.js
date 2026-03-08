import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

// Comprehensive ResizeObserver error suppression
// This error is benign - it occurs when ResizeObserver cannot deliver 
// all notifications in a single animation frame (common with React Flow, etc.)
const suppressResizeObserverError = () => {
  // Method 1: Override window.onerror
  const originalOnError = window.onerror;
  window.onerror = (message, source, lineno, colno, error) => {
    if (message && typeof message === 'string' && message.includes('ResizeObserver')) {
      return true;
    }
    return originalOnError ? originalOnError(message, source, lineno, colno, error) : false;
  };

  // Method 2: Event listener with capture
  window.addEventListener('error', (event) => {
    if (event.message && event.message.includes('ResizeObserver')) {
      event.stopImmediatePropagation();
      event.preventDefault();
      return true;
    }
  }, true);

  // Method 3: Override console.error for ResizeObserver warnings
  const originalConsoleError = console.error;
  console.error = (...args) => {
    if (args[0] && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
      return;
    }
    originalConsoleError.apply(console, args);
  };
};

suppressResizeObserverError();

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register service worker for offline support
serviceWorkerRegistration.register({
  onSuccess: (registration) => {
    console.log('[Azories] App is available offline');
  },
  onUpdate: (registration) => {
    console.log('[Azories] New version available - refresh to update');
  }
});
