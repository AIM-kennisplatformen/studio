// POC(fcose): temporary manual focus picker. The MCP server will decide which
// subgraph to return, so delete this component when that path lands.
export default function GraphFocusPicker({
  options,
  focusId,
  hops,
  nodeCount = 0,
  edgeCount = 0,
  onFocusChange,
  onHopsChange,
}) {
  return (
    <div className="absolute top-3 left-3 z-10 flex items-center gap-3 rounded-md border border-gray-300 bg-white/95 px-2 py-1.5 text-sm shadow">
      <label className="flex items-center gap-1">
        <span className="text-gray-600">Focus</span>
        <select
          className="max-w-[22rem] rounded border border-gray-300 bg-white px-1 py-0.5"
          value={focusId ?? ""}
          onChange={(event) =>
            onFocusChange(
              event.target.value ? Number(event.target.value) : null
            )
          }>
          <option value="">Full graph</option>
          {options.map((option) => (
            <option key={option.id} value={option.id}>
              {option.title}
            </option>
          ))}
        </select>
      </label>
      <label className="flex items-center gap-1">
        <span className="text-gray-600">Depth</span>
        <select
          className="rounded border border-gray-300 bg-white px-1 py-0.5"
          value={hops}
          disabled={focusId == null}
          onChange={(event) => onHopsChange(Number(event.target.value))}>
          <option value={1}>1</option>
          <option value={2}>2</option>
        </select>
      </label>
      {focusId != null && (
        <span className="text-xs text-gray-500">
          {nodeCount} nodes · {edgeCount} edges
        </span>
      )}
    </div>
  );
}
