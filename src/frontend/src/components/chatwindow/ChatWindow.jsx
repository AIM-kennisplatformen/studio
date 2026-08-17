import { useState, useCallback } from "react";
import Chat from "./chat/Chat";
import UserMenu from "./UserMenu";
import ChatSessionOverview from "./ChatSessionOverview";
import ChatSelectionToggle from "./ChatSelectionToggle";
import SettingsDrawer from "../slideover/settings";
import { PencilIcon, Check, X } from "lucide-react";
import { updateSession } from "@/data/api";

export default function ChatWindow() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(true);
  const [pendingMessage, setPendingMessage] = useState(null);

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
          currentChatTitle={currentChat?.name}
          currentChat={currentChat}
          setCurrentChat={setCurrentChat}
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
    </>
  );
}

function ChatHeader({
  setChatActive,
  chatActive,
  setSettingsOpen,
  currentChat,
  currentChatTitle,
  setCurrentChat,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(currentChatTitle || "New Chat");

  const handleSave = async () => {
    const updated = await updateSession(currentChat.session_id, {
      name: editValue,
    });
    if (updated) {
      setCurrentChat((prev) =>
        prev?.session_id === currentChat.session_id
          ? { ...prev, name: editValue }
          : prev
      );
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    // Zet de input weer terug naar de originele title
    setEditValue(currentChatTitle || "New Chat");
    setIsEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") handleCancel();
  };
  return (
    <div className="z-20 flex shrink-0 items-start justify-between border-b border-gray-200 bg-white px-4 py-2">
      <ChatSelectionToggle
        setChatActive={setChatActive}
        chatActive={chatActive}
      />
      {chatActive && (
        <div className="group inline-flex items-center gap-2">
          {isEditing ? (
            // De wrapper div fungeert nu visueel als het inputveld
            <div className="focus-within:border-primary focus-within:ring-primary flex items-center rounded border border-gray-300 bg-white pr-1 transition-all focus-within:ring-1">
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                autoFocus
                // De input zelf heeft geen achtergrond of borders meer
                className="font-inherit text-primary w-full min-w-[150px] bg-transparent py-[0.4em] pr-2 pl-[1.2em] text-[1em] leading-normal font-medium outline-none"
                aria-label="Edit Chat Name"
              />
              <div className="flex items-center gap-0.5">
                <button
                  type="button"
                  title="Save chat name"
                  onClick={handleSave}
                  // Transparante achtergrond, hover effect blijft
                  className="flex h-6 w-6 items-center justify-center rounded-md !bg-white transition-all duration-200 hover:!bg-gray-200"
                  aria-label="Save chat title">
                  <Check className="h-4 w-4 shrink-0 text-green-600" />
                </button>
                <button
                  type="button"
                  title="Cancel chat name"
                  onClick={handleCancel}
                  className="flex h-6 w-6 items-center justify-center rounded-md !bg-white transition-all duration-200 hover:!bg-gray-200"
                  aria-label="Cancel editing">
                  <X className="h-4 w-4 shrink-0 text-red-500" />
                </button>
              </div>
            </div>
          ) : (
            <>
              <h2
                className="font-inherit text-primary py-[0.5em] pl-[1.2em] text-[1em] leading-normal font-medium transition-colors duration-200 hover:cursor-default"
                aria-label="Chat Name">
                {!currentChatTitle ? "New Chat" : currentChatTitle}
              </h2>
              {currentChat && (
                <button
                  type="button"
                  title="Edit chat name"
                  onClick={() => {
                    if (currentChat) {
                      setEditValue(currentChatTitle || "New Chat");
                      setIsEditing(true);
                    }
                  }}
                  className="flex h-6 w-6 items-center justify-center rounded-md !bg-white opacity-0 transition-all duration-200 group-hover:opacity-100 hover:!bg-gray-200"
                  aria-label="Edit chat title">
                  <PencilIcon className="text-primary h-4 w-4 shrink-0" />
                </button>
              )}
            </>
          )}
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
