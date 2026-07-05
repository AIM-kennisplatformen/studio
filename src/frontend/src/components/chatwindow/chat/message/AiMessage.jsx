import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon, Copy, Check } from "lucide-react";
import { Response } from "@/components/shadcn-io/ai/response";
import { logResponseFeedback } from "../../../../data/api";
import { useRef, useState } from "react";

export default function AiMessage({
  index,
  value,
  lastDoneKey,
  status,
  lastDoneMessage,
  questionForFeedback,
  setShowFeedback,
  setFeedbackText,
  feedbackText,
  showFeedback,
}) {
  return (
    <div
      key={index}
      className="flex w-full items-start justify-start gap-2 pr-[5%]">
      <div className="flex w-full flex-col items-start">
        <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
          {value}
        </Response>
        {index === lastDoneKey &&
          status === "ready" &&
          lastDoneMessage?.name === "ai" && (
            <div
              onClick={(e) => e.stopPropagation()}
              onSubmit={(e) => e.preventDefault()}
              className="mt-1">
              {questionForFeedback && (
                <p className="mb-1 text-xs text-gray-400 italic">
                  Feedback for: "
                  {questionForFeedback.length > 80
                    ? questionForFeedback.slice(0, 80) + "…"
                    : questionForFeedback}
                  "
                </p>
              )}
              <MessageOptions
                value={value}
                index={index}
                setShowFeedback={setShowFeedback}
                setFeedbackText={setFeedbackText}
                feedbackText={feedbackText}
                showFeedback={showFeedback}
              />
            </div>
          )}
      </div>
    </div>
  );
}

function MessageOptions({
  value,
  index,
  setShowFeedback,
  setFeedbackText,
  feedbackText,
  showFeedback,
}) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef(null);

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

  return (
    <Actions>
      <Action
        label="Copy Message"
        className="!bg-white hover:!bg-gray-200"
        onClick={() => {
          navigator.clipboard.writeText(value);
          setCopied(true);
          clearTimeout(timeoutRef.current);
          timeoutRef.current = setTimeout(() => setCopied(false), 2000);
        }}>
        <div className="relative flex size-4 items-center justify-center">
          <Copy
            className={`text-primary absolute size-4 transition-all duration-300 ease-in-out ${
              copied
                ? "pointer-events-none scale-75 rotate-45 opacity-0"
                : "scale-100 rotate-0 opacity-100"
            }`}
          />
          <Check
            className={`text-primary absolute size-4 transition-all duration-300 ease-in-out ${
              copied
                ? "scale-100 rotate-0 opacity-100"
                : "pointer-events-none scale-75 -rotate-45 opacity-0"
            }`}
          />
        </div>
      </Action>
      <div className="relative flex min-h-[32px] items-center overflow-hidden">
        <div
          className={`flex transition-all duration-300 ease-in-out ${
            showFeedback
              ? "dynamic translate-x-0 scale-100 opacity-100"
              : "pointer-events-none invisible absolute -translate-x-4 scale-95 opacity-0"
          }`}>
          <Action
            label="Good response"
            className="!bg-white hover:!bg-gray-200"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleFeedback(
                index,
                "positive",
                setShowFeedback,
                setFeedbackText
              );
            }}>
            <ThumbsUpIcon className="text-primary size-4" />
          </Action>
          <Action
            label="Bad response"
            className="!bg-white hover:!bg-gray-200"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleFeedback(
                index,
                "negative",
                setShowFeedback,
                setFeedbackText
              );
            }}>
            <ThumbsDownIcon className="text-primary size-4" />
          </Action>
        </div>
        <div
          className={`flex items-center gap-2 transition-all duration-300 ease-in-out ${
            !showFeedback
              ? "translate-x-0 scale-100 opacity-100"
              : "pointer-events-none invisible absolute translate-x-4 scale-95 opacity-0"
          }`}>
          <p className="text-sm whitespace-nowrap text-gray-600">
            {feedbackText}
          </p>
          <a
            type="button"
            onClick={() => setShowFeedback(true)}
            className="text-primary text-sm whitespace-nowrap italic select-none hover:cursor-pointer hover:underline">
            Edit Feedback
          </a>
        </div>
      </div>
    </Actions>
  );
}
