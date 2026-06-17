import { useState } from "react";
import Chat from "./components/chat/chat";
import UserMenu from "@/components/UserMenu.jsx";
import ChatSelectionToggle from "@/components/chat/ChatSelectionToggle.jsx";
import ChatSessionOverview from "@/components/chat/ChatSessionOverview.jsx";

export default function ChatWindow() {
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(true);
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
            setCurrentChat={setCurrentChat}
            setChatActive={setChatActive}
            pendingMessage={pendingMessage}
            setPendingMessage={setPendingMessage}
          />
        ) : (
          <ChatSessionOverview
            setChatActive={setChatActive}
            setCurrentChat={setCurrentChat}
            setPendingMessage={setPendingMessage}
            currentChat={currentChat}
          />
        )}
      </div>
    </div>
  );
}

function ChatName({ currentChat }) {
  return (
    <h2
      className="inline-block text-[#038061] rounded-[8px] border border-transparent px-[1.2em] py-[0.6em] text-[1em] font-medium font-inherit transition-colors duration-250 hover:text-[#016048] hover:cursor-default"
      aria-label="Chat Name"
    >
      {!currentChat ? "New Chat" : currentChat.name}
    </h2>
  );
}
