import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4 text-center px-4 bg-gradient-to-b from-gray-900 to-purple-900">
      <h1 className="text-6xl font-bold text-purple-400">404</h1>
      <h2 className="text-2xl font-semibold text-white">Page Not Found</h2>
      <p className="text-gray-400 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link
        to="/"
        className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
      >
        Go Home
      </Link>
    </div>
  );
}
