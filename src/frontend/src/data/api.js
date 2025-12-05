const BASE_URL = "http://localhost:10090";

const errorResponse = {
  value: "Sorry, I couldn't reach the server. Please try again later.",
  name: "chatbot",
};

export async function sendChatMessage(chatId = "1", message) {
  const url = `${BASE_URL}/chats/${chatId}/messages`;

  try {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include",   // Required for cookie-based Auth
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

	if (!response.ok) {
	  console.error("Failed to fetch chatbot response:", response.status);
      return errorResponse;
    }

    const data = await response.json();
    const chatResponse = {
      value: data?.message || "",
      name: "chatbot",
    };

    if (!chatResponse.value) {
      return errorResponse;
    }

    return chatResponse;
  } catch (err) {
    console.error("Failed to fetch chatbot response:", err);
    return errorResponse;
  }
}

export async function sendNodeSelection(nodeId) {
  const url = `${BASE_URL}/nodes/${nodeId}/context`;

  try {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include",   // Required for cookie-based Auth
    });

    if (!response.ok) {
      console.error("Failed to send node selection:", response.status);
      return null;
    }

    return await response.json();
  } catch (err) {
    console.error("Failed to send node selection:", err);
    return null;
  }
}