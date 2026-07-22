export default function LayoutMenu2({ options, setOptions, setMenuState }) {
  function handleSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newOptions = {};

    // Define all checkbox keys to ensure they are set to false if unchecked
    const checkboxKeys = ["incremental", "tile", "nodeDimensionsIncludeLabels"];
    checkboxKeys.forEach((key) => {
      newOptions[key] = false;
    });

    for (let [key, value] of formData.entries()) {
      if (value === "on") {
        newOptions[key] = true;
      } else if (value !== "" && !isNaN(value)) {
        newOptions[key] = Number(value);
      } else {
        newOptions[key] = value;
      }
    }
    console.log("New Options:", newOptions);
    setOptions(newOptions);
  }

  return (
    <>
      <div className="h-auto bg-cyan-100 p-3">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#546e7a]">
            Layout Options
          </h2>
          <button
            type="button"
            onClick={() => setMenuState("CONSTRAINTS")}
            className="rounded bg-[#78909c] px-4 py-1 text-white transition-colors hover:bg-[#607d8b]">
            Go to Constraints
          </button>
        </div>
        <form
          onSubmit={handleSubmit}
          className="grid grid-cols-[1fr_100px] items-center gap-x-4 gap-y-2 text-sm">
          {/* Quality */}
          <label htmlFor="quality">Quality</label>
          <select
            id="quality"
            name="quality"
            defaultValue={options?.quality || "default"}
            className="h-8 rounded border px-2">
            <option value="draft">Draft</option>
            <option value="default">Default</option>
            <option value="proof">Proof</option>
          </select>
          {/* Node Separation */}
          <label htmlFor="nodeSeparation">Node Separation</label>
          <input
            id="nodeSeparation"
            name="nodeSeparation"
            type="number"
            defaultValue={options?.nodeSeparation}
            className="h-8 rounded border px-2"
          />
          {/* Ideal Edge Length */}
          <label htmlFor="idealEdgeLength">Ideal Edge Length</label>
          <input
            id="idealEdgeLength"
            name="idealEdgeLength"
            type="number"
            defaultValue={options?.idealEdgeLength}
            className="h-8 rounded border px-2"
          />
          {/* Node Repulsion */}
          <label htmlFor="nodeRepulsion">Node Repulsion</label>
          <input
            id="nodeRepulsion"
            name="nodeRepulsion"
            type="number"
            defaultValue={options?.nodeRepulsion}
            className="h-8 rounded border px-2"
          />
          {/* Max Iterations */}
          <label htmlFor="maxIterations">Max Iterations</label>
          <input
            id="maxIterations"
            name="maxIterations"
            type="number"
            defaultValue={options?.maxIterations}
            className="h-8 rounded border px-2"
          />
          {/* Animation Duration */}
          <label htmlFor="animationDuration">Animation Duration (ms)</label>
          <input
            id="animationDuration"
            name="animationDuration"
            type="number"
            defaultValue={options?.animationDuration}
            className="h-8 rounded border px-2"
          />
          {/* Gravity */}
          <label htmlFor="gravity">Gravity</label>
          <input
            id="gravity"
            name="gravity"
            type="number"
            step="any"
            defaultValue={options?.gravity}
            className="h-8 rounded border px-2"
          />
          <label htmlFor="gravityRange">Gravity Range</label>
          <input
            id="gravityRange"
            name="gravityRange"
            type="number"
            step="any"
            defaultValue={options?.gravityRange}
            className="h-8 rounded border px-2"
          />
          {/* Number of Iterations */}
          <label htmlFor="numIter">Number of Iterations</label>
          <input
            id="numIter"
            name="numIter"
            type="number"
            defaultValue={options?.numIter}
            className="h-8 rounded border px-2"
          />
          {/* Node Dimensions Include Labels (Checkbox) */}
          <label htmlFor="nodeDimensionsIncludeLabels">
            Include Labels in Dimensions
          </label>
          <input
            id="nodeDimensionsIncludeLabels"
            name="nodeDimensionsIncludeLabels"
            type="checkbox"
            defaultChecked={options?.nodeDimensionsIncludeLabels}
            className="h-4 w-4 justify-self-start"
          />
          {/* Tile (Checkbox) */}
          <label htmlFor="tile">Tile Disconnected</label>
          <input
            id="tile"
            name="tile"
            type="checkbox"
            defaultChecked={options?.tile}
            className="h-4 w-4 justify-self-start"
          />
          {/* Incremental (Checkbox) */}
          <label htmlFor="incremental">Incremental</label>
          <input
            id="incremental"
            name="incremental"
            type="checkbox"
            defaultChecked={options?.incremental}
            className="h-4 w-4 justify-self-start"
          />
          <label htmlFor="initialEnergyOnIncremental">
            Initial Energy on Incremental
          </label>
          <input
            id="initialEnergyOnIncremental"
            name="initialEnergyOnIncremental"
            type="number"
            defaultValue={options?.initialEnergyOnIncremental}
            className="h-8 rounded border px-2"
          />
          <div></div> {/* Grid spacing helper */}
          <button
            type="submit"
            className="rounded bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600">
            Apply
          </button>
        </form>
      </div>
    </>
  );
}
