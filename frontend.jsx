import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

const API_BASE_URL = window.__APP_CONFIG__?.apiBaseUrl || "http://localhost:8000";
const DEFAULT_PAGE_SIZE = 20;

const FIELDS = {
  id: { label: "ID", type: "number" },
  title: { label: "Название", type: "string" },
  category: { label: "Категория", type: "string" },
  price: { label: "Цена", type: "number" },
  stock: { label: "Остаток", type: "number" },
  available: { label: "В наличии", type: "boolean" },
  description: { label: "Описание", type: "string", nullable: true },
  created_at: { label: "Создан", type: "date" },
  updated_at: { label: "Обновлён", type: "date" },
};

const OPERATORS = {
  string: [
    { value: "contains", label: "содержит" },
    { value: "startswith", label: "начинается" },
    { value: "endswith", label: "заканчивается" },
    { value: "eq", label: "=" },
    { value: "neq", label: "≠" },
    { value: "in", label: "в списке" },
  ],
  stringNullable: [
    { value: "contains", label: "содержит" },
    { value: "startswith", label: "начинается" },
    { value: "endswith", label: "заканчивается" },
    { value: "eq", label: "=" },
    { value: "neq", label: "≠" },
    { value: "isnull", label: "пусто" },
  ],
  number: [
    { value: "eq", label: "=" },
    { value: "neq", label: "≠" },
    { value: "gt", label: ">" },
    { value: "gte", label: "≥" },
    { value: "lt", label: "<" },
    { value: "lte", label: "≤" },
    { value: "between", label: "между" },
    { value: "in", label: "в списке" },
  ],
  boolean: [
    { value: "istrue", label: "истина" },
    { value: "isfalse", label: "ложь" },
    { value: "eq", label: "=" },
    { value: "neq", label: "≠" },
  ],
  date: [
    { value: "eq", label: "=" },
    { value: "neq", label: "≠" },
    { value: "gt", label: ">" },
    { value: "gte", label: "≥" },
    { value: "lt", label: "<" },
    { value: "lte", label: "≤" },
    { value: "between", label: "между" },
  ],
};

const operatorLabel = Object.values(OPERATORS)
  .flat()
  .reduce((map, op) => ({ ...map, [op.value]: op.label }), {});

function parseFilters(raw) {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed;
    if (parsed && parsed.field) return [parsed];
  } catch (error) {
    console.warn("Invalid filters", error);
  }
  return [];
}

function parseSort(raw) {
  if (!raw) return [{ field: "id", direction: "asc" }];
  return raw
    .split(";")
    .map((chunk) => chunk.trim())
    .filter(Boolean)
    .map((chunk) => {
      const [field, direction = "asc"] = chunk.split(",");
      return { field: field.trim(), direction: direction.trim().toLowerCase() === "desc" ? "desc" : "asc" };
    })
    .filter((entry) => FIELDS[entry.field]);
}

function formatSort(sort) {
  return sort.map((entry) => `${entry.field},${entry.direction}`).join(";");
}

function parseUrlState() {
  const params = new URLSearchParams(window.location.search);
  return {
    page: Math.max(1, Number.parseInt(params.get("page") ?? "1", 10)),
    pageSize: Math.min(100, Math.max(1, Number.parseInt(params.get("page_size") ?? `${DEFAULT_PAGE_SIZE}`, 10))),
    q: params.get("q") ?? "",
    filters: parseFilters(params.get("filters")),
    sort: params.get("sort") ?? "",
  };
}

function buildQuery({ page, pageSize, q, filters, sort }) {
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  if (q) params.set("q", q);
  if (filters.length) params.set("filters", JSON.stringify(filters));
  if (sort) params.set("sort", sort);
  return params.toString();
}

function debounce(value, delay) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handle);
  }, [value, delay]);
  return debounced;
}

