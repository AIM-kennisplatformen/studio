import { useEffect } from "react";
import { getChatSessions } from "../../data/api";

const exampleChats = [
  {
    name: "Chat Session 1",
    updated_at: "2024-01-01",
  },
  {
    name: "Chat Session 2",
    updated_at: "2024-01-02",
  },
];

async function fetchChatSessions() {
  try {
    const sessions = await getChatSessions();
    console.log("Fetched chat sessions:", sessions);
    return sessions;
  } catch (err) {
    console.error("Error fetching chat sessions:", err);
    return [];
  }
}

// useEffect(() => {
//   //fetchChatSessions();
// }, []);

export default function ChatSessionOverview({ setChatActive, setCurrentChat }) {
  return (
    <div className="p-4">
      <h2 className="text-sm font-semibold mb-2 text-black/70">
        CONTINUE A PREVIOUS CHAT
      </h2>
      <ul className="space-y-2">
        {exampleChats.map((chat, index) => (
          <li key={index}>
            <button
              onClick={() => {
                setCurrentChat(chat);
                setChatActive(true);
              }}
              className="flex w-full items-center justify-between p-2 !bg-gray-100 !border !border-gray-300 hover:!bg-gray-200 transition duration-150 cursor-pointer rounded text-left"
            >
              <span className="font-semibold text-black">{chat.name}</span>
              <span className="text-sm font-semibold text-gray-500">
                {chat.updated_at}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
