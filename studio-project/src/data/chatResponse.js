const standardChatbotResponse = {
    value: `Here's some code:
  
\`\`\`javascript
const greeting = "Hello, world!";
console.log(greeting);
\`\`\`
`,
    name: "chatbot",
};


export async function fetchAnswer(chatId = "1", message) {
  const url = `http://localhost:8000/chats/${chatId}/messages`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    return standardChatbotResponse;;
  }

  const data = await response.json();
  const chatResponse = {
    value: data.message,
    name: "chatbot",
  }

  return chatResponse;
}