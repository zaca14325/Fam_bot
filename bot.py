import asyncio
import json
import os
import re
import time
import uuid
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class RoleInfo:
    label: str
    role_id: int
    emoji: str
    count_only: bool = False

ROLE_ORDER = [
    RoleInfo('Owner', 1342073308023099413, '👑'),
    RoleInfo('Dep.Leader', 1363988534356344872, '✨'),
    RoleInfo('Рекрут', 1518186204493906060, '🪖'),
    RoleInfo('YoungMentor', 1509889918200053880, '🌟'),
    RoleInfo('YoungWarrior', 1509888639973326899, '⚔️'),
    RoleInfo('YoungHooligan', 1509888026397114499, '🔥'),
    RoleInfo('Young Junior', 1509909783527030784, '⭐'),
    RoleInfo('YoungHill', 1509884678839079033, '🌿', True),
]

RECRUIT_ROLE_ID = 1518186204493906060
THUMBNAIL_URL = 'https://media.discordapp.net/attachments/1509878666782445678/1517471349679849603/file_00000000f4a8722fafeb213d214c0763_4.png?ex=6a443e93&is=6a42ed13&hm=0c9589eead2a223a954137051b31fb35949d7c69dc49cbb934419c963c55cc66&=&format=webp&quality=lossless&width=864&height=864'
MAIN_IMAGE_URL = 'https://cdn.discordapp.com/attachments/1346126083363307651/1346128287000297563/YOUNGHILL-03-03-2025.gif?ex=6a43d3a9&is=6a428229&hm=8f89a624939d58b8ac6505a6bb4c5ee1b3430fae2e9b99e5bd0333a54ccf306c&'
WELCOME_IMAGE_URL = 'https://cdn.discordapp.com/attachments/1342073128112623666/1520871241353793608/welcome.png?ex=6a456838&is=6a4416b8&hm=07c5a8cf2126711faa146c83bdf3e11e7abf207939280eeb6ec9f9b743721301&'
STATE_FILE = Path(__file__).with_name('board-state.json')
RECRUIT_STATE_FILE = Path(__file__).with_name('recruit-state.json')
REPORT_BUTTON_STATE_FILE = Path(__file__).with_name('report-button-state.json')
BIRTHDAY_STATE_FILE = Path(__file__).with_name('birthday-state.json')
AUTOMOD_STATE_FILE = Path(__file__).with_name('automod-state.json')
APP_STATE_FILE = Path(__file__).with_name('app-state.json')
RECRUIT_APP_STATE_FILE = Path(__file__).with_name('recruit-app-state.json')
STATS_STATE_FILE = Path(__file__).with_name('stats-state.json')
REMINDERS_STATE_FILE = Path(__file__).with_name('reminders-state.json')
ADMIN_PANEL_CHANNEL_ID = int(os.getenv('ADMIN_PANEL_CHANNEL_ID', '1523819460538925086'))
MEETING_ROLE_ID = int(os.getenv('MEETING_ROLE_ID', '1509884678839079033'))
MEETING_VOICE_CHANNEL_ID = int(os.getenv('MEETING_VOICE_CHANNEL_ID', '1342078486419869762'))
AUTO_REFRESH_SECONDS = 5 * 60
REFRESH_BUTTON_ID = 'family_refresh'
CREATE_RECRUIT_INVITE_BUTTON_ID = 'recruit_create_invite'
REFRESH_RECRUIT_BOARD_BUTTON_ID = 'recruit_refresh_board'
REPORT_RECRUIT_INVITE_BUTTON_ID = 'recruit_report_invite'
BIRTHDAY_SUBMIT_BUTTON_ID = 'birthday_submit'
RECRUIT_APP_BUTTON_ID = 'recruit_app_submit'
ADMIN_MEETING_BUTTON_ID = 'admin_meeting_button'
ADMIN_MEETING_SMS_BUTTON_ID = 'admin_meeting_sms'
ADMIN_REMIND_1H_BUTTON_ID = 'admin_remind_1h'
ANNOUNCEMENT_BUTTON_ID = 'admin_announcement'
LEADERBOARD_PREV_BUTTON_ID = 'leaderboard_prev'
LEADERBOARD_NEXT_BUTTON_ID = 'leaderboard_next'

BOT_TOKEN = os.getenv('BOT_TOKEN')
CLIENT_ID = os.getenv('CLIENT_ID')
GUILD_ID = os.getenv('GUILD_ID')
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID', '1521295122204201163'))
RECRUIT_BOARD_CHANNEL_ID = int(os.getenv('RECRUIT_BOARD_CHANNEL_ID', str(TARGET_CHANNEL_ID)))
INVITE_CHANNEL_ID = int(os.getenv('INVITE_CHANNEL_ID', str(TARGET_CHANNEL_ID)))
RECRUIT_REPORT_CHANNEL_ID = int(os.getenv('RECRUIT_REPORT_CHANNEL_ID', '1518190906749095946'))
BIRTHDAY_BOARD_CHANNEL_ID = int(os.getenv('BIRTHDAY_BOARD_CHANNEL_ID', '0'))
BIRTHDAY_GREETING_CHANNEL_ID = int(os.getenv('BIRTHDAY_GREETING_CHANNEL_ID', '0'))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '1342073128112623666'))
AUTOMOD_CHANNEL_ID = int(os.getenv('AUTOMOD_CHANNEL_ID', '0'))
APP_CREATE_CHANNEL_ID = int(os.getenv('APP_CREATE_CHANNEL_ID', '0'))
APP_LOG_CHANNEL_ID = int(os.getenv('APP_LOG_CHANNEL_ID', '0'))
APP_CATEGORY_ID = int(os.getenv('APP_CATEGORY_ID', '0'))
RECRUIT_APP_BANNER_CHANNEL_ID = int(os.getenv('RECRUIT_APP_BANNER_CHANNEL_ID', '0'))
RECRUIT_APP_LIST_CHANNEL_ID = int(os.getenv('RECRUIT_APP_LIST_CHANNEL_ID', '0'))

if not BOT_TOKEN:
    raise SystemExit('Please set BOT_TOKEN in your .env file.')

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

class RefreshView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label='Обновить', style=discord.ButtonStyle.primary, emoji='🔄', custom_id=REFRESH_BUTTON_ID)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message('Обновляю баннер...', ephemeral=True)
        asyncio.create_task(send_log('🔄 Обновление состава', f'{interaction.user.mention} нажал кнопку **Обновить** (состав семьи)', color=0x3B82F6, user=interaction.user))
        asyncio.create_task(refresh_board_safely())



class RecruitReportModal(discord.ui.Modal, title='Отписать приглашённого'):
    full_name = discord.ui.TextInput(
        label='Имя Фамилия',
        placeholder='Например: Иван Иванов',
        max_length=80,
    )
    passport_number = discord.ui.TextInput(
        label='Номер паспорта',
        placeholder='Например: 123456',
        max_length=40,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member) or not has_recruit_role(interaction.user):
            await interaction.response.send_message('Эта форма доступна только рекрутам.', ephemeral=True)
            return

        channel = await get_text_channel(RECRUIT_REPORT_CHANNEL_ID)
        embed = discord.Embed(
            title='📝 Новый отчёт рекрута',
            color=0x38BDF8,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name='Рекрут', value=format_member(interaction.user), inline=False)
        embed.add_field(name='Имя Фамилия', value=str(self.full_name), inline=True)
        embed.add_field(name='Номер паспорта', value=str(self.passport_number), inline=True)
        embed.set_thumbnail(url=THUMBNAIL_URL)

        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        await interaction.response.send_message('Отчёт отправлен.', ephemeral=True)
        asyncio.create_task(send_log(
            '📝 Новый отчёт рекрута',
            f'{interaction.user.mention} отправил отчёт\n'
            f'**Имя Фамилия:** {self.full_name}\n'
            f'**Паспорт:** {self.passport_number}',
            color=0x38BDF8, user=interaction.user,
        ))


class BirthdayModal(discord.ui.Modal, title='Добавить день рождения'):
    birthday_date = discord.ui.TextInput(
        label='Дата рождения',
        placeholder='01.01.2007 или 01.01',
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта форма работает только на сервере.', ephemeral=True)
            return

        parsed = parse_birthday_text(str(self.birthday_date))
        if parsed is None:
            await interaction.response.send_message('Не понял дату. Используй формат DD.MM.YYYY или DD.MM.', ephemeral=True)
            return

        async with bot.birthday_lock:
            state = read_birthday_state()
            state['entries'][str(interaction.user.id)] = {
                'day': parsed['day'],
                'month': parsed['month'],
                'year': parsed.get('year'),
                'text': parsed['text'],
                'updated_at': discord.utils.utcnow().isoformat(),
            }
            write_birthday_state(state)

        await refresh_birthday_board_safely()
        await interaction.response.send_message('Дата сохранена.', ephemeral=True)
        asyncio.create_task(send_log(
            '🎂 День рождения добавлен',
            f'{interaction.user.mention} установил дату: **{parsed["text"]}**',
            color=0xF97316, user=interaction.user,
        ))


class BirthdayButtonView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label='Добавить дату', style=discord.ButtonStyle.primary, emoji='🎂', custom_id=BIRTHDAY_SUBMIT_BUTTON_ID)
    async def add_birthday_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(BirthdayModal())

class RecruitReportButtonView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label='Отписать приглашённого', style=discord.ButtonStyle.primary, emoji='📝', custom_id=REPORT_RECRUIT_INVITE_BUTTON_ID)
    async def report_invite_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not isinstance(interaction.user, discord.Member) or not has_recruit_role(interaction.user):
            await interaction.response.send_message('Эта кнопка доступна только рекрутам.', ephemeral=True)
            return
        await interaction.response.send_modal(RecruitReportModal())

