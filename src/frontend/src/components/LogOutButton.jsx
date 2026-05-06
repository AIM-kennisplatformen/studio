import { logOut } from "../data/api.js";

export default function LogOutButton() {
  return (
    <button
      style={{ backgroundColor: "#038061" }}
      className="text-white px-3 py-1 rounded"
      onClick={() => logOut()}
      aria-label="Log Out"
    >
      Log Out
    </button>
  );
}
