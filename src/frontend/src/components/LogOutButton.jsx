import { logOut } from "../data/api.js";

export default function LogOutButton() {
  return (
    <button
      style={{ backgroundColor: "#038061" }}
      className="rounded px-3 py-1 text-white"
      onClick={() => logOut()}
      aria-label="Log Out">
      Log Out
    </button>
  );
}
