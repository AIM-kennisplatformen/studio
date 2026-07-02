import { Message, MessageContent } from "@/components/shadcn-io/ai/message";

export default function UserMessage({ index, value }) {
  return (
    <>
      <Message from="user" key={index} className="flex justify-end pl-[5%]">
        <MessageContent
          className="max-w-prose wrap-break-word"
          style={{ backgroundColor: "#038061", color: "#ffffff" }}>
          {value}
        </MessageContent>
      </Message>
    </>
  );
}
