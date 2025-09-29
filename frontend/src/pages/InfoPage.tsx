import { useEffect, useState } from "react";
import http from "../shared/api/http";

const InfoPage = () => {
  const [info, setInfo] = useState<Record<string, any>>({});

  useEffect(() => {
    const fetchInfo = async () => {
      const [health, version] = await Promise.all([
        http.get("/api/v1/health"),
        http.get("/api/v1/version")
      ]);
      setInfo({ health: health.data, version: version.data });
    };
    fetchInfo();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
      <div className="max-w-lg space-y-4">
        <h1 className="text-3xl font-semibold">Состояние сервиса</h1>
        <pre className="bg-slate-800 p-4 rounded">{JSON.stringify(info, null, 2)}</pre>
      </div>
    </div>
  );
};

export default InfoPage;
