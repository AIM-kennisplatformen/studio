import { useEffect, useState } from "react";
import { createPortal } from "react-dom";

export default function Drawer({ children, isOpen, onClose }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return createPortal(
    <div
      className={`fixed inset-0 z-50 flex justify-end ${
        isOpen ? "pointer-events-auto" : "pointer-events-none"
      }`}>
      <div
        className={`fixed inset-0 bg-black/30 transition-all duration-[800ms] ease-in-out ${
          isOpen
            ? "opacity-100 backdrop-blur-[3px]"
            : "opacity-0 backdrop-blur-none"
        }`}
        onClick={onClose}
      />

      <div
        className={`relative z-10 h-full w-full max-w-md transform bg-white p-6 shadow-xl transition-transform duration-[500ms] ease-in-out ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}>
        {children}
      </div>
    </div>,
    document.body
  );
}
