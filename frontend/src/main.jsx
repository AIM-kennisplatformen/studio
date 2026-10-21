import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { BACKEND_BASE_URL } from "./data/api.js";

const rootElement = document.getElementById("root");

async function startApplication() {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/me`, {
      credentials: "include",
    });

    if (response.status === 401) {
      window.location.replace(`${BACKEND_BASE_URL}/auth/login`);
      return;
    }

    if (!response.ok) {
      throw new Error(`Authentication check failed with ${response.status}`);
    }

    createRoot(rootElement).render(
      <StrictMode>
        <App />
      </StrictMode>
    );
  } catch (error) {
    console.error("Unable to verify the current session", error);
    rootElement.textContent = "Unable to connect to the application.";
  }
}

startApplication();
