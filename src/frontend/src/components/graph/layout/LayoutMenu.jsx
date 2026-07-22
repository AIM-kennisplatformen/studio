import React, { useState } from "react";
import { nodesAtom } from "../../../lib/atoms";
import { useAtomValue } from "jotai";
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
  console.log("LayoutMenu nodes:", nodes);
  // --- HANDLER FUNCTIONS ---

  // Add a Fixed Node Constraint
  const addFixedConstraint = (nodeId, x, y) => {
    const newConstraint = {
      id: `fixed-${Date.now()}`,
      nodeId: String(nodeId),
      position: { x: Number(x) || 0, y: Number(y) || 0 },
    };
    setFixedNodes((prev) => [...prev, newConstraint]);
  };

  // Add an Alignment Constraint
  const addAlignmentConstraint = (type, nodeIds) => {
    const newConstraint = {
      id: `align-${Date.now()}`,
      type, // "horizontal" or "vertical"
      nodeIds: nodeIds.map((id) => String(id)),
    };
    setAlignmentConstraints((prev) => [...prev, newConstraint]);
  };

  // Add a Relative Placement Constraint
  const buildRelativeConstraint = () => {
    if (!relNode1 || !relNode2 || relNode1 === relNode2) {
      setErrorMessage("Please select two different nodes.");
      return;
    }
    setErrorMessage("");
    // config shape: { left, right, gap } OR { top, bottom, gap }
    if (relDir === "left-right") {
      const config = {
        left: relNode1,
        right: relNode2,
        gap: relGap ? Number(relGap) : 20,
      };
      addRelativePlacementConstraint(config);
    } else if (relDir === "top-bottom") {
      const config = {
        top: relNode1,
        bottom: relNode2,
        gap: relGap ? Number(relGap) : 20,
      };
      addRelativePlacementConstraint(config);
    }
  };

  const addRelativePlacementConstraint = (config) => {
    const newConstraint = {
      id: `rel-${Date.now()}`,
      ...config,
      gap: Number(config.gap) || 20,
    };
    setRelativePlacementConstraints((prev) => [...prev, newConstraint]);
  };

  // Delete any constraint by ID
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

  // State veur de versjillende input velder
  const [fixedNode, setFixedNode] = useState("1");
  const [fixedX, setFixedX] = useState("-56");
  const [fixedY, setFixedY] = useState("132");

  const [relNode1, setRelNode1] = useState("1");
  const [relNode2, setRelNode2] = useState("2");
  const [relDir, setRelDir] = useState("left-right");
  const [relGap, setRelGap] = useState("");

  // Dummy data veur de tabel
  const [constraints, setConstraints] = useState([
    { id: 1, type: "Fixed", nodes: "f1", info: "x: -150 y: -100" },
    { id: 2, type: "Fixed", nodes: "f2", info: "x: -50 y: -150" },
    { id: 3, type: "Fixed", nodes: "f3", info: "x: 100 y: 150" },
  ]);

  return (
    <div className="w-[450px] rounded-sm bg-[#e0f7fa] p-4 font-sans text-sm text-[#37474f] shadow-md select-none">
      {/* Header */}
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
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.title}
              </option>
            ))}
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
              onClick={addFixedConstraint}
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

        <div className="mb-2 flex items-center justify-between">
          <span className="text-[#78909c]">Selected Nodes Vertically</span>
          <button className="rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
            Add
          </button>
        </div>

        <div className="mb-3 flex items-center justify-between">
          <span className="text-[#78909c]">Selected Nodes Horizontally</span>
          <button className="rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
            Add
          </button>
        </div>

        <p className="text-xs text-[#546e7a] italic">
          Click on a node for selecting. Shift + click for extending selection.
        </p>
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
              className="w-20 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
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
              className="w-20 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
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
          {errorMessage === ""
            ? "Click the × button to delete a constraint."
            : errorMessage}
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
                  className={`"bg-[#c8e6c9]/10" transition-colors hover:bg-[#b2dfdb]`}>
                  <td className="p-2">Fixed</td>
                  <td className="p-2">{c.id}</td>
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
                    {c.top ? "Top-Bottom" : c.left ? "Left-Right" : "None"}
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
