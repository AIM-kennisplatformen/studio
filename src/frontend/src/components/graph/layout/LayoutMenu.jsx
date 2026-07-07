import React, { useState } from "react";

export default function LayoutMenu({
  setFixedNodes,
  setAlignmentConstraints,
  setRelativePlacementConstraints,
}) {
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
  const addRelativeConstraint = (config) => {
    // config shape: { left, right, gap } OR { top, bottom, gap }
    const newConstraint = {
      id: `rel-${Date.now()}`,
      ...config,
      gap: Number(config.gap) || 20,
    };
    setRelativePlacementConstraints((prev) => [...prev, newConstraint]);
  };

  // Delete any constraint by ID
  const deleteConstraint = (id) => {
    if (id.startsWith("fixed-")) {
      setFixedNodes((prev) => prev.filter((c) => c.id !== id));
    } else if (id.startsWith("align-")) {
      setAlignmentConstraints((prev) => prev.filter((c) => c.id !== id));
    } else if (id.startsWith("rel-")) {
      setRelativePlacementConstraints((prev) =>
        prev.filter((c) => c.id !== id)
      );
    }
  };
  // State veur de versjillende input velder
  const [fixedNode, setFixedNode] = useState("n1");
  const [fixedX, setFixedX] = useState("-56");
  const [fixedY, setFixedY] = useState("132");

  const [relNode1, setRelNode1] = useState("n1");
  const [relNode2, setRelNode2] = useState("n1");
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

      <hr className="mb-4 border-[#b2ebf2]" />

      {/* Fixed Node Constraint */}
      <div className="mb-6">
        <h3 className="mb-2 font-semibold text-[#546e7a]">
          Fixed Node Constraint
        </h3>
        <div className="flex items-center gap-2">
          <select
            value={fixedNode}
            onChange={(e) => setFixedNode(e.target.value)}
            className="rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
            <option value="n1">n1</option>
            <option value="n2">n2</option>
            <option value="n3">n3</option>
          </select>

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
              <option value="n1">n1</option>
              <option value="n2">n2</option>
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
            <button className="self-center rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
              Add
            </button>
          </div>

          <div className="col-span-3 mt-1">
            <select
              value={relNode2}
              onChange={(e) => setRelNode2(e.target.value)}
              className="w-20 rounded border border-[#b2ebf2] bg-white px-2 py-1 text-sm outline-none">
              <option value="n1">n1</option>
              <option value="n2">n2</option>
            </select>
          </div>
        </div>
      </div>

      <hr className="mb-2 border-[#b2ebf2]" />

      {/* Constraints Table */}
      <div>
        <p className="mb-2 text-xs text-[#546e7a] italic">
          Hover a constraint row to see involved nodes.
        </p>
        <div className="overflow-x-auto">
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
              {constraints.map((c, index) => (
                <tr
                  key={c.id}
                  className={`transition-colors hover:bg-[#b2dfdb] ${index % 2 === 1 ? "bg-[#c8e6c9]/10" : ""}`}>
                  <td className="p-2">{c.type}</td>
                  <td className="p-2">{c.nodes}</td>
                  <td className="p-2">{c.info}</td>
                  <td className="p-2 text-center">
                    <button
                      onClick={() => deleteConstraint(c.id)}
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