function normalizeValue(field, operator, value, extra) {
  const type = FIELDS[field]?.type ?? "string";
  const sanitize = (input) => {
    if (input === undefined || input === null || (typeof input === "string" && !input.trim())) return null;
    if (type === "number") {
      const parsed = Number(input);
      return Number.isNaN(parsed) ? null : parsed;
    }
    if (type === "boolean") {
      if (typeof input === "boolean") return input;
      const normalized = String(input).toLowerCase();
      if (["true", "1", "yes", "да"].includes(normalized)) return true;
      if (["false", "0", "no", "нет"].includes(normalized)) return false;
      return null;
    }
    if (type === "date") {
      const date = new Date(input);
      return Number.isNaN(date.getTime()) ? null : date.toISOString();
    }
    return String(input);
  };

  if (["istrue", "isfalse", "isnull"].includes(operator)) return { ok: true, value: null };
  if (operator === "between") {
    const first = sanitize(value);
    const second = sanitize(extra);
    return first !== null && second !== null ? { ok: true, value: [first, second] } : { ok: false, error: "Нужны два значения" };
  }
  if (operator === "in") {
    const tokens = String(value ?? "")
      .split(",")
      .map((chunk) => chunk.trim())
      .filter(Boolean);
    if (!tokens.length) return { ok: false, error: "Список пуст" };
    const converted = tokens.map(sanitize);
    return converted.every((item) => item !== null) ? { ok: true, value: converted } : { ok: false, error: "Некорректное значение" };
  }
  const single = sanitize(value);
  return single !== null ? { ok: true, value: single } : { ok: false, error: "Некорректное значение" };
}

