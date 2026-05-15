import { Link, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="flex min-h-full flex-col bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-4 sm:px-6">
          <Link
            to="/"
            className="text-lg font-semibold tracking-tight text-zinc-900"
          >
            Gravitas
          </Link>
          <nav className="flex items-center gap-4 text-sm font-medium text-zinc-600">
            <Link
              to="/"
              className="rounded-md px-2 py-1 transition hover:bg-zinc-100 hover:text-zinc-900"
            >
              Documents
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>
      <footer className="border-t border-zinc-200 bg-white py-4 text-center text-xs text-zinc-500">
        Gravitas
      </footer>
    </div>
  );
}
