import { useRef, useEffect } from "react";
import { Response } from "@/components/shadcn-io/ai/response";
import { Message, MessageContent } from "@/components/shadcn-io/ai/message";

import {
  Conversation,
  ConversationContent,
} from "@/components/shadcn-io/ai/conversation";
import { useAtomValue } from "jotai";
import {
  Reasoning,
  ReasoningTrigger,
} from "@/components/shadcn-io/ai/reasoning";
import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";
import { logEvent, logResponseFeedback } from "../../../data/api";
import {
  lastDoneMessageKeyAtom,
  messagesAtom,
  selectedNodeAtom,
  textStatusAtom,
} from "@/data/atoms";

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
            if (name === "system_prompt") {
              return (
                <div
                  key={key}
                  className="flex w-full items-start justify-start gap-2 pr-[5%]">
                  <div className="flex w-full flex-col items-start">
                    <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
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
                  className="flex w-full items-start justify-start gap-2 pr-[5%]">
                  <div className="flex w-full flex-col items-start">
                    <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
                      {value}
                    </Response>
                    {key === lastDoneKey &&
                      status === "ready" &&
                      lastDoneMessage?.name === "ai" && (
                        <div
                          onClick={(e) => e.stopPropagation()}
                          onSubmit={(e) => e.preventDefault()}
                          className="mt-1 ml-7">
                          {questionForFeedback && (
                            <p className="mb-1 text-xs text-gray-400 italic">
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
                                      setFeedbackText
                                    );
                                  }}>
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
                                      setFeedbackText
                                    );
                                  }}>
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
                                  className="cursor-pointer border-0 p-0 text-sm hover:underline"
                                  style={{
                                    color: "white",
                                    backgroundColor: "#038061",
                                  }}>
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
              <Message
                from="user"
                key={key}
                className="flex justify-end pl-[5%]">
                <MessageContent
                  className="max-w-prose wrap-break-word"
                  style={{ backgroundColor: "#038061", color: "#ffffff" }}>
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
