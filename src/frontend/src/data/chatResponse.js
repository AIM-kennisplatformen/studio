const standardChatbotResponse = {
  value: "Sorry, I couldn't reach the server. Please try again later.",
  name: "chatbot",
};

export async function fetchAnswer(chatId = "1", message) {
  const url = `http://kg.localhost:8090/chats/${chatId}/messages`;

  try {
    const response = await fetch(url, {
      method: "POST",
      credentials: "include",   // <-- REQUIRED for cookie-based Auth!
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    

    if (!response.ok) {
      // Backend returned an error status
      return standardChatbotResponse;
    }

    const data = await response.json();

    const chatResponse = {
      value: data?.message || "",
      name: "chatbot",
    };

    // If backend returned empty message, fallback
    if (!chatResponse.value) {
      return standardChatbotResponse;
    }

    return chatResponse;

  } catch (err) {
    // Network error, server not running, etc.
    console.error("Failed to fetch chatbot response:", err);
    return standardChatbotResponse;
  }
}
