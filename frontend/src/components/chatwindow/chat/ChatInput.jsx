import { useEffect } from "react";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";
import { useAtom, useSetAtom } from "jotai";

import { useChatWebSocket } from "../../../data/chatWebsocket";
import {
  BACKEND_BASE_URL,
  newSession,
  setActiveChatSession,
} from "../../../data/api";
import {
  helpMode,
  messagesAtom,
  textAtom,
  textStatusAtom,
} from "../../../lib/atoms.js";
import { startTour } from "@/data/user-tours/tourHandler";

export default function ChatInput({
  // setShowFeedback,
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

  const isHelpModeActive = useAtom(helpMode);

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
    // setShowFeedback(true);
  };

  useEffect(() => {
    if (!initialText) return;

    sendMessage(initialText);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialText, sessionReady, status]);

  async function chooseTour(question) {
    const response = await fetch(`${BACKEND_BASE_URL}/tours/select`, {
      method: "POST",
      credentials: "include", // send the session cookie
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      console.error("Tour selection failed:", response.status);
      return null;
    }
    return response.json(); // { tour_id, probability, distribution, coverage }
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text || status !== "ready") return;

    if (isHelpModeActive) {
      setStatus("thinking");
      const selection = await chooseTour(text);
      setStatus("ready");

      if (startTour(selection, text)) {
        setText("");
      }
      return;
    } else {
      sendMessage(text);
    }
  };

  return (
    <div className="w-full p-4" data-tour="chat-input">
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
