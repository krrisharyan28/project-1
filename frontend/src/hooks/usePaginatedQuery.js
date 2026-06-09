import { useCallback, useEffect, useState } from "react";

/**
 * Generic paginated-list hook for DRF endpoints.
 *
 * @param {(params) => Promise} fetcher  API function returning {count, results}
 * @param {object} filters               extra query params (re-fetches on change)
 */
export default function usePaginatedQuery(fetcher, filters = {}) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ count: 0, results: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const filterKey = JSON.stringify(filters);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher({ page, ...filters });
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetcher, page, filterKey]);

  useEffect(() => {
    load();
  }, [load]);

  // Reset to first page whenever filters change.
  useEffect(() => {
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterKey]);

  return { ...data, page, setPage, loading, error, reload: load };
}
