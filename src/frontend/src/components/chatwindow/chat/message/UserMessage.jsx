import { Message, MessageContent } from "@/components/shadcn-io/ai/message";
import { User } from "lucide-react";

export default function UserMessage({ value }) {
  return (
    <div className="flex w-full flex-col items-end">
      <span className="text-muted-foreground mb-1 flex items-center gap-1 text-[10px] font-semibold tracking-wider uppercase">
        You <User className="h-3 w-3" />
      </span>
      <Message from="user" className="flex w-full justify-end !pt-0 pl-[5%]">
        <MessageContent className="bg-primary selection:!text-primary max-w-prose wrap-break-word text-white selection:!bg-white">
          {value}
        </MessageContent>
      </Message>
    </div>
  );
}
