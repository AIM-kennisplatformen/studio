export const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL ?? "";

import createClient from "openapi-fetch";

/** @typedef {import("./api.generated").paths} paths */
/** @type {import("openapi-fetch").Client<paths>} */
const client = createClient({ baseUrl: BACKEND_BASE_URL, credentials: "include" });

export async function logResponseFeedback(key, feedback) {
  const url = `${BACKEND_BASE_URL}/log_event`;

  const messages = [
    "Thanks!",
    "Thank you for the feedback!",
    "Appreciated!",
    "Noted, thanks!",
    "Good to know, thanks!",
    "Helpful, thank you!",
    "Got it, thanks!",
    "Thank you — that's useful!",
    "Thanks for the direction!",
    "Much appreciated!",
    "That helps, thank you!",
    "Thanks for letting me know!",
    "Thanks for the input!",
    "Noted — thank you!",
    "Thanks — that's clear!",
    "Thank you for the guidance!",
  ];

  const getFeedbackMessage = () =>
    messages[Math.floor(Math.random() * messages.length)];

  try {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include", // Required for cookie-based Auth
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "response_feedback",
        metadata: {
          messagekey: key,
          feedback: feedback,
        },
      }),
    });

    if (!response.ok) {
      console.error("Failed to log response feedback:", response.status);
      return null;
    }
    return getFeedbackMessage();
  } catch (err) {
    console.error("Failed to log response feedback:", err);
    return null;
  }
}

export async function logEvent(name, metadata) {
  const url = `${BACKEND_BASE_URL}/log_event`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, metadata }),
    });
    if (!response.ok) {
      console.error("Failed to log event:", await response.text());
    }
  } catch (err) {
    console.error("Error logging event:", err);
  }
}

export function logOut() {
  window.location.href = `${BACKEND_BASE_URL}/auth/logout`;
}

export async function getChatSessions() {
  try {
    const { data, error } = await client.GET("/sessions/");
    if (error) {
      console.error("Failed to fetch chat sessions:", error);
      return [];
    }
    return data;
  } catch (err) {
    console.error("Error fetching chat sessions:", err);
    return [];
  }
}

export async function getChatSessionDetails(sessionId) {
  const url = `${BACKEND_BASE_URL}/sessions/${sessionId}`;
  try {
    const response = await fetch(url, {
      method: "GET",
      credentials: "include", // Required for cookie-based Auth
    });
    if (!response.ok) {
      console.error("Failed to fetch chat session details:", response.status);
      return null;
    }
    const json = await response.json();
    return json;
  } catch (err) {
    console.error("Error fetching chat session details:", err);
    return null;
  }
}

export async function setActiveChatSession(sessionId) {
  const url = `${BACKEND_BASE_URL}/sessions/${sessionId}`;
  try {
    await fetch(url, {
      method: "POST",
      credentials: "include", // Required for cookie-based Auth
    });
    return;
  } catch (err) {
    console.error("Error setting active chat session:", err);
    return;
  }
}

export async function deleteSession(sessionId) {
  const url = `${BACKEND_BASE_URL}/sessions/${sessionId}`;
  try {
    const response = await fetch(url, {
      method: "DELETE",
      credentials: "include",
    });
    return response.ok;
  } catch (err) {
    console.error("Error deleting session:", err);
    return false;
  }
}

export async function updateSession(sessionId, data) {
  const url = `${BACKEND_BASE_URL}/sessions/${sessionId}`;
  try {
    const response = await fetch(url, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      console.error("Failed to update session:", response.status);
      return null;
    }
    return await response.json();
  } catch (err) {
    console.error("Error updating session:", err);
    return null;
  }
}

export async function newSession() {
  const url = `${BACKEND_BASE_URL}/sessions`; //POST
  try {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include", // Required for cookie-based Auth
    });
    if (!response.ok) {
      console.error("Failed to create new chat session:", response.status);
      return null;
    }
    return await response.json();
  } catch (err) {
    console.error("Error creating new chat session:", err);
    return null;
  }
}
