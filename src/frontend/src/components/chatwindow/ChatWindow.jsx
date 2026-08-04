import { useState, useCallback } from "react";
import Chat from "./chat/Chat";
import UserMenu from "./UserMenu";
import ChatSessionOverview from "./ChatSessionOverview";
import ChatSelectionToggle from "./ChatSelectionToggle";
import SettingsDrawer from "../slideover/settings";
import { PencilIcon } from "lucide-react";

export default function ChatWindow() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(true);
  const [pendingMessage, setPendingMessage] = useState(null);
  const [currentChatTitle, setCurrentChatTitle] = useState(null);

  const handleTitleUpdate = useCallback((sessionId, name) => {
    setCurrentChat((prev) =>
      prev?.session_id === sessionId ? { ...prev, name } : prev
    );
  }, []);

  return (
    <>
      <SettingsDrawer setIsOpen={setSettingsOpen} isOpen={settingsOpen} />
      <div className="relative z-10 flex h-full flex-col bg-white">
        <ChatHeader
          setChatActive={setChatActive}
          chatActive={chatActive}
          setSettingsOpen={setSettingsOpen}
          currentChatTitle={currentChatTitle}
        />

        <ChatBody
          currentChat={currentChat}
          setCurrentChat={setCurrentChat}
          pendingMessage={pendingMessage}
          setPendingMessage={setPendingMessage}
          setChatActive={setChatActive}
          chatActive={chatActive}
          onTitleUpdate={handleTitleUpdate}
          setCurrentChatTitle={setCurrentChatTitle}
        />
      </div>
    </>
  );
}

function ChatHeader({
  setChatActive,
  chatActive,
  setSettingsOpen,
  currentChatTitle,
  setCurrentChat,
}) {
  return (
    <div className="z-20 flex shrink-0 items-start justify-between border-b border-gray-200 bg-white px-4 py-2">
      <ChatSelectionToggle
        setChatActive={setChatActive}
        chatActive={chatActive}
      />
      {chatActive && (
        <div className="group inline-flex items-start gap-2">
          <h2
            className="font-inherit text-primary py-[0.5em] pl-[1.2em] text-[1em] leading-normal font-medium transition-colors duration-200 hover:cursor-default"
            aria-label="Chat Name">
            {!currentChatTitle ? "New Chat" : currentChatTitle}
          </h2>
          <PencilIcon className="text-primary mt-[0.5em] h-4 w-4 shrink-0 opacity-0 transition-opacity duration-200 group-hover:opacity-100 hover:cursor-pointer" />
        </div>
      )}
      <UserMenu setSettingsOpen={setSettingsOpen} />
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
  setCurrentChatTitle,
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
          setCurrentChatTitle={setCurrentChatTitle}
        />
      )}
    </div>
  );
}
