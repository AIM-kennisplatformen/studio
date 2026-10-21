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
      icon: <Settings className="size-4" />,
      action: () => {
        setSettingsOpen(true);
        setIsOpen(false);
      },
      textColor: "!text-gray-700 hover:!text-gray-900",
      title: "Open settings",
    },
    {
      label: "Log Out",
      icon: <LogOut className="size-4" />,
      action: () => {
        logOut();
        setIsOpen(false);
      },
      textColor: "!text-red-600 hover:!text-red-700",
      title: "",
    },
  ];

  return (
    <div className="relative inline-block text-left" ref={menuRef}>
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="!bg-primary/20 hover:!bg-primary/30 flex items-center justify-center rounded-md p-2 transition-colors"
        aria-expanded={isOpen}
        title="Open menu"
        aria-label="Toggle settings menu">
        <Menu className="text-primary size-6" />
      </button>

      {isOpen && (
        <div className="animate-in fade-in-0 zoom-in-95 absolute right-0 z-50 mt-2 w-44 origin-top-right rounded-xl border border-gray-100 bg-white p-1 shadow-lg ring-1 ring-black/5">
          <MenuContent menuOptions={menuOptions} />
        </div>
      )}
    </div>
  );
}

function MenuContent({ menuOptions }) {
  return (
    <div className="flex flex-col gap-0.5">
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
      title={option.title}
      className={`flex w-full items-center gap-2.5 rounded-lg !bg-white px-3 py-2 text-sm font-medium transition-colors hover:!bg-gray-100/80 ${option.textColor}`}>
      <span className={`shrink-0 ${option.textColor}`}>{option.icon}</span>
      <span>{option.label}</span>
    </button>
  );
}
