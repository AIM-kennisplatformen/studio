import { logOut } from "../../data/api.js";
import { useEffect, useRef, useState } from "react";
import { Menu, Settings, LogOut } from "lucide-react";

export default function UserMenu({ setSettingsOpen }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const menuOptions = [
    {
      label: "Settings",
      icon: <Settings />,
      action: () => setSettingsOpen(true),
      textColor: "!text-black",
    },
    {
      label: "Log Out",
      icon: <LogOut />,
      action: () => logOut(),
      textColor: "!text-red-700",
    },
  ];

  return (
    <>
      <div className="relative inline-block text-left" ref={menuRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="!bg-primary/20 hover:!bg-primary/30 rounded-md p-2"
          aria-expanded={isOpen}
          title="Open menu"
          aria-label="Toggle settings menu">
          <span className="sr-only">Settings</span>
          <Menu />
        </button>
        {isOpen && (
          <div className="absolute right-0 z-10 mt-6 w-48 origin-top-right">
            <Menu menuOptions={menuOptions} />
          </div>
        )}
      </div>
    </>
  );
}

function Menu({ menuOptions }) {
  return (
    <div className="absolute left-0 z-20 w-48 rounded-md border border-gray-200 bg-white shadow-lg">
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
      className={`flex w-full items-center rounded !bg-white text-sm hover:!bg-gray-100 ${option.textColor} transition duration-150`}>
      <div className="mr-3">{option.icon}</div>
      {option.label}
    </button>
  );
}
