import { defineConfig } from "vite";

const backendProxy = {
  target: "http://127.0.0.1:8000",
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api/, ""),
};

export default defineConfig({
  server: {
    port: 5173,
    proxy: { "/api": backendProxy },
  },
  preview: {
    port: 4173,
    proxy: { "/api": backendProxy },
  },
});
