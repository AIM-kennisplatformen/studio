export default function LayoutMenu2() {
  return (
    <>
      <div className="h-auto bg-cyan-100 p-3">
        <div className="grid grid-cols-[1fr_100px] items-center gap-x-4 gap-y-2 text-sm">
          <label>Quality</label>
          <select className="h-8 rounded border px-2">
            <option>Draft</option>
            <option>Default</option>
            <option>Proof</option>
          </select>

          <label>Incremental</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Animate</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Fit</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Uniform Node Dimensions</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Pack Components to Window</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Tile Disconnected</label>
          <input type="checkbox" className="h-4 w-4 justify-self-start" />

          <label>Ideal Edge Length</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Edge Elasticity</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Nesting Factor</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Gravity</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Gravity Range</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Compound Gravity</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Compound Gravity Range</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Number of Iterations</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Tiling Vertical Padding</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Tiling Horizontal Padding</label>
          <input type="number" className="h-8 rounded border px-2" />

          <label>Incremental Cooling Factor</label>
          <input type="number" className="h-8 rounded border px-2" />
        </div>
      </div>
    </>
  );
}
