# Python Family Bot

Это Python-версия бота на discord.py.

## Что умеет

- показывает состав семьи по ролям в нужном порядке
- у YoungHill выводит только количество участников
- ставит кнопку Обновить
- обновляет сообщение автоматически каждые 5 минут
- ведёт отдельную плашку рекрутов
- создаёт каждому рекруту одну вечную персональную ссылку
- считает людей, которые зашли по ссылке рекрута
- даёт рекрутам форму отчёта: имя фамилия и номер паспорта приглашённого
- ведёт отдельную плашку дней рождения с кнопкой для добавления даты
- система заявок в рекруты (форма + кнопки принять/отклонить + автоматическая выдача роли)
- система заявок в семью (форма + кнопки принять/отклонить + автоматическая выдача ролей Young Junior и YoungHill)

## Настройка

Заполните .env:

```env
BOT_TOKEN=your_bot_token_here
CLIENT_ID=your_application_client_id_here
GUILD_ID=1342073127668289578
TARGET_CHANNEL_ID=1521295122204201163
RECRUIT_BOARD_CHANNEL_ID=1518656998902730853
INVITE_CHANNEL_ID=1518656998902730853
RECRUIT_REPORT_CHANNEL_ID=1518190906749095946
BIRTHDAY_BOARD_CHANNEL_ID=put_birthday_channel_id_here
LOG_CHANNEL_ID=put_log_channel_id_here
RECRUIT_APP_BANNER_CHANNEL_ID=put_recruit_app_banner_channel_id_here
RECRUIT_APP_LIST_CHANNEL_ID=put_recruit_app_list_channel_id_here
ADMIN_PANEL_CHANNEL_ID=put_admin_panel_channel_id_here
MEETING_ROLE_ID=put_meeting_role_id_here
MEETING_VOICE_CHANNEL_ID=put_meeting_voice_channel_id_here
```

RECRUIT_BOARD_CHANNEL_ID это канал, где будет отдельная плашка рекрутов.
INVITE_CHANNEL_ID это канал, на который будут вести личные ссылки рекрутов.
RECRUIT_REPORT_CHANNEL_ID это канал, куда рекруты отправляют отчёты по приглашённым людям.
BIRTHDAY_BOARD_CHANNEL_ID это канал, где будет список дней рождения.
LOG_CHANNEL_ID это канал, куда бот будет отправлять логи всех действий (команды, кнопки, входы, ошибки).
RECRUIT_APP_BANNER_CHANNEL_ID это канал с баннером и кнопкой подачи заявки в рекруты.
RECRUIT_APP_LIST_CHANNEL_ID это канал, куда публикуются все поданные заявки.
ADMIN_PANEL_CHANNEL_ID это канал панели управления (кнопка «На собрание»).
MEETING_ROLE_ID это ID роли участников, которых нужно переместить на собрание.
MEETING_VOICE_CHANNEL_ID это ID голосового канала, куда перемещаются участники.

## Установка

```bash
pip install -r requirements.txt
python bot.py
```

## Команды

- /family обновляет таблицу состава семьи
- /recruit показывает рекруту его личную ссылку и счётчик
- /report_invite открывает форму отчёта по приглашённому человеку
- /recruits обновляет отдельную плашку рекрутов, доступно тем, у кого есть Manage Server
- /birthday открывает форму для добавления дня рождения
- /admin_panel обновляет панель управления, доступно тем, у кого есть Manage Server
- /clear N удалить N сообщений из канала (1-100), требует Manage Messages
- /poll "вопрос" "вариант1,вариант2" создать опрос с реакциями
- /schedule "текст" 30m запланировать через 30 минут (поддержка: 30m/2h/3d/1w/15.07.2026 18:00)
- /schedule "текст" 3d daily повторять ежедневно (none/daily/weekly/monthly)
- /schedules показать все запланированные сообщения
- /schedule_cancel N отменить запланированное сообщение по номеру
- /rules показать правила сервера
- /setrules "правило1;правило2" установить правила через точку с запятой
- /stats показать статистику сервера

## Права бота

Для состава семьи нужны Server Members Intent и доступ к участникам.
Для рекрутов нужны права Create Invite и Manage Server, чтобы бот мог создавать ссылки и видеть, какая ссылка была использована.
Для формы отчёта нужны Send Messages и Embed Links в канале отчётов.
Для дня рождения нужны Send Messages и Embed Links в канале дней рождения.
Для заявок в рекруты нужны Send Messages, Embed Links, Manage Roles в каналах заявок, а также права Manage Roles для бота.
Для панели управления нужны Send Messages, Embed Links, Move Members (для перемещения в голосовые каналы).
Для очистки каналов нужны Manage Messages.
Для опросов и запланированных сообщений нужны Manage Server.
Анти-рейд работает автоматически — уведомляет админов при подозрительных входах.