class RecruitView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(label='Создать ссылку', style=discord.ButtonStyle.success, emoji='🔗', custom_id=CREATE_RECRUIT_INVITE_BUTTON_ID)
    async def create_invite_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта кнопка работает только на сервере.', ephemeral=True)
            return
        if not has_recruit_role(interaction.user):
            await interaction.response.send_message('Эта кнопка доступна только рекрутам.', ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            record = await create_or_get_recruit_invite(interaction.user)
            await refresh_recruit_board_safely()
            await interaction.followup.send(
                f'Твоя личная ссылка уже закреплена за тобой:\n{record["invite_url"]}',
                ephemeral=True,
            )
            asyncio.create_task(send_log(
                '🔗 Ссылка рекрута',
                f'{interaction.user.mention} получил ссылку (кнопка)\n{record["invite_url"]}',
                color=0x22C55E, user=interaction.user,
            ))
        except Exception as exc:
            await interaction.followup.send(f'Не смог создать ссылку: {exc}', ephemeral=True)
            asyncio.create_task(send_log(
                '❌ Ошибка создания ссылки',
                f'{interaction.user.mention} — не удалось создать ссылку\n```{exc}```',
                color=0xEF4444, user=interaction.user,
            ))

    @discord.ui.button(label='Обновить', style=discord.ButtonStyle.secondary, emoji='🔄', custom_id=REFRESH_RECRUIT_BOARD_BUTTON_ID)
    async def refresh_recruit_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_message('Обновляю плашку рекрутов...', ephemeral=True)
        asyncio.create_task(send_log('🔄 Обновление рекрутов', f'{interaction.user.mention} нажал кнопку **Обновить** (рекруты)', color=0x3B82F6, user=interaction.user))
        asyncio.create_task(refresh_recruit_board_safely())

# --------------- Автомодерация (Dyno-style) ---------------

class AutomodSpamModal(discord.ui.Modal, title='⚙️ Анти-Спам'):
    spam_m = discord.ui.TextInput(label='Макс. сообщений', placeholder='5')
    spam_s = discord.ui.TextInput(label='За сколько секунд', placeholder='5')
    async def on_submit(self, interaction: discord.Interaction):
        try:
            sm, ss = int(self.spam_m.value), int(self.spam_s.value)
        except ValueError:
            await interaction.response.send_message('Нужно ввести числа.', ephemeral=True)
            return
        async with bot.automod_lock:
            state = read_automod_state()
            state['modules']['spam']['limit'] = sm
            state['modules']['spam']['interval'] = ss
            write_automod_state(state)
        await interaction.response.send_message('✅ Настройки спама сохранены!', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())

class AutomodImageModal(discord.ui.Modal, title='⚙️ Анти-Картинки'):
    img_m = discord.ui.TextInput(label='Макс. вложений', placeholder='3')
    img_s = discord.ui.TextInput(label='За сколько секунд', placeholder='10')
    async def on_submit(self, interaction: discord.Interaction):
        try:
            im, is_ = int(self.img_m.value), int(self.img_s.value)
        except ValueError:
            await interaction.response.send_message('Нужно ввести числа.', ephemeral=True)
            return
        async with bot.automod_lock:
            state = read_automod_state()
            state['modules']['images']['limit'] = im
            state['modules']['images']['interval'] = is_
            write_automod_state(state)
        await interaction.response.send_message('✅ Настройки картинок сохранены!', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())

class AutomodContentModal(discord.ui.Modal, title='⚙️ Контент'):
    emojis = discord.ui.TextInput(label='Макс. эмодзи в сообщении', placeholder='5')
    mentions = discord.ui.TextInput(label='Макс. упоминаний', placeholder='3')
    caps = discord.ui.TextInput(label='Макс. % заглавных букв', placeholder='70')
    async def on_submit(self, interaction: discord.Interaction):
        try:
            em, mn, cp = int(self.emojis.value), int(self.mentions.value), int(self.caps.value)
        except ValueError:
            await interaction.response.send_message('Нужно ввести числа.', ephemeral=True)
            return
        async with bot.automod_lock:
            state = read_automod_state()
            state['modules']['emoji']['limit'] = em
            state['modules']['mentions']['limit'] = mn
            state['modules']['caps']['percent'] = cp
            write_automod_state(state)
        await interaction.response.send_message('✅ Настройки контента сохранены!', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())

class AutomodBadwordsModal(discord.ui.Modal, title='⚙️ Анти-Мат'):
    words = discord.ui.TextInput(label='Слова через запятую', style=discord.TextStyle.paragraph, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        w_list = sorted(set(w.strip().lower() for w in self.words.value.split(',') if w.strip()))
        async with bot.automod_lock:
            state = read_automod_state()
            state['modules']['badwords']['words'] = w_list
            write_automod_state(state)
        await interaction.response.send_message(f'✅ Сохранено слов: **{len(w_list)}**', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())

class AutomodPunishModal(discord.ui.Modal, title='⚖️ Система наказаний'):
    w1 = discord.ui.TextInput(label='1-е нарушение', placeholder='warn')
    w2 = discord.ui.TextInput(label='2-е нарушение', placeholder='mute')
    w3 = discord.ui.TextInput(label='3-е нарушение', placeholder='kick')
    w4 = discord.ui.TextInput(label='4-е нарушение', placeholder='ban')
    mute_min = discord.ui.TextInput(label='Мут (минут)', placeholder='10')
    async def on_submit(self, interaction: discord.Interaction):
        valid = {'warn', 'mute', 'kick', 'ban', 'none'}
        actions = []
        for field in [self.w1, self.w2, self.w3, self.w4]:
            v = field.value.strip().lower()
            if v not in valid:
                await interaction.response.send_message(f'Недопустимое действие: `{v}`. Допустимые: warn, mute, kick, ban, none', ephemeral=True)
                return
            actions.append(v)
        try:
            mute = int(self.mute_min.value)
        except ValueError:
            await interaction.response.send_message('Длительность мута — число.', ephemeral=True)
            return
        async with bot.automod_lock:
            state = read_automod_state()
            state['punishment']['actions'] = actions
            state['punishment']['mute_minutes'] = mute
            write_automod_state(state)
        await interaction.response.send_message('✅ Наказания сохранены!', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())

class AutomodWordsModal(discord.ui.Modal, title='⚙️ Исключения'):
    whitelist_channels = discord.ui.TextInput(label='ID каналов через запятую', style=discord.TextStyle.paragraph, required=False)
    exempt_roles = discord.ui.TextInput(label='ID ролей через запятую', style=discord.TextStyle.paragraph, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        channels = [int(x.strip()) for x in self.whitelist_channels.value.split(',') if x.strip().isdigit()]
        roles = [int(x.strip()) for x in self.exempt_roles.value.split(',') if x.strip().isdigit()]
        async with bot.automod_lock:
            state = read_automod_state()
            state['whitelist_channels'] = channels
            state['exempt_roles'] = roles
            write_automod_state(state)
        await interaction.response.send_message('✅ Исключения сохранены!', ephemeral=True)
        asyncio.create_task(refresh_automod_board_safely())


class AutomodConfigView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # --- Строка 0: Тоглы ---
    @discord.ui.button(label='🔴 Спам', style=discord.ButtonStyle.secondary, custom_id='am_tog_spam', row=0)
    async def toggle_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'spam', button, 'Спам')

    @discord.ui.button(label='🔴 Мат', style=discord.ButtonStyle.secondary, custom_id='am_tog_bw', row=0)
    async def toggle_badwords(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'badwords', button, 'Мат')

    @discord.ui.button(label='🔴 Инвайты', style=discord.ButtonStyle.secondary, custom_id='am_tog_inv', row=0)
    async def toggle_invites(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'invites', button, 'Инвайты')

    @discord.ui.button(label='🔴 Эмодзи', style=discord.ButtonStyle.secondary, custom_id='am_tog_emo', row=0)
    async def toggle_emojis(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'emoji', button, 'Эмодзи')

    @discord.ui.button(label='🔴 Пинги', style=discord.ButtonStyle.secondary, custom_id='am_tog_men', row=0)
    async def toggle_mentions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'mentions', button, 'Пинги')

    # --- Строка 1: Тоглы ---
    @discord.ui.button(label='🔴 Картинки', style=discord.ButtonStyle.secondary, custom_id='am_tog_img', row=1)
    async def toggle_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'images', button, 'Картинки')

    @discord.ui.button(label='🔴 Caps', style=discord.ButtonStyle.secondary, custom_id='am_tog_caps', row=1)
    async def toggle_caps(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._toggle(interaction, 'caps', button, 'Caps')

    # --- Строка 2: Настройки ---
    @discord.ui.button(label='⚙️ Спам', style=discord.ButtonStyle.primary, custom_id='am_cfg_spam', row=2)
    async def config_spam(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodSpamModal()
        m.spam_m.default = str(state['modules']['spam']['limit'])
        m.spam_s.default = str(state['modules']['spam']['interval'])
        await interaction.response.send_modal(m)

    @discord.ui.button(label='⚙️ Картинки', style=discord.ButtonStyle.primary, custom_id='am_cfg_img', row=2)
    async def config_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodImageModal()
        m.img_m.default = str(state['modules']['images']['limit'])
        m.img_s.default = str(state['modules']['images']['interval'])
        await interaction.response.send_modal(m)

    @discord.ui.button(label='⚙️ Контент', style=discord.ButtonStyle.primary, custom_id='am_cfg_cnt', row=2)
    async def config_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodContentModal()
        m.emojis.default = str(state['modules']['emoji']['limit'])
        m.mentions.default = str(state['modules']['mentions']['limit'])
        m.caps.default = str(state['modules']['caps']['percent'])
        await interaction.response.send_modal(m)

    @discord.ui.button(label='⚙️ Мат', style=discord.ButtonStyle.primary, custom_id='am_cfg_bw', row=2)
    async def config_badwords(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodBadwordsModal()
        m.words.default = ', '.join(state['modules']['badwords']['words'])
        await interaction.response.send_modal(m)

    # --- Строка 3: Наказания + Исключения ---
    @discord.ui.button(label='⚖️ Наказания', style=discord.ButtonStyle.danger, custom_id='am_cfg_punish', row=3)
    async def config_punishment(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodPunishModal()
        actions = state['punishment']['actions']
        m.w1.default = actions[0] if len(actions) > 0 else 'warn'
        m.w2.default = actions[1] if len(actions) > 1 else 'mute'
        m.w3.default = actions[2] if len(actions) > 2 else 'kick'
        m.w4.default = actions[3] if len(actions) > 3 else 'ban'
        m.mute_min.default = str(state['punishment']['mute_minutes'])
        await interaction.response.send_modal(m)

    @discord.ui.button(label='🛡️ Исключения', style=discord.ButtonStyle.secondary, custom_id='am_cfg_whitelist', row=3)
    async def config_whitelist(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = read_automod_state()
        m = AutomodWordsModal()
        m.whitelist_channels.default = ', '.join(str(x) for x in state.get('whitelist_channels', []))
        m.exempt_roles.default = ', '.join(str(x) for x in state.get('exempt_roles', []))
        await interaction.response.send_modal(m)

    async def _toggle(self, interaction: discord.Interaction, key: str, button: discord.ui.Button, label: str):
        async with bot.automod_lock:
            state = read_automod_state()
            state['modules'][key]['enabled'] = not state['modules'][key]['enabled']
            write_automod_state(state)
        is_on = state['modules'][key]['enabled']
        button.label = f'{"🟢" if is_on else "🔴"} {label}'
        button.style = discord.ButtonStyle.success if is_on else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)
        asyncio.create_task(refresh_automod_board_safely())

# --------------- Заявка в семью (тикеты + кнопки решения) ---------------

YOUNG_JUNIOR_ROLE_ID = 1509909783527030784
YOUNGHILL_ROLE_ID = 1509884678839079033
GUEST_ROLE_ID = 1504073438929883157

# Хранилище собранных данных заявки по user_id
family_applications: dict[int, dict] = {}


class FamilyAppDecisionView(discord.ui.View):
    """Кнопки Принять/Отклонить на финальной заявке (как у рекрутов)."""
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    def _is_recruit_or_above(self, member: discord.Member) -> bool:
        recruit_role = member.guild.get_role(RECRUIT_ROLE_ID)
        if recruit_role is None:
            return False
        return member.top_role.position >= recruit_role.position

    @discord.ui.button(label='✅ Принять', style=discord.ButtonStyle.success, emoji='✅', custom_id='family_app_accept')
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not self._is_recruit_or_above(interaction.user):
            await interaction.response.send_message('У тебя нет прав принимать заявки.', ephemeral=True)
            return

        await interaction.response.defer()

        guild = interaction.guild
        applicant = guild.get_member(self.applicant_id)
        roles_to_add = [r for r in (guild.get_role(YOUNG_JUNIOR_ROLE_ID), guild.get_role(YOUNGHILL_ROLE_ID)) if r is not None]
        if applicant and roles_to_add:
            try:
                await applicant.add_roles(*roles_to_add, reason=f'Заявка принята {interaction.user}')
            except Exception:
                pass

        # Снимаем роль «Гость» при принятии
        guest_role = guild.get_role(GUEST_ROLE_ID)
        if applicant and guest_role and guest_role in applicant.roles:
            try:
                await applicant.remove_roles(guest_role, reason=f'Заявка принята {interaction.user}')
            except Exception:
                pass

        if applicant:
            try:
                await applicant.send('Ваша заявка была рассмотрена, Вас приняли в **семью**.\nПоздравляем! 🎉')
            except Exception:
                pass

        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            new_embed = embed.copy()
            new_embed.color = 0x10B981
            new_embed.set_footer(text=f'✅ Принята — {interaction.user.display_name}')
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=new_embed, view=self)

        asyncio.create_task(send_log(
            '✅ Заявка в семью принята',
            fields=[
                ('Участник', f'<@{self.applicant_id}> (`{self.applicant_id}`)', True),
                ('Рассмотрел', _log_user_field(interaction.user), True),
            ],
            color=0x10B981, user=interaction.user,
        ))

    @discord.ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger, emoji='❌', custom_id='family_app_reject')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not self._is_recruit_or_above(interaction.user):
            await interaction.response.send_message('У тебя нет прав отклонять заявки.', ephemeral=True)
            return

        await interaction.response.defer()

        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant:
            try:
                await applicant.send('Ваша заявка была рассмотрена, **Отказано**.')
            except Exception:
                pass

        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            new_embed = embed.copy()
            new_embed.color = 0xEF4444
            new_embed.set_footer(text=f'❌ Отклонена — {interaction.user.display_name}')
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=new_embed, view=self)

        asyncio.create_task(send_log(
            '❌ Заявка в семью отклонена',
            fields=[
                ('Участник', f'<@{self.applicant_id}> (`{self.applicant_id}`)', True),
                ('Рассмотрел', _log_user_field(interaction.user), True),
            ],
            color=0xEF4444, user=interaction.user,
        ))

    @discord.ui.button(label='📞 Вызвать на связь', style=discord.ButtonStyle.primary, emoji='📞', custom_id='family_app_call')
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not self._is_recruit_or_above(interaction.user):
            await interaction.response.send_message('У тебя нет прав вызывать на связь.', ephemeral=True)
            return

        await interaction.response.defer()

        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant:
            try:
                await applicant.send(
                    'Ваша заявка была рассмотрена, ждём вас в войсе для собеседования.\nЖдём вас. 🎙️'
                )
                await interaction.followup.send(f'Сообщение отправлено {applicant.mention}', ephemeral=True)
            except Exception:
                await interaction.followup.send('Не удалось отправить сообщение (возможно, закрыты ЛС).', ephemeral=True)
        else:
            await interaction.followup.send('Участник не найден на сервере.', ephemeral=True)

        asyncio.create_task(send_log(
            '📞 Вызов на собеседование',
            fields=[
                ('Участник', f'<@{self.applicant_id}> (`{self.applicant_id}`)', True),
                ('Вызвал', _log_user_field(interaction.user), True),
            ],
            color=0x3B82F6, user=interaction.user,
        ))


class TicketAdminView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Закрыть тикет', style=discord.ButtonStyle.danger, custom_id='app_close_ticket', emoji='🔒')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message('У вас нет прав закрывать тикет.', ephemeral=True)
            return
        await interaction.response.send_message('Тикет будет удален через 5 секунд...')
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except Exception:
            pass


class TicketFinalStageView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label='Завершить заявку', style=discord.ButtonStyle.success, custom_id='app_stage_final', emoji='✅')
    async def finish_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        import io
        data = family_applications.get(self.applicant_id, {})

        # Собираем скриншоты из сообщений тикета (до 2 штук)
        attachments: list[discord.Attachment] = []
        try:
            async for msg in interaction.channel.history(limit=50, oldest_first=False):
                for att in msg.attachments:
                    if att.content_type and att.content_type.startswith('image'):
                        attachments.append(att)
                if len(attachments) >= 2:
                    break
        except Exception:
            pass

        await interaction.response.send_message(
            'Ваша заявка будет рассмотрена в течение от 1 часа до 1 дня.'
        )
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        # Строим итоговый embed с кнопками решения
        embed = discord.Embed(title='📋 Заявка в семью', color=0xF59E0B)
        embed.set_thumbnail(url=THUMBNAIL_URL)
        applicant = interaction.guild.get_member(self.applicant_id)
        embed.add_field(name='Участник', value=_log_user_field(applicant) if applicant else f'<@{self.applicant_id}>', inline=False)

        # Часть 1
        embed.add_field(name='Имя Фамилия', value=data.get('name', '—'), inline=True)
        embed.add_field(name='Уровень', value=data.get('level', '—'), inline=True)
        embed.add_field(name='Возраст (ООС)', value=data.get('age', '—'), inline=True)
        embed.add_field(name='Почему к нам', value=data.get('why', '—'), inline=False)
        embed.add_field(name='Знания РП', value=data.get('rp', '—'), inline=True)

        # Часть 2
        embed.add_field(name='Смена фамилии', value=data.get('surname', '—'), inline=True)
        embed.add_field(name='Правила', value=data.get('rules', '—'), inline=True)
        embed.add_field(name='Прайм тайм', value=data.get('prime', '—'), inline=True)

        embed.add_field(name='Скриншоты', value=f'прикреплены к сообщению ({len(attachments)} шт.)' if attachments else 'не прикреплены', inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text='Ожидает рассмотрения')

        # Постим в канал заявок: embed + кнопки + файлы скриншотов
        if APP_LOG_CHANNEL_ID:
            try:
                log_channel = bot.get_channel(APP_LOG_CHANNEL_ID)
                if log_channel is None:
                    log_channel = await bot.fetch_channel(APP_LOG_CHANNEL_ID)
                if isinstance(log_channel, discord.TextChannel):
                    files: list[discord.File] = []
                    for att in attachments:
                        try:
                            fp = await att.to_file()
                            files.append(fp)
                        except Exception as exc:
                            print(f'Failed to download attachment: {exc}')

                    if files:
                        # Картинка в embed — первая, чтобы был превью
                        embed.set_image(url=f'attachment://{files[0].filename}')
                        await log_channel.send(embed=embed, view=FamilyAppDecisionView(self.applicant_id), files=files)
                    else:
                        await log_channel.send(embed=embed, view=FamilyAppDecisionView(self.applicant_id))
            except Exception as exc:
                print(f'Failed to post family app decision: {exc}')

        await interaction.channel.send(
            embed=discord.Embed(description='⏳ Тикет будет автоматически удалён через **5 минут**.', color=0xF59E0B),
        )
        await interaction.channel.send(
            embed=discord.Embed(description='Панель управления тикетом (только для администрации):', color=0x374151),
            view=TicketAdminView()
        )

        # Чистим хранилище
        family_applications.pop(self.applicant_id, None)

        asyncio.create_task(send_log(
            '📋 Заявка в семью подана',
            fields=[
                ('Участник', _log_user_field(applicant) if applicant else f'<@{self.applicant_id}>', True),
                ('Тикет', f'[перейти]({interaction.channel.jump_url})', True),
            ],
            color=0xF59E0B, user=applicant,
        ))

        # Автоудаление тикета через 5 минут
        ticket_channel = interaction.channel
        asyncio.create_task(_delete_ticket_after(ticket_channel, 5 * 60))


async def _delete_ticket_after(channel: discord.abc.GuildChannel, delay: int) -> None:
    """Удаляет тикет через delay секунд, предупреждая в чате."""
    try:
        await asyncio.sleep(delay)
        await channel.send(embed=discord.Embed(description='🗑️ Удаление тикета...', color=0xEF4444))
        await asyncio.sleep(3)
        await channel.delete(reason='Автоудаление после завершения заявки')
    except (discord.NotFound, discord.Forbidden):
        pass
    except Exception as exc:
        print(f'Ticket auto-delete failed: {exc}')


class AppModalPartTwo(discord.ui.Modal, title='Заявка: Часть 2'):
    q1 = discord.ui.TextInput(label='Готовы сменить фамилию на YoungHill?', placeholder='Да/Нет', style=discord.TextStyle.short)
    q2 = discord.ui.TextInput(label='Готовы соблюдать правила семьи?', placeholder='Да/Нет', style=discord.TextStyle.short)
    q3 = discord.ui.TextInput(label='Прайм тайм (1. вечер, 2. день, 3. всегда)', placeholder='Например: 1', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        # Сохраняем ответы
        family_applications.setdefault(interaction.user.id, {})
        family_applications[interaction.user.id].update({
            'surname': self.q1.value,
            'rules': self.q2.value,
            'prime': self.q3.value,
        })

        embed = discord.Embed(title='Ответы (Часть 2)', color=0x3B82F6)
        embed.add_field(name='Смена фамилии:', value=self.q1.value, inline=False)
        embed.add_field(name='Соблюдение правил:', value=self.q2.value, inline=False)
        embed.add_field(name='Прайм тайм:', value=self.q3.value, inline=False)
        await interaction.response.send_message(embed=embed)

        await interaction.channel.send(
            f"{interaction.user.mention}, отлично! Теперь **прикрепите в этот чат два скриншота**:\n"
            f"1. Скриншот вашего паспорта в игре.\n"
            f"2. Скриншот меню персонажа F10.\n\n"
            f"После отправки скриншотов нажмите кнопку ниже:",
            view=TicketFinalStageView(interaction.user.id)
        )


class TicketStageTwoView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label='Заполнить Часть 2', style=discord.ButtonStyle.primary, custom_id='app_stage_two', emoji='📝')
    async def next_stage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppModalPartTwo())
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)


class AppModalPartOne(discord.ui.Modal, title='Заявка: Часть 1'):
    q1 = discord.ui.TextInput(label='Имя Фамилия (IC)', placeholder='Иван Иванов', style=discord.TextStyle.short)
    q2 = discord.ui.TextInput(label='Уровень в игре', placeholder='Например: 15', style=discord.TextStyle.short)
    q3 = discord.ui.TextInput(label='Ваш реальный возраст (ООС)', placeholder='Например: 20', style=discord.TextStyle.short)
    q4 = discord.ui.TextInput(label='Как узнали о семье и почему к нам?', placeholder='Ваш ответ...', style=discord.TextStyle.paragraph)
    q5 = discord.ui.TextInput(label='Знания РП (от 0 до 10)', placeholder='Например: 8', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        # Сохраняем ответы
        family_applications[interaction.user.id] = {
            'name': self.q1.value,
            'level': self.q2.value,
            'age': self.q3.value,
            'why': self.q4.value,
            'rp': self.q5.value,
        }

        embed = discord.Embed(title='Ответы (Часть 1)', color=0x3B82F6)
        embed.add_field(name='Имя Фамилия:', value=self.q1.value, inline=False)
        embed.add_field(name='Уровень:', value=self.q2.value, inline=False)
        embed.add_field(name='Возраст:', value=self.q3.value, inline=False)
        embed.add_field(name='Почему к нам:', value=self.q4.value, inline=False)
        embed.add_field(name='Знания РП:', value=self.q5.value, inline=False)
        await interaction.response.send_message(embed=embed)

        await interaction.channel.send(
            'Отлично! Нажмите кнопку ниже, чтобы заполнить вторую часть:',
            view=TicketStageTwoView(interaction.user.id)
        )


class TicketStageOneView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label='Заполнить Часть 1', style=discord.ButtonStyle.primary, custom_id='app_stage_one', emoji='📝')
    async def next_stage(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AppModalPartOne())
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)


class ApplicationCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Подать заявку', style=discord.ButtonStyle.success, emoji='📝', custom_id='app_create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(APP_CATEGORY_ID) if APP_CATEGORY_ID else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        try:
            await interaction.response.defer(ephemeral=True)
            ticket_channel = await guild.create_text_channel(
                name=f'заявка-{interaction.user.name}',
                category=category,
                overwrites=overwrites
            )
        except Exception as exc:
            await interaction.followup.send(f'Ошибка создания тикета: {exc}', ephemeral=True)
            return

        await ticket_channel.send(
            f"Привет, {interaction.user.mention}! Добро пожаловать на собеседование.\n"
            f"Нажмите кнопку ниже, чтобы начать заполнение заявки.",
            view=TicketStageOneView(interaction.user.id)
        )

        await interaction.followup.send(f'Тикет создан! Перейдите в канал {ticket_channel.mention}', ephemeral=True)

# --------------- Заявка в рекруты ---------------

class RecruitAppModal(discord.ui.Modal, title='Заявка в рекруты'):
    full_name = discord.ui.TextInput(
        label='Имя Фамилия',
        placeholder='Например: Иван Иванов',
        max_length=80,
    )
    hours_online = discord.ui.TextInput(
        label='Сколько часов в онлайне?',
        placeholder='Например: 500',
        max_length=40,
    )
    previous_experience = discord.ui.TextInput(
        label='Принимали ли людей раньше?',
        placeholder='Да/Нет и кратко где',
        max_length=200,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта форма работает только на сервере.', ephemeral=True)
            return
        if has_recruit_role(interaction.user):
            await interaction.response.send_message('У тебя уже есть роль рекрута.', ephemeral=True)
            return

        await interaction.response.send_message('Заявка отправлена!', ephemeral=True)

        embed = discord.Embed(title='🪖 Заявка в рекруты', color=0x22C55E)
        embed.set_thumbnail(url=THUMBNAIL_URL)
        embed.add_field(name='Участник', value=_log_user_field(interaction.user), inline=True)
        embed.add_field(name='Имя Фамилия', value=str(self.full_name), inline=True)
        embed.add_field(name='Часов онлайн', value=str(self.hours_online), inline=True)
        embed.add_field(name='Опыт рекрутинга', value=str(self.previous_experience), inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text='Ожидает рассмотрения')

        if RECRUIT_APP_LIST_CHANNEL_ID:
            try:
                channel = bot.get_channel(RECRUIT_APP_LIST_CHANNEL_ID)
                if channel is None:
                    channel = await bot.fetch_channel(RECRUIT_APP_LIST_CHANNEL_ID)
                if isinstance(channel, discord.TextChannel):
                    msg = await channel.send(embed=embed, view=RecruitAppDecisionView(interaction.user.id))
                    # Сохраняем ID сообщения заявки
                    async with bot.recruit_app_lock:
                        state = read_recruit_app_state()
                        state['applications'][str(interaction.user.id)] = {
                            'message_id': msg.id,
                            'channel_id': channel.id,
                            'full_name': str(self.full_name),
                            'hours': str(self.hours_online),
                            'experience': str(self.previous_experience),
                            'submitted_at': discord.utils.utcnow().isoformat(),
                            'status': 'pending',
                        }
                        write_recruit_app_state(state)
            except Exception as exc:
                print(f'Failed to post recruit app: {exc}')

        asyncio.create_task(send_log(
            '🪖 Новая заявка в рекруты',
            fields=[
                ('Участник', _log_user_field(interaction.user), True),
                ('Имя Фамилия', str(self.full_name), True),
            ],
            color=0x22C55E, user=interaction.user,
        ))


class RecruitAppDecisionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    def _is_higher_role(self, member: discord.Member) -> bool:
        recruit_role = member.guild.get_role(RECRUIT_ROLE_ID)
        if recruit_role is None:
            return False
        return member.top_role.position > recruit_role.position

    @discord.ui.button(label='✅ Принять', style=discord.ButtonStyle.success, emoji='✅', custom_id='recruit_app_accept')
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not self._is_higher_role(interaction.user):
            await interaction.response.send_message('У тебя нет прав принимать заявки.', ephemeral=True)
            return

        await interaction.response.defer()

        # Обновляем state
        async with bot.recruit_app_lock:
            state = read_recruit_app_state()
            app = state['applications'].get(str(self.applicant_id))
            if app:
                app['status'] = 'accepted'
                app['reviewed_by'] = interaction.user.id
                app['reviewed_at'] = discord.utils.utcnow().isoformat()
                write_recruit_app_state(state)

        # Даём роль
        guild = interaction.guild
        recruit_role = guild.get_role(RECRUIT_ROLE_ID)
        applicant = guild.get_member(self.applicant_id)
        if applicant and recruit_role:
            try:
                await applicant.add_roles(recruit_role, reason=f'Заявка принята {interaction.user}')
            except Exception:
                pass

        # ДМ заявителю
        if applicant:
            try:
                await applicant.send(
                    'Ваша заявка была рассмотрена, Вас приняли на роль **Рекрута**.\nПоздравляем! 🎉'
                )
            except Exception:
                pass

        # Обновляем embed
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            new_embed = embed.copy()
            new_embed.color = 0x10B981
            new_embed.set_footer(text=f'✅ Принята — {interaction.user.display_name}')
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=new_embed, view=self)

        asyncio.create_task(send_log(
            '✅ Заявка в рекруты принята',
            fields=[
                ('Рекрут', f'<@{self.applicant_id}> (`{self.applicant_id}`)', True),
                ('Рассмотрел', _log_user_field(interaction.user), True),
            ],
            color=0x10B981, user=interaction.user,
        ))

    @discord.ui.button(label='❌ Отклонить', style=discord.ButtonStyle.danger, emoji='❌', custom_id='recruit_app_reject')
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member) or not self._is_higher_role(interaction.user):
            await interaction.response.send_message('У тебя нет прав отклонять заявки.', ephemeral=True)
            return

        await interaction.response.defer()

        # Обновляем state
        async with bot.recruit_app_lock:
            state = read_recruit_app_state()
            app = state['applications'].get(str(self.applicant_id))
            if app:
                app['status'] = 'rejected'
                app['reviewed_by'] = interaction.user.id
                app['reviewed_at'] = discord.utils.utcnow().isoformat()
                write_recruit_app_state(state)

        # ДМ заявителю
        applicant = interaction.guild.get_member(self.applicant_id)
        if applicant:
            try:
                await applicant.send('Ваша заявка была рассмотрена, **Отказано**.')
            except Exception:
                pass

        # Обновляем embed
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        if embed:
            new_embed = embed.copy()
            new_embed.color = 0xEF4444
            new_embed.set_footer(text=f'❌ Отклонена — {interaction.user.display_name}')
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(embed=new_embed, view=self)

        asyncio.create_task(send_log(
            '❌ Заявка в рекруты отклонена',
            fields=[
                ('Рекрут', f'<@{self.applicant_id}> (`{self.applicant_id}`)', True),
                ('Рассмотрел', _log_user_field(interaction.user), True),
            ],
            color=0xEF4444, user=interaction.user,
        ))


class RecruitAppBannerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Подать заявку в рекруты', style=discord.ButtonStyle.success, emoji='🪖', custom_id=RECRUIT_APP_BUTTON_ID)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта кнопка работает только на сервере.', ephemeral=True)
            return
        if has_recruit_role(interaction.user):
            await interaction.response.send_message('У тебя уже есть роль рекрута.', ephemeral=True)
            return
        await interaction.response.send_modal(RecruitAppModal())

class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='На собрание', style=discord.ButtonStyle.danger, emoji='📢', custom_id=ADMIN_MEETING_BUTTON_ID)
    async def meeting_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта кнопка работает только на сервере.', ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('У тебя нет прав для использования этой кнопки.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return

        meeting_role = guild.get_role(MEETING_ROLE_ID)
        target_channel = guild.get_channel(MEETING_VOICE_CHANNEL_ID)

        if not meeting_role or not isinstance(target_channel, discord.VoiceChannel):
            await interaction.followup.send('Ошибка: не удалось найти роль или голосовой канал.', ephemeral=True)
            return

        moved = 0
        failed = 0
        for member in meeting_role.members:
            if member.voice and member.voice.channel:
                if member.voice.channel.id != MEETING_VOICE_CHANNEL_ID:
                    try:
                        await member.move_to(target_channel, reason='Собрание')
                        moved += 1
                    except (discord.Forbidden, discord.HTTPException):
                        failed += 1

        desc = f'Перемещено: **{moved}**'
        if failed:
            desc += f'\nНе удалось: **{failed}**'
        if moved == 0:
            desc = 'Нет участников с ролью в голосовых каналах.'

        await interaction.followup.send(desc, ephemeral=True)

        asyncio.create_task(send_log(
            '📢 На собрание',
            description=desc,
            fields=[
                ('Инициатор', _log_user_field(interaction.user), True),
                ('Целевой канал', _log_channel_field(target_channel), True),
            ],
            color=0xEF4444, user=interaction.user,
        ))

    @discord.ui.button(label='1 час до Собрания', style=discord.ButtonStyle.primary, emoji='⏰', custom_id=ADMIN_REMIND_1H_BUTTON_ID)
    async def remind_1h_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта кнопка работает только на сервере.', ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('У тебя нет прав для использования этой кнопки.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return

        meeting_role = guild.get_role(MEETING_ROLE_ID)
        if not meeting_role:
            await interaction.followup.send('Ошибка: не удалось найти роль собрания.', ephemeral=True)
            return

        dm_embed = discord.Embed(
            title='📢 Внимание — Собрание через час!',
            description=(
                'Здравствуй!\n\n'
                'Через **1 час** начинается наше **Собрание**.\n'
                'Пожалуйста, будь в голосовом канале — ждём тебя!\n\n'
                '🎙️ До встречи!'
            ),
            color=0xF59E0B,
            timestamp=discord.utils.utcnow(),
        )
        dm_embed.set_thumbnail(url=THUMBNAIL_URL)
        dm_embed.set_footer(text='YoungHill — Собрание')

        sent = 0
        failed = 0
        for member in meeting_role.members:
            try:
                await member.send(embed=dm_embed)
                sent += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1

        desc = f'Уведомления отправлены: **{sent}**'
        if failed:
            desc += f'\nНе удалось (ЛС закрыты): **{failed}**'
        if sent == 0:
            desc = 'Нет участников с ролью для отправки уведомлений.'

        await interaction.followup.send(desc, ephemeral=True)

        asyncio.create_task(send_log(
            '⏰ Напоминание: Собрание через час',
            description=desc,
            fields=[
                ('Инициатор', _log_user_field(interaction.user), True),
                ('Роль', f'<@&{MEETING_ROLE_ID}>', True),
            ],
            color=0xF59E0B, user=interaction.user,
        ))

    @discord.ui.button(label='На собрание (СМС)', style=discord.ButtonStyle.success, emoji='💬', custom_id=ADMIN_MEETING_SMS_BUTTON_ID)
    async def meeting_sms_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message('Эта кнопка работает только на сервере.', ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('У тебя нет прав для использования этой кнопки.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return

        meeting_role = guild.get_role(MEETING_ROLE_ID)
        if not meeting_role:
            await interaction.followup.send('Ошибка: не удалось найти роль собрания.', ephemeral=True)
            return

        sms_embed = discord.Embed(
            title='📢 Собрание началось!',
            description=(
                '**Переходите в канал собрания!**\n\n'
                'Все участники с ролью приглашаются присоединиться.\n'
                '🎙️ Ждём вас!'
            ),
            color=0xEF4444,
            timestamp=discord.utils.utcnow(),
        )
        sms_embed.set_thumbnail(url=THUMBNAIL_URL)
        sms_embed.set_footer(text='YoungHill — Собрание')

        sent = 0
        failed = 0
        for member in meeting_role.members:
            if member.bot:
                continue
            try:
                await member.send(embed=sms_embed)
                sent += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1

        desc = f'ЛС отправлено: **{sent}**'
        if failed:
            desc += f'\nНе удалось (ЛС закрыты): **{failed}**'
        if sent == 0:
            desc = 'Нет участников для отправки.'

        await interaction.followup.send(desc, ephemeral=True)

        asyncio.create_task(send_log(
            '💬 На собрание (СМС)',
            description=desc,
            fields=[
                ('Инициатор', _log_user_field(interaction.user), True),
                ('Роль', f'<@&{MEETING_ROLE_ID}>', True),
            ],
            color=0x10B981, user=interaction.user,
        ))

    @discord.ui.button(label='Объявление', style=discord.ButtonStyle.primary, emoji='📣', custom_id=ANNOUNCEMENT_BUTTON_ID, row=1)
    async def announcement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('У тебя нет прав.', ephemeral=True)
            return
        await interaction.response.send_modal(AnnouncementModal())

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.page = 0
        self.category = 'messages'

    def build_embed(self, guild: discord.Guild) -> discord.Embed:
        state = read_stats_state()
        category_labels = {
            'messages': '📝 Сообщения',
            'voice': '🔊 Голосовое время',
            'commands': '⚡ Команды',
        }
        stat_data = state.get(self.category, {})
        sorted_users = sorted(stat_data.items(), key=lambda x: int(x[1]), reverse=True)[:10]

        lines = []
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id_str, value) in enumerate(sorted_users):
            member = guild.get_member(int(user_id_str))
            name = member.display_name if member else f'ID: {user_id_str}'
            medal = medals[i] if i < 3 else f'**{i+1}.**'
            if self.category == 'voice':
                val_str = format_voice_time(int(value))
            else:
                val_str = f'{int(value):,}'
            lines.append(f'{medal} {name} — {val_str}')

        description = '\n'.join(lines) if lines else '*Пока нет данных*'
        embed = discord.Embed(
            title=f'🏆 Таблица лидеров — {category_labels.get(self.category, self.category)}',
            description=description,
            color=0xF59E0B,
        )
        embed.set_footer(text=f'Страница {self.page + 1}')
        return embed

    @discord.ui.select(
        placeholder='Выбери категорию',
        options=[
            discord.SelectOption(label='Сообщения', value='messages', emoji='📝'),
            discord.SelectOption(label='Голос', value='voice', emoji='🔊'),
            discord.SelectOption(label='Команды', value='commands', emoji='⚡'),
        ],
        custom_id='leaderboard_category',
    )
    async def select_category(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.category = select.values[0]
        self.page = 0
        embed = self.build_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='◄', style=discord.ButtonStyle.secondary, custom_id=LEADERBOARD_PREV_BUTTON_ID)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
        embed = self.build_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='►', style=discord.ButtonStyle.secondary, custom_id=LEADERBOARD_NEXT_BUTTON_ID)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        embed = self.build_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

class FamilyBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix='!', intents=intents)
        self.refresh_lock = asyncio.Lock()
        self.recruit_lock = asyncio.Lock()
        self.birthday_lock = asyncio.Lock()
        self.automod_lock = asyncio.Lock()
        self.recruit_app_lock = asyncio.Lock()
        self.invite_cache: dict[int, dict[str, int]] = {}
        self.spam_cache: dict[int, list[float]] = {}
        self.image_cache: dict[int, list[float]] = {}
        self.stats_voice_sessions: dict[int, float] = {}

    async def setup_hook(self) -> None:
        self.add_view(RefreshView())
        self.add_view(RecruitView())
        self.add_view(RecruitReportButtonView())
        self.add_view(BirthdayButtonView())
        self.add_view(AutomodConfigView())
        self.add_view(ApplicationCreateView())
        self.add_view(TicketAdminView())
        self.add_view(RecruitAppBannerView())
        self.add_view(AdminPanelView())
        self.add_view(LeaderboardView())
        guild_obj = discord.Object(id=int(GUILD_ID)) if GUILD_ID else None
        if guild_obj is not None:
            self.tree.copy_global_to(guild=guild_obj)
            await self.tree.sync(guild=guild_obj)
        else:
            await self.tree.sync()

bot = FamilyBot()

def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def read_state() -> dict:
    return read_json(STATE_FILE)

def write_state(data: dict) -> None:
    write_json(STATE_FILE, data)

