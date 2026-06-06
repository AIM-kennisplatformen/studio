import { useState } from "react";
import Chat from "./components/chat/chat";
import UserMenu from "@/components/UserMenu.jsx";
import ChatSelectionToggle from "@/components/chat/ChatSelectionToggle.jsx";
import ChatSessionOverview from "@/components/chat/ChatSessionOverview.jsx";

export default function ChatWindow() {
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(false);
  // Message typed in the overview input before a chat session exists.
  // It's handed to <Chat /> and sent to the backend once the session starts.
  const [pendingMessage, setPendingMessage] = useState(null);

  return (
    <div className="flex flex-col h-full bg-white relative z-10">
      {/* Header */}
      <div className="flex justify-between px-4 py-2 border-b border-gray-200 bg-white shrink-0 z-20">
        <ChatSelectionToggle
          setCurrentChat={setCurrentChat}
          setChatActive={setChatActive}
          chatActive={chatActive}
        />
        {chatActive && <ChatName currentChat={currentChat} />}
        <UserMenu />
      </div>

      {/* Body */}
      <div className="flex-1 min-h-0">
        {chatActive ? (
          <Chat
            currentChat={currentChat}
            setChatActive={setChatActive}
            pendingMessage={pendingMessage}
            setPendingMessage={setPendingMessage}
          />
        ) : (
          <ChatSessionOverview
            setChatActive={setChatActive}
            setCurrentChat={setCurrentChat}
            setPendingMessage={setPendingMessage}
          />
        )}
      </div>
    </div>
  );
}

function ChatName({ currentChat }) {
  return (
    <button
      className="!bg-white text-[#038061] px-3 py-1 rounded"
      onClick={() => {}}
      aria-label="Chat Name"
    >
      {!currentChat ? "New Chat" : currentChat.name}
    </button>
  );
}
