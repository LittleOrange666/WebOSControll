from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
from loguru import logger

from modules.tools import run_alarm, get_env, test_alarm

TOKEN = get_env("DC_TOKEN")


class AlarmBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

        self.alarm_time = None
        self.is_enabled = False
        self.alarm_duration = 60
        self.alarm_volume = 15

    async def setup_hook(self):
        self.check_alarm.start()
        await self.tree.sync()

    @tasks.loop(seconds=30)
    async def check_alarm(self):
        if not self.is_enabled or self.alarm_time is None:
            return

        now = datetime.now().time()
        if now.hour == self.alarm_time.hour and now.minute == self.alarm_time.minute:
            logger.info("觸發鬧鐘！")
            self.is_enabled = False
            await run_alarm(self.alarm_duration, self.alarm_volume)

    @check_alarm.before_loop
    async def before_check_alarm(self):
        await self.wait_until_ready()


bot = AlarmBot()


@bot.tree.command(name="set_alarm", description="設置鬧鐘時間 (格式 HH:MM)")
@app_commands.describe(time_str="請輸入 24 小時制時間，例如 08:30")
async def set_alarm(interaction: discord.Interaction, time_str: str):
    try:
        t = datetime.strptime(time_str, "%H:%M").time()
        bot.alarm_time = t
        bot.is_enabled = True
        await interaction.response.send_message(f"✅ 鬧鐘已設定為 **{t.strftime('%H:%M')}**，目前狀態：**ON**")
    except ValueError:
        await interaction.response.send_message("❌ 格式錯誤！請使用 HH:MM 格式（例如 07:00 或 23:15）。", ephemeral=True)


@bot.tree.command(name="switch", description="開啟或關閉鬧鐘")
@app_commands.choices(status=[
    app_commands.Choice(name="ON", value="on"),
    app_commands.Choice(name="OFF", value="off")
])
async def switch(interaction: discord.Interaction, status: app_commands.Choice[str]):
    if status.value == "on":
        if bot.alarm_time is None:
            await interaction.response.send_message("⚠️ 尚未設定鬧鐘時間，請先使用 `/set_alarm`。", ephemeral=True)
            return
        bot.is_enabled = True
        await interaction.response.send_message(f"⏰ 鬧鐘已 **開啟** (設定時間: {bot.alarm_time.strftime('%H:%M')})")
    else:
        bot.is_enabled = False
        await interaction.response.send_message("🔕 鬧鐘已 **關閉**")

@bot.tree.command(name="check", description="檢查鬧鐘可否運行")
async def stat(interaction: discord.Interaction):
    await interaction.response.defer()
    success = await test_alarm()
    if success:
        await interaction.followup.send("✅ 鬧鐘連線測試成功！系統可以正常運行。")
    else:
        await interaction.followup.send("❌ 鬧鐘連線測試失敗！請檢查鬧鐘狀態。")


@bot.tree.command(name="stat", description="查看鬧鐘狀態與倒數")
async def stat(interaction: discord.Interaction):
    if bot.alarm_time is None:
        await interaction.response.send_message("🔔 目前尚未設定鬧鐘時間。")
        return

    now = datetime.now()
    target_dt = datetime.combine(now.date(), bot.alarm_time)

    if target_dt <= now:
        target_dt += timedelta(days=1)

    time_diff = target_dt - now
    hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)

    status_emoji = "🟢 ON" if bot.is_enabled else "🔴 OFF"

    embed = discord.Embed(
        title="⏰ 鬧鐘詳細狀態",
        color=discord.Color.green() if bot.is_enabled else discord.Color.light_grey()
    )
    embed.add_field(name="設定時間", value=f"`{bot.alarm_time.strftime('%H:%M')}`", inline=True)
    embed.add_field(name="開關狀態", value=f"**{status_emoji}**", inline=True)
    embed.add_field(name="音量 / 時長", value=f"🔊 `{bot.alarm_volume}%` / ⏳ `{bot.alarm_duration}s`", inline=False)

    if bot.is_enabled:
        embed.add_field(name="距離響鈴還有", value=f"**{hours} 小時 {minutes} 分鐘**", inline=False)
    else:
        embed.add_field(name="距離響鈴還有", value="*鬧鐘已關閉*", inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_duration", description="設定鬧鐘響鈴持續時間（秒）")
@app_commands.describe(seconds="請輸入響鈴持續的秒數（例如：30）")
async def set_duration(interaction: discord.Interaction, seconds: int):
    if seconds <= 0:
        await interaction.response.send_message("❌ 秒數必須是大於 0 的整數！", ephemeral=True)
        return

    bot.alarm_duration = seconds

    await interaction.response.send_message(f"✅ 鬧鐘響鈴時長已設定為 **{seconds}** 秒。")

@bot.tree.command(name="set_volume", description="設定鬧鐘音量 (0-100)")
@app_commands.describe(volume="請輸入 0 到 100 之間的整數")
async def set_volume(interaction: discord.Interaction, volume: int):
    if 0 <= volume <= 100:
        bot.alarm_volume = volume
        await interaction.response.send_message(f"🔊 音量已設定為 **{volume}%**")
    else:
        await interaction.response.send_message("❌ 請輸入有效的音量範圍 (0-100)。", ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)