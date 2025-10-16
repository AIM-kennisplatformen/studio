import { useState, useRef } from "react";
import Graph from "./graph.jsx";import { Chat } from "./chat.jsx";
;
function App() {
  const [leftWidth, setLeftWidth] = useState(66.6); // start ~2/3
  const containerRef = useRef(null);

  const handleMouseDown = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = leftWidth;

    const onMouseMove = (e) => {
      if (!containerRef.current) return;
      const containerWidth = containerRef.current.offsetWidth;
      const newWidth = ((startWidth / 100) * containerWidth + (e.clientX - startX)) / containerWidth * 100;
      if (newWidth > 10 && newWidth < 90) {
        setLeftWidth(newWidth);
      }
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  return (
    <div ref={containerRef} className="flex h-screen w-screen overflow-hidden">
      <div
        className="h-full bg-gray-100"
        style={{ width: `${leftWidth}%` }}
      >
        <Graph />
      </div>

      <div
        className="w-1 bg-gray-400 cursor-col-resize hover:bg-gray-600"
        onMouseDown={handleMouseDown}
      />

      <div className="flex-1 h-full bg-gray-50">
        <Chat />
      </div>
    </div>
  );
}

export default App;
