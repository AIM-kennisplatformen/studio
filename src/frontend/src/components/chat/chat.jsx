"use client";

import { useState, useRef, useEffect } from "react";

import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
} from "@/components/shadcn-io/ai/prompt-input";

import { Response } from "@/components/shadcn-io/ai/response";
import { Message, MessageContent } from "@/components/shadcn-io/ai/message";

import {
  Conversation,
  ConversationContent,
} from "@/components/shadcn-io/ai/conversation";

import { useAtom, useAtomValue, useSetAtom } from "jotai";
import {
  initialMessages,
  messagesAtom,
  textAtom,
  textStatusAtom,
  lastDoneMessageKeyAtom,
  selectedNodeAtom,
} from "../../data/atoms";

import { useChatWebSocket } from "../../data/chatWebsocket";
import {
  Reasoning,
  ReasoningTrigger,
} from "@/components/shadcn-io/ai/reasoning";
import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";
import {
  logResponseFeedback,
  logEvent,
  getChatSessionDetails,
  newSession,
  setActiveChatSession,
} from "../../data/api";

async function handleFeedback(
  messageKey,
  feedback,
  setShowFeedback,
  setFeedbackText,
) {
  setShowFeedback(false);
  const response = await logResponseFeedback(messageKey, feedback);
  if (response === null) {
    setFeedbackText(
      "An error occurred while sending your feedback. Please try again.",
    );
    return;
  }
  setFeedbackText(response);
}

function mapRestoredMessages(sessionMessages) {
  const restoredMessages = sessionMessages.map((message, index) => ({
    key: index + 1,
    value: message.content,
    name: message.role,
  }));

  return restoredMessages.length > 0
    ? restoredMessages.reverse()
    : [...initialMessages];
}

export default function Chat({
  currentChat,
  pendingMessage,
  setPendingMessage,
}) {
  const [feedbackText, setFeedbackText] = useState("");
  const [showFeedback, setShowFeedback] = useState(true);
  const [sessionReady, setSessionReady] = useState(false);
  const shouldLog = useRef(false);
  const setMessages = useSetAtom(messagesAtom);
  const setText = useSetAtom(textAtom);
  const setStatus = useSetAtom(textStatusAtom);
  const setLastDoneMessageKey = useSetAtom(lastDoneMessageKeyAtom);

  useEffect(() => {
    let isCurrent = true;

    async function restoreChat() {
      setText("");
      setStatus("ready");
      setLastDoneMessageKey(null);
      setFeedbackText("");
      setShowFeedback(true);
      setSessionReady(false);
      shouldLog.current = false;

      if (currentChat === null) {
        setMessages([...initialMessages]);
        try {
          await newSession();
        } catch (err) {
          console.error("Error creating new chat session:", err);
        }
        if (isCurrent) setSessionReady(true);
        return;
      }

      const sessionId = currentChat?.session_id;
      if (!sessionId) return;

      setMessages([]);

      try {
        await setActiveChatSession(sessionId);
        const details = await getChatSessionDetails(sessionId);
        if (!isCurrent) return;

        setMessages(
          details?.messages ? mapRestoredMessages(details.messages) : [],
        );
        setSessionReady(true);
      } catch (err) {
        console.error("Error restoring chat session:", err);
      }
    }

    restoreChat();

    return () => {
      isCurrent = false;
    };
  }, [currentChat, setLastDoneMessageKey, setMessages, setStatus, setText]);

  return (
    <div className="flex flex-col h-full bg-white relative z-10">
      {/* Messages - scrollable */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <Messages
          feedbackText={feedbackText}
          showFeedback={showFeedback}
          setFeedbackText={setFeedbackText}
          setShowFeedback={setShowFeedback}
          shouldLog={shouldLog}
        />
      </div>

      {/* Input - sticky at bottom */}
      <div className="border-t border-gray-200 bg-white shrink-0">
        <InputArea
          setShowFeedback={setShowFeedback}
          shouldLog={shouldLog}
          initialText={pendingMessage}
          setPendingMessage={setPendingMessage}
          sessionReady={sessionReady}
        />
      </div>
    </div>
  );
}

function InputArea({
  setShowFeedback,
  shouldLog,
  initialText,
  setPendingMessage,
  sessionReady,
}) {
  const [text, setText] = useAtom(textAtom);
  const [status, setStatus] = useAtom(textStatusAtom);
  const setMessages = useSetAtom(messagesAtom);

  const { send } = useChatWebSocket(setStatus);

  const sendMessage = (message) => {
    shouldLog.current = true;

    setMessages((prev) => [
      { key: prev.length + 1, value: message, name: "user" },
      ...prev,
    ]);

    setStatus("thinking");
    send(message);
    setText("");
    setShowFeedback(true);
  };

  useEffect(() => {
    if (!initialText) return;
    if (!sessionReady || status !== "ready") return;

    sendMessage(initialText);
    setPendingMessage?.(null);
  }, [initialText, sessionReady, status]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text || status !== "ready") return;

    sendMessage(text);
  };

  return (
    <div className="p-4 w-full">
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
            style={{ backgroundColor: "#038061", color: "white" }}
          />
        </PromptInputToolbar>
      </PromptInput>
    </div>
  );
}

