const ExampleSessions = [
  { title: "Chat Session 1" },
  { title: "Chat Session 2" },
  { title: "Chat Session 3" },
];

export default function ChatSelection({
  setCurrentChat = () => {},
  setChatActive,
  chatActive,
}) {
  return (
    <>
      <div className="relative inline-block text-left">
        <button
          onClick={() => setChatActive(!chatActive)}
          className="flex items-center gap-1 text-white !bg-[#038061] p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-500"
          aria-expanded={chatActive}
          aria-label="Toggle chat history menu"
        >
          Chats
          <span className="sr-only">Chat History</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className={`size-6 transition-transform duration-300 ${
              chatActive ? "rotate-180" : "rotate-0"
            }`}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m4.5 15.75 7.5-7.5 7.5 7.5"
            />
          </svg>
        </button>
      </div>
    </>
  );
}
