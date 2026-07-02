import { useState } from "react";
import Chat from "./chat/Chat";
import UserMenu from "./UserMenu";
import ChatSessionOverview from "./ChatSessionOverview";
import ChatSelectionToggle from "./ChatSelectionToggle";



export default function ChatWindow() {
  const [currentChat, setCurrentChat] = useState(null);
  const [chatActive, setChatActive] = useState(true);
  const [pendingMessage, setPendingMessage] = useState(null);

  return (
    <div className="relative z-10 flex h-full flex-col bg-white">
      {/* Header */}
      <div className="z-20 flex shrink-0 justify-between border-b border-gray-200 bg-white px-4 py-2">
        <ChatSelectionToggle
          setChatActive={setChatActive}
          chatActive={chatActive}
        />
        {chatActive && <ChatName currentChat={currentChat} />}
        <UserMenu />
      </div>

      {/* Body */}
      <div className="min-h-0 flex-1">
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
      className="font-inherit inline-block rounded-[8px] border border-transparent px-[1.2em] py-[0.6em] text-[1em] font-medium text-[#038061] transition-colors duration-250 hover:cursor-default hover:text-[#016048]"
      aria-label="Chat Name">
      {!currentChat ? "New Chat" : currentChat.name}
    </h2>
  );
}
