import Drawer from "./Drawer";
import { useEffect, useState } from "react";
import { useAtom } from "jotai";
import { getSettings, updateSettings } from "../../data/api";
import { showTitleNotificationsAtom } from "../../lib/atoms";
import { X } from "lucide-react";

export default function SettingsDrawer({ setIsOpen, isOpen }) {
  //states for mocksettings
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState("en");
  const [showSystemMessages, setShowSystemMessages] = useState(true);
  const [isDynamicTitle, setIsDynamicTitle] = useState(true);
  const [showTitleNotifications, setShowTitleNotifications] = useAtom(
    showTitleNotificationsAtom
  );

  useEffect(() => {
    if (!isOpen) return;
    getSettings().then((res) => setIsDynamicTitle(res.dynamic_title));
  }, [isOpen]);

  const handleDynamicTitleChange = (checked) => {
    setIsDynamicTitle(checked);
    updateSettings(checked);
  };

  const settingsHeader = (
    <div className="mb-2 border-b border-gray-200 pb-1">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Settings</h2>
        <button
          onClick={() => setIsOpen(false)}
          className="group rounded-md !bg-white p-2 text-gray-500 transition duration-150 hover:!bg-gray-100 hover:text-red-600 focus:outline-none">
          <X className="size-6 text-gray-400 transition duration-350 group-hover:text-red-700" />
        </button>
      </div>
    </div>
  );
  const settingsBody = (
    <div className="flex w-full max-w-md flex-col gap-6">
      <div className="flex flex-col gap-5">
        {/* 1. Dark / Light Mode Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <label
              htmlFor="theme-toggle"
              className="block cursor-pointer font-semibold text-black">
              Dark Theme
            </label>
            <span className="text-sm text-gray-500">Toggle dark mode</span>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              id="theme-toggle"
              type="checkbox"
              checked={isDarkMode} // Koppel aan je eigen state
              onChange={(e) => setIsDarkMode(e.target.checked)}
              className="peer sr-only"
            />
            <div className="peer peer-checked:bg-primary h-6 w-11 rounded-full bg-gray-300 peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
          </label>
        </div>

        {/* 3. Language Select */}
        <div className="flex items-center justify-between">
          <div>
            <label
              htmlFor="language-select"
              className="block font-semibold text-black">
              Language & region
            </label>
            <span className="text-sm text-gray-500">Interface language</span>
          </div>
          <select
            id="language-select"
            value={selectedLanguage} // Koppel aan je eigen state
            onChange={(e) => setSelectedLanguage(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:ring-2 focus:ring-emerald-500 focus:outline-none">
            <option key="en" value="en">
              English
            </option>
            <option key="es" value="es">
              Español
            </option>
            <option key="fr" value="fr">
              Français
            </option>
            <option key="nl" value="nl">
              Nederlands
            </option>
            <option key="de" value="de">
              Deutsch
            </option>
          </select>
        </div>

        {/* 4. System Messages Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <label
              htmlFor="system-messages-toggle"
              className="block cursor-pointer font-semibold text-black">
              System messages
            </label>
            <span className="text-sm text-gray-500">
              Show platform notices in chat
            </span>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              id="system-messages-toggle"
              type="checkbox"
              checked={showSystemMessages} // Koppel aan je eigen state
              onChange={(e) => setShowSystemMessages(e.target.checked)}
              className="peer sr-only"
            />
            <div className="peer peer-checked:bg-primary h-6 w-11 rounded-full bg-gray-300 peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
          </label>
        </div>

        <hr />

        {/* 2. Chat Title Generation Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <label
              htmlFor="title-gen-toggle"
              className="block cursor-pointer font-semibold text-black">
              Dynamic Chat Titles
            </label>
            <span className="text-sm text-gray-500">
              Automatically generate titles based on conversation content
            </span>
          </div>
          <label className="relative inline-flex cursor-pointer items-center">
            <input
              id="title-gen-toggle"
              type="checkbox"
              checked={isDynamicTitle} // Koppel aan je eigen state
              onChange={(e) => handleDynamicTitleChange(e.target.checked)}
              className="peer sr-only"
            />
            <div className="peer peer-checked:bg-primary h-6 w-11 rounded-full bg-gray-300 peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
          </label>
        </div>
        {isDynamicTitle && (
          <div className="ms-6 flex items-center justify-between">
            <div>
              <label
                htmlFor="title-gen-toggle"
                className="block cursor-pointer font-semibold text-black">
                Title change notifications
              </label>
              <span className="text-sm text-gray-500">
                Get notifications in chat about dynamic title changes
              </span>
            </div>
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                id="title-gen-toggle"
                type="checkbox"
                checked={showTitleNotifications} // Koppel aan je eigen state
                onChange={(e) => setShowTitleNotifications(e.target.checked)}
                className="peer sr-only"
              />
              <div className="peer peer-checked:bg-primary h-6 w-11 rounded-full bg-gray-300 peer-focus:outline-none after:absolute after:top-[2px] after:left-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white"></div>
            </label>
          </div>
        )}
        <hr />
      </div>
    </div>
  );

  return (
    <Drawer onClose={() => setIsOpen(false)} isOpen={isOpen}>
      {settingsHeader}
      {settingsBody}
    </Drawer>
  );
}
