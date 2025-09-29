import { FormEvent, useState } from "react";
import http from "../shared/api/http";
import { useAuthStore } from "../features/auth/store";

const LoginPage = () => {
  const { setAuth } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const username = String(form.get("email"));
    const password = String(form.get("password"));
    try {
      setLoading(true);
      const { data } = await http.post("/api/v1/auth/login", new URLSearchParams({
        username,
        password
      }), {
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      setAuth(data.access_token, "admin");
      window.location.href = "/";
    } catch (err: any) {
      setError(err.response?.data?.detail?.message ?? "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded shadow-lg w-full max-w-md space-y-6"
      >
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            OPPO KZ Data Platform
          </h1>
          <p className="text-sm text-slate-500">Вход в административную панель</p>
        </div>
        {error && <div className="text-sm text-red-500">{error}</div>}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="w-full border border-slate-200 rounded px-3 py-2"
          />
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700" htmlFor="password">
            Пароль
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            className="w-full border border-slate-200 rounded px-3 py-2"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-emerald-600 text-white py-2 rounded hover:bg-emerald-700 disabled:opacity-50"
        >
          {loading ? "Загрузка..." : "Войти"}
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
