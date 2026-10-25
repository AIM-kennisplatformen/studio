import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig, globalIgnores } from "eslint/config";
import prettier from "eslint-config-prettier";

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{js,jsx}"],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat["recommended-latest"],
      reactRefresh.configs.vite,
      prettier,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: "latest",
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    rules: {
      "no-unused-vars": [
        "error",
        { varsIgnorePattern: "^[A-Z_]", argsIgnorePattern: "^_" },
      ],
    },
  },
  {
    // Existing components use these effect patterns; keep the new rule active elsewhere.
    files: [
      "src/components/chatwindow/ChatSessionOverview.jsx",
      "src/components/shadcn-io/ai/inline-citation.jsx",
      "src/components/shadcn-io/ai/reasoning.jsx",
      "src/components/shadcn-io/code-block/index.jsx",
      "src/components/slideover/Drawer.jsx",
      "src/components/ui/carousel.jsx",
    ],
    rules: { "react-hooks/set-state-in-effect": "off" },
  },
  {
    files: [
      "src/components/chatwindow/chat/ChatInput.jsx",
      "src/components/chatwindow/chat/Messages.jsx",
    ],
    rules: { "react-hooks/immutability": "off" },
  },
  {
    files: ["src/components/ui/sidebar.jsx"],
    rules: { "react-hooks/purity": "off" },
  },
]);
