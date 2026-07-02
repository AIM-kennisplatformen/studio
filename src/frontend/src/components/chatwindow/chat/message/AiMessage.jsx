import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";
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
                      <ThumbsUpIcon className="size-4" />
                    </Action>
                    <Action
                      label="Bad response"
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
                      <ThumbsDownIcon className="size-4" />
                    </Action>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-gray-600">{feedbackText}</p>
                    <button
                      type="button"
                      onClick={() => setShowFeedback(true)}
                      className="!bg-primary hover:!bg-primary-dark cursor-pointer border-0 p-0 text-sm !text-white hover:underline">
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
