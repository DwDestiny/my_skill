// GEB-L3
// Input: caller, project conventions, and local dependencies
// Output: behavior defined by dashboard/src/main.tsx
// Pos: dashboard/src/main.tsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
