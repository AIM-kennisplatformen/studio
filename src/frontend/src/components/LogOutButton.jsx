import { logOut } from "../data/api.js";
import { useState } from "react";

const menuOptions = [
  {
    label: "Settings",
    icon: "",
    action: () => console.log("Opening settings..."),
    textColor: "black",
  },
  {
    label: "Log Out",
    icon: "",
    action: () => logOut(),
    textColor: "red",
  },
];

export default function LogOutButton() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <div className="relative inline-block text-left">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="!bg-[#038061] p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-inset focus:ring-green-500"
          aria-expanded={isOpen}
          aria-label="Toggle settings menu"
        >
          <span className="sr-only">Settings</span>
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
          <div className="absolute right-0 mt-2 z-10 w-48 origin-top-right">
            <Menu />
          </div>
        )}
      </div>
    </>
  );
}

function Menu() {
  return (
    <div className="absolute left-0 mt-4 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-20">
      {menuOptions.map((option, index) => (
        <MenuButton key={index} option={option} />
      ))}
    </div>
  );
}

function MenuButton({ option }) {
  return (
    <button
      onClick={option.action}
      className={`flex rounded items-center px-4 py-2 text-sm !text-black !bg-white hover:bg-white/90 transition duration-150`}
    >
      {option.icon && (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
          stroke="currentColor"
          className="size-5 mr-2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d={option.icon} />
        </svg>
      )}
      {option.label}
    </button>
  );
}
