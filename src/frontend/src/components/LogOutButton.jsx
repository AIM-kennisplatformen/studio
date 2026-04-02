import logOut from "../data/api.js";

export default function LogOutButton() {
  const handleLogOut = async () => {
    logOut();
  };
  return <button onClick={handleLogOut}>Log Out</button>;
}
