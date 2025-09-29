import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, Zap, Trash2, LogOut, Loader2, User } from 'lucide-react';

// --- Конфигурация API и WS ---
// Убедитесь, что ваш FastAPI запущен на этом порту (обычно 8000)
const API_BASE_URL = 'http://127.0.0.1:8000'; 
// Используем ws:// для WebSocket, так как это локальное HTTP-соединение
const WS_BASE_URL = 'ws://127.0.0.1:8000'; 
const MOCK_USER_ID = "admin_user_id"; // ID, который возвращает mock_get_current_user в бэкенде

// --- Контекст для аутентификации (Упрощенный для одного файла) ---
// В реальном приложении использовался бы React Context

const useAuth = () => {
  const [token, setToken] = useState(localStorage.getItem('authToken') || '');
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);
  const [loading, setLoading] = useState(false);
  
  // Функция, извлекающая ID пользователя из мок-токена
  const getUserIdFromToken = (t) => {
      // Mock token format: header.payload.signature
      try {
          const parts = t.split('.');
          if (parts.length === 3) {
              // В реальном приложении нужно декодировать Base64 URL, 
              // но здесь мы просто возвращаем константный ID, 
              // поскольку это mock-бэкенд, который всегда его использует.
              return MOCK_USER_ID; 
          }
          // Обработка случая, когда токен пуст или некорректен
          if (t === '') return null;
      } catch (e) {
          console.error("Ошибка парсинга токена:", e);
      }
      return null;
  };
  
  const userId = getUserIdFromToken(token);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/auth/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      });

      if (!response.ok) {
        // Заменяем alert() на console.error() и возвращаем false для обработки ошибки в UI
        console.error('Неправильное имя пользователя или пароль (ошибка API).');
        throw new Error('Неправильное имя пользователя или пароль.');
      }

      const data = await response.json();
      localStorage.setItem('authToken', data.access_token);
      setToken(data.access_token);
      setIsAuthenticated(true);
      return true;

    } catch (error) {
      console.error('Ошибка входа:', error.message);
      // Важно: в реальном приложении здесь должен быть кастомный Modal/Toast, а не alert
      // alert('Ошибка входа: ' + error.message); 
      setIsAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken('');
    setIsAuthenticated(false);
  };

  return { token, isAuthenticated, loading, login, logout, userId };
};

// --- Компонент: Вход в систему (Login) ---

const LoginComponent = ({ login, loading }) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('secret');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const success = await login(username, password);
    if (!success) {
        setError('Не удалось войти. Убедитесь, что бэкенд запущен.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
      <div className="w-full max-w-md bg-white shadow-2xl rounded-xl p-8 transform transition duration-500 hover:shadow-3xl">
        <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">Вход в Админ-панель</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm" role="alert">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Имя пользователя (любое)</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
              placeholder="Введите имя пользователя"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Пароль (любой)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 transition duration-150"
              placeholder="Введите пароль"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-md text-white font-semibold bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="animate-spin mr-2" size={20} />
            ) : (
              'Войти'
            )}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
            *Для этого мок-бэкенда работают любые непустые логин и пароль.
        </p>
      </div>
    </div>
  );
};

// --- Компонент: Управление продуктами ---

