import { defineConfig } from "orval";

export default defineConfig({
  studio: {
    input: { target: "/tmp/opencode/studio-openapi.json" },
    output: {
      client: "zod",
      mode: "single",
      target: "./src/data/",
      override: {
        zod: {
          variant: "mini",
          version: 4,
        },
      },
    },
  },
});
