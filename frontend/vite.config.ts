import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [react()],
    define: {
      __APP_VERSION__: JSON.stringify(env.APP_VERSION || "0.1.0")
    },
    server: {
      port: 5173
    }
  };
});
