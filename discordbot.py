import os
import discord
import requests
import youtube_dl
import logging
from discord.ext import commands

# 봇 설정
PREFIX = '!'  # 봇의 명령어 접두사

intents = discord.Intents.default()
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# 경고 시스템을 위한 딕셔너리
warnings = {}

# 웹 서버 정보
WEB_SERVER_URL: str = 'https://github.com/TimeSpaceG/tpsaceg4.git'

# 로깅 설정
logging.basicConfig(filename='bot.log', level=logging.INFO)

# 토큰 관리: 환경 변수에서 토큰 가져오기
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
if not TOKEN:
    logging.error('봇 토큰이 설정되지 않았습니다. 프로그램을 종료합니다.')
    exit()

# 허가된 사용자 목록 (사용자 ID)
AUTHORIZED_USERS = [1234567890, 2345678901]  # 허가된 사용자의 ID를 여기에 추가하세요

# 디스코드 권한 설정
BOT_PERMISSIONS = discord.Permissions(
    send_messages=True,
    read_messages=True,
    connect=True,
    speak=True,
    # 필요한 권한을 추가로 설정하세요
)

# 봇이 명령어를 사용할 수 있는 권한을 가진 사용자인지 확인하는 데 사용되는 함수
def is_authorized(ctx):
    return ctx.author.id in AUTHORIZED_USERS

# 봇이 음성 채널에 연결할 권한이 있는지 확인하는 데 사용되는 함수
def has_voice_permissions(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return False
    permissions = ctx.author.voice.channel.permissions_for(ctx.me)
    return permissions.connect and permissions.speak

# 명령어 실행 전에 권한을 확인하는 데 사용되는 데코레이터
def check_permissions():
    async def predicate(ctx):
        if not is_authorized(ctx):
            await ctx.send("해당 명령어를 실행할 권한이 없습니다.")
            return False
        if not has_voice_permissions(ctx):
            await ctx.send("음성 채널에 연결할 권한이 없습니다.")
            return False
        return True
    return commands.check(predicate)

# "안녕하세요" 명령어 처리
@bot.command(name='정애니맨안녕')
@check_permissions()  # 데코레이터 추가
async def say_hello(ctx):
    await ctx.send('안녕하세요! 정애니맨님')

# 음성 채널 지원: 음성 채널 입장
@bot.command(name='들어와')
@check_permissions()  # 데코레이터 추가
async def join_voice(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()

# 추방된 사용자를 알리는 함수
async def notify_ban(member):
    # 추방된 사용자 정보를 웹 서버로 전송합니다.
    url = f'{WEB_SERVER_URL}/ban_notification'
    data = {'user_id': member.id}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print('Ban notification sent successfully')
    else:
        print('Failed to send ban notification')

# 사용자를 추방하는 함수
async def kick_user(user, reason):
    await user.kick(reason=reason)

# 사용자에게 경고를 보내는 함수
async def warn_user(user):
    await user.send("경고를 받았습니다.")

# 경고 횟수를 확인하고 3회 이상이면 사용자를 추방하는 함수
async def check_warnings(user, kick_reasons=None):
    user_id = user.id
    if user_id in warnings and warnings[user_id] >= 3:
        kick_reason = kick_reasons.get(user_id, "경고 3회 누적")
        await kick_user(user, kick_reason)
    else:
        await warn_user(user)

# 추방 이유를 저장하는 함수
def record_kick_reason(user_id, reason, kick_reasons=None):
    kick_reasons[user_id] = reason

# 관리자에게 메시지를 보내는 예시 명령어
@bot.command(name='send_message_to_admin')
async def send_message_to_admin(ctx, *, message):
    # 관리자의 ID
    admin_id = 610708164572086284  # 여기에 관리자의 ID를 입력합니다.

    # 관리자에게 메시지를 보냅니다.
    admin = bot.get_user(admin_id)
    if not admin:
        await ctx.send("관리자를 찾을 수 없습니다.")
    else:
        await admin.send(message)
        await ctx.send("메시지를 관리자에게 전송했습니다.")

# 추방 이벤트를 처리하는 코드
@bot.event
async def on_member_remove(member):
    # 추방된 멤버의 정보를 가져옵니다.
    guild = member.guild
    ban_reason = None  # 추방된 이유
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target == member:
            ban_reason = entry.reason
            break

    # 추방된 이유가 경고 시스템과 관련된 것인지 확인합니다.
    if ban_reason == '경고 3회 누적':
        await notify_ban(member)

# 음성 채널 지원: 음성 채널 입장
@bot.command(name='봇들어와')
@check_permissions()  # 데코레이터 추가
async def join_voice(ctx):
    channel = ctx.author.voice.channel
    if channel:
        await channel.connect()
    else:
        await ctx.send("음성 채널에 먼저 들어가주세요.")

# 일시 정지
@bot.command(name='일시정지')
async def pause(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("음악을 일시 정지했습니다.")
    else:
        await ctx.send("현재 재생 중인 음악이 없습니다.")


# 정지
@bot.command(name='정지')
async def stop(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("음악을 정지했습니다.")
    else:
        await ctx.send("현재 재생 중인 음악이 없습니다.")


# 자동 초기화
@bot.command(name='재시작')
async def restart(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send("현재 재생 중인 음악이 없습니다.")
    await voice_client.disconnect()
    await ctx.send("음성 채널에서 나갔습니다. 다시 들어올게요!")


# 일부 반복
@bot.command(name='일부반복')
async def repeat_some(ctx, times: int):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        for i in range(times):
            voice_client.stop()
            await ctx.send(f"음악을 일부 반복 중입니다. 반복 횟수: {i + 1}")
    else:
        await ctx.send("현재 재생 중인 음악이 없습니다.")


# 전체 반복
@bot.command(name='전체반복')
async def repeat_all(ctx):
    voice_client = ctx.voice_client
    if voice_client.is_playing():
        voice_client.stop()
        await ctx.send("음악을 전체 반복합니다.")
    else:
        await ctx.send("현재 재생 중인 음악이 없습니다.")


# 경고 부여
@bot.command(name='경고')
async def give_warning(ctx, member: discord.Member):
    if member.id not in warnings:
        warnings[member.id] = 1
    else:
        warnings[member.id] += 1
    await ctx.send(f'{member.mention}님에게 경고를 부여하였습니다. 현재 경고 횟수: {warnings[member.id]}')

    # 3회 이상 경고를 받은 경우 추방
    if warnings[member.id] >= 3:
        await member.send("3회 이상 경고를 받아서 서버에서 추방되었습니다.")
        await member.kick(reason="3회 이상 경고를 받음")
        await ctx.send(f"{member.mention}님이 서버에서 추방되었습니다.")

        # 관리자에게 메시지 전송
        admin_role = discord.utils.get(ctx.guild.roles, name="관리자")
        for admin in ctx.guild.members:
            if admin_role in admin.roles:
                await admin.send(f"{member.mention}님이 서버에서 추방되었습니다.")

        # 추방된 사용자를 알리는 역할 부여
        ban_role = discord.utils.get(ctx.guild.roles, name="추방된 사용자")
        await member.add_roles(ban_role)


# 음악 재생
@bot.command(name='재생')
async def play(ctx, url):
    # 봇이 음성 채널에 없으면 입장
    if not ctx.voice_client:
        channel = ctx.author.voice.channel
        await channel.connect()

    # YouTube 영상 다운로드 및 재생
    voice_client = ctx.voice_client
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        voice_client.play(discord.FFmpegPCMAudio(url2), after=lambda e: print('재생 완료', e))



# 봇 실행
bot.run(TOKEN)
