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
    <>
      <div className="flex flex-col h-full p-4">
        <div className="flex-1 min-h-0 overflow-hidden">
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
        <div className="border-t border-gray-200 bg-white shrink-0 pt-4">
          <button
            onClick={() => {
              setCurrentChat(null);
              setChatActive(true);
            }}
            className="flex w-full items-center justify-center p-3 !bg-[#038061] text-white rounded-md hover:!bg-[#02664a] transition duration-150"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="size-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
              />
            </svg>
            <p className="ml-2">New Chat</p>
          </button>
        </div>
      </div>
    </>
  );
}
