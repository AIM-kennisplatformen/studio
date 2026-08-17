import { ChevronUp } from "lucide-react";

export default function ChatSelection({ setChatActive, chatActive }) {
  return (
    <>
      <div className="relative inline-block text-left">
        <button
          onClick={() => setChatActive(!chatActive)}
          className="flex items-center gap-1 rounded-md p-2 text-white"
          aria-expanded={chatActive}
          aria-label="Toggle chat history menu">
          Chats
          <span className="sr-only">Chat History</span>
          <ChevronUp
            className={`size-6 transition-transform duration-300 ${
              chatActive ? "rotate-180" : "rotate-0"
            }`}
          />
        </button>
      </div>
    </>
  );
}
