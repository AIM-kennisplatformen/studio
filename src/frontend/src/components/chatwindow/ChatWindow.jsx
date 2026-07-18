import { useState, useCallback } from "react";
import Chat from "./chat/Chat";
import UserMenu from "./UserMenu";
import ChatSessionOverview from "./ChatSessionOverview";
import ChatSelectionToggle from "./ChatSelectionToggle";

export default function ChatWindow() {
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(true);
  const [pendingMessage, setPendingMessage] = useState(null);

  const handleTitleUpdate = useCallback((sessionId, name) => {
    setCurrentChat((prev) =>
      prev?.session_id === sessionId ? { ...prev, name } : prev
    );
  }, []);

  return (
    <div className="relative z-10 flex h-full flex-col bg-white">
      <ChatHeader
        currentChat={currentChat}
        setChatActive={setChatActive}
        chatActive={chatActive}
      />

      <ChatBody
        currentChat={currentChat}
        setCurrentChat={setCurrentChat}
        pendingMessage={pendingMessage}
        setPendingMessage={setPendingMessage}
        setChatActive={setChatActive}
        chatActive={chatActive}
        onTitleUpdate={handleTitleUpdate}
      />
    </div>
  );
}

function ChatHeader({ currentChat, setChatActive, chatActive }) {
  return (
    <div className="z-20 flex shrink-0 justify-between border-b border-gray-200 bg-white px-4 py-2">
      <ChatSelectionToggle
        setChatActive={setChatActive}
        chatActive={chatActive}
      />
      {chatActive && (
        <h2
          className="font-inherit text-primary inline-block px-[1.2em] py-[0.6em] text-[1em] font-medium transition-colors duration-200 hover:cursor-default"
          aria-label="Chat Name">
          {!currentChat ? "New Chat" : currentChat.name}
        </h2>
      )}
      <UserMenu />
    </div>
  );
}

function ChatBody({
  currentChat,
  setCurrentChat,
  pendingMessage,
  setPendingMessage,
  setChatActive,
  chatActive,
  onTitleUpdate,
}) {
  return (
    <div className="min-h-0 flex-1">
      {chatActive ? (
        <Chat
          currentChat={currentChat}
          setCurrentChat={setCurrentChat}
          setChatActive={setChatActive}
          pendingMessage={pendingMessage}
          setPendingMessage={setPendingMessage}
          onTitleUpdate={onTitleUpdate}
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
  );
}
