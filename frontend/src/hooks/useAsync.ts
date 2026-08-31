import { useEffect, useState } from "react";
import type { Dispatch, DependencyList, SetStateAction } from "react";
import { ApiError } from "../api";

export interface AsyncResult<T> {
  data: T;
  setData: Dispatch<SetStateAction<T>>;
  loading: boolean;
  error: string | null;
}

function toErrorMessage(err: unknown): string {
  return err instanceof ApiError ? err.detail : "Something went wrong.";
}

function depsEqual(a: DependencyList, b: DependencyList): boolean {
  return a.length === b.length && a.every((value, index) => Object.is(value, b[index]));
}

/**
 * Runs `fetcher` on mount and whenever `deps` changes, exposing
 * {data, loading, error}, plus `setData` for callers that need to apply an
 * update outside the fetch lifecycle (e.g. a pessimistic update after a
 * successful mutation elsewhere).
 *
 * Every state update from the fetch itself is guarded by a `cancelled` flag
 * set in the effect's cleanup, so a response that resolves after `deps` has
 * changed again (or after the component unmounts) is ignored rather than
 * overwriting newer state with stale data — the same pattern this project's
 * views used individually before this hook existed.
 *
 * `loading` is reset to `true` during render (comparing `deps` against the
 * previous render, not inside the effect) rather than as the first line of
 * the effect body: setting state synchronously in an effect is exactly what
 * `react-hooks/set-state-in-effect` flags (and what issues #21/#22 fixed
 * elsewhere in this app), and doing it during render instead means callers
 * no longer need their own `setLoading(true)` calls before changing deps.
 */
export function useAsync<T>(
  fetcher: () => Promise<T>,
  initialValue: T,
  deps: DependencyList,
): AsyncResult<T> {
  const [data, setData] = useState<T>(initialValue);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [prevDeps, setPrevDeps] = useState<DependencyList>(deps);

  if (!depsEqual(prevDeps, deps)) {
    setPrevDeps(deps);
    setLoading(true);
  }

  useEffect(() => {
    let cancelled = false;

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(toErrorMessage(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, setData, loading, error };
}
