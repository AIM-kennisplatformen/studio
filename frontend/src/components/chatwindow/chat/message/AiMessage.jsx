import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import {
  ThumbsUpIcon,
  ThumbsDownIcon,
  Copy,
  Check,
  BotMessageSquare,
} from "lucide-react";
import { Response } from "@/components/shadcn-io/ai/response";
import { logResponseFeedback } from "../../../../data/api";
import { useRef, useState } from "react";
import CopyButton from "@/components/CopyButton";

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
  const isFeedbackVisible =
    index === lastDoneKey && status === "ready" && lastDoneMessage?.name === "ai";

  return (
    <div
      key={index}
      className="group flex w-full items-start justify-start gap-2 pr-[5%]">
      <div className="flex w-full flex-col items-start">
        <span className="text-muted-foreground mb-1 flex items-center gap-1.5 text-[10px] font-semibold tracking-wider uppercase">
          <BotMessageSquare className="h-3 w-3" /> AI
        </span>
        <Response className="w-full rounded-lg border border-gray-200 bg-gray-50 p-2 text-sm wrap-break-word">
          {value}
        </Response>

        <div className="flex flex-row">
        {isFeedbackVisible ? (
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
          ) : (
        <div className="pointer-events-none mr-1 translate-y-1 opacity-0 transition-all duration-200 ease-out group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100">
          <CopyButton value={value} />
        </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MessageOptions({ value, index, feedbackText, setFeedbackText }) {
  const [copied, setCopied] = useState(false);
  const [activeFeedback, setActiveFeedback] = useState(null);
  const timeoutRef = useRef(null);

  async function handleFeedback(messageKey, feedback) {
    if (activeFeedback === feedback) {
      setActiveFeedback(null);
      return;
    }
    setActiveFeedback(feedback);
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
      <div className="flex items-center gap-2">
        <div className="flex items-center">
          <Action
            label="Good response"
            className="!bg-white hover:!bg-gray-200"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleFeedback(index, "positive");
            }}>
            <ThumbsUpIcon
              className={`text-primary size-4 transition-colors duration-200 ${
                activeFeedback === "positive" ? "fill-primary" : ""
              }`}
            />
          </Action>

          <Action
            label="Bad response"
            className="!bg-white hover:!bg-gray-200"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              handleFeedback(index, "negative");
            }}>
            <ThumbsDownIcon
              className={`text-primary size-4 transition-colors duration-200 ${
                activeFeedback === "negative" ? "fill-primary" : ""
              }`}
            />
          </Action>
        </div>
        {feedbackText && (
          <div
            className={`overflow-hidden transition-all duration-300 ease-in-out ${
              activeFeedback !== null
                ? "max-w-xs translate-x-0 opacity-100"
                : "pointer-events-none max-w-0 -translate-x-2 opacity-0"
            }`}>
            <p className="text-sm whitespace-nowrap text-gray-600">
              {feedbackText}
            </p>
          </div>
        )}
      </div>
    </Actions>
  );
}
