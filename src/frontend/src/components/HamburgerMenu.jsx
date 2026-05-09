import { useState } from "react";

export default function HamburgerMenu(setCurrentChat = () => {}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <div className="relative inline-block text-left">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="!bg-[#038061] p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-500"
          aria-expanded={isOpen}
          aria-label="Toggle chat history menu"
        >
          <span className="sr-only">Chat History</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="white"
            className="size-6"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"
            />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-20">
            <a
              href="#"
              className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            >
              Chat History
            </a>
            <p>
              Lorem ipsum, dolor sit amet consectetur adipisicing elit.
              Assumenda, explicabo illo! Nesciunt molestiae distinctio provident
              laborum consequatur quam optio laboriosam itaque eaque expedita in
              unde blanditiis, iusto ipsam esse ab.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
