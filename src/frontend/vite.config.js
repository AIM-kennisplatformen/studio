import path from "path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  base: "/app/",
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "../../kg",
    emptyOutDir: true,
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    hmr: {
      clientPort: 5173,
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
  },
  resolve: {
    alias: {
      // eslint-disable-next-line no-undef
      "@": path.resolve(__dirname, "./src"),
      "@repo/shadcn-ui/lib/utils": path.resolve("src/lib/utils.js"),
      "@repo/shadcn-ui/components": path.resolve("src/components"),
    },
  },
});
