<div align="center">

# 🏠 YoungHill Family Bot

**Многофункциональный Discord-бот для управления семьёй**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.4+-7289DA?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)](https://github.com/zaca14325/Fam_bot)

---

</div>

## 📋 Описание

Бот автоматизирует управление Discord-семьёй: отображает состав, обрабатывает заявки, ведёт статистику и логирует активность.

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 👥 **Состав семьи** | Автоматическое отображение участников по ролям |
| 🪖 **Рекруты** | Персональные инвайт-ссылки со счётчиком приглашённых |
| 📝 **Заявки в семью** | Многоступенчатая форма с анкетой и скриншотами |
| 🎂 **Дни рождения** | Плашка с напоминаниями и поздравлениями |
| ⚙️ **Панель управления** | Кнопки для собраний и объявления |
| 📊 **Статистика** | Таблица лидеров по сообщениям и голосовому времени |
| ⏰ **Расписание** | Планирование сообщений с повторением |
| 🗳️ **Опросы** | Создание опросов с реакциями |
| 📢 **Уведомления** | Автоматические приветствия и логирование |

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/zaca14325/Fam_bot.git
cd Fam_bot
```

### 2. Установите зависимости

```bash
pip install -r requirements.txt
```

### 3. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните значениями:

```bash
cp .env.example .env
```

### 4. Запустите бота

```bash
python bot.py
```

## ⚙️ Переменные окружения

| Переменная | Описание | Обязательна |
|------------|----------|-------------|
| `BOT_TOKEN` | Токен бота из Developer Portal | ✅ |
| `CLIENT_ID` | ID приложения Discord | ✅ |
| `GUILD_ID` | ID сервера | ✅ |
| `TARGET_CHANNEL_ID` | Канал состава семьи | ✅ |
| `RECRUIT_BOARD_CHANNEL_ID` | Канал плашки рекрутов | ❌ |
| `RECRUIT_REPORT_CHANNEL_ID` | Канал отчётов рекрутов | ❌ |
| `BIRTHDAY_BOARD_CHANNEL_ID` | Канал дней рождения | ❌ |
| `LOG_CHANNEL_ID` | Канал логов | ❌ |
| `ADMIN_PANEL_CHANNEL_ID` | Канал панели управления | ❌ |

## 🎮 Команды

| Команда | Описание | Права |
|---------|----------|-------|
| `/family` | Обновить таблицу состава | — |
| `/recruit` | Показать инвайт-ссылку | Рекрут |
| `/report_invite` | Отчёт по приглашённому | Рекрут |
| `/recruits` | Обновить плашку рекрутов | Manage Server |
| `/birthday` | Добавить день рождения | — |
| `/admin_panel` | Обновить панель управления | Manage Server |
| `/clear N` | Удалить N сообщений | Manage Messages |
| `/poll "вопрос" "варианты"` | Создать опрос | — |
| `/schedule "текст" 30m` | Запланировать сообщение | Manage Server |
| `/stats` | Показать статистику | — |

## 📦 Деплой

### Railway (рекомендуется)

1. Зайдите на [railway.app](https://railway.app)
2. Подключите GitHub-репозиторий
3. Добавьте переменные окружения
4. Нажмите **Deploy**

### Render

1. Зайдите на [render.com](https://render.com)
2. Создайте **Background Worker**
3. Подключите репозиторий
4. Настройте Build/Start команды
5. Добавьте переменные окружения

## 📁 Структура проекта

```
Fam_bot/
├── bot.py              # Основной файл бота
├── requirements.txt    # Зависимости
├── .env.example        # Пример переменных окружения
├── .gitignore          # Игнорируемые файлы
└── README.md           # Этот файл
```

## 🤝 Участие

1. Fork проект
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Коммитьте изменения (`git commit -m 'Add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Проект лицензирован по MIT — смотрите файл [LICENSE](LICENSE) для подробностей.

## 📞 Контакты

- **Discord**: zaca14325
- **GitHub**: [@zaca14325](https://github.com/zaca14325)

---

<div align="center">

**Сделано с ❤️ для семьи YoungHill**

</div>
