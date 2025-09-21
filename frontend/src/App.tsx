import React, { useState, useEffect } from 'react';
import './App.css';

// 1. Определяем тип объекта недвижимости
interface RealEstateItem {
    id: number;
    title: string;
    description: string;
    price: number;
    image_url: string;
}

// 2. Указываем URL вашего бэкенда.
// ВАЖНО: При локальной разработке используйте 'http://localhost:8000'.
// Когда выложите фронтенд на Vercel, замените это на ваш публичный URL от ngrok.
// Читаем URL API из переменных окружения. 
// VITE_API_URL - это переменная, которую мы зададим в Vercel и локально.
// 'http://localhost:8000' будет использоваться только если переменная не задана (для удобства локальной разработки).
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WEBSOCKET_URL = API_BASE_URL.replace(/^http/, 'ws') + '/ws';

function App() {
    const [listings, setListings] = useState<RealEstateItem[]>([]);
    const [newItem, setNewItem] = useState({ title: '', description: '', price: '', image_url: '' });

    // Загрузка данных при старте
    useEffect(() => {
        const fetchListings = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/listings`);
                const data: RealEstateItem[] = await response.json();
                setListings(data.reverse()); // Показываем новые сверху
            } catch (error) {
                console.error("Не удалось загрузить объявления:", error);
            }
        };
        fetchListings();
    }, []);

    // Подключение по WebSocket для real-time обновлений
    useEffect(() => {
        const ws = new WebSocket(WEBSOCKET_URL);
        ws.onmessage = (event) => {
            const newListing: RealEstateItem = JSON.parse(event.data);
            setListings(prev => [newListing, ...prev]); // Добавляем новое объявление в начало списка
        };
        return () => ws.close(); // Закрываем соединение при уходе со страницы
    }, []);

    // Обработчик изменений в полях формы
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setNewItem(prev => ({ ...prev, [e.target.name]: e.target.value }));
    };

    // Обработчик отправки формы
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await fetch(`${API_BASE_URL}/listings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...newItem,
                    price: parseFloat(newItem.price) || 0,
                    id: 0 // ID будет назначен на бэкенде
                }),
            });
            setNewItem({ title: '', description: '', price: '', image_url: '' });
        } catch (error) {
            console.error("Ошибка при создании объявления:", error);
        }
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>Агентство Недвижимости</h1>
            </header>
            <main className="main-content">
                <div className="form-container">
                    <h2>Добавить новое объявление</h2>
                    <form onSubmit={handleSubmit}>
                        <input name="title" value={newItem.title} onChange={handleInputChange} placeholder="Заголовок" required />
                        <textarea name="description" value={newItem.description} onChange={handleInputChange} placeholder="Описание" required />
                        <input name="price" type="number" value={newItem.price} onChange={handleInputChange} placeholder="Цена" required />
                        <input name="image_url" value={newItem.image_url} onChange={handleInputChange} placeholder="URL изображения" required />
                        <button type="submit">Добавить</button>
                    </form>
                </div>
                <div className="listings-container">
                    <h2>Актуальные объявления</h2>
                    <div className="listings-grid">
                        {listings.map((item) => (
                            <div key={item.id} className="listing-card">
                                <img src={item.image_url} alt={item.title} className="listing-image" />
                                <div className="listing-details">
                                    <h3>{item.title}</h3>
                                    <p>{item.description}</p>
                                    <div className="listing-price">${item.price.toLocaleString()}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </main>
        </div>
    );
}

export default App;