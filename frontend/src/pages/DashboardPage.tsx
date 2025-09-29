import { useEffect, useState } from "react";
import http from "../shared/api/http";
import { useAuthStore } from "../features/auth/store";

interface Product {
  id: number;
  title: string;
  price: string;
  in_stock: boolean;
}

const DashboardPage = () => {
  const { token, logout } = useAuthStore();
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await http.get("/api/v1/products/", {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProducts(data.items);
      } catch (err: any) {
        setError(err.response?.data?.detail?.message ?? "Ошибка загрузки");
      }
    };
    if (token) {
      load();
    }
  }, [token]);

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
            {products.map((product) => (
              <tr key={product.id} className="odd:bg-white even:bg-slate-50">
                <td className="px-4 py-2 text-sm text-slate-700">{product.id}</td>
                <td className="px-4 py-2 text-sm text-slate-700">{product.title}</td>
                <td className="px-4 py-2 text-sm text-slate-700">{product.price}</td>
                <td className="px-4 py-2 text-sm text-slate-700">
                  {product.in_stock ? "В наличии" : "Нет"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DashboardPage;
