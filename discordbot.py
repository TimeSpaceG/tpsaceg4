import discord
from discord.ext import commands
import youtube_dl
import os

# 봇 설정
TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
PREFIX = os.environ.get('PREFIX', '!')  # PREFIX 환경 변수를 가져오고, 없으면 기본값 '!'을 사용합니다.

intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# 경고 시스템을 위한 딕셔너리
warnings = {}

# 봇이 준비되었을 때 실행할 코드
@bot.event
async def on_ready():
    print(f'{bot.user}이(가) 성공적으로 로그인했습니다.')

# "안녕하세요" 명령어 처리
@bot.command(name='정애니맨안녕')
async def say_hello(ctx):
    await ctx.send('안녕하세요! 정애니맨님')

# 음성 채널 지원: 음성 채널 입장
@bot.command(name='들어와')
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
