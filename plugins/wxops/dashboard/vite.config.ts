// GEB-L3
// Input: caller, project conventions, and local dependencies
// Output: behavior defined by dashboard/vite.config.ts
// Pos: dashboard/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
});
