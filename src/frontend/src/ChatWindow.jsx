import { useState } from "react";
import Chat from "./components/chat/chat";
import UserMenu from "@/components/UserMenu.jsx";
import ChatSelectionToggle from "@/components/ChatSelectionToggle.jsx";
import ChatSessionOverview from "@/components/chat/ChatSessionOverview.jsx";

export default function ChatWindow() {
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(false);
  return (
    <div className="flex flex-col h-full bg-white relative z-10">
      {/* Header */}
      <div className="flex justify-between px-4 py-2 border-b border-gray-200 bg-white shrink-0 z-20">
        <ChatSelectionToggle
          setCurrentChat={setCurrentChat}
          setChatActive={setChatActive}
          chatActive={chatActive}
        />
        {chatActive && <ChatName />}
        <UserMenu />
      </div>

      <div className="flex-1 min-h-0">
        {chatActive ? (
          <Chat currentChat={currentChat} setChatActive={setChatActive} />
        ) : (
          <ChatSessionOverview
            setChatActive={setChatActive}
            setCurrentChat={setCurrentChat}
          />
        )}
      </div>
    </div>
  );
}

function ChatName() {
  return (
    <button
      className="!bg-white text-[#038061] px-3 py-1 rounded"
      onClick={() => {}}
      aria-label="New Chat"
    >
      Current Chat Name
    </button>
  );
}