def read_recruit_state() -> dict:
    state = read_json(RECRUIT_STATE_FILE)
    state.setdefault('recruits', {})
    state.setdefault('accepted_members', {})
    return state

def write_recruit_state(data: dict) -> None:
    write_json(RECRUIT_STATE_FILE, data)

def read_birthday_state() -> dict:
    state = read_json(BIRTHDAY_STATE_FILE)
    state.setdefault('entries', {})
    return state

def write_birthday_state(data: dict) -> None:
    write_json(BIRTHDAY_STATE_FILE, data)

def read_automod_state() -> dict:
    state = read_json(AUTOMOD_STATE_FILE)
    state.setdefault('modules', {
        'spam':     {'enabled': False, 'limit': 5, 'interval': 5},
        'badwords': {'enabled': False, 'words': []},
        'invites':  {'enabled': False},
        'emoji':    {'enabled': False, 'limit': 5},
        'mentions': {'enabled': False, 'limit': 3},
        'images':   {'enabled': False, 'limit': 3, 'interval': 10},
        'caps':     {'enabled': False, 'percent': 70},
    })
    state.setdefault('punishment', {
        'actions': ['warn', 'mute', 'kick', 'ban'],
        'mute_minutes': 10,
    })
    state.setdefault('warnings', {})
    state.setdefault('whitelist_channels', [])
    state.setdefault('exempt_roles', [])
    return state

def write_automod_state(data: dict) -> None:
    write_json(AUTOMOD_STATE_FILE, data)

def read_app_state() -> dict:
    state = read_json(APP_STATE_FILE)
    state.setdefault('message_id', None)
    return state

def write_app_state(data: dict) -> None:
    write_json(APP_STATE_FILE, data)

def read_recruit_app_state() -> dict:
    state = read_json(RECRUIT_APP_STATE_FILE)
    state.setdefault('banner_message_id', None)
    state.setdefault('applications', {})
    return state

def write_recruit_app_state(data: dict) -> None:
    write_json(RECRUIT_APP_STATE_FILE, data)

def read_stats_state() -> dict:
    state = read_json(STATS_STATE_FILE)
    state.setdefault('messages', {})
    state.setdefault('voice', {})
    state.setdefault('voice_sessions', {})
    state.setdefault('commands', {})
    return state

def write_stats_state(data: dict) -> None:
    write_json(STATS_STATE_FILE, data)

def read_reminders_state() -> dict:
    state = read_json(REMINDERS_STATE_FILE)
    state.setdefault('reminders', [])
    return state

def write_reminders_state(data: dict) -> None:
    write_json(REMINDERS_STATE_FILE, data)

def parse_birthday_text(raw: str) -> Optional[dict]:
    text = raw.strip().replace('/', '.').replace('-', '.')
    parts = [p.strip() for p in text.split('.') if p.strip()]
    if len(parts) not in (2, 3):
        return None
    if not all(part.isdigit() for part in parts):
        return None
    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2]) if len(parts) == 3 else None
    if not 1 <= day <= 31 or not 1 <= month <= 12:
        return None
    if year is not None and not 1900 <= year <= 2100:
        return None
    text = f'{day:02d}.{month:02d}' + (f'.{year:04d}' if year is not None else '')
    result = {'day': day, 'month': month, 'text': text}
    if year is not None:
        result['year'] = year
    return result

def calculate_age(year: Optional[int], month: int, day: int) -> Optional[int]:
    if year is None:
        return None
    today = discord.utils.utcnow().date()
    age = today.year - int(year)
    if (today.month, today.day) < (month, day):
        age -= 1
    return age

def age_suffix(age: int) -> str:
    if age % 10 == 1 and age % 100 != 11:
        return 'год'
    if age % 10 in (2, 3, 4) and age % 100 not in (12, 13, 14):
        return 'года'
    return 'лет'

def parse_relative_time(text: str) -> Optional[timedelta]:
    """Парсит относительное время: 30m, 2h, 1d, 1w, 30мин, 2часа, 1день."""
    text = text.strip().lower()
    patterns = [
        (r'^(\d+)\s*(?:m|min|мин|минут)$', 'm'),
        (r'^(\d+)\s*(?:h|hr|ч|час(?:а|ов)?)$', 'h'),
        (r'^(\d+)\s*(?:d|д|день|дня|дней)$', 'd'),
        (r'^(\d+)\s*(?:w|н|недел[яьи]|недель)$', 'w'),
    ]
    for pattern, unit in patterns:
        match = re.match(pattern, text)
        if match:
            value = int(match.group(1))
            if unit == 'm':
                return timedelta(minutes=value)
            elif unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
            elif unit == 'w':
                return timedelta(weeks=value)
    return None

def format_voice_time(seconds: int) -> str:
    """Форматирует секунды в читаемый вид: '2ч 15м', '45м', '1ч 02м'."""
    if seconds < 60:
        return f'{seconds}с'
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f'{hours}ч {minutes:02d}м'
    return f'{minutes}м'

def format_birthday_line(member: discord.Member | None, user_id: int, entry: dict) -> str:
    display = f'<@{user_id}>' if member is None else format_member(member)
    month = int(entry.get('month', 0) or 0)
    day = int(entry.get('day', 0) or 0)
    year = int(entry['year']) if entry.get('year') is not None else None
    age = calculate_age(year, month, day) if month and day else None
    line = f'{display} — {entry.get("text", "??.??")}'
    if age is not None:
        line += f' ({age} {age_suffix(age)})'
    return line

def birthday_sort_key(item: tuple[int, dict], guild: discord.Guild) -> tuple[int, int, int, str]:
    user_id, entry = item
    member = guild.get_member(user_id)
    month = int(entry.get('month', 0) or 0)
    day = int(entry.get('day', 0) or 0)
    year = int(entry['year']) if entry.get('year') is not None else 0
    name = member.display_name.casefold() if member else str(user_id)
    return (month, day, year, name)

def format_member(member: discord.Member) -> str:
    return f'<@{member.id}>'

def sort_members(members):
    return sorted(members, key=lambda m: m.display_name.casefold())

def has_recruit_role(member: discord.Member) -> bool:
    return any(role.id == RECRUIT_ROLE_ID for role in member.roles)

async def get_text_channel(channel_id: int) -> discord.TextChannel:
    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        raise RuntimeError('Target channel is not a text channel or was not found.')
    return channel


# --------------- Логирование (компактный единый стиль) ---------------

def _format_log_time(dt: datetime | None = None) -> str:
    """Формат времени как на картинке: «Сегодня, в 21:23» / «Вчера, в ...» / «05.07.2026, в ...»."""
    dt = dt or discord.utils.utcnow()
    today = discord.utils.utcnow().date()
    if dt.date() == today:
        day = 'Сегодня'
    elif (today - dt.date()).days == 1:
        day = 'Вчера'
    else:
        day = dt.strftime('%d.%m.%Y')
    return f'{day}, в {dt.strftime("%H:%M")}'


async def send_log(
    title: str,
    description: str | None = None,
    *,
    color: int = 0x6366F1,
    user: discord.Member | discord.User | None = None,
    fields: list[tuple[str, str, bool]] | None = None,
    thumbnail: str | None = None,
) -> None:
    """
    Компактный лог в едином стиле.
    - title:     заголовок-событие (например «🔊 Подключился к голосовому»)
    - fields:    список (название, значение, inline) — например Участник / Канал
    - user:      участник (аватар сбоку + ID в футере)
    - thumbnail: маленькая картинка сбоку
    """
    if not LOG_CHANNEL_ID:
        return
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        if channel is None:
            channel = await bot.fetch_channel(LOG_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(title=title, color=color)
        if description:
            embed.description = description

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        # Футер: время + ID (как на картинке)
        footer_parts = [_format_log_time()]
        if user is not None:
            footer_parts.append(f'ID: {user.id}')
        embed.set_footer(text=' • '.join(footer_parts))

        # Аватар сбоку
        if user is not None and user.display_avatar:
            embed.set_thumbnail(url=user.display_avatar.url)
        elif thumbnail:
            embed.set_thumbnail(url=thumbnail)

        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
    except Exception as exc:
        print(f'[LOG ERROR] Could not send log: {exc}')


def _log_user_field(user: discord.Member | discord.User) -> str:
    """Поле «Участник» в формате: @упоминание (ID)."""
    return f'{user.mention} (`{user.id}`)'


def _log_channel_field(channel: discord.abc.GuildChannel | None) -> str | None:
    """Поле «Канал» в формате: #имя (ID). Если канала нет — None."""
    if channel is None:
        return None
    return f'{channel.mention} (`{channel.id}`)'

async def fetch_invites(guild: discord.Guild) -> dict[str, discord.Invite]:
    invites = await guild.invites()
    return {invite.code: invite for invite in invites}

async def update_invite_cache(guild: discord.Guild) -> dict[str, discord.Invite]:
    invites = await fetch_invites(guild)
    bot.invite_cache[guild.id] = {code: invite.uses or 0 for code, invite in invites.items()}
    return invites

def build_payload(guild: discord.Guild) -> tuple[discord.Embed, discord.ui.View]:
    sections = []
    for role in ROLE_ORDER:
        guild_role = guild.get_role(role.role_id)
        members = sort_members(guild_role.members) if guild_role else []
        header = f'{role.emoji} {role.label} ({len(members)})'
        if role.count_only:
            sections.append(header)
            continue
        body = '\n'.join(f'• {format_member(member)}' for member in members) if members else '• нет участников'
        sections.append(f'{header}\n{body}')

    embed = discord.Embed(title=f'👥 Состав семьи {guild.name}', description='\n\n'.join(sections), color=0xF59E0B)
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_image(url=MAIN_IMAGE_URL)
    embed.add_field(name='📊 Всего на сервере', value=f'**{guild.member_count}** участников', inline=False)
    embed.set_footer(text='Автообновление каждые 5 минут')
    embed.timestamp = discord.utils.utcnow()
    return embed, RefreshView()

async def create_or_get_recruit_invite(member: discord.Member) -> dict:
    async with bot.recruit_lock:
        state = read_recruit_state()
        recruiter_id = str(member.id)
        record = state['recruits'].get(recruiter_id)
        if record and record.get('invite_url'):
            return record

        channel = await get_text_channel(INVITE_CHANNEL_ID)
        invite = await channel.create_invite(max_age=0, max_uses=0, unique=True, reason=f'Personal recruit invite for {member} ({member.id})')
        record = {
            'member_id': member.id,
            'invite_code': invite.code,
            'invite_url': invite.url,
            'accepted_count': invite.uses or 0,
            'created_at': discord.utils.utcnow().isoformat(),
        }
        state['recruits'][recruiter_id] = record
        write_recruit_state(state)
        await update_invite_cache(member.guild)
        return record

async def build_recruit_payload(guild: discord.Guild) -> tuple[discord.Embed, discord.ui.View]:
    state = read_recruit_state()
    recruit_role = guild.get_role(RECRUIT_ROLE_ID)
    recruits = sort_members(recruit_role.members) if recruit_role else []

    try:
        invites = await fetch_invites(guild)
    except Exception as exc:
        invites = {}
        print(f'Could not fetch invites for recruit board: {exc}')

    lines = []
    changed = False
    for member in recruits:
        record = state['recruits'].get(str(member.id), {})
        code = record.get('invite_code')
        if code and code in invites:
            uses = invites[code].uses or 0
            if uses > int(record.get('accepted_count', 0)):
                record['accepted_count'] = uses
                state['recruits'][str(member.id)] = record
                changed = True
        count = int(record.get('accepted_count', 0))
        url = record.get('invite_url', 'ещё не создана')
        lines.append(f'**{member.display_name}**\nПринял людей: **{count}**\nСсылка: {url}')

    if changed:
        write_recruit_state(state)

    description = '\n\n'.join(lines) if lines else 'Пока нет участников с ролью Рекрут.'
    if len(description) > 3900:
        description = description[:3900] + '\n\nСписок слишком длинный, часть рекрутов скрыта.'

    embed = discord.Embed(title='🪖 Рекруты и приглашения', description=description, color=0x22C55E)
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Кнопка создаёт одну вечную ссылку. Поменять её после создания нельзя.')
    embed.timestamp = discord.utils.utcnow()
    return embed, RecruitView()

def build_report_button_payload() -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        title='📝 Отписать приглашённого',
        description='Нажми кнопку ниже и заполни форму: имя фамилия и номер паспорта.',
        color=0x38BDF8,
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Форма доступна только рекрутам')
    return embed, RecruitReportButtonView()

async def refresh_report_button_message() -> None:
    channel = await get_text_channel(RECRUIT_REPORT_CHANNEL_ID)
    embed, view = build_report_button_payload()
    state = read_json(REPORT_BUTTON_STATE_FILE)
    message = None
    if state.get('message_id'):
        try:
            message = await channel.fetch_message(int(state['message_id']))
        except Exception:
            message = None
    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)
    write_json(REPORT_BUTTON_STATE_FILE, {
        'message_id': message.id,
        'channel_id': channel.id,
        'updated_at': discord.utils.utcnow().isoformat(),
    })

async def refresh_report_button_message_safely() -> None:
    try:
        await refresh_report_button_message()
    except Exception as exc:
        print(f'Report button refresh failed: {exc}')


def build_birthday_payload(guild: discord.Guild) -> tuple[discord.Embed, discord.ui.View]:
    state = read_birthday_state()
    entries = []
    for user_id_str, entry in state['entries'].items():
        try:
            user_id = int(user_id_str)
        except ValueError:
            continue
        entries.append((user_id, entry))

    entries.sort(key=lambda item: birthday_sort_key(item, guild))
    lines = []
    for user_id, entry in entries:
        member = guild.get_member(user_id)
        lines.append(f'• {format_birthday_line(member, user_id, entry)}')

    description = '\n'.join(lines) if lines else 'Пока никто не добавил дату рождения.'
    if len(description) > 3900:
        description = description[:3900] + '\n\nСписок слишком длинный, часть записей скрыта.'

    embed = discord.Embed(title='🎂 Список дней рождения', description=description, color=0xF97316)
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Нажми кнопку, чтобы добавить или обновить свою дату')
    embed.timestamp = discord.utils.utcnow()
    return embed, BirthdayButtonView()

async def refresh_birthday_board() -> None:
    if not BIRTHDAY_BOARD_CHANNEL_ID:
        return
    channel = await get_text_channel(BIRTHDAY_BOARD_CHANNEL_ID)
    embed, view = build_birthday_payload(channel.guild)
    state = read_birthday_state()
    message = None
    if state.get('message_id'):
        try:
            message = await channel.fetch_message(int(state['message_id']))
        except Exception:
            message = None
    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)
    state['message_id'] = message.id
    state['channel_id'] = channel.id
    state['updated_at'] = discord.utils.utcnow().isoformat()
    write_birthday_state(state)

async def refresh_birthday_board_safely() -> None:
    try:
        await refresh_birthday_board()
    except Exception as exc:
        print(f'Birthday board refresh failed: {exc}')


GREETED_TODAY: set[int] = set()

async def auto_birthday_greeting() -> None:
    """Каждый час проверяет — чей сегодня день рождения, и поздравляет."""
    if not BIRTHDAY_GREETING_CHANNEL_ID:
        return
    while True:
        await asyncio.sleep(60 * 60)
        try:
            today = discord.utils.utcnow()
            today_day = today.day
            today_month = today.month

            state = read_birthday_state()
            entries = state.get('entries', {})

            channel = bot.get_channel(BIRTHDAY_GREETING_CHANNEL_ID)
            if not channel:
                channel = await bot.fetch_channel(BIRTHDAY_GREETING_CHANNEL_ID)
            if not isinstance(channel, discord.TextChannel):
                continue

            for user_id_str, entry in entries.items():
                user_id = int(user_id_str)
                if entry.get('day') == today_day and entry.get('month') == today_month:
                    if user_id in GREETED_TODAY:
                        continue

                    member = channel.guild.get_member(user_id)
                    if not member:
                        continue

                    year = entry.get('year')
                    age_text = ''
                    if year:
                        age = calculate_age(year, today_month, today_day)
                        if age is not None:
                            age_text = f'\n🎉 С днём рождения! Тебе **{age}** {age_suffix(age)}!'

                    embed = discord.Embed(
                        title='🎂 С Днём Рождения!',
                        description=(
                            f'{member.mention}, поздравляем тебя с днём рождения! 🎉\n\n'
                            f'Желаем тебе счастья, здоровья и удачи! 🥳🎊'
                            f'{age_text}'
                        ),
                        color=0xF97316,
                        timestamp=discord.utils.utcnow(),
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text='С любовью, YoungHill Family 💛')

                    try:
                        await channel.send(content=member.mention, embed=embed)
                        GREETED_TODAY.add(user_id)
                        print(f'[BIRTHDAY] Greeted {member.display_name} in #{channel.name}')
                    except Exception as exc:
                        print(f'[BIRTHDAY] Failed to greet {member}: {exc}')

            # Сброс приветствий в полночь
            if today.hour == 0 and len(GREETED_TODAY) > 0:
                GREETED_TODAY.clear()

        except Exception as exc:
            print(f'[BIRTHDAY] Auto-greeting error: {exc}')


