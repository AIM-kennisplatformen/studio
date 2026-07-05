import { Message, MessageContent } from "@/components/shadcn-io/ai/message";

export default function UserMessage({ value }) {
  return (
    <>
      <Message from="user" className="flex justify-end pl-[5%]">
        <MessageContent className="bg-primary selection:!text-primary max-w-prose wrap-break-word text-white selection:!bg-white">
          {value}
        </MessageContent>
      </Message>
    </>
  );
}
