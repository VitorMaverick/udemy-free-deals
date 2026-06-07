import { Link } from "react-router-dom";

export default function Header() {
  return (
    <header className="bg-purple-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold">
          🎓 Udemy Free Deals
        </Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/" className="hover:underline">Home</Link>
          <Link to="/admin" className="hover:underline opacity-70">Admin</Link>
        </nav>
      </div>
    </header>
  );
}
