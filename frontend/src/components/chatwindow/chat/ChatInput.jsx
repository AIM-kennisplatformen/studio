import { useEffect } from "react";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";
import { useAtom, useSetAtom } from "jotai";

import { useChatWebSocket } from "../../../data/chatWebsocket";
import { newSession, setActiveChatSession } from "../../../data/api";
import { messagesAtom, textAtom, textStatusAtom } from "@/lib/atoms";

export default function ChatInput({
  setShowFeedback,
  shouldLog,
  initialText,
  setPendingMessage,
  sessionReady,
  isNewSessionRef,
  setCurrentChat,
  currentChat,
  onTitleUpdate,
}) {
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);

  const { send } = useChatWebSocket(setStatus, onTitleUpdate);

  const sendMessage = async (message) => {
    if (!sessionReady || status !== "ready") return;

    shouldLog.current = true;

    setMessages((prev) => [
      { key: prev.length + 1, value: message, name: "user" },
      ...prev,
    ]);

    setStatus("thinking");

    let activeSession = currentChat;
    if (activeSession === null) {
      try {
        isNewSessionRef.current = true;
        activeSession = await newSession();
        await setActiveChatSession(activeSession.session_id);
        setCurrentChat(activeSession);
      } catch (err) {
        console.error("Error creating new chat session:", err);
        setMessages((prev) => [
          {
            key: prev.length + 1,
            value: "Something went wrong. Please try again.",
            name: "ai",
          },
          ...prev,
        ]);
      }
    }

    send(message);
    setPendingMessage?.(null);
    setText("");
    setShowFeedback(true);
  };

  useEffect(() => {
    if (!initialText) return;

    sendMessage(initialText);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialText, sessionReady, status]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text || status !== "ready") return;

    sendMessage(text);
  };

  return (
    <div className="w-full p-4">
      <PromptInput onSubmit={handleSubmit} className="flex items-center">
        <PromptInputTextarea
          onChange={(e) => setText(e.target.value)}
          value={text}
          placeholder="Type your message..."
          className="flex-1"
        />
        <PromptInputToolbar className="ml-2">
          <PromptInputSubmit
            disabled={!text || status !== "ready"}
            status={status === "thinking" ? "submitted" : status}
            className="!bg-primary hover:!bg-primary-dark !text-white"
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}
