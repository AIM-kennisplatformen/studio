import path from "path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  // eslint-disable-next-line no-undef
  ...(process.env.VITE_CACHE_DIR
    ? // eslint-disable-next-line no-undef
      { cacheDir: process.env.VITE_CACHE_DIR }
    : {}),
  plugins: [react(), tailwindcss()],
  build: {
    outDir: "dist",
  },
  server: {
    host: "0.0.0.0",
    port: 5174,
    strictPort: true,
    hmr: {
      // eslint-disable-next-line no-undef
      clientPort: Number(process.env.VITE_HMR_CLIENT_PORT || 5174),
    },
    watch: {
      usePolling: true,
      interval: 100,
    },
    proxy: {
      "/api": {
        // eslint-disable-next-line no-undef
        target: process.env.VITE_API_PROXY_TARGET || "http://localhost:10092",
        changeOrigin: true,
        ws: true,
      },
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
