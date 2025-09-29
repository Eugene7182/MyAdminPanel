import {
  ChangeEvent,
  FormEvent,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import { useSearchParams } from "react-router-dom";
import http from "../shared/api/http";
import { useAuthStore } from "../features/auth/store";

interface Product {
  id: number;
  title: string;
  price: string;
  in_stock: boolean;
}

interface PaginatedProductsResponse {
  items: Product[];
  total: number;
  page: number;
  size: number;
  next_offset: number | null;
  prev_offset: number | null;
  sort: { by: string; order: string };
  filters_applied: Record<string, unknown>;
}

interface PaginationMeta {
  total: number;
  page: number;
  size: number;
  next_offset: number | null;
  prev_offset: number | null;
}

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 20;

const DashboardPage = () => {
  const { token, logout } = useAuthStore();
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pageInput, setPageInput] = useState<string>(String(DEFAULT_PAGE));
  const [meta, setMeta] = useState<PaginationMeta>({
    total: 0,
    page: DEFAULT_PAGE,
    size: DEFAULT_SIZE,
    next_offset: null,
    prev_offset: null
  });
  const criteriaRef = useRef({ q: "", filters: "", sort: "" });

  const parsePositiveInt = (value: string | null, fallback: number, max?: number) => {
    if (!value) {
      return fallback;
    }
    const numeric = Number(value);
    if (!Number.isFinite(numeric) || numeric <= 0) {
      return fallback;
    }
    const normalized = Math.floor(numeric);
    if (max) {
      return Math.min(normalized, max);
    }
    return normalized;
  };

  const currentPage = parsePositiveInt(searchParams.get("page"), DEFAULT_PAGE);
  const currentSize = parsePositiveInt(searchParams.get("size"), DEFAULT_SIZE, 200);
  const q = searchParams.get("q") ?? "";
  const filters = searchParams.get("filters") ?? "";
  const sort = searchParams.get("sort") ?? "";

  useEffect(() => {
    const next = new URLSearchParams(searchParams);
    let changed = false;
    if (next.get("page") !== String(currentPage)) {
      next.set("page", String(currentPage));
      changed = true;
    }
    if (next.get("size") !== String(currentSize)) {
      next.set("size", String(currentSize));
      changed = true;
    }
    if (changed) {
      setSearchParams(next, { replace: true });
    }
  }, [currentPage, currentSize, searchParams, setSearchParams]);

  useEffect(() => {
    const prev = criteriaRef.current;
    if (prev.q !== q || prev.filters !== filters || prev.sort !== sort) {
      criteriaRef.current = { q, filters, sort };
      if (currentPage !== DEFAULT_PAGE) {
        const next = new URLSearchParams(searchParams);
        next.set("page", String(DEFAULT_PAGE));
        setSearchParams(next, { replace: true });
      }
    }
  }, [q, filters, sort, currentPage, searchParams, setSearchParams]);

  useEffect(() => {
    if (!token) {
      return;
    }
    const controller = new AbortController();
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const requestParams: Record<string, string | number> = {
          page: currentPage,
          size: currentSize
        };
        if (q) {
          requestParams.q = q;
        }
        if (filters) {
          requestParams.filters = filters;
        }
        if (sort) {
          requestParams.sort = sort;
        }
        const { data } = await http.get<PaginatedProductsResponse>(
          "/api/v1/products/",
          {
            headers: { Authorization: `Bearer ${token}` },
            params: requestParams,
            signal: controller.signal
          }
        );
        setProducts(data.items);
        setMeta({
          total: data.total,
          page: data.page,
          size: data.size,
          next_offset: data.next_offset,
          prev_offset: data.prev_offset
        });
        setPageInput(String(data.page));
      } catch (err: any) {
        if (err?.name === "CanceledError") {
          return;
        }
        setError(err?.response?.data?.detail?.message ?? "Ошибка загрузки");
        setProducts([]);
        setMeta({
          total: 0,
          page: DEFAULT_PAGE,
          size: currentSize,
          next_offset: null,
          prev_offset: null
        });
      } finally {
        setIsLoading(false);
      }
    };
    load();
    return () => controller.abort();
  }, [token, currentPage, currentSize, q, filters, sort]);

  useEffect(() => {
    setPageInput(String(meta.page));
  }, [meta.page]);

  const totalPages = useMemo(() => {
    if (meta.size <= 0) {
      return 1;
    }
    return Math.max(1, Math.ceil(meta.total / meta.size));
  }, [meta.total, meta.size]);

  const visibleRange = useMemo(() => {
    if (meta.total === 0) {
      return { start: 0, end: 0 };
    }
    const start = (meta.page - 1) * meta.size + 1;
    const end = Math.min(meta.page * meta.size, meta.total);
    return { start, end };
  }, [meta.page, meta.size, meta.total]);

  const updatePage = (targetPage: number) => {
    const bounded = Math.max(1, Math.min(targetPage, totalPages));
    const next = new URLSearchParams(searchParams);
    const activeSize = meta.size || currentSize;
    next.set("page", String(bounded));
    next.set("size", String(activeSize));
    setPageInput(String(bounded));
    setSearchParams(next);
  };

  const handlePageSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const parsed = Number(pageInput);
    if (!Number.isFinite(parsed)) {
      setPageInput(String(meta.page));
      return;
    }
    updatePage(Math.floor(parsed));
  };

  const handleSizeChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextSize = parsePositiveInt(event.target.value, meta.size || DEFAULT_SIZE, 200);
    const next = new URLSearchParams(searchParams);
    next.set("size", String(nextSize));
    next.set("page", String(DEFAULT_PAGE));
    setPageInput(String(DEFAULT_PAGE));
    setSearchParams(next);
  };

  const canPrev = meta.page > 1;
  const canNext = meta.page < totalPages;

  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">
            Товары
          </h1>
          <p className="text-sm text-slate-500">
            Мониторинг складских остатков и цен
          </p>
        </div>
        <button
          className="px-4 py-2 bg-slate-800 text-white rounded"
          onClick={() => logout()}
        >
          Выйти
        </button>
      </div>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      <div className="bg-white shadow rounded">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">
                ID
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">
                Название
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">
                Цена
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium text-slate-500 uppercase">
                Статус
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td className="px-4 py-6 text-center text-sm text-slate-500" colSpan={4}>
                  Загрузка...
                </td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-center text-sm text-slate-500" colSpan={4}>
                  Данных нет
                </td>
              </tr>
            ) : (
              products.map((product) => (
                <tr key={product.id} className="odd:bg-white even:bg-slate-50">
                  <td className="px-4 py-2 text-sm text-slate-700">{product.id}</td>
                  <td className="px-4 py-2 text-sm text-slate-700">{product.title}</td>
                  <td className="px-4 py-2 text-sm text-slate-700">{product.price}</td>
                  <td className="px-4 py-2 text-sm text-slate-700">
                    {product.in_stock ? "В наличии" : "Нет"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="flex flex-col gap-3 px-4 py-3 border-t border-slate-200 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-600">
            Показаны {visibleRange.start}–{visibleRange.end} из {meta.total}
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              На странице:
              <select
                className="rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                value={meta.size || currentSize}
                onChange={handleSizeChange}
              >
                {[10, 20, 50, 100, 200].map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex items-center gap-2">
              <button
                className="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => updatePage(meta.page - 1)}
                disabled={!canPrev}
              >
                Назад
              </button>
              <form onSubmit={handlePageSubmit} className="flex items-center gap-2">
                <span className="text-sm text-slate-600">Стр.</span>
                <input
                  type="number"
                  min={1}
                  className="w-16 rounded border border-slate-300 px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                  value={pageInput}
                  onChange={(event) => setPageInput(event.target.value)}
                />
              </form>
              <span className="text-sm text-slate-500">/ {totalPages}</span>
              <button
                className="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => updatePage(meta.page + 1)}
                disabled={!canNext}
              >
                Вперёд
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