// Используем React.forwardRef, чтобы родительский компонент мог вызвать fetchProducts
const ProductManager = React.forwardRef(({ token, userId, addNotification }, ref) => {
  const [products, setProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/products/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка загрузки продуктов');
      }

      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Ошибка:', error);
      addNotification({ message: 'Ошибка загрузки данных. Проверьте консоль.', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  }, [token, addNotification]);
  
  // Expose fetchProducts via ref (for the WebSocket hook to call)
  React.useImperativeHandle(ref, () => ({
    fetchProducts
  }));

  // Initial data load
  useEffect(() => {
    if (token) {
      fetchProducts();
    }
  }, [token, fetchProducts]);

  const handleDelete = async (productId) => {
    // NOTE: В реальном приложении это должно быть кастомное модальное окно, а не window.confirm
    if (!window.confirm(`Вы уверены, что хотите удалить продукт ID: ${productId}?`)) {
      return;
    }
    
    addNotification({ message: `Удаление продукта ${productId}...`, type: 'info' });

    try {
      const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Ошибка удаления продукта');
      }

      // Бэкенд должен отправить WS-сообщение, которое обновит данные
      addNotification({ message: `Продукт ID ${productId} удален. Обновление через WS ожидается...`, type: 'success' });

    } catch (error) {
      console.error('Ошибка удаления:', error);
      addNotification({ message: 'Ошибка при удалении продукта.', type: 'error' });
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 border-b pb-4">
        <h3 className="text-2xl font-semibold text-gray-800">Список продуктов ({products.length})</h3>
        <button
          onClick={fetchProducts}
          disabled={isLoading}
          className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg shadow-md hover:bg-indigo-700 transition duration-150 disabled:opacity-70"
        >
          {isLoading ? (
            <Loader2 className="animate-spin mr-2" size={18} />
          ) : (
            <RefreshCw className="mr-2" size={18} />
          )}
          Обновить
        </button>
      </div>

      <div className="overflow-y-auto flex-grow">
        {isLoading && products.length === 0 ? (
            <div className="text-center py-10 text-lg text-indigo-500">Загрузка данных...</div>
        ) : products.length === 0 ? (
             <div className="text-center py-10 text-lg text-gray-500">
                Нет доступных продуктов. 
                <button 
                    onClick={fetchProducts}
                    className="block mx-auto mt-4 text-indigo-600 hover:underline"
                >
                    Нажмите, чтобы попробовать загрузить снова.
                </button>
             </div>
        ) : (
          <div className="space-y-4">
            {products.map((product) => (
              <div
                key={product.id}
                className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition duration-150"
              >
                <div className="flex-grow">
                  <p className="text-lg font-medium text-gray-900">{product.name} ({product.sku})</p>
                  <p className="text-sm text-gray-600">
                    Категория: <span className="font-semibold text-indigo-700">{product.category?.name || 'N/A'}</span>
                  </p>
                  <p className="text-sm text-gray-600">
                    Цена: **${product.price.toFixed(2)}**
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(product.id)}
                  className="p-2 ml-4 text-red-600 bg-red-100 rounded-full hover:bg-red-200 transition duration-150 shadow-md"
                  title="Удалить продукт"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
    </div>
  );
});

// --- Компонент: Уведомления (Notifications) ---

const Notification = ({ id, message, type, removeNotification }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      removeNotification(id);
    }, 5000); // Скрыть через 5 секунд

    return () => clearTimeout(timer);
  }, [id, removeNotification]);

  const baseClasses = "flex items-center p-4 rounded-lg shadow-xl mb-3 text-white transition-all duration-300";
  let colorClasses = '';

  switch (type) {
    case 'success':
      colorClasses = 'bg-green-500';
      break;
    case 'error':
      colorClasses = 'bg-red-500';
      break;
    case 'info':
    default:
      colorClasses = 'bg-blue-500';
      break;
  }

  return (
    <div className={`${baseClasses} ${colorClasses} transform translate-x-0 hover:translate-x-1`}>
      <Zap size={20} className="mr-3 flex-shrink-0" />
      <span>{message}</span>
      <button onClick={() => removeNotification(id)} className="ml-auto text-sm opacity-80 hover:opacity-100">
        &times;
      </button>
    </div>
  );
};

// --- Хук: WebSocket Manager ---

