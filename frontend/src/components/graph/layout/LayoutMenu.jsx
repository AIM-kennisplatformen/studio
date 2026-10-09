import React, { useState } from "react";
import data from "./nodes.json";

export default function LayoutMenu({
  setFixedNodes,
  setAlignmentConstraints,
  setRelativePlacementConstraints,
  setMenuState,
  fixedNodes,
  alignmentConstraints,
  relativePlacementConstraints,
}) {
  const [nodes, setNodes] = useState(data.nuggets);
  const [errorMessage, setErrorMessage] = useState("");

  // Form states
  const [fixedNode, setFixedNode] = useState("1");
  const [fixedX, setFixedX] = useState("-56");
  const [fixedY, setFixedY] = useState("132");

  const [relNode1, setRelNode1] = useState("1");
  const [relNode2, setRelNode2] = useState("2");
  const [relDir, setRelDir] = useState("left-right");
  const [relGap, setRelGap] = useState("");

  // Alignment menu state
  const [showAlignmentMenu, setShowAlignmentMenu] = useState(false);
  const [currentAlignmentType, setCurrentAlignmentType] = useState("");
  const [selectedAlignmentNodes, setSelectedAlignmentNodes] = useState([]);

  // --- HANDLERS ---
  const handleAddFixedConstraint = () => {
    const newConstraint = {
      id: `fixed-${Date.now()}`,
      nodeId: String(fixedNode),
      position: { x: Number(fixedX) || 0, y: Number(fixedY) || 0 },
    };
    setFixedNodes((prev) => [...prev, newConstraint]);
  };

  const addAlignmentConstraint = (type, nodeIds) => {
    const newConstraint = {
      id: `align-${Date.now()}`,
      type,
      nodeIds: nodeIds.map((id) => String(id)),
    };
    setAlignmentConstraints((prev) => [...prev, newConstraint]);
  };

  const buildRelativeConstraint = () => {
    if (!relNode1 || !relNode2 || relNode1 === relNode2) {
      setErrorMessage("Please select two different nodes.");
      return;
    }
    setErrorMessage("");

    const config =
      relDir === "left-right"
        ? { left: relNode1, right: relNode2, gap: relGap ? Number(relGap) : 20 }
        : {
            top: relNode1,
            bottom: relNode2,
            gap: relGap ? Number(relGap) : 20,
          };

    setRelativePlacementConstraints((prev) => [
      ...prev,
      { id: `rel-${Date.now()}`, ...config },
    ]);
  };

  const deleteConstraint = (id, type) => {
    if (type === "fixed") {
      setFixedNodes((prev) => prev.filter((c) => c.id !== id));
    } else if (type === "alignment") {
      setAlignmentConstraints((prev) => prev.filter((c) => c.id !== id));
    } else if (type === "relative") {
      setRelativePlacementConstraints((prev) =>
        prev.filter((c) => c.id !== id)
      );
    }
  };

  const handleOpenAlignmentMenu = (type) => {
    setCurrentAlignmentType(type);
    setSelectedAlignmentNodes([]);
    setErrorMessage("");
    setShowAlignmentMenu(true);
  };

  const handleToggleAlignmentNode = (nodeId) => {
    setSelectedAlignmentNodes((prev) =>
      prev.includes(nodeId)
        ? prev.filter((id) => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  const handleAddAlignmentConstraint = () => {
    if (selectedAlignmentNodes.length < 2) {
      setErrorMessage("Please select at least two nodes for alignment.");
      return;
    }
    setErrorMessage("");
    addAlignmentConstraint(currentAlignmentType, selectedAlignmentNodes);
    setShowAlignmentMenu(false);
    setSelectedAlignmentNodes([]);
  };

  return (
    <div className="w-[450px] rounded-sm bg-white p-4 font-sans text-sm text-[#37474f] shadow-md select-none">
      <h2 className="mb-4 text-xl font-bold text-[#546e7a]">Constraints</h2>
      <button
        onClick={() => setMenuState("LAYOUT")}
        className="mb-4 rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
        Go to Layout Options
      </button>

      <hr className="mb-4 border-[#b2ebf2]" />

      {/* Fixed Node Constraint */}
      <div className="mb-6">
        <h3 className="mb-2 font-semibold text-[#546e7a]">
          Fixed Node Constraint
        </h3>
        <div className="flex flex-col gap-2">
          <select
            value={fixedNode}
            onChange={(e) => setFixedNode(e.target.value)}
            className="rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
            {nodes
              .filter(
                (node) =>
                  !fixedNodes.some(
                    (fixedNode) => fixedNode.nodeId === String(node.id)
                  )
              )
              .map((node) => {
                return (
                  <option key={node.id} value={node.id}>
                    {node.title}
                  </option>
                );
              })}
          </select>
          <div className="flex items-center gap-2">
            <span className="ml-2">x :</span>
            <input
              type="text"
              value={fixedX}
              onChange={(e) => setFixedX(e.target.value)}
              className="w-16 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none"
            />
            <span>y :</span>
            <input
              type="text"
              value={fixedY}
              onChange={(e) => setFixedY(e.target.value)}
              className="w-16 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none"
            />
            <button
              onClick={handleAddFixedConstraint}
              className="ml-auto rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
              Add
            </button>
          </div>
        </div>
      </div>

      <hr className="mb-4 border-[#b2ebf2]" />

      {/* Alignment Constraint */}
      <div className="mb-6">
        <h3 className="mb-2 font-semibold text-[#546e7a]">
          Alignment Constraint
        </h3>
        {!showAlignmentMenu ? (
          <div className="flex gap-2">
            <button
              onClick={() => handleOpenAlignmentMenu("vertical")}
              className="rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
              Vertical
            </button>
            <button
              onClick={() => handleOpenAlignmentMenu("horizontal")}
              className="rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
              Horizontal
            </button>
          </div>
        ) : (
          <div className="rounded border border-[#b2ebf2] bg-white p-3">
            <h4 className="mb-2 font-medium text-[#546e7a]">
              Select Nodes for{" "}
              {currentAlignmentType === "vertical" ? "Vertical" : "Horizontal"}{" "}
              Alignment
            </h4>
            <div className="mb-2 max-h-32 overflow-y-auto border-b border-[#b2ebf2] pb-2">
              {nodes.map((node) => (
                <div key={node.id} className="mb-1 flex items-center">
                  <input
                    type="checkbox"
                    id={`align-node-${node.id}`}
                    checked={selectedAlignmentNodes.includes(node.id)}
                    onChange={() => handleToggleAlignmentNode(node.id)}
                    className="mr-2 accent-[#78909c]"
                  />
                  <label
                    htmlFor={`align-node-${node.id}`}
                    className="cursor-pointer text-sm">
                    {node.title} (ID: {node.id})
                  </label>
                </div>
              ))}
            </div>
            {errorMessage && (
              <p className="mb-2 text-xs text-red-400">{errorMessage}</p>
            )}
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAlignmentMenu(false)}
                className="rounded bg-[#90a4ae] px-3 py-1 text-white transition-colors hover:bg-[#78909c]">
                Cancel
              </button>
              <button
                onClick={handleAddAlignmentConstraint}
                className="rounded bg-[#78909c] px-3 py-1 text-white transition-colors hover:bg-[#607d8b]">
                Add Constraint
              </button>
            </div>
          </div>
        )}
      </div>

      <hr className="mb-4 border-[#b2ebf2]" />

      {/* Relative Placement Constraint */}
      <div className="mb-6">
        <h3 className="mb-2 font-semibold text-[#546e7a]">
          Relative Placement Constraint
        </h3>
        <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2">
          <div className="flex flex-col gap-2">
            <select
              value={relNode1}
              onChange={(e) => setRelNode1(e.target.value)}
              className="w-24 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
              {nodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.title}
                </option>
              ))}
            </select>
            <select
              value={relDir}
              onChange={(e) => setRelDir(e.target.value)}
              className="w-24 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
              <option value="left-right">left-right</option>
              <option value="top-bottom">top-bottom</option>
            </select>
          </div>

          <div className="flex items-center justify-center gap-2">
            <span>Gap:</span>
            <input
              type="text"
              value={relGap}
              onChange={(e) => setRelGap(e.target.value)}
              className="w-16 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none"
            />
          </div>

          <div className="flex h-full items-end">
            <button
              onClick={buildRelativeConstraint}
              className="self-center rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
              Add
            </button>
          </div>

          <div className="col-span-3 mt-1">
            <select
              value={relNode2}
              onChange={(e) => setRelNode2(e.target.value)}
              className="w-24 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
              {nodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {node.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <hr className="mb-2 border-[#b2ebf2]" />

      {/* Constraints Table */}
      <div>
        <p
          className={`mb-2 text-xs ${errorMessage ? "text-red-400" : "text-[#546e7a]"} italic`}>
          {errorMessage || "Click the × button to delete a constraint."}
        </p>
        <div className="max-h-56 overflow-x-auto overflow-y-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="bg-[#b2ebf2] text-[#37474f]">
                <th className="p-2 font-bold">Type</th>
                <th className="p-2 font-bold">Nodes</th>
                <th className="p-2 font-bold">Info</th>
                <th className="w-8 p-2 text-center"></th>
              </tr>
            </thead>
            <tbody>
              {fixedNodes.map((c) => (
                <tr
                  key={c.id}
                  className="bg-[#c8e6c9]/10 transition-colors hover:bg-[#b2dfdb]">
                  <td className="p-2">Fixed</td>
                  <td className="p-2">{c.nodeId}</td>
                  <td className="p-2">
                    X: {c.position.x}, Y: {c.position.y}
                  </td>
                  <td className="p-2 text-center">
                    <button
                      onClick={() => deleteConstraint(c.id, "fixed")}
                      className="text-sm font-bold text-red-400 hover:text-red-600">
                      &times;
                    </button>
                  </td>
                </tr>
              ))}
              {alignmentConstraints.map((c) => (
                <tr
                  key={c.id}
                  className="bg-[#c8e6c9]/10 transition-colors hover:bg-[#b2dfdb]">
                  <td className="p-2">Alignment</td>
                  <td className="p-2">{c.nodeIds.join(", ")}</td>
                  <td className="p-2">
                    {c.type === "horizontal" ? "Horizontal" : "Vertical"}
                  </td>
                  <td className="p-2 text-center">
                    <button
                      onClick={() => deleteConstraint(c.id, "alignment")}
                      className="text-sm font-bold text-red-400 hover:text-red-600">
                      &times;
                    </button>
                  </td>
                </tr>
              ))}
              {relativePlacementConstraints.map((c) => (
                <tr
                  key={c.id}
                  className="bg-[#c8e6c9]/10 transition-colors hover:bg-[#b2dfdb]">
                  <td className="p-2">Relative Placement</td>
                  <td className="p-2">
                    {c.top
                      ? `${c.top} ↓ ${c.bottom}`
                      : `${c.left} → ${c.right}`}
                  </td>
                  <td className="p-2">
                    {c.top ? "Top-Bottom" : "Left-Right"}
                    {c.gap ? `, Gap: ${c.gap}` : ""}
                  </td>
                  <td className="p-2 text-center">
                    <button
                      onClick={() => deleteConstraint(c.id, "relative")}
                      className="text-sm font-bold text-red-400 hover:text-red-600">
                      &times;
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
