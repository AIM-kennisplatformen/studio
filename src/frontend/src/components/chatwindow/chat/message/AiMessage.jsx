import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon, Copy } from "lucide-react";
import { Response } from "@/components/shadcn-io/ai/response";
import { logResponseFeedback } from "../../../../data/api";

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
              <Actions>
                <Action
                  label="Copy Message"
                  className="!bg-white hover:!bg-gray-200"
                  onClick={(e) => {
                    navigator.clipboard.writeText(value);
                  }}>
                  <Copy className="text-primary size-4" />
                </Action>
                {showFeedback ? (
                  <>
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
                  </>
                ) : (
                  <>
                    <p className="text-sm text-gray-600">{feedbackText}</p>
                    <a
                      type="button"
                      onClick={() => setShowFeedback(true)}
                      className="text-primary text-sm italic hover:cursor-pointer hover:underline">
                      Edit Feedback
                    </a>
                  </>
                )}
              </Actions>
            </div>
          )}
      </div>
    </div>
  );
}
