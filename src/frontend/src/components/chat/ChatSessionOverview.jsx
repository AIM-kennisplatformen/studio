import { useEffect, useState } from "react";
import { getChatSessions } from "../../data/api";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";

export default function ChatSessionOverview({
  setChatActive,
  setCurrentChat,
  setPendingMessage,
}) {
  const [chats, setChats] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  async function fetchChatSessions() {
    setIsLoading(true);
    try {
      const sessions = await getChatSessions();
      setChats(sessions);
    } catch {
      setChats([]);
    }
    setIsLoading(false);
  }

  useEffect(() => {
    fetchChatSessions();
  }, []);

  return (
    <>
      <div className="flex flex-col h-full p-4">
        <div className="flex-1 min-h-0 overflow-hidden">
          {isLoading ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
              className="size-6"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
          ) : chats.length === 0 ? (
            <p className="text-gray-500 font-semibold">
              No previous chats available.
            </p>
          ) : (
            <>
              <h3 className="text-sm font-semibold mb-2 text-black/70">
                CONTINUE A PREVIOUS CHAT
              </h3>

              <ul className="space-y-2">
                {chats.map((chat, index) => (
                  <li key={index}>
                    <button
                      onClick={() => {
                        setCurrentChat(chat);
                        setChatActive(true);
                      }}
                      className="flex w-full items-center justify-between p-2 !bg-gray-100 !border !border-gray-300 hover:!bg-gray-200 transition duration-150 cursor-pointer rounded text-left"
                    >
                      <span className="font-semibold text-black">
                        {chat.name}
                      </span>
                      <span className="text-sm font-semibold text-gray-500">
                        {chat.updated_at}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
        <div className="border-t border-gray-200 bg-white shrink-0 pt-4">
          <h3 className="text-sm font-semibold mb-2 text-black/50">
            Or start a new conversation
          </h3>
          <InputArea
            setChatActive={setChatActive}
            setCurrentChat={setCurrentChat}
            setPendingMessage={setPendingMessage}
          />
        </div>
      </div>
    </>
  );
}

function InputArea({ setChatActive, setCurrentChat, setPendingMessage }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const message = text.trim();
    if (!message) return;

    setPendingMessage(message);
    setCurrentChat(null);
    setChatActive(true);
    setText("");
  };

  return (
    <div className="p-4 w-full">
      <PromptInput onSubmit={handleSubmit} className="flex items-center">
        <PromptInputTextarea
          onChange={(e) => setText(e.target.value)}
          value={text}
          placeholder="Type your message..."
          className="flex-1"
        />
        <PromptInputToolbar className="ml-2">
          <PromptInputSubmit
            disabled={!text.trim()}
            status="ready"
            style={{ backgroundColor: "#038061", color: "white" }}
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}