async def refresh_board() -> None:
    async with bot.refresh_lock:
        channel = await get_text_channel(TARGET_CHANNEL_ID)
        embed, view = build_payload(channel.guild)
        state = read_state()
        message = None
        if state.get('message_id'):
            try:
                message = await channel.fetch_message(int(state['message_id']))
            except Exception:
                message = None
        if message is None:
            message = await channel.send(embed=embed, view=view)
        else:
            await message.edit(embed=embed, view=view)
        write_state({'message_id': message.id, 'channel_id': channel.id, 'updated_at': discord.utils.utcnow().isoformat()})

async def refresh_recruit_board() -> None:
    async with bot.recruit_lock:
        channel = await get_text_channel(RECRUIT_BOARD_CHANNEL_ID)
        embed, view = await build_recruit_payload(channel.guild)
        state = read_recruit_state()
        message = None
        if state.get('board_message_id'):
            try:
                message = await channel.fetch_message(int(state['board_message_id']))
            except Exception:
                message = None
        if message is None:
            message = await channel.send(embed=embed, view=view)
        else:
            await message.edit(embed=embed, view=view)
        state['board_message_id'] = message.id
        state['board_channel_id'] = channel.id
        state['updated_at'] = discord.utils.utcnow().isoformat()
        write_recruit_state(state)

async def refresh_board_safely() -> None:
    try:
        await refresh_board()
    except Exception as exc:
        print(f'Family board refresh failed: {exc}')
        asyncio.create_task(send_log('❌ Ошибка обновления состава', f'```{traceback.format_exc()[-1500:]}```', color=0xEF4444))

async def refresh_recruit_board_safely() -> None:
    try:
        await refresh_recruit_board()
    except Exception as exc:
        print(f'Recruit board refresh failed: {exc}')
        asyncio.create_task(send_log('❌ Ошибка обновления рекрутов', f'```{traceback.format_exc()[-1500:]}```', color=0xEF4444))


async def refresh_automod_board() -> None:
    if not AUTOMOD_CHANNEL_ID: return
    channel = await get_text_channel(AUTOMOD_CHANNEL_ID)
    state = read_automod_state()
    m = state['modules']

    def st(key): return '🟢 ВКЛ' if m[key]['enabled'] else '🔴 ВЫКЛ'

    embed = discord.Embed(title='🛡️ Автомодерация', color=0x3B82F6)
    embed.description = '\n'.join([
        f'**Анти-Спам** — {st("spam")}  `> {m["spam"]["limit"]} сообщ. / {m["spam"]["interval"]} сек`',
        f'**Анти-Мат** — {st("badwords")}  `{len(m["badwords"]["words"])} слов в базе`',
        f'**Анти-Инвайты** — {st("invites")}',
        f'**Анти-Эмодзи** — {st("emoji")}  `> {m["emoji"]["limit"]} в сообщении`',
        f'**Анти-Пинги** — {st("mentions")}  `> {m["mentions"]["limit"]} в сообщении`',
        f'**Анти-Картинки** — {st("images")}  `> {m["images"]["limit"]} / {m["images"]["interval"]} сек`',
        f'**Анти-Caps** — {st("caps")}  `> {m["caps"]["percent"]}% заглавных`',
    ])

    actions = state['punishment']['actions']
    action_icons = {'warn': '⚠️', 'mute': '🔇', 'kick': '👢', 'ban': '🔨', 'none': '—'}
    punish_str = ' → '.join(f'{action_icons.get(a, "")} {a}' for a in actions)
    embed.add_field(
        name='⚖️ Наказания (по порядку)',
        value=f'`{punish_str}`\nМут: **{state["punishment"]["mute_minutes"]}** мин.',
        inline=False,
    )

    wl = state.get('whitelist_channels', [])
    er = state.get('exempt_roles', [])
    if wl or er:
        parts = []
        if wl:
            parts.append(f'Каналы: {", ".join(f"<#{c}>" for c in wl)}')
        if er:
            parts.append(f'Роли: {", ".join(f"<@&{r}>" for r in er)}')
        embed.add_field(name='🛡️ Исключения', value='\n'.join(parts), inline=False)

    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text='Нажми 🟢/🔴 чтобы включить/выключить')

    view = AutomodConfigView()
    msg_id = state.get('message_id')
    message = None
    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
        except Exception:
            pass
    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)

    state['message_id'] = message.id
    write_automod_state(state)

async def refresh_automod_board_safely() -> None:
    try:
        await refresh_automod_board()
    except Exception as exc:
        print(f'Automod board error: {exc}')
        asyncio.create_task(send_log('❌ Ошибка обновления Automod', f'```{traceback.format_exc()[-1500:]}```', color=0xEF4444))


async def refresh_application_board() -> None:
    if not APP_CREATE_CHANNEL_ID: return
    channel = await get_text_channel(APP_CREATE_CHANNEL_ID)
    state = read_app_state()

    embed = discord.Embed(
        title='📋 Набор в семью',
        description='Хочешь вступить в семью?\nНажми кнопку **Подать заявку**, чтобы открыть тикет и заполнить анкету.\n\n'
                    'Твоя заявка будет рассмотрена администрацией.',
        color=0xF59E0B,
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Нажми «Подать заявку», чтобы открыть тикет')
    embed.timestamp = discord.utils.utcnow()

    view = ApplicationCreateView()

    msg_id = state.get('message_id')
    message = None
    if msg_id:
        try:
            message = await channel.fetch_message(int(msg_id))
        except Exception:
            pass

    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)

    state['message_id'] = message.id
    write_app_state(state)

async def refresh_application_board_safely() -> None:
    try:
        await refresh_application_board()
    except Exception as exc:
        print(f'App board refresh error: {exc}')


async def refresh_recruit_app_banner() -> None:
    if not RECRUIT_APP_BANNER_CHANNEL_ID:
        return
    channel = await get_text_channel(RECRUIT_APP_BANNER_CHANNEL_ID)
    state = read_recruit_app_state()

    embed = discord.Embed(
        title='🪖 Заявка в рекруты',
        description='Хочешь стать рекрутом семьи?\nНажми кнопку **Подать заявку** и заполни форму.\n\n'
                    'Твоя заявка будет рассмотрена администрацией.',
        color=0x22C55E,
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Требуется роль выше Рекрута для принятия/отклонения')
    embed.timestamp = discord.utils.utcnow()

    view = RecruitAppBannerView()
    message = None
    if state.get('banner_message_id'):
        try:
            message = await channel.fetch_message(int(state['banner_message_id']))
        except Exception:
            message = None
    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)
    state['banner_message_id'] = message.id
    write_recruit_app_state(state)


async def refresh_recruit_app_banner_safely() -> None:
    try:
        await refresh_recruit_app_banner()
    except Exception as exc:
        print(f'Recruit app banner refresh error: {exc}')


ADMIN_PANEL_STATE_FILE = Path(__file__).with_name('admin-panel-state.json')

def read_admin_panel_state() -> dict:
    state = read_json(ADMIN_PANEL_STATE_FILE)
    state.setdefault('message_id', None)
    return state

def write_admin_panel_state(data: dict) -> None:
    write_json(ADMIN_PANEL_STATE_FILE, data)


async def refresh_admin_panel() -> None:
    if not ADMIN_PANEL_CHANNEL_ID:
        return
    channel = await get_text_channel(ADMIN_PANEL_CHANNEL_ID)

    embed = discord.Embed(
        title='⚙️ Панель управления',
        description=(
            '**На собрание** — переместит всех участников с ролью '
            f'<@&{MEETING_ROLE_ID}> в голосовой канал <#{MEETING_VOICE_CHANNEL_ID}>.\n\n'
            '**1 час до Собрания** — отправит ЛС-уведомление всем участникам с ролью '
            f'<@&{MEETING_ROLE_ID}>.\n\n'
            '**Объявление** — отправит красивый embed в любой канал.\n\n'
            'Кнопки доступны только администрации (Manage Server).'
        ),
        color=0xEF4444,
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.timestamp = discord.utils.utcnow()

    view = AdminPanelView()
    state = read_admin_panel_state()
    message = None

    if state.get('message_id'):
        try:
            message = await channel.fetch_message(int(state['message_id']))
        except discord.NotFound:
            print(f'[ADMIN] Panel message {state["message_id"]} not found — creating new')
            state['message_id'] = None
            write_admin_panel_state(state)
        except discord.HTTPException as exc:
            print(f'[ADMIN] Failed to fetch panel message: {exc}')

    if message is None:
        message = await channel.send(embed=embed, view=view)
    else:
        await message.edit(embed=embed, view=view)

    state['message_id'] = message.id
    state['channel_id'] = channel.id
    state['updated_at'] = discord.utils.utcnow().isoformat()
    write_admin_panel_state(state)


async def refresh_admin_panel_safely() -> None:
    try:
        await refresh_admin_panel()
    except Exception as exc:
        print(f'Admin panel refresh error: {exc}')


async def track_member_invite(member: discord.Member) -> None:
    try:
        current_invites = await fetch_invites(member.guild)
    except Exception as exc:
        print(f'Could not check invite use for {member}: {exc}')
        return

    previous = bot.invite_cache.get(member.guild.id, {})
    used_code = None
    for code, invite in current_invites.items():
        old_uses = previous.get(code, 0)
        new_uses = invite.uses or 0
        if new_uses > old_uses:
            used_code = code
            break

    bot.invite_cache[member.guild.id] = {code: invite.uses or 0 for code, invite in current_invites.items()}
    if not used_code:
        asyncio.create_task(send_log(
            '👋 Новый участник',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Источник', '**не определён**', True),
            ],
            color=0xA855F7, user=member,
        ))
        return

    recruiter_name = None
    async with bot.recruit_lock:
        state = read_recruit_state()
        for recruiter_id, record in state['recruits'].items():
            if record.get('invite_code') == used_code:
                record['accepted_count'] = max(int(record.get('accepted_count', 0)) + 1, current_invites[used_code].uses or 0)
                state['accepted_members'][str(member.id)] = {'recruiter_id': recruiter_id, 'joined_at': discord.utils.utcnow().isoformat()}
                write_recruit_state(state)
                recruiter_member = member.guild.get_member(int(recruiter_id))
                recruiter_name = recruiter_member.mention if recruiter_member else f'<@{recruiter_id}>'
                break

    if recruiter_name:
        asyncio.create_task(send_log(
            '👋 Новый участник (по ссылке рекрута)',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Пригласил', recruiter_name, True),
                ('Код ссылки', f'`{used_code}`', False),
            ],
            color=0x22C55E, user=member,
        ))
    else:
        asyncio.create_task(send_log(
            '👋 Новый участник',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Ссылка', f'`{used_code}` (без рекрута)', True),
            ],
            color=0xA855F7, user=member,
        ))

    await refresh_recruit_board_safely()

@bot.event
async def on_ready() -> None:
    print(f'Logged in as {bot.user}')
    for guild in bot.guilds:
        try:
            await update_invite_cache(guild)
        except Exception as exc:
            print(f'Invite cache failed for {guild}: {exc}')
    if not auto_refresh.is_running():
        auto_refresh.start()
    asyncio.create_task(refresh_board_safely())
    asyncio.create_task(refresh_recruit_board_safely())
    asyncio.create_task(refresh_report_button_message_safely())
    asyncio.create_task(refresh_birthday_board_safely())
    asyncio.create_task(auto_birthday_greeting())
    asyncio.create_task(refresh_automod_board_safely())
    asyncio.create_task(refresh_application_board_safely())
    asyncio.create_task(refresh_recruit_app_banner_safely())
    asyncio.create_task(refresh_admin_panel_safely())
    await restore_scheduled_tasks()
    await send_log(
        '🟢 Бот запущен',
        f'**{bot.user}** успешно подключился\n'
        f'Серверов: **{len(bot.guilds)}**\n'
        f'Пинг: **{round(bot.latency * 1000)}** мс',
        color=0x10B981,
    )

@bot.event
async def on_member_join(member: discord.Member) -> None:
    await track_member_invite(member)
    asyncio.create_task(send_welcome_message(member))
    asyncio.create_task(check_raid(member))

    # Лог входа
    account_age = (discord.utils.utcnow() - member.created_at).days
    fields = [
        ('Участник', _log_user_field(member), True),
        ('Аккаунт создан', f'{account_age} дн. назад', True),
        ('Участников', str(member.guild.member_count), True),
    ]
    if member.guild.icon:
        fields.append(('Иконка', f'[Ссылка]({member.guild.icon.url})', True))

    asyncio.create_task(send_log(
        '📥 Участник вошёл',
        fields=fields,
        color=0x00FF00, user=member,
    ))



async def _purge_user_messages(channel: discord.TextChannel, user_id: int, seconds: int, only_images: bool = False) -> int:
    """Собирает и удаляет все сообщения пользователя за N секунд."""
    cutoff = discord.utils.utcnow() - timedelta(seconds=seconds)
    ids_to_delete = []
    try:
        async for msg in channel.history(limit=200, oldest_first=False):
            if msg.created_at < cutoff:
                break
            if msg.author.id == user_id and not msg.pinned:
                if only_images and not msg.attachments:
                    continue
                ids_to_delete.append(msg.id)
    except Exception as exc:
        print(f'[AUTOMOD] History scan error: {exc}')
        return 0

    if not ids_to_delete:
        return 0

    deleted = 0
    # Пробуем bulk delete
    for i in range(0, len(ids_to_delete), 100):
        batch = ids_to_delete[i:i+100]
        try:
            await channel.delete_messages([discord.Object(id=mid) for mid in batch])
            deleted += len(batch)
        except discord.Forbidden:
            # Нет права Manage Messages — пробуем по одному (только свои)
            print(f'[AUTOMOD] No Manage Messages permission — cannot delete other users messages')
            break
        except discord.HTTPException as exc:
            print(f'[AUTOMOD] Bulk delete failed: {exc}')
            # Fallback: удаление сообщений старше 14 дней не работает через bulk
            # Пробуем по одному
            for mid in batch:
                try:
                    await channel.delete_message(discord.Object(id=mid))
                    deleted += 1
                except discord.Forbidden:
                    pass
                except discord.HTTPException:
                    pass
    return deleted