function Messages({
  feedbackText,
  showFeedback,
  setFeedbackText,
  setShowFeedback,
  shouldLog,
}) {
  const messages = useAtomValue(messagesAtom);
  const status = useAtomValue(textStatusAtom);
  const lastDoneKey = useAtomValue(lastDoneMessageKeyAtom);
  const selectedNode = useAtomValue(selectedNodeAtom);
  const prevStatusRef = useRef(null);

  // Log response_generated event
  useEffect(() => {
    const prevStatus = prevStatusRef.current;
    prevStatusRef.current = status;

    if (status !== "ready" || !["thinking", "streaming"].includes(prevStatus))
      return;
    if (!lastDoneKey) return;
    if (!shouldLog.current) return;
    shouldLog.current = false;

    const chronological = [...messages].reverse();
    const botIndex = chronological.findIndex(({ key }) => key === lastDoneKey);
    const question = botIndex > 0 ? chronological[botIndex - 1]?.value : null;

    logEvent("response_generated", {
      messageKey: lastDoneKey,
      question,
      selectedNodeId: selectedNode?.id ?? null,
      selectedNodeLabel: selectedNode?.data?.label ?? null,
      timestamp: new Date().toISOString(),
    });
  }, [status, lastDoneKey]);

  const reversedMessages = [...messages].reverse();
  const lastDoneIndex = reversedMessages.findIndex(
    ({ key }) => key === lastDoneKey,
  );
  const lastDoneMessage = reversedMessages.find(
    ({ key }) => key === lastDoneKey,
  );
  const questionForFeedback =
    lastDoneIndex !== -1 && lastDoneIndex + 1 < reversedMessages.length
      ? reversedMessages[lastDoneIndex + 1]?.value
      : null;

  return (
    <Conversation className="h-full">
      <ConversationContent className="flex flex-col gap-4 p-4 min-h-full">
        <div className="flex-1" />
        {reversedMessages.map(({ key, value, name }) => {
          if (name === "system_prompt") {
            return (
              <div
                key={key}
                className="flex items-start gap-2 justify-start w-full pr-[5%]"
              >
                <div className="flex flex-col items-start w-full">
                  <Response className="w-full text-sm border border-gray-200 rounded-lg p-2 bg-gray-50 break-words">
                    {value}
                  </Response>
                </div>
              </div>
            );
          }

          if (name === "ai") {
            return (
              <div
                key={key}
                className="flex items-start gap-2 justify-start w-full pr-[5%]"
              >
                <div className="flex flex-col items-start w-full">
                  <Response className="w-full text-sm border border-gray-200 rounded-lg p-2 bg-gray-50 break-words">
                    {value}
                  </Response>
                  {key === lastDoneKey &&
                    status === "ready" &&
                    lastDoneMessage?.name === "ai" && (
                      <div
                        onClick={(e) => e.stopPropagation()}
                        onSubmit={(e) => e.preventDefault()}
                        className="ml-7 mt-1"
                      >
                        {questionForFeedback && (
                          <p className="text-xs text-gray-400 mb-1 italic">
                            Feedback for: "
                            {questionForFeedback.length > 80
                              ? questionForFeedback.slice(0, 80) + "…"
                              : questionForFeedback}
                            "
                          </p>
                        )}
                        <Actions>
                          {showFeedback ? (
                            <>
                              <Action
                                label="Good response"
                                style={{
                                  backgroundColor: "#038061",
                                  color: "white",
                                }}
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  handleFeedback(
                                    key,
                                    "positive",
                                    setShowFeedback,
                                    setFeedbackText,
                                  );
                                }}
                              >
                                <ThumbsUpIcon className="size-4" />
                              </Action>
                              <Action
                                label="Bad response"
                                style={{
                                  backgroundColor: "#038061",
                                  color: "white",
                                }}
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  handleFeedback(
                                    key,
                                    "negative",
                                    setShowFeedback,
                                    setFeedbackText,
                                  );
                                }}
                              >
                                <ThumbsDownIcon className="size-4" />
                              </Action>
                            </>
                          ) : (
                            <>
                              <p className="text-sm text-gray-600">
                                {feedbackText}
                              </p>
                              <button
                                type="button"
                                onClick={() => setShowFeedback(true)}
                                className="text-sm cursor-pointer hover:underline border-0 p-0"
                                style={{
                                  color: "white",
                                  backgroundColor: "#038061",
                                }}
                              >
                                Edit Feedback
                              </button>
                            </>
                          )}
                        </Actions>
                      </div>
                    )}
                </div>
              </div>
            );
          }

          return (
            <Message from="user" key={key} className="flex justify-end pl-[5%]">
              <MessageContent
                className="max-w-prose break-words"
                style={{ backgroundColor: "#038061", color: "#ffffff" }}
              >
                {value}
              </MessageContent>
            </Message>
          );
        })}
        {status === "thinking" && (
          <div>
            <Reasoning isStreaming={status === "thinking"}>
              <ReasoningTrigger
                style={{
                  backgroundColor: "transparent",
                  color: "black",
                  border: "none",
                  padding: "0",
                  outline: "none",
                  cursor: "text",
                }}
              >
                🧠 Thinking...
              </ReasoningTrigger>
            </Reasoning>
          </div>
        )}
      </ConversationContent>
    </Conversation>
  );
}
