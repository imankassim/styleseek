"use client";

import { useId, type FormEvent } from "react";

type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  isLoading: boolean;
};

export function SearchBar({ value, onChange, onSubmit, isLoading }: SearchBarProps) {
  const inputId = useId();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(value);
  }

  return (
    <form
      role="search"
      onSubmit={handleSubmit}
      className="flex w-full max-w-2xl gap-2"
    >
      <label htmlFor={inputId} className="sr-only">
        Search products
      </label>
      <input
        id={inputId}
        type="search"
        name="q"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search, e.g. petite green wedding guest dress under £60"
        className="w-full rounded-md border border-neutral-300 bg-white px-4 py-2 text-neutral-900 shadow-sm focus:border-neutral-900 focus:outline-none focus:ring-2 focus:ring-neutral-900"
        autoComplete="off"
      />
      <button
        type="submit"
        disabled={isLoading}
        className="shrink-0 rounded-md bg-neutral-900 px-4 py-2 font-medium text-white hover:bg-neutral-700 focus:outline-none focus:ring-2 focus:ring-neutral-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? "Searching…" : "Search"}
      </button>
    </form>
  );
}