async def _automod_punish(message: discord.Message, module: str, reason: str, state: dict) -> None:
    """Система наказаний как в Dyno: warn → mute → kick → ban."""
    uid = str(message.author.id)
    actions = state['punishment']['actions']
    mute_min = state['punishment']['mute_minutes']

    # Админы — только лог + warn, без жёстких наказаний
    is_admin = isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_guild

    async with bot.automod_lock:
        state = read_automod_state()
        count = state['warnings'].get(uid, 0)
        new_count = count + 1
        state['warnings'][uid] = new_count
        write_automod_state(state)

    action_idx = min(new_count - 1, len(actions) - 1)
    action = actions[action_idx]

    module_labels = {
        'spam': '⚠️ Анти-Спам',
        'badwords': '🤬 Анти-Мат',
        'invites': '🔗 Анти-Инвайты',
        'emoji': '😀 Анти-Эмодзи',
        'mentions': '📢 Анти-Пинги',
        'images': '🖼️ Анти-Картинки',
        'caps': '🔠 Анти-Caps',
    }

    # Админы — только warn + лог, без мута/кика/бана
    if is_admin:
        action = 'warn'

    result_msg = ''

    if action == 'warn':
        suffix = ' — админ' if is_admin else ''
        result_msg = f'{message.author.mention}, предупреждение **{new_count}** ({reason}){suffix}'
    elif action == 'mute':
        until = discord.utils.utcnow() + timedelta(minutes=mute_min)
        try:
            await message.author.timeout(until, reason=f'Автомод: {module} — {reason}')
            result_msg = f'{message.author.mention}, **МУТ на {mute_min} мин** ({reason})'
            async with bot.automod_lock:
                state = read_automod_state()
                state['warnings'][uid] = 0
                write_automod_state(state)
        except (discord.Forbidden, discord.HTTPException):
            result_msg = f'{message.author.mention}, попытка мута не удалась — нет прав'
    elif action == 'kick':
        try:
            await message.author.kick(reason=f'Автомод: {module} — {reason}')
            result_msg = f'{message.author.mention} **кикнут** ({reason})'
            async with bot.automod_lock:
                state = read_automod_state()
                state['warnings'][uid] = 0
                write_automod_state(state)
        except (discord.Forbidden, discord.HTTPException):
            result_msg = f'{message.author.mention}, попытка кика не удалась — нет прав'
    elif action == 'ban':
        try:
            await message.author.ban(reason=f'Автомод: {module} — {reason}')
            result_msg = f'{message.author.mention} **забанен** ({reason})'
            async with bot.automod_lock:
                state = read_automod_state()
                state['warnings'][uid] = 0
                write_automod_state(state)
        except (discord.Forbidden, discord.HTTPException):
            result_msg = f'{message.author.mention}, попытка бана не удалась — нет прав'
    elif action == 'none':
        pass

    if result_msg:
        try:
            await message.channel.send(result_msg, delete_after=10)
        except (discord.Forbidden, discord.NotFound):
            pass

    asyncio.create_task(send_log(
        module_labels.get(module, '🛡️ Автомод'),
        fields=[
            ('Участник', _log_user_field(message.author), True),
            ('Канал', _log_channel_field(message.channel), True),
            ('Нарушение', f'**{new_count}** — {action}', True),
            ('Причина', reason, False),
            ('Статус', '👑 Админ (только warn)' if is_admin else '👤 Участник', True),
        ],
        color=0xEF4444, user=message.author,
    ))


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    state = read_automod_state()
    m = state['modules']
    is_admin = isinstance(message.author, discord.Member) and message.author.guild_permissions.manage_guild

    # Проверка исключений (каналы и роли)
    if message.channel.id in state.get('whitelist_channels', []):
        await bot.process_commands(message)
        return
    if isinstance(message.author, discord.Member):
        user_role_ids = {r.id for r in message.author.roles}
        if user_role_ids & set(state.get('exempt_roles', [])):
            await bot.process_commands(message)
            return

    violations = []

    # --- 1. Анти-Мат (по словам) ---
    if m['badwords']['enabled'] and m['badwords']['words']:
        msg_words = set(re.findall(r'[\w\u0400-\u04FF]+', message.content.lower()))
        bad_found = msg_words & set(m['badwords']['words'])
        if bad_found:
            violations.append(('badwords', f'Запрещённые слова: {", ".join(bad_found)}'))

    # --- 2. Анти-Инвайты ---
    if not violations and m['invites']['enabled']:
        if re.search(r'(discord\.gg/|discord\.com/invite/|discordapp\.com/invite/)', message.content, re.I):
            violations.append(('invites', 'Ссылка-инвайт'))

    # --- 3. Анти-Эмодзи ---
    if not violations and m['emoji']['enabled']:
        emoji_count = len(re.findall(r'<a?:[^:]+:[0-9]+>', message.content)) + len(re.findall(r'[\U00010000-\U0010ffff]', message.content))
        if emoji_count > m['emoji']['limit']:
            violations.append(('emoji', f'{emoji_count} эмодзи (лимит {m["emoji"]["limit"]})'))

    # --- 4. Анти-Пинги ---
    if not violations and m['mentions']['enabled']:
        mention_count = len(message.mentions) + len(message.role_mentions) + (1 if '@everyone' in message.content or '@here' in message.content else 0)
        if mention_count > m['mentions']['limit']:
            violations.append(('mentions', f'{mention_count} упоминаний (лимит {m["mentions"]["limit"]})'))

    # --- 5. Анти-Caps ---
    if not violations and m['caps']['enabled']:
        alpha = [c for c in message.content if c.isalpha()]
        if len(alpha) >= 10:
            upper = sum(1 for c in alpha if c.isupper())
            pct = (upper / len(alpha)) * 100
            if pct > m['caps']['percent']:
                violations.append(('caps', f'{pct:.0f}% заглавных (лимит {m["caps"]["percent"]}%)'))

    # --- 6. Анти-Картинки (пакетная очистка) ---
    if not violations and m['images']['enabled'] and message.attachments:
        uid = message.author.id
        now = discord.utils.utcnow().timestamp()
        timestamps = bot.image_cache.get(uid, [])
        timestamps = [t for t in timestamps if now - t <= m['images']['interval']]
        timestamps.extend([now] * len(message.attachments))
        bot.image_cache[uid] = timestamps
        if len(timestamps) > m['images']['limit']:
            deleted = await _purge_user_messages(message.channel, uid, m['images']['interval'] + 30, only_images=True)
            bot.image_cache[uid] = []
            await _automod_punish(message, 'images', f'Спам картинками (удалено {deleted})', state)
            await bot.process_commands(message)
            return

    # --- 7. Анти-Спам (пакетная очистка) ---
    if not violations and m['spam']['enabled']:
        uid = message.author.id
        now = discord.utils.utcnow().timestamp()
        timestamps = bot.spam_cache.get(uid, [])
        timestamps = [t for t in timestamps if now - t <= m['spam']['interval']]
        timestamps.append(now)
        bot.spam_cache[uid] = timestamps
        if len(timestamps) > m['spam']['limit']:
            deleted = await _purge_user_messages(message.channel, uid, m['spam']['interval'] + 30)
            bot.spam_cache[uid] = []
            await _automod_punish(message, 'spam', f'Спам (удалено {deleted})', state)
            await bot.process_commands(message)
            return

    # --- Обработка остальных нарушений ---
    if violations:
        vtype, vdesc = violations[0]
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass
        await _automod_punish(message, vtype, vdesc, state)

    await bot.process_commands(message)


async def send_welcome_message(member: discord.Member) -> None:
    """Send a welcome embed to the welcome channel."""
    print(f'[WELCOME] Triggered for {member} ({member.id})')
    if not WELCOME_CHANNEL_ID:
        print(f'[WELCOME] No WELCOME_CHANNEL_ID set')
        return
    try:
        channel = bot.get_channel(WELCOME_CHANNEL_ID)
        print(f'[WELCOME] Channel from cache: {channel}')
        if channel is None:
            channel = await bot.fetch_channel(WELCOME_CHANNEL_ID)
            print(f'[WELCOME] Channel from API: {channel}')
        if not isinstance(channel, discord.TextChannel):
            print(f'[WELCOME] Channel is not TextChannel: {type(channel)}')
            return

        embed = discord.Embed(
            title=f'{member.display_name}, Добро пожаловать!',
            description=(
                f'📋 Ознакомься с <#1342073128112623667>\n'
                f'📩 Подавай <#1346126083363307651>\n\n'
                f'🎙️ И ждем тебя в войсе!'
            ),
            color=0xF59E0B,
        )
        embed.set_image(url=WELCOME_IMAGE_URL)
        embed.set_thumbnail(url=member.display_avatar.url if member.display_avatar else None)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text='YoungHill')

        # Пингуем участника отдельным сообщением
        await channel.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True),
        )
        print(f'[WELCOME] Message sent successfully')
    except Exception as exc:
        print(f'[WELCOME ERROR] {type(exc).__name__}: {exc}')

@bot.event
async def on_member_remove(member: discord.Member) -> None:
    roles = [r.mention for r in member.roles if r.name != '@everyone']
    role_list = ', '.join(roles[:10]) if roles else 'Нет ролей'

    asyncio.create_task(send_log(
        '📤 Участник вышел',
        fields=[
            ('Участник', _log_user_field(member), True),
            ('Роли', role_list, False),
            ('Участников', str(member.guild.member_count), True),
        ],
        color=0xFF6600, user=member,
    ))


# --------------- Voice state logging ---------------

@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState,
) -> None:
    if member.bot:
        return

    if before.channel is None and after.channel is not None:
        # Зашёл в войс
        asyncio.create_task(send_log(
            '🔊 Подключился к голосовому',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Канал', _log_channel_field(after.channel), True),
            ],
            color=0x22C55E, user=member,
        ))
    elif before.channel is not None and after.channel is None:
        # Вышел из войса
        asyncio.create_task(send_log(
            '🔇 Отключился от голосового',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Канал', _log_channel_field(before.channel), True),
            ],
            color=0xEF4444, user=member,
        ))
    elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        # Перешёл / перекинули в другой войс
        asyncio.create_task(send_log(
            '🔀 Перемещён в голосовом',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Откуда', _log_channel_field(before.channel), True),
                ('Куда', _log_channel_field(after.channel), True),
            ],
            color=0xF59E0B, user=member,
        ))


# --------------- Message edit / delete logging ---------------

def _truncate(text: str, limit: int = 1000) -> str:
    """Truncate text for embed fields."""
    if not text:
        return '*пусто*'
    if len(text) <= limit:
        return text
    return text[:limit] + '…'

def _message_link(message: discord.Message) -> str:
    if message.guild:
        return f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}'
    return ''

@bot.event
async def on_message_delete(message: discord.Message) -> None:
    if message.author.bot or message.guild is None:
        return

    content = _truncate(message.content) if message.content else '*нет текста (возможно вложение)*'
    link = _message_link(message)

    fields = [
        ('Участник', _log_user_field(message.author), True),
        ('Канал', _log_channel_field(message.channel), True),
        ('Содержимое', content, False),
    ]
    if link:
        fields.append(('Сообщение', f'[перейти]({link})', False))

    asyncio.create_task(send_log(
        '🗑️ Сообщение удалено',
        fields=fields,
        color=0xEF4444, user=message.author,
    ))

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if after.author.bot or after.guild is None:
        return
    if before.content == after.content:
        return  # embed update, pin, etc — не текстовое изменение

    link = _message_link(after)
    fields = [
        ('Участник', _log_user_field(after.author), True),
        ('Канал', _log_channel_field(after.channel), True),
        ('До', _truncate(before.content), False),
        ('После', _truncate(after.content), False),
    ]
    if link:
        fields.append(('Сообщение', f'[перейти]({link})', False))

    asyncio.create_task(send_log(
        '✏️ Сообщение изменено',
        fields=fields,
        color=0xF59E0B, user=after.author,
    ))


# --------------- Role change logging ---------------

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member) -> None:
    old_roles = set(before.roles)
    new_roles = set(after.roles)

    added = new_roles - old_roles
    removed = old_roles - new_roles

    if not added and not removed:
        return

    # Ищем кто выдал/забрал роль через raw API
    moderator = None
    await asyncio.sleep(2)
    try:
        guild_id = after.guild.id
        member_id = after.id
        action_type = discord.AuditLogAction.member_role_update.value
        url = f'https://discord.com/api/v10/guilds/{guild_id}/audit-logs?limit=20&action_type={action_type}'
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bot {BOT_TOKEN}'}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for entry in data.get('audit_log_entries', []):
                        if int(entry.get('target_id', 0)) == member_id:
                            user_id = entry.get('user_id')
                            if user_id:
                                moderator = after.guild.get_member(int(user_id))
                                if moderator is None:
                                    try:
                                        moderator = await after.guild.fetch_member(int(user_id))
                                    except Exception:
                                        pass
                            break
    except Exception:
        pass

    fields = [('Участник', _log_user_field(after), True)]
    if moderator:
        fields.append(('👤 Модератор', _log_user_field(moderator), True))
    if added:
        role_names = ', '.join(r.mention for r in added if r.name != '@everyone')
        if role_names:
            fields.append(('➕ Выданы', role_names, True))
    if removed:
        role_names = ', '.join(r.mention for r in removed if r.name != '@everyone')
        if role_names:
            fields.append(('➖ Забраны', role_names, True))

    asyncio.create_task(send_log(
        '🏷️ Изменение ролей',
        fields=fields,
        color=0x8B5CF6, user=after,
    ))


# --------------- Ban / Unban / Kick logging ---------------

@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User) -> None:
    await asyncio.sleep(2)
    moderator = None
    reason = ''
    try:
        url = f'https://discord.com/api/v10/guilds/{guild.id}/audit-logs?limit=10&action_type={discord.AuditLogAction.ban.value}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'Authorization': f'Bot {BOT_TOKEN}'}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for entry in data.get('audit_log_entries', []):
                        if int(entry.get('target_id', 0)) == user.id:
                            user_id = entry.get('user_id')
                            if user_id:
                                moderator = guild.get_member(int(user_id))
                                reason = entry.get('reason', '') or ''
                            break
    except Exception:
        pass

    fields = [('Участник', _log_user_field(user), True)]
    if moderator:
        fields.append(('👤 Модератор', _log_user_field(moderator), True))
    if reason:
        fields.append(('📝 Причина', reason, False))

    asyncio.create_task(send_log(
        '🔨 Бан',
        fields=fields,
        color=0xFF0000, user=user,
    ))


@bot.event
async def on_member_unban(guild: discord.Guild, user: discord.User) -> None:
    await asyncio.sleep(2)
    moderator = None
    try:
        url = f'https://discord.com/api/v10/guilds/{guild.id}/audit-logs?limit=10&action_type={discord.AuditLogAction.unban.value}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'Authorization': f'Bot {BOT_TOKEN}'}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for entry in data.get('audit_log_entries', []):
                        if int(entry.get('target_id', 0)) == user.id:
                            user_id = entry.get('user_id')
                            if user_id:
                                moderator = guild.get_member(int(user_id))
                            break
    except Exception:
        pass

    fields = [('Участник', _log_user_field(user), True)]
    if moderator:
        fields.append(('👤 Модератор', _log_user_field(moderator), True))

    asyncio.create_task(send_log(
        '✅ Разбан',
        fields=fields,
        color=0x00FF00, user=user,
    ))


# --------------- Member join / leave logging ---------------

# --------------- Channel logging ---------------

@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel) -> None:
    channel_type = 'Текстовый' if isinstance(channel, discord.TextChannel) else 'Голосовой' if isinstance(channel, discord.VoiceChannel) else 'Другой'
    asyncio.create_task(send_log(
        '📁 Канал создан',
        fields=[
            ('Канал', f'{channel.mention} (`{channel.id}`)', True),
            ('Тип', channel_type, True),
        ],
        color=0x00FF00,
    ))


@bot.event
async def on_guild_channel_delete(channel: discord.abc.GuildChannel) -> None:
    channel_type = 'Текстовый' if isinstance(channel, discord.TextChannel) else 'Голосовой' if isinstance(channel, discord.VoiceChannel) else 'Другой'
    asyncio.create_task(send_log(
        '🗑️ Канал удалён',
        fields=[
            ('Канал', f'#{channel.name} (`{channel.id}`)', True),
            ('Тип', channel_type, True),
        ],
        color=0xFF0000,
    ))


@bot.event
async def on_guild_channel_update(before: discord.abc.GuildChannel, after: discord.abc.GuildChannel) -> None:
    changes = []
    if before.name != after.name:
        changes.append(f'Название: `{before.name}` → `{after.name}`')
    if hasattr(before, 'bitrate') and hasattr(after, 'bitrate') and before.bitrate != after.bitrate:
        changes.append(f'Битрейт: {before.bitrate} → {after.bitrate}')
    if hasattr(before, 'user_limit') and hasattr(after, 'user_limit') and before.user_limit != after.user_limit:
        changes.append(f'Лимит: {before.user_limit} → {after.user_limit}')
    if before.category_id != after.category_id:
        changes.append('Категория изменена')

    if changes:
        asyncio.create_task(send_log(
            '📝 Канал изменён',
            fields=[
                ('Канал', f'{after.mention}', True),
                ('Изменения', '\n'.join(changes), False),
            ],
            color=0xF59E0B,
        ))


# --------------- Invite logging ---------------

@bot.event
async def on_invite_create(invite: discord.Invite) -> None:
    inviter = invite.inviter
    fields = [
        ('Инвайт', f'`{invite.code}`', True),
        ('Канал', f'{invite.channel.mention}' if invite.channel else 'Неизвестно', True),
    ]
    if inviter:
        fields.append(('👤 Создал', _log_user_field(inviter), True))
    if invite.max_uses:
        fields.append(('Лимит использований', str(invite.max_uses), True))
    if invite.max_age:
        fields.append(('Время жизни', f'{invite.max_age // 3600}ч', True))

    asyncio.create_task(send_log(
        '🔗 Инвайт создан',
        fields=fields,
        color=0x00FF00,
    ))


@bot.event
async def on_invite_delete(invite: discord.Invite) -> None:
    asyncio.create_task(send_log(
        '🔗 Инвайт удалён',
        fields=[
            ('Инвайт', f'`{invite.code}`', True),
            ('Канал', f'{invite.channel.mention}' if invite.channel else 'Неизвестно', True),
            ('Использований', str(invite.uses or 0), True),
        ],
        color=0xFF0000,
    ))


@tasks.loop(seconds=AUTO_REFRESH_SECONDS)
async def auto_refresh() -> None:
    await refresh_board_safely()
    await refresh_recruit_board_safely()
    await refresh_report_button_message_safely()
    await refresh_birthday_board_safely()
    await refresh_automod_board_safely()
    await refresh_application_board_safely()
    await refresh_recruit_app_banner_safely()
    await refresh_admin_panel_safely()