function ProductsPage() {
  const [urlState, setUrlState] = useState(parseUrlState);
  const [search, setSearch] = useState(urlState.q);
  const [draft, setDraft] = useState({ field: "title", operator: "contains", value: "", extra: "" });
  const [filtersError, setFiltersError] = useState(null);
  const [products, setProducts] = useState([]);
  const [meta, setMeta] = useState({ total: 0, page: urlState.page, totalPages: 1 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reloadToken, setReloadToken] = useState(0);
  const initial = useRef(true);
  const debouncedSearch = debounce(search, 350);

  useEffect(() => {
    const handler = () => setUrlState(parseUrlState());
    window.addEventListener("popstate", handler);
    return () => window.removeEventListener("popstate", handler);
  }, []);

  useEffect(() => {
    if (!initial.current) {
      const query = buildQuery(urlState);
      const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}`;
      window.history.replaceState({}, "", nextUrl);
    } else {
      initial.current = false;
    }
    setSearch(urlState.q);
  }, [urlState]);

  useEffect(() => {
    if (debouncedSearch !== urlState.q) {
      setUrlState((prev) => ({ ...prev, page: 1, q: debouncedSearch }));
    }
  }, [debouncedSearch, urlState.q]);

  const sortOrder = useMemo(() => parseSort(urlState.sort), [urlState.sort]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    const query = buildQuery(urlState);
    fetch(`${API_BASE_URL}/products?${query}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          throw new Error(payload?.detail?.message || payload?.message || `Ошибка ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setProducts(Array.from(new Map(data.items.map((item) => [item.id, item])).values()));
        setMeta({ total: data.total, page: data.page, totalPages: data.total_pages });
        setError(null);
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError(err.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [urlState, reloadToken]);

  useEffect(() => {
    let closed = false;
    let timeoutId;
    const connect = () => {
      const url = new URL("/ws/products", API_BASE_URL);
      url.protocol = url.protocol.replace("http", "ws");
      const ws = new WebSocket(url);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (["product.created", "product.updated", "product.deleted"].includes(payload?.event)) {
            setReloadToken((value) => value + 1);
          }
        } catch (error) {
          console.warn("WS payload error", error);
        }
      };
      ws.onclose = () => {
        if (!closed) timeoutId = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws.close();
      return ws;
    };
    const socket = connect();
    return () => {
      closed = true;
      clearTimeout(timeoutId);
      socket.close();
    };
  }, []);

  const updateState = useCallback((updater) => {
    setUrlState((prev) => {
      const next = typeof updater === "function" ? updater(prev) : { ...prev, ...updater };
      next.filters = (next.filters || []).filter(Boolean);
      return next;
    });
  }, []);

  const handleSort = (field) => {
    updateState((prev) => {
      const current = parseSort(prev.sort);
      const index = current.findIndex((entry) => entry.field === field);
      let next = [...current];
      if (index === 0) {
        next[0] = { field, direction: current[0].direction === "asc" ? "desc" : "asc" };
      } else if (index > 0) {
        next.splice(index, 1);
        next.unshift({ field, direction: "asc" });
      } else {
        next.unshift({ field, direction: "asc" });
      }
      if (!next.length) next = [{ field: "id", direction: "asc" }];
      return { ...prev, sort: formatSort(next), page: 1 };
    });
  };

  const currentOperators = useMemo(() => {
    const meta = FIELDS[draft.field];
    if (!meta) return OPERATORS.string;
    if (meta.type === "string" && meta.nullable) return OPERATORS.stringNullable;
    if (meta.type === "string") return OPERATORS.string;
    if (meta.type === "number") return OPERATORS.number;
    if (meta.type === "boolean") return OPERATORS.boolean;
    if (meta.type === "date") return OPERATORS.date;
    return OPERATORS.string;
  }, [draft.field]);

  useEffect(() => {
    if (!currentOperators.some((option) => option.value === draft.operator)) {
      setDraft((prev) => ({ ...prev, operator: currentOperators[0]?.value ?? "contains", value: "", extra: "" }));
    }
  }, [currentOperators, draft.operator]);

  const applyFilter = (event) => {
    event.preventDefault();
    const normalized = normalizeValue(draft.field, draft.operator, draft.value, draft.extra);
    if (!normalized.ok) {
      setFiltersError(normalized.error);
      return;
    }
    setFiltersError(null);
    updateState((prev) => ({
      ...prev,
      filters: [...prev.filters, { field: draft.field, operator: draft.operator, value: normalized.value }],
      page: 1,
    }));
  };

  const removeFilter = (index) => {
    updateState((prev) => ({ ...prev, filters: prev.filters.filter((_, i) => i !== index), page: 1 }));
  };

  const clearFilters = () => updateState((prev) => ({ ...prev, filters: [], page: 1 }));

  const changePage = (step) => updateState((prev) => ({ ...prev, page: Math.min(Math.max(prev.page + step, 1), meta.totalPages) }));

  return (
    <div className="products-app" style={{ fontFamily: "Inter, sans-serif", padding: "24px", maxWidth: "1100px", margin: "0 auto" }}>
      <h1 style={{ fontSize: "22px", fontWeight: 600, marginBottom: "16px" }}>Товары</h1>
      <section style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
        <div>
          <label style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Поиск</label>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Название, категория" style={{ padding: "8px", borderRadius: "6px", border: "1px solid #d0d5dd" }} />
        </div>
        <form onSubmit={applyFilter} style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "flex-end" }}>
          <div>
            <label style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Поле</label>
            <select value={draft.field} onChange={(e) => setDraft({ field: e.target.value, operator: currentOperators[0]?.value ?? "contains", value: "", extra: "" })} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #d0d5dd" }}>
              {Object.entries(FIELDS).map(([value, meta]) => (
                <option key={value} value={value}>
                  {meta.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Оператор</label>
            <select value={draft.operator} onChange={(e) => setDraft((prev) => ({ ...prev, operator: e.target.value, value: "", extra: "" }))} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #d0d5dd" }}>
              {currentOperators.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          {!['istrue', 'isfalse', 'isnull'].includes(draft.operator) && (
            <div>
              <label style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>Значение</label>
              <input value={draft.value} onChange={(e) => setDraft((prev) => ({ ...prev, value: e.target.value }))} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #d0d5dd" }} />
            </div>
          )}
          {draft.operator === 'between' && (
            <div>
              <label style={{ display: "block", fontSize: "12px", marginBottom: "4px" }}>и</label>
              <input value={draft.extra} onChange={(e) => setDraft((prev) => ({ ...prev, extra: e.target.value }))} style={{ padding: "8px", borderRadius: "6px", border: "1px solid #d0d5dd" }} />
            </div>
          )}
          <button type="submit" style={{ padding: "9px 14px", background: "#2563eb", color: "#fff", borderRadius: "6px", border: "none", fontWeight: 600 }}>Добавить</button>
        </form>
      </section>
      {filtersError && <div style={{ color: "#d92d20", marginBottom: "12px" }}>{filtersError}</div>}
      {urlState.filters.length > 0 && (
        <div style={{ marginBottom: "12px", display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {urlState.filters.map((filter, index) => (
            <span key={`${filter.field}-${index}`} style={{ display: "inline-flex", gap: "6px", alignItems: "center", background: "#eef2ff", color: "#4338ca", padding: "4px 10px", borderRadius: "999px", fontSize: "13px" }}>
              {FIELDS[filter.field]?.label ?? filter.field} {operatorLabel[filter.operator] ?? filter.operator} {Array.isArray(filter.value) ? filter.value.join(" – ") : filter.value ?? ""}
              <button onClick={() => removeFilter(index)} style={{ border: "none", background: "transparent", color: "#4338ca", cursor: "pointer" }}>×</button>
            </span>
          ))}
          <button onClick={clearFilters} style={{ border: "none", background: "transparent", color: "#2563eb", cursor: "pointer" }}>Очистить всё</button>
        </div>
      )}
      <div style={{ border: "1px solid #e5e7eb", borderRadius: "10px", overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {Object.keys(FIELDS).filter((key) => key !== "description").map((field) => {
                const active = sortOrder.find((entry) => entry.field === field);
                return (
                  <th key={field} onClick={() => handleSort(field)} style={{ cursor: "pointer", padding: "10px", textAlign: "left", fontSize: "13px", color: "#475467" }}>
                    {FIELDS[field].label} {active ? (active.direction === "asc" ? "▲" : "▼") : ""}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ padding: "20px", textAlign: "center" }}>Загрузка…</td>
              </tr>
            ) : error ? (
              <tr>
                <td colSpan={7} style={{ padding: "20px", textAlign: "center", color: "#d92d20" }}>{error}</td>
              </tr>
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: "20px", textAlign: "center" }}>Нет данных</td>
              </tr>
            ) : (
              products.map((product) => (
                <tr key={product.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                  <td style={{ padding: "10px" }}>{product.id}</td>
                  <td style={{ padding: "10px" }}>{product.title}</td>
                  <td style={{ padding: "10px" }}>{product.category}</td>
                  <td style={{ padding: "10px" }}>{product.price.toFixed(2)}</td>
                  <td style={{ padding: "10px" }}>{product.stock}</td>
                  <td style={{ padding: "10px" }}>{product.available ? "Да" : "Нет"}</td>
                  <td style={{ padding: "10px" }}>{new Date(product.updated_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <footer style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
        <span style={{ fontSize: "13px", color: "#475467" }}>Всего: {meta.total} · Стр. {meta.page} из {Math.max(meta.totalPages, 1)}</span>
        <div style={{ display: "flex", gap: "8px" }}>
          <button disabled={meta.page <= 1 || loading} onClick={() => changePage(-1)} style={{ padding: "8px 14px", borderRadius: "6px", border: "1px solid #d0d5dd", background: meta.page <= 1 || loading ? "#f9fafb" : "#fff" }}>Назад</button>
          <button disabled={meta.page >= meta.totalPages || loading} onClick={() => changePage(1)} style={{ padding: "8px 14px", borderRadius: "6px", border: "1px solid #d0d5dd", background: meta.page >= meta.totalPages || loading ? "#f9fafb" : "#fff" }}>Вперёд</button>
        </div>
      </footer>
    </div>
  );
}

const rootElement = document.getElementById("root");
if (rootElement) {
  createRoot(rootElement).render(<ProductsPage />);
}
