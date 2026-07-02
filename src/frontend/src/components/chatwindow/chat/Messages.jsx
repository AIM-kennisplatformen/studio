import { useRef, useEffect } from "react";

import {
  Conversation,
  ConversationContent,
} from "@/components/shadcn-io/ai/conversation";
import { useAtomValue } from "jotai";
import {
  Reasoning,
  ReasoningTrigger,
} from "@/components/shadcn-io/ai/reasoning";

import { logEvent, logResponseFeedback } from "../../../data/api";
import {
  lastDoneMessageKeyAtom,
  messagesAtom,
  selectedNodeAtom,
  textStatusAtom,
} from "@/lib/atoms";
import SystemMessage from "./message/SystemMessage";
import UserMessage from "./message/UserMessage";
import AiMessage from "./message/AiMessage";

async function handleFeedback(
  messageKey,
  feedback,
  setShowFeedback,
  setFeedbackText
) {
  setShowFeedback(false);
  const response = await logResponseFeedback(messageKey, feedback);
  if (response === null) {
    setFeedbackText(
      "An error occurred while sending your feedback. Please try again."
    );
    return;
  }
  setFeedbackText(response);
}

export default function Messages({
  feedbackText,
  showFeedback,
  setFeedbackText,
  setShowFeedback,
  shouldLog,
  showSystemMessages,
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, lastDoneKey, messages]);

  const reversedMessages = [...messages].reverse();
  const lastDoneIndex = reversedMessages.findIndex(
    ({ key }) => key === lastDoneKey
  );
  const lastDoneMessage = reversedMessages.find(
    ({ key }) => key === lastDoneKey
  );
  const questionForFeedback =
    lastDoneIndex !== -1 && lastDoneIndex + 1 < reversedMessages.length
      ? reversedMessages[lastDoneIndex + 1]?.value
      : null;

  return (
    <Conversation className="h-full">
      <ConversationContent className="flex min-h-full flex-col gap-4 p-4">
        <div className="flex-1" />
        {reversedMessages
          .filter(({ name }) =>
            showSystemMessages ? true : name !== "system_prompt"
          )
          .map(({ key, value, name }) => {
            switch (name) {
              case "system_prompt":
                return <SystemMessage key={key} value={value} />;
              case "ai":
                return (
                  <AiMessage
                    key={key}
                    index={key}
                    value={value}
                    lastDoneKey={lastDoneKey}
                    status={status}
                    lastDoneMessage={lastDoneMessage}
                    questionForFeedback={questionForFeedback}
                    setShowFeedback={setShowFeedback}
                    setFeedbackText={setFeedbackText}
                    feedbackText={feedbackText}
                    showFeedback={showFeedback}
                  />
                );
            }

            return <UserMessage key={key} value={value} />;
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
                }}>
                🧠 Thinking...
              </ReasoningTrigger>
            </Reasoning>
          </div>
        )}
      </ConversationContent>
    </Conversation>
  );
}