@bot.tree.command(name='family', description='Обновить таблицу состава семьи')
async def family(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('Принял, обновляю баннер в канале.', ephemeral=True)
    asyncio.create_task(send_log('📋 Команда /family', f'{interaction.user.mention} обновил состав семьи', color=0xF59E0B, user=interaction.user))
    asyncio.create_task(refresh_board_safely())

@bot.tree.command(name='recruit', description='Показать твою личную ссылку рекрута')
async def recruit(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member) or not has_recruit_role(interaction.user):
        await interaction.response.send_message('Эта команда доступна только рекрутам.', ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True, thinking=True)
    record = await create_or_get_recruit_invite(interaction.user)
    await refresh_recruit_board_safely()
    await interaction.followup.send(f'Твоя личная ссылка: {record["invite_url"]}\nПринял людей: {record.get("accepted_count", 0)}', ephemeral=True)
    asyncio.create_task(send_log(
        '🔗 Команда /recruit',
        f'{interaction.user.mention} запросил свою ссылку\n{record["invite_url"]}\nПринял людей: **{record.get("accepted_count", 0)}**',
        color=0x22C55E, user=interaction.user,
    ))

@bot.tree.command(name='report_invite', description='Отписать, кого ты пригласил')
async def report_invite(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member) or not has_recruit_role(interaction.user):
        await interaction.response.send_message('Эта команда доступна только рекрутам.', ephemeral=True)
        return
    asyncio.create_task(send_log('📝 Команда /report_invite', f'{interaction.user.mention} открыл форму отчёта', color=0x38BDF8, user=interaction.user))
    await interaction.response.send_modal(RecruitReportModal())

@bot.tree.command(name='birthday', description='Добавить или изменить свой день рождения')
async def birthday(interaction: discord.Interaction) -> None:
    asyncio.create_task(send_log('🎂 Команда /birthday', f'{interaction.user.mention} открыл форму дня рождения', color=0xF97316, user=interaction.user))
    await interaction.response.send_modal(BirthdayModal())

@bot.tree.command(name='recruits', description='Обновить плашку рекрутов')
@app_commands.default_permissions(manage_guild=True)
async def recruits(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('Обновляю плашку рекрутов.', ephemeral=True)
    asyncio.create_task(send_log('📋 Команда /recruits', f'{interaction.user.mention} обновил плашку рекрутов', color=0x22C55E, user=interaction.user))
    asyncio.create_task(refresh_recruit_board_safely())

@bot.tree.command(name='admin_panel', description='Обновить панель управления')
@app_commands.default_permissions(manage_guild=True)
async def admin_panel(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('Обновляю панель управления.', ephemeral=True)
    asyncio.create_task(send_log('⚙️ Команда /admin_panel', f'{interaction.user.mention} обновил панель управления', color=0xEF4444, user=interaction.user))
    asyncio.create_task(refresh_admin_panel_safely())

@bot.tree.command(name='clear', description='Удалить сообщения из канала')
@app_commands.describe(amount='Количество сообщений для удаления (1-100)')
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int) -> None:
    if amount < 1 or amount > 100:
        await interaction.response.send_message('Можно удалить от 1 до 100 сообщений.', ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    deleted = 0
    try:
        messages = [msg async for msg in interaction.channel.history(limit=amount + 1)]
        # Удаляем само сообщение команды тоже
        await interaction.channel.delete_messages(messages)
        deleted = len(messages)
    except discord.Forbidden:
        await interaction.followup.send('Нет права **Управление сообщениями**.', ephemeral=True)
        return
    except discord.HTTPException as exc:
        await interaction.followup.send(f'Ошибка: {exc}', ephemeral=True)
        return

    await interaction.followup.send(f'🗑️ Удалено **{deleted}** сообщений.', ephemeral=True)
    asyncio.create_task(send_log(
        '🗑️ Очистка канала',
        fields=[
            ('Модератор', _log_user_field(interaction.user), True),
            ('Канал', _log_channel_field(interaction.channel), True),
            ('Удалено', f'**{deleted}** сообщений', True),
        ],
        color=0xF59E0B, user=interaction.user,
    ))


# --------------- Slowmode ---------------

@bot.tree.command(name='slowmode', description='Установить слоу-мод в канале')
@app_commands.describe(seconds='Задержка в секундах (0 = выключить)')
@app_commands.default_permissions(manage_channels=True)
async def slowmode(interaction: discord.Interaction, seconds: int) -> None:
    if seconds < 0 or seconds > 21600:
        await interaction.response.send_message('Значение от 0 до 21600 секунд (6 часов).', ephemeral=True)
        return

    try:
        await interaction.channel.edit(slowmode_delay=seconds)
    except discord.Forbidden:
        await interaction.response.send_message('Нет права **Управление каналами**.', ephemeral=True)
        return

    if seconds == 0:
        text = '✅ Слоу-мод выключен.'
    else:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            text = f'✅ Слоу-мод: **{h}ч {m}м {s}с**'
        elif m:
            text = f'✅ Слоу-мод: **{m}м {s}с**'
        else:
            text = f'✅ Слоу-мод: **{s}с**'

    await interaction.response.send_message(text, ephemeral=True)
    asyncio.create_task(send_log(
        '🐌 Слоу-мод',
        fields=[
            ('Модератор', _log_user_field(interaction.user), True),
            ('Канал', _log_channel_field(interaction.channel), True),
            ('Задержка', f'**{seconds}** сек', True),
        ],
        color=0xF59E0B, user=interaction.user,
    ))


# --------------- Nuke (clone & delete) ---------------

class NukeConfirmView(discord.ui.View):
    def __init__(self, channel: discord.TextChannel):
        super().__init__(timeout=30)
        self.channel = channel

    @discord.ui.button(label='Да, нuke', style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message('Нет прав.', ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            new_channel = await self.channel.clone(reason=f'Nuke by {interaction.user}')
            await self.channel.delete(reason=f'Nuke by {interaction.user}')

            embed = discord.Embed(
                title='💥 Канал очищен',
                description=f'{new_channel.mention} — все сообщения удалены.',
                color=0xFF0000,
            )
            await new_channel.send(embed=embed)

            asyncio.create_task(send_log(
                '💥 Nuke',
                fields=[
                    ('Модератор', _log_user_field(interaction.user), True),
                    ('Канал', f'{new_channel.mention} (`{new_channel.id}`)', True),
                ],
                color=0xFF0000, user=interaction.user,
            ))
        except discord.Forbidden:
            await interaction.followup.send('Нет права **Управление каналами**.', ephemeral=True)

        self.stop()

    @discord.ui.button(label='Отмена', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('❌ Отменено.', ephemeral=True)
        self.stop()


@bot.tree.command(name='nuke', description='Полная очистка канала (clone + delete)')
@app_commands.default_permissions(manage_channels=True)
async def nuke(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message('Только для текстовых каналов.', ephemeral=True)
        return

    view = NukeConfirmView(interaction.channel)
    await interaction.response.send_message(
        '⚠️ **Внимание!** Все сообщения в канале будут удалены.\nКанал будет пересоздан.\n\nВы уверены?',
        view=view,
        ephemeral=True,
    )


# --------------- Embargo (temp ban) ---------------

class EmbargoModal(discord.ui.Modal, title='⏳ Embargo (временный бан)'):
    user_id_input = discord.ui.TextInput(label='ID пользователя', placeholder='926404329450143815')
    duration_input = discord.ui.TextInput(label='Длительность', placeholder='1d, 7d, 24h, 30m', max_length=10)
    reason_input = discord.ui.TextInput(label='Причина', placeholder='Нарушение правил', style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message('Нет прав.', ephemeral=True)
            return

        try:
            user_id = int(self.user_id_input.value.strip())
        except ValueError:
            await interaction.response.send_message('ID — число.', ephemeral=True)
            return

        duration_str = self.duration_input.value.strip().lower()
        total_seconds = 0
        try:
            if 'd' in duration_str:
                total_seconds = int(duration_str.replace('d', '')) * 86400
            elif 'h' in duration_str:
                total_seconds = int(duration_str.replace('h', '')) * 3600
            elif 'm' in duration_str:
                total_seconds = int(duration_str.replace('m', '')) * 60
            else:
                total_seconds = int(duration_str) * 86400
        except ValueError:
            await interaction.response.send_message('Неверный формат времени. Используй: `1d`, `24h`, `30m`', ephemeral=True)
            return

        if total_seconds < 60 or total_seconds > 2419200:
            await interaction.response.send_message('Длительность от 1 минуты до 28 дней.', ephemeral=True)
            return

        reason = self.reason_input.value.strip() or f'Embargo by {interaction.user}'

        try:
            member = await interaction.guild.fetch_member(user_id)
        except discord.NotFound:
            await interaction.response.send_message('Участник не найден на сервере.', ephemeral=True)
            return

        try:
            await member.ban(reason=reason, delete_message_days=0)
        except discord.Forbidden:
            await interaction.response.send_message('Нет права **Бан**.', ephemeral=True)
            return

        await interaction.response.send_message(
            f'⏳ **Embargo** — {member.mention} забанен на **{duration_str}**\nПричина: {reason}',
        )

        asyncio.create_task(send_log(
            '⏳ Embargo',
            fields=[
                ('Участник', _log_user_field(member), True),
                ('Модератор', _log_user_field(interaction.user), True),
                ('Длительность', f'**{duration_str}**', True),
                ('Причина', reason, False),
            ],
            color=0xFF6600, user=member,
        ))

        # Автоматический разбан через asyncio
        async def auto_unban(uid: int, guild_id: int, delay: int):
            await asyncio.sleep(delay)
            try:
                g = bot.get_guild(guild_id)
                if g:
                    await g.unban(discord.Object(id=uid), reason='Embargo истёк')
            except Exception:
                pass

        asyncio.create_task(auto_unban(user_id, interaction.guild.id, total_seconds))


@bot.tree.command(name='embargo', description='Временный бан через UI')
@app_commands.default_permissions(ban_members=True)
async def embargo(interaction: discord.Interaction) -> None:
    await interaction.response.send_modal(EmbargoModal())


class AnnouncementModal(discord.ui.Modal, title='📢 Объявление'):
    title_input = discord.ui.TextInput(label='Заголовок', placeholder='Важное объявление', max_length=100)
    message_input = discord.ui.TextInput(label='Текст', style=discord.TextStyle.paragraph, placeholder='Напиши сообщение...')
    channel_id_input = discord.ui.TextInput(label='ID канала', placeholder='1521295122204201163')

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('Нет прав.', ephemeral=True)
            return

        try:
            channel_id = int(self.channel_id_input.value.strip())
        except ValueError:
            await interaction.response.send_message('ID канала — число.', ephemeral=True)
            return

        channel = interaction.guild.get_channel(channel_id)
        if channel is None:
            try:
                channel = await interaction.guild.fetch_channel(channel_id)
            except Exception:
                await interaction.response.send_message('Канал не найден.', ephemeral=True)
                return

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message('Это не текстовый канал.', ephemeral=True)
            return

        embed = discord.Embed(
            title=f'📢 {self.title_input}',
            description=str(self.message_input),
            color=0xF59E0B,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_thumbnail(url=THUMBNAIL_URL)
        embed.set_footer(text=f'Объявление от {interaction.user.display_name}')

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message(f'Нет прав писать в {channel.mention}.', ephemeral=True)
            return

        await interaction.response.send_message(f'✅ Объявление отправлено в {channel.mention}', ephemeral=True)
        asyncio.create_task(send_log(
            '📢 Объявление',
            fields=[
                ('Модератор', _log_user_field(interaction.user), True),
                ('Канал', _log_channel_field(channel), True),
                ('Заголовок', self.title_input.value, False),
            ],
            color=0xF59E0B, user=interaction.user,
        ))



# --------------- Опросы ---------------

@bot.tree.command(name='poll', description='Создать опрос')
@app_commands.describe(question='Вопрос', options='Варианты через запятую (2-10)')
@app_commands.default_permissions(manage_guild=True)
async def poll(interaction: discord.Interaction, question: str, options: str):
    opts = [o.strip() for o in options.split(',') if o.strip()]
    if len(opts) < 2:
        await interaction.response.send_message('Нужно минимум 2 варианта.', ephemeral=True)
        return
    if len(opts) > 10:
        await interaction.response.send_message('Максимум 10 вариантов.', ephemeral=True)
        return

    emojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    lines = [f'{emojis[i]} {opt}' for i, opt in enumerate(opts)]

    embed = discord.Embed(
        title=f'📊 {question}',
        description='\n'.join(lines),
        color=0x3B82F6,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text=f'Опрос от {interaction.user.display_name}')

    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    for i in range(len(opts)):
        await msg.add_reaction(emojis[i])

    asyncio.create_task(send_log(
        '📊 Опрос',
        fields=[
            ('Модератор', _log_user_field(interaction.user), True),
            ('Канал', _log_channel_field(interaction.channel), True),
            ('Вопрос', question, False),
            ('Варианты', '\n'.join(f'{emojis[i]} {o}' for i, o in enumerate(opts)), False),
        ],
        color=0x3B82F6, user=interaction.user,
    ))


# --------------- Запланированные сообщения ---------------

scheduled_tasks: list[asyncio.Task] = []
SCHEDULE_STATE_FILE = Path(__file__).with_name('schedule-state.json')

def read_schedule_state() -> dict:
    state = read_json(SCHEDULE_STATE_FILE)
    state.setdefault('scheduled', [])
    return state

def write_schedule_state(data: dict) -> None:
    write_json(SCHEDULE_STATE_FILE, data)


async def restore_scheduled_tasks() -> None:
    """Восстанавливает запланированные задачи из state-файла после перезапуска."""
    state = read_schedule_state()
    now = discord.utils.utcnow()
    repeat_labels = {'none': 'без повтора', 'daily': 'ежедневно', 'weekly': 'еженедельно', 'monthly': 'ежемесячно'}
    repeat_intervals = {'daily': 86400, 'weekly': 604800, 'monthly': 2592000}

    remaining = []
    for entry in state.get('scheduled', []):
        try:
            send_at = datetime.fromisoformat(entry['send_at'])
        except Exception:
            continue

        delay = (send_at - now).total_seconds()

        if delay > 0:
            # Пробуем найти канал через fetch (надёжнее чем get_channel)
            ch = bot.get_channel(entry['channel_id'])
            if not ch:
                try:
                    ch = await bot.fetch_channel(entry['channel_id'])
                except Exception:
                    print(f'[SCHEDULE] Cannot fetch channel {entry["channel_id"]}')
                    remaining.append(entry)
                    continue

            if not isinstance(ch, discord.TextChannel):
                remaining.append(entry)
                continue

            msg = entry['message']
            rep = entry.get('repeat', 'none')

            async def _make_task(channel, message, wait, repeat_type):
                await asyncio.sleep(wait)
                embed = discord.Embed(description=message, color=0xF59E0B, timestamp=discord.utils.utcnow())
                embed.set_thumbnail(url=THUMBNAIL_URL)
                embed.set_footer(text=f'Запланированное • {repeat_labels.get(repeat_type, "")}')
                try:
                    await channel.send(embed=embed)
                    print(f'[SCHEDULE] Sent restored message to #{channel.name}')
                except Exception as exc:
                    print(f'[SCHEDULE] Restored task send FAILED: {exc}')
                    return
                if repeat_type != 'none' and repeat_type in repeat_intervals:
                    async def _rep(ch, msg, interval, rep):
                        while True:
                            await asyncio.sleep(interval)
                            e = discord.Embed(description=msg, color=0xF59E0B, timestamp=discord.utils.utcnow())
                            e.set_thumbnail(url=THUMBNAIL_URL)
                            e.set_footer(text=f'Повтор • {repeat_labels.get(rep, "")}')
                            try:
                                await ch.send(embed=e)
                            except Exception:
                                break
                    task = asyncio.create_task(_rep(ch, message, repeat_intervals[repeat_type], repeat_type))
                    scheduled_tasks.append(task)

            print(f'[SCHEDULE] Restoring: "{_truncate(msg, 30)}" -> #{ch.name} in {int(delay)}s')
            task = asyncio.create_task(_make_task(ch, msg, delay, rep))
            scheduled_tasks.append(task)
            remaining.append(entry)
        elif entry.get('repeat', 'none') != 'none':
            remaining.append(entry)

    state['scheduled'] = remaining
    write_schedule_state(state)
    print(f'[SCHEDULE] Restored {len(scheduled_tasks)} tasks')


REPEAT_OPTIONS = [
    app_commands.Choice(name='Без повтора', value='none'),
    app_commands.Choice(name='Ежедневно', value='daily'),
    app_commands.Choice(name='Еженедельно', value='weekly'),
    app_commands.Choice(name='Ежемесячно', value='monthly'),
]


class ScheduleModal(discord.ui.Modal, title='⏰ Запланировать сообщение'):
    msg_text = discord.ui.TextInput(
        label='Текст сообщения',
        style=discord.TextStyle.paragraph,
        placeholder='Напиши сообщение...',
        max_length=2000,
    )
    date_time = discord.ui.TextInput(
        label='Дата и время',
        placeholder='15.07.2026 18:00 ИЛИ 30m / 2h / 3d / 1w',
        max_length=30,
    )
    repeat = discord.ui.TextInput(
        label='Повтор (необязательно)',
        placeholder='none / daily / weekly / monthly',
        required=False,
        max_length=10,
    )
    channel_id = discord.ui.TextInput(
        label='ID канала (необязательно)',
        placeholder='Оставь пустым = текущий канал',
        required=False,
        max_length=20,
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message('Нет прав.', ephemeral=True)
            return

        # --- Канал ---
        if self.channel_id.value:
            try:
                ch_id = int(self.channel_id.value.strip())
            except ValueError:
                await interaction.response.send_message('ID канала — число.', ephemeral=True)
                return
            channel = interaction.guild.get_channel(ch_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                await interaction.response.send_message('Текстовый канал не найден.', ephemeral=True)
                return
        else:
            channel = interaction.channel

        # --- Парсим время ---
        now = discord.utils.utcnow()
        time_str = self.date_time.value.strip()
        send_at = None
        delay_seconds = None
        time_label = ''

        # Относительное: 30m / 2h / 3d / 1w
        relative_patterns = [
            (r'^(\d+)\s*(?:m|min|мин|минут)$', lambda v: timedelta(minutes=v), 'мин'),
            (r'^(\d+)\s*(?:h|hr|ч|час(?:а|ов)?)$', lambda v: timedelta(hours=v), 'час'),
            (r'^(\d+)\s*(?:d|д|день|дня|дней)$', lambda v: timedelta(days=v), 'дн'),
            (r'^(\d+)\s*(?:w|н|недел[яьи]|недель)$', lambda v: timedelta(weeks=v), 'нед'),
        ]

        for pattern, calc, label in relative_patterns:
            match = re.match(pattern, time_str.lower())
            if match:
                val = int(match.group(1))
                delay = calc(val)
                send_at = now + delay
                delay_seconds = int(delay.total_seconds())
                time_label = f'через **{val}** {label}'
                break

        # Абсолютное: 15.07.2026 18:00
        if send_at is None:
            from datetime import timezone
            is_MSK = time_str.upper().endswith(' MSK') or time_str.upper().endswith(' МСК')
            clean_time = re.sub(r'\s*(MSK|МСК)\s*$', '', time_str, flags=re.I).strip()

            for fmt in ('%d.%m.%Y %H:%M', '%d.%m.%Y %H:%M:%S', '%d.%m %H:%M'):
                try:
                    parsed = datetime.strptime(clean_time, fmt)
                    if parsed.year == 1900:
                        parsed = parsed.replace(year=now.year)
                    if is_MSK:
                        send_at = parsed.replace(tzinfo=timezone(timedelta(hours=3)))
                        time_label = f'**{send_at.strftime("%d.%m.%Y %H:%M")}** МСК'
                    else:
                        send_at = parsed.replace(tzinfo=timezone.utc)
                        time_label = f'**{send_at.strftime("%d.%m.%Y %H:%M")}** UTC'
                    delay_seconds = int((send_at - now).total_seconds())
                    break
                except ValueError:
                    continue

        if send_at is None or delay_seconds is None or delay_seconds < 0:
            await interaction.response.send_message(
                '❌ Не понял время.\n'
                'Форматы: `30m` `2h` `3d` `1w` `15.07.2026 18:00`',
                ephemeral=True,
            )
            return

        # --- Повтор ---
        repeat_val = (self.repeat.value or 'none').strip().lower()
        if repeat_val not in ('none', 'daily', 'weekly', 'monthly'):
            repeat_val = 'none'
        repeat_labels = {'none': 'без повтора', 'daily': 'ежедневно', 'weekly': 'еженедельно', 'monthly': 'ежемесячно'}

        # --- Сохраняем ---
        entry = {
            'message': self.msg_text.value,
            'channel_id': channel.id,
            'send_at': send_at.isoformat(),
            'repeat': repeat_val,
            'created_by': interaction.user.id,
            'created_at': now.isoformat(),
        }

        async with bot.automod_lock:
            state = read_schedule_state()
            state['scheduled'].append(entry)
            write_schedule_state(state)

        # --- Ответ ---
        await interaction.response.send_message(
            f'✅ Сообщение запланировано!\n'
            f'📅 **{time_label}**\n'
            f'📍 {channel.mention}\n'
            f'🔁 {repeat_labels[repeat_val]}',
            ephemeral=True,
        )

        asyncio.create_task(send_log(
            '⏰ Запланировано сообщение',
            fields=[
                ('Модератор', _log_user_field(interaction.user), True),
                ('Канал', _log_channel_field(channel), True),
                ('Отправка', time_label, True),
                ('Повтор', repeat_labels[repeat_val], True),
                ('Текст', _truncate(self.msg_text.value), False),
            ],
            color=0x3B82F6, user=interaction.user,
        ))

        # --- Запуск задачи ---
        ch_ref = channel
        msg_ref = self.msg_text.value
        rep_ref = repeat_val

        async def _send_once():
            await asyncio.sleep(delay_seconds)
            embed = discord.Embed(description=msg_ref, color=0xF59E0B, timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url=THUMBNAIL_URL)
            embed.set_footer(text=f'Запланированное сообщение • {repeat_labels[rep_ref]}')
            try:
                await ch_ref.send(embed=embed)
            except Exception as exc:
                print(f'[SCHEDULE] Send failed: {exc}')
                return
            if rep_ref != 'none':
                intervals = {'daily': 86400, 'weekly': 604800, 'monthly': 2592000}
                task = asyncio.create_task(_repeat_send(ch_ref, msg_ref, intervals[rep_ref], rep_ref))
                scheduled_tasks.append(task)

        async def _repeat_send(ch, msg, interval, rep):
            while True:
                await asyncio.sleep(interval)
                embed = discord.Embed(description=msg, color=0xF59E0B, timestamp=discord.utils.utcnow())
                embed.set_thumbnail(url=THUMBNAIL_URL)
                embed.set_footer(text=f'Повтор • {repeat_labels[rep]}')
                try:
                    await ch.send(embed=embed)
                except Exception:
                    break

        task = asyncio.create_task(_send_once())
        scheduled_tasks.append(task)


@bot.tree.command(name='schedule', description='Запланировать сообщение')
@app_commands.default_permissions(manage_guild=True)
async def schedule_cmd(interaction: discord.Interaction) -> None:
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message('Нет прав.', ephemeral=True)
        return
    await interaction.response.send_modal(ScheduleModal())


@bot.tree.command(name='schedules', description='Показать запланированные сообщения')
@app_commands.default_permissions(manage_guild=True)
async def schedules_cmd(interaction: discord.Interaction) -> None:
    state = read_schedule_state()
    scheduled = state.get('scheduled', [])

    if not scheduled:
        await interaction.response.send_message('📋 Нет запланированных сообщений.', ephemeral=True)
        return

    lines = []
    repeat_labels = {'none': '—', 'daily': 'ежедн.', 'weekly': 'еженед.', 'monthly': 'ежемес.'}
    for i, entry in enumerate(scheduled, 1):
        ch = interaction.guild.get_channel(entry['channel_id'])
        ch_name = ch.mention if ch else f'ID:{entry["channel_id"]}'
        rep = repeat_labels.get(entry.get('repeat', 'none'), '—')
        lines.append(f'**{i}.** {_truncate(entry["message"], 40)} → {ch_name} | `{rep}`')

    embed = discord.Embed(title='📋 Запланированные сообщения', description='\n'.join(lines[:20]), color=0x3B82F6)
    embed.set_footer(text=f'Всего: {len(scheduled)}')
    await interaction.response.send_message(embed=embed, ephemeral=True)


class ScheduleCancelSelect(discord.ui.Select):
    def __init__(self, scheduled: list[dict], guild: discord.Guild):
        options = []
        for i, entry in enumerate(scheduled[:25]):
            ch = guild.get_channel(entry['channel_id'])
            ch_name = ch.name if ch else '???'
            repeat_labels = {'none': '', 'daily': ' 🔄дн', 'weekly': ' 🔄нед', 'monthly': ' 🔄мес'}
            rep = repeat_labels.get(entry.get('repeat', 'none'), '')
            label = _truncate(entry['message'], 80)
            options.append(discord.SelectOption(
                label=label,
                description=f'#{ch_name}{rep}',
                value=str(i),
            ))
        super().__init__(placeholder='Выбери сообщение для отмены...', options=options)

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        state = read_schedule_state()
        scheduled = state.get('scheduled', [])

        if idx >= len(scheduled):
            await interaction.response.send_message('Сообщение уже удалено.', ephemeral=True)
            return

        removed = scheduled.pop(idx)
        async with bot.automod_lock:
            state['scheduled'] = scheduled
            write_schedule_state(state)

        await interaction.response.edit_message(
            content=f'❌ Отменено: **{_truncate(removed["message"], 60)}**',
            view=None,
        )

        asyncio.create_task(send_log(
            '❌ Отменено запланированное',
            fields=[('Модератор', _log_user_field(interaction.user), True), ('Текст', _truncate(removed['message']), False)],
            color=0xEF4444, user=interaction.user,
        ))


class ScheduleCancelView(discord.ui.View):
    def __init__(self, scheduled: list[dict], guild: discord.Guild):
        super().__init__(timeout=60)
        self.add_item(ScheduleCancelSelect(scheduled, guild))


@bot.tree.command(name='schedule_cancel', description='Отменить запланированное сообщение')
@app_commands.default_permissions(manage_guild=True)
async def schedule_cancel_cmd(interaction: discord.Interaction) -> None:
    state = read_schedule_state()
    scheduled = state.get('scheduled', [])

    if not scheduled:
        await interaction.response.send_message('📋 Нет запланированных сообщений.', ephemeral=True)
        return

    view = ScheduleCancelView(scheduled, interaction.guild)
    await interaction.response.send_message('Выбери сообщение для отмены:', view=view, ephemeral=True)


# --------------- Авто-правила ---------------

RULES_STATE_FILE = Path(__file__).with_name('rules-state.json')

def read_rules_state() -> dict:
    state = read_json(RULES_STATE_FILE)
    state.setdefault('rules', [
        '1. Уважай других участников — оскорбления и травля запрещены.',
        '2. Запрещён мат, спам и флуд.',
        '3. Нельзя рекламовать другие серверы и ссылки.',
        '4. Используй каналы по назначению.',
        '5. Слушай администрацию и модераторов.',
        '6. Запрещены NSFW контент и насилие.',
        '7. Не создавай фейковые аккаунты.',
        '8. Нарушение = предупреждение, повтор = мут/бан.',
    ])
    state.setdefault('message_id', None)
    return state

def write_rules_state(data: dict) -> None:
    write_json(RULES_STATE_FILE, data)


@bot.tree.command(name='rules', description='Показать правила сервера')
async def rules_cmd(interaction: discord.Interaction) -> None:
    state = read_rules_state()
    rules_text = '\n\n'.join(state['rules'])

    embed = discord.Embed(
        title='📜 Правила сервера',
        description=rules_text,
        color=0xF59E0B,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Незнание правил не освобождает от ответственности')

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='setrules', description='Установить правила сервера')
@app_commands.describe(rules='Правила через ; (каждое правило через точку с запятой)')
@app_commands.default_permissions(manage_guild=True)
async def setrules_cmd(interaction: discord.Interaction, rules: str) -> None:
    rules_list = [r.strip() for r in rules.split(';') if r.strip()]
    if len(rules_list) < 1:
        await interaction.response.send_message('Нужно минимум 1 правило.', ephemeral=True)
        return

    # Нумеруем правила
    numbered = [f'{i+1}. {r}' for i, r in enumerate(rules_list)]

    async with bot.automod_lock:
        state = read_rules_state()
        state['rules'] = numbered
        write_rules_state(state)

    rules_text = '\n\n'.join(numbered)
    embed = discord.Embed(
        title='📜 Правила сервера',
        description=rules_text,
        color=0xF59E0B,
        timestamp=discord.utils.utcnow(),
    )
    embed.set_thumbnail(url=THUMBNAIL_URL)
    embed.set_footer(text='Незнание правил не освобождает от ответственности')

    await interaction.response.send_message(embed=embed)

    asyncio.create_task(send_log(
        '📜 Правила обновлены',
        fields=[
            ('Модератор', _log_user_field(interaction.user), True),
            ('Правил', f'**{len(numbered)}**', True),
        ],
        color=0xF59E0B, user=interaction.user,
    ))


# --------------- Статистика ---------------

@bot.tree.command(name='stats', description='Показать статистику сервера')
async def stats_cmd(interaction: discord.Interaction) -> None:
    guild = interaction.guild
    if not guild:
        return

    online = sum(1 for m in guild.members if m.status != discord.Status.offline)
    bots = sum(1 for m in guild.members if m.bot)
    humans = guild.member_count - bots
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    roles = len(guild.roles) - 1  # minus @everyone
    boost = guild.premium_subscription_count or 0

    state = read_stats_state()
    total_messages = sum(state.get('messages', {}).values())
    total_voice = sum(state.get('voice', {}).values())

    embed = discord.Embed(
        title=f'📊 Статистика {guild.name}',
        color=0x3B82F6,
        timestamp=discord.utils.utcnow(),
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    embed.add_field(name='👥 Участники', value=f'Всего: **{guild.member_count}**\nЛюдей: **{humans}**\nБотов: **{bots}**\nОнлайн: **{online}**', inline=True)
    embed.add_field(name='📁 Каналы', value=f'Текстовых: **{text_channels}**\nГолосовых: **{voice_channels}**', inline=True)
    embed.add_field(name='🏷️ Роли', value=f'**{roles}**', inline=True)
    embed.add_field(name='🚀 Бусты', value=f'**{boost}**', inline=True)
    embed.add_field(name='📝 Сообщений (всего)', value=f'**{total_messages:,}**', inline=True)
    embed.add_field(name='🔊 Голос (всего)', value=format_voice_time(total_voice), inline=True)

    embed.set_footer(text=f'ID: {guild.id}')

    await interaction.response.send_message(embed=embed)


# --------------- Анти-рейд ---------------

raid_cache: dict[str, list[float]] = {}
RAID_THRESHOLD = 5       # сколько входов
RAID_WINDOW = 30          # за столько секунд
RAID_ACTION = 'alert'     # alert / lockdown / kick

async def check_raid(member: discord.Member) -> None:
    """Проверяет не является ли вход частью рейда."""
    guild = member.guild
    invite_code = None

    # Проверяем какой инвайт был использован
    try:
        current_invites = await guild.invites()
    except Exception:
        return

    previous = bot.invite_cache.get(guild.id, {})
    for inv in current_invites:
        old_uses = previous.get(inv.code, 0)
        new_uses = inv.uses or 0
        if new_uses > old_uses:
            invite_code = inv.code
            break

    # Если инвайт не найден — возможно рандомный вход
    key = invite_code or 'unknown'

    now = discord.utils.utcnow().timestamp()
    timestamps = raid_cache.get(key, [])
    timestamps = [t for t in timestamps if now - t <= RAID_WINDOW]
    timestamps.append(now)
    raid_cache[key] = timestamps

    if len(timestamps) >= RAID_THRESHOLD:
        raid_cache[key] = []

        # Уведомление в лог
        asyncio.create_task(send_log(
            '🚨 ВОЗМОЖНЫЙ РЕЙД!',
            fields=[
                ('Инвайт', f'`{invite_code}`' if invite_code else '**неизвестен**', True),
                ('Входов за секунд', f'**{RAID_THRESHOLD}+** за **{RAID_WINDOW}** сек', True),
                ('Последний участник', _log_user_field(member), True),
            ],
            color=0xFF0000, user=member,
        ))

        # Пинг админов
        admin_channel = guild.get_channel(LOG_CHANNEL_ID)
        if admin_channel and isinstance(admin_channel, discord.TextChannel):
            try:
                admins = [m for m in guild.members if m.guild_permissions.manage_guild and not m.bot]
                admin_mentions = ' '.join(a.mention for a in admins[:5])
                await admin_channel.send(
                    f'🚨 **ВОЗМОЖНЫЙ РЕЙД!** {RAID_THRESHOLD}+ входов за {RAID_WINDOW} сек через инвайт `{invite_code}`\n{admin_mentions}',
                    allowed_mentions=discord.AllowedMentions(users=True),
                )
            except Exception:
                pass


# --------------- Бот запускается ---------------

bot.run(BOT_TOKEN)