const useWebSocket = (userId, token, fetchCallback, addNotification) => {
  useEffect(() => {
    if (!userId || !token) return;

    let ws = null;
    let reconnectTimeout = null;

    const connect = () => {
        // Убедитесь, что ws-адрес соответствует userId
        ws = new WebSocket(`${WS_BASE_URL}/ws/${userId}`);
        
        ws.onopen = () => {
            console.log(`WebSocket: Connected for user ${userId}`);
            addNotification({ message: 'Соединение в реальном времени установлено.', type: 'success' });
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.entity === 'products') {
                    // Если получено сообщение об изменении данных (например, после DELETE)
                    addNotification({ message: 'WS: Обнаружено изменение продуктов. Обновляю данные...', type: 'info' });
                    fetchCallback(); // Запускаем обновление данных в компоненте
                } else {
                    addNotification({ message: `WS: Получено уведомление: ${data.message}`, type: 'info' });
                }
            } catch (e) {
                console.error("WS: Ошибка парсинга сообщения:", e);
            }
        };

        ws.onclose = (event) => {
            console.log('WebSocket: Disconnected. Code:', event.code);
            addNotification({ message: 'Соединение WS потеряно. Попытка переподключения...', type: 'error' });
            // Попытка переподключения через 3 секунды
            reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = (error) => {
            console.error("WebSocket: Error", error);
            ws.close();
        };
    };

    connect();

    // Очистка при размонтировании компонента или изменении зависимостей
    return () => {
        if (ws) {
            ws.close();
        }
        if (reconnectTimeout) {
            clearTimeout(reconnectTimeout);
        }
    };
  }, [userId, token, fetchCallback, addNotification]);

  return null;
};


// --- Главный компонент Приложения (Обертка) ---

const AppWrapper = () => {
    const auth = useAuth();
    
    const [notifications, setNotifications] = useState([]);

    const addNotification = useCallback(({ message, type = 'info' }) => {
        const id = Date.now();
        setNotifications(prev => [...prev, { id, message, type }]);
    }, []);

    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    const productManagerRef = React.useRef(null);

    // Функция для принудительной загрузки данных, вызываемая из WS
    const forceProductFetch = useCallback(() => {
        if (productManagerRef.current && productManagerRef.current.fetchProducts) {
            productManagerRef.current.fetchProducts();
        } else {
            // Ошибка: компонент еще не готов
            console.error('Ошибка: ProductManager не готов для обновления.');
        }
    }, []);
    
    // Подключение WebSocket
    useWebSocket(auth.userId, auth.token, forceProductFetch, addNotification);

    if (!auth.isAuthenticated) {
        return <LoginComponent login={auth.login} loading={auth.loading} />;
    }

    return (
        <div className="flex h-screen bg-gray-100 font-sans">
            {/* Sidebar / Header */}
            <header className="fixed top-0 left-0 right-0 h-16 bg-white shadow-md z-10 flex items-center justify-between px-6">
                <h1 className="text-xl font-extrabold text-indigo-600 flex items-center">
                    <Zap className="mr-2 text-yellow-500" size={24} /> 
                    Admin Mock Panel
                </h1>
                <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-700 font-medium flex items-center">
                        <User size={16} className="mr-1 text-indigo-500"/>
                        ID пользователя: {auth.userId}
                    </span>
                    <button
                        onClick={auth.logout}
                        className="flex items-center px-3 py-1.5 bg-red-500 text-white rounded-lg shadow-md hover:bg-red-600 transition duration-150 text-sm"
                    >
                        <LogOut size={16} className="mr-1" />
                        Выход
                    </button>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-grow p-6 pt-20 overflow-y-auto">
                <div className="max-w-4xl mx-auto">
                    {/* Передаем ProductManagerWithRef, который имеет доступ к методу fetchProducts */}
                    <ProductManager 
                        token={auth.token} 
                        userId={auth.userId} 
                        addNotification={addNotification} 
                        ref={productManagerRef}
                    />
                </div>
            </main>

            {/* Notification Area */}
            <div className="fixed bottom-6 right-6 z-20 w-80">
                {notifications.map(n => (
                    <Notification 
                        key={n.id} 
                        id={n.id} 
                        message={n.message} 
                        type={n.type} 
                        removeNotification={removeNotification} 
                    />
                ))}
            </div>
        </div>
    );
};

export default AppWrapper;
