import { useEffect, useState } from "react";
import { getChatSessions, deleteSession } from "../../data/api";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";
import { Trash2, X } from "lucide-react";

export default function ChatSessionOverview({
  setChatActive,
  setCurrentChat,
  currentChat,
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
      <div className="flex h-full flex-col">
        <div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex h-full flex-col items-center justify-center text-gray-500">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
                className="size-6 animate-spin">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
                />
              </svg>
            </div>
          ) : chats.length === 0 ? (
            <p className="font-semibold text-gray-500">
              No previous chats available.
            </p>
          ) : (
            <>
              <h3 className="mb-2 text-sm font-semibold text-black/70">
                CONTINUE A PREVIOUS CHAT
              </h3>

              <ul className="space-y-2">
                {chats.map((chat) => (
                  <ChatSessionItem
                    key={chat.session_id}
                    chat={chat}
                    currentChat={currentChat}
                    fetchChatSessions={fetchChatSessions}
                    setCurrentChat={setCurrentChat}
                    setChatActive={setChatActive}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
        <div className="shrink-0 border-t border-gray-200 bg-white p-4">
          <h3 className="mb-2 text-sm font-semibold text-black/50">
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

function SelectSessionCard({
  chat,
  currentChat,
  setCurrentChat,
  setChatActive,
  setIsDeleting,
}) {
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => {
        setCurrentChat(chat);
        setChatActive(true);
      }}
      className={
        "group flex w-full cursor-pointer items-center justify-between rounded p-2 text-left transition duration-150 " +
        (currentChat?.session_id === chat.session_id
          ? "!border-primary !bg-primary/70 hover:!bg-primary/80 !border"
          : "!border !border-gray-300 !bg-gray-100 hover:!bg-gray-200")
      }>
      <div className="flex min-w-0 flex-col pr-2">
        <span
          className={
            "truncate font-semibold " +
            (currentChat?.session_id === chat.session_id
              ? "text-white"
              : "text-black")
          }>
          {chat.name}
        </span>

        {currentChat?.session_id === chat.session_id && (
          <span className="text-xs font-medium text-white/80 italic">
            Currently Active
          </span>
        )}
      </div>
      <div className="flex shrink-0 items-center">
        <span
          className={
            "text-sm font-semibold transition-all duration-300 " +
            (currentChat?.session_id === chat.session_id
              ? "text-white/80"
              : "text-gray-500")
          }>
          {chat.updated_at.split("T")[0].split("-").reverse().join("-")}
        </span>

        <div className="grid translate-x-3 grid-cols-[0fr] opacity-0 transition-all duration-300 ease-out group-hover:translate-x-0 group-hover:grid-cols-[1fr] group-hover:opacity-100">
          <div className="flex items-center overflow-hidden">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsDeleting(true);
              }}
              className="ml-2 shrink-0 rounded !bg-red-700 p-1.5 text-gray-400 transition-colors hover:!bg-red-800"
              title="Delete session">
              <Trash2 />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function DeleteSessionCard({
  chat,
  currentChat,
  fetchChatSessions,
  setCurrentChat,
  setIsDeleting,
}) {
  return (
    <div
      className={
        "group flex w-full cursor-pointer items-center justify-between rounded p-2 text-left transition duration-150 " +
        (currentChat?.session_id === chat.session_id
          ? "!border-2 !border-red-800 !bg-red-800/70 hover:!bg-red-800/80"
          : "!border-2 !border-red-700 !bg-gray-100 hover:!bg-gray-200")
      }>
      <div className="flex min-w-0 flex-col pr-2">
        <span
          className={
            "truncate font-semibold " +
            (currentChat?.session_id === chat.session_id
              ? "text-white"
              : "text-black")
          }>
          Are you sure you want to delete the following chat:
        </span>
        <span
          className={
            "truncate font-semibold italic " +
            (currentChat?.session_id === chat.session_id
              ? "text-white"
              : "text-black")
          }>
          "{chat.name}"
        </span>

        <span
          className={
            "text-xs font-medium italic " +
            (currentChat?.session_id === chat.session_id
              ? "text-white/80"
              : "text-red-700")
          }>
          This action cannot be undone.
        </span>
      </div>
      <div className="flex shrink-0 items-center">
        <div className="grid translate-x-3 grid-cols-[0fr] opacity-0 transition-all duration-300 ease-out group-hover:translate-x-0 group-hover:grid-cols-[1fr] group-hover:opacity-100">
          <div className="flex items-center overflow-hidden">
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteSession(chat.session_id).then((ok) => {
                  if (!ok) return;
                  if (currentChat?.session_id === chat.session_id) {
                    setCurrentChat(null);
                  }
                  fetchChatSessions();
                });
              }}
              className={
                "ml-2 shrink-0 rounded p-1.5 text-gray-400 transition-colors " +
                (currentChat?.session_id === chat.session_id
                  ? "!bg-white hover:!bg-gray-200"
                  : "!bg-red-700 hover:!bg-red-800")
              }
              title="Delete session">
              <Trash2
                className={
                  currentChat?.session_id === chat.session_id
                    ? "text-red-700"
                    : "text-white"
                }
              />
            </button>
            <button
              onClick={() => {
                setIsDeleting(false);
              }}
              className={
                "ml-2 shrink-0 rounded p-1.5 text-gray-400 transition-colors " +
                (currentChat?.session_id === chat.session_id
                  ? "!bg-white hover:!bg-gray-200"
                  : "!bg-primary/80 hover:!bg-primary")
              }
              title="Cancel deletion">
              <X
                className={
                  currentChat?.session_id === chat.session_id
                    ? "text-primary"
                    : "text-white"
                }
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatSessionItem({
  chat,
  currentChat,
  fetchChatSessions,
  setCurrentChat,
  setChatActive,
}) {
  const [isDeleting, setIsDeleting] = useState(false);
  return (
    <li key={chat.session_id}>
      {!isDeleting ? (
        <SelectSessionCard
          chat={chat}
          currentChat={currentChat}
          setCurrentChat={setCurrentChat}
          setChatActive={setChatActive}
          setIsDeleting={setIsDeleting}
        />
      ) : (
        <DeleteSessionCard
          chat={chat}
          currentChat={currentChat}
          fetchChatSessions={fetchChatSessions}
          setCurrentChat={setCurrentChat}
          setIsDeleting={setIsDeleting}
        />
      )}
    </li>
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
    <div className="w-full">
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
            className="!bg-primary hover:!bg-primary-dark !text-white"
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}
