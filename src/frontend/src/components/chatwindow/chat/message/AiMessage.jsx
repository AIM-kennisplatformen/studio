import { Action, Actions } from "@/components/shadcn-io/ai/actions";
import { ThumbsUpIcon, ThumbsDownIcon } from "lucide-react";
import { Response } from "@/components/shadcn-io/ai/response";

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
                    <p className="text-sm text-gray-600">{feedbackText}</p>
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
