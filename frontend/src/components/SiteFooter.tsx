export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-neutral-200 bg-neutral-50">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-2 px-6 py-8 text-center text-sm text-neutral-500 sm:flex-row sm:justify-between sm:text-left">
        <p>
          <span className="font-medium text-neutral-700">StyleSeek</span> — a research prototype,
          not a real store. No real payments or orders.
        </p>
        <a
          href="https://github.com/imankassim/styleseek"
          target="_blank"
          rel="noreferrer"
          className="text-neutral-500 underline underline-offset-2 hover:text-neutral-900"
        >
          Source & evaluation on GitHub
        </a>
      </div>
    </footer>
  );
}
