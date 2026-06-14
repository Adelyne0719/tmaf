import os
import re
import sys
import hgtk
import discord
import json
import asyncio  # 윈도우 이벤트 루프 설정을 위해 추가
from datetime import datetime
from discord.ext import commands
from hanspell_adelyne import spell_checker

# --- [추가] 윈도우 이벤트 루프 설정 ---
if os.name == 'nt':  # 'nt'는 Windows를 의미합니다.
    try:
        import winloop
        print("Winloop를 이벤트 루프로 설정합니다.")
        asyncio.set_event_loop_policy(winloop.EventLoopPolicy())
    except ImportError:
        print("winloop 라이브러리를 찾을 수 없습니다. 'pip install winloop'를 실행했는지 확인해주세요.")
# --- [추가 끝] ---


# --- [*** 수정 ***] 파일 경로 설정 (패키징 지원) ---
if getattr(sys, 'frozen', False):
    # .exe로 실행 중인 경우
    # .exe 파일이 있는 '실제 폴더' (e.g., dist 폴더)
    exe_dir = os.path.dirname(sys.executable)
    # .py가 풀리는 '임시 폴더' (_MEIPASS)
    temp_dir = os.path.dirname(os.path.abspath(__file__))
else:
    # .py 스크립트로 실행 중인 경우 (경로가 동일함)
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.dirname(os.path.abspath(__file__))

# 토큰 파일의 절대 경로
# token.txt는 --add-data로 인해 임시 폴더(temp_dir)에 풀림
token_path = os.path.join(temp_dir, "token.txt")
with open(token_path, "r") as f:
    TOKEN = f.read().strip()

# 횟수 저장 JSON 파일의 절대 경로
# .json 파일은 데이터 보존을 위해 '실제 폴더'(exe_dir)에 저장
COUNT_FILE = os.path.join(exe_dir, "spell_check_counts.json")
# --- [*** 수정 끝 ***] ---


# --- [*** NEW ***] 공통 접두사 찾기 헬퍼 함수 ---
def find_lcp(s1, s2):
    """두 문자열의 '최장 공통 접두사(LCP)'를 찾습니다."""
    length = min(len(s1), len(s2))
    for i in range(length):
        if s1[i] != s2[i]:
            return s1[:i] # 다른 문자가 나오면 그 앞까지 반환
    return s1[:length] # (e.g., "안녕", "안녕히") -> "안녕"
# --- [*** NEW ***] ---


# [추가] 횟수 로드 함수
def load_counts():
    if os.path.exists(COUNT_FILE):
        try:
            with open(COUNT_FILE, "r", encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # [수정] 파일이 손상된 경우, 덮어쓰는 대신 백업
            print(f"[경고] {COUNT_FILE} 파일이 손상되었습니다. 백업을 생성합니다.")
            backup_file_name = f"spell_check_counts_CORRUPTED_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = os.path.join(exe_dir, backup_file_name)
            try:
                # 파일 이름을 변경하여 백업
                os.rename(COUNT_FILE, backup_path)
                print(f"손상된 파일이 {backup_file_name} (으)로 백업되었습니다.")
            except Exception as e:
                print(f"백업 실패: {e}")
            return {}  # 새 딕셔너리로 시작
    else:
        return {}

# [추가] 횟수 저장 함수
def save_counts(counts):
    with open(COUNT_FILE, "w", encoding='utf-8') as f: # 인코딩 추가
        json.dump(counts, f, indent=4, ensure_ascii=False) # 한글 깨짐 방지

# Intents 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.typing = False
intents.presences = False

# [*** 수정 ***] 봇 객체 생성 (command_prefix="!")
bot = commands.Bot(command_prefix="!", intents=intents)

# 봇 시작 시 저장된 횟수를 불러옵니다.
user_spell_counts = load_counts()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    # 메시지 작성자가 봇인 경우 무시
    if message.author.bot:
        return

    # [*** 수정 ***] 메시지가 '!'로 시작하면 명령어 처리기로 넘기고, 맞춤법 검사는 종료
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    now = datetime.now()
    formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
    author_name = getattr(message.author, "global_name", message.author.name)
    print(f'{message.guild.name} {message.channel.name} {author_name} {formatted_now}')
    print(message.content)

    # --- [수정] 검사할 오류 그룹 정의 ---
    spell_check_groups = [
        {
            "family": "되/돼", # 오류 계열
            "inputs": ['되', '돼']
        }
        # (나중에 다른 맞춤법 규칙을 추가하고 싶다면 여기에 추가)
        # {
        #     "family": "안/않",
        #     "inputs": ['안', '않']
        # },
    ]
    
    # 한글 자음/모음 정의
    korean_vowel = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
    korean_consonants = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎㄲㄳㄶㄵㄸㄺㄻㄼㄽㄾㄿㅀㅄㅃㅆㅉ'
    
    word_list = message.content.split()
    
    final_differences = {}
    mistake_counts_by_subkey = {} 
    corrected_word_list = list(word_list) 

    
    # --- 그룹별로 루프 시작 ---
    for group in spell_check_groups:
        group_family = group["family"]    # e.g., "되/돼"
        input_list = group["inputs"]  # e.g., ['되', '돼']

        # (기존 자모 분해, 패턴 검색, matches_dict 생성 로직...)
        # 1. 현재 그룹의 input을 자모 분해
        decomposed_dict_input = {}
        for i, word in enumerate(input_list):
            decomposed_string = hgtk.text.decompose(word)
            decomposed_dict_input[i] = ''.join(decomposed_string)[:-1]

        # 2. 현재 단어 목록(다른 그룹에 의해 수정되었을 수 있음)을 자모 분해
        current_word_list_split = corrected_word_list
        current_decomposed_dict_word = {}
        for idx, word in enumerate(current_word_list_split):
            decomposed_word = hgtk.text.decompose(word)
            current_decomposed_dict_word[idx] = ''.join(decomposed_word)
        
        pattern_template = r'{input_value}[{korean_consonants}]*ᴥ'
        
        matches_dict = {}
        order_key = []
        order_text = []
        
        # 3. 현재 그룹의 input과 메시지 단어들을 비교
        for input_key, input_value in decomposed_dict_input.items():
            pattern = pattern_template.format(input_value=re.escape(input_value), korean_consonants=korean_consonants)
            
            for word_key, word_value in current_decomposed_dict_word.items():
                if word_key in final_differences:
                    continue 
                matches = re.findall(pattern, word_value)
                if matches:
                    if word_key not in order_key:
                        order_key.append(word_key)
                        order_text.append(current_word_list_split[word_key])
        
        sorted_keys = sorted(order_key)
        for key in sorted_keys:
            index = order_key.index(key)
            matches_dict[key] = order_text[index]
        
        # 4. 맞춤법 검사기 실행
        matches_dict_checked = {}
        if matches_dict:
            matches_text = ' '.join(matches_dict.values())
            
            try:
                checked_sentence = spell_checker.check(matches_text).checked
            except KeyError as e:
                print(f"[오류] hanspell API 응답 오류 (KeyError: {e}). 그룹 {group_family} 검사를 건너뜁니다.")
                continue 
            except Exception as e:
                print(f"[오류] hanspell 검사 중 예기치 않은 오류 발생: {e}. 그룹 {group_family} 검사를 건너뜁니다.")
                continue

            checked_sentence_list = checked_sentence.split()
            for idx, word in enumerate(checked_sentence_list):
                matches_dict_checked[idx] = word

            mdv = list(matches_dict.values())
            mdcv = list(matches_dict_checked.values())
            while len(mdv) != len(mdcv) and len(mdcv) > 1:
                for l in range(len(mdv)):
                    if len(mdv[l]) != len(mdcv[l]) and l+1 < len(mdcv):
                        mdcv[l] = mdcv[l] + mdcv[l+1]
                        del mdcv[l+1]
                        break
            
            matches_dict_checked_new = {}
            code = 0
            for key in matches_dict:
                if code < len(mdcv):
                    word_corrected = mdcv[code]
                    if len(word_corrected) - len(matches_dict[key]) == 1:
                        word_corrected = word_corrected[:-1]
                    matches_dict_checked_new[key] = word_corrected
                    code += 1
            matches_dict_checked = matches_dict_checked_new

            differences = {}
            for key in matches_dict_checked:
                if matches_dict.get(key) != matches_dict_checked.get(key):
                    differences[key] = (matches_dict[key], matches_dict_checked[key])
            
            # 5. 이 그룹에 해당하는 오류인지 필터링
            delete_keys = []
            for key, (orig, corr) in differences.items():
                for m in range(min(len(orig), len(corr))):
                    decomposed_orig = hgtk.text.decompose(orig[m])
                    decomposed_corr = hgtk.text.decompose(corr[m])
                    if decomposed_orig != decomposed_corr:
                        pattern_found = False
                        for input_word in input_list:
                            pattern = pattern_template.format(
                                input_value=re.escape(hgtk.text.decompose(input_word)[:-1]),
                                korean_consonants=korean_consonants
                            )
                            if re.findall(pattern, decomposed_orig):
                                pattern_found = True
                                break
                        if not pattern_found:
                            delete_keys.append(key)
                            break
            for key in delete_keys:
                if key in differences:
                    del differences[key]

            # 6. [*** 핵심 수정 ***]
            # '공통 접두사'를 제외한 '틀린 부분'을 동적으로 찾아 키로 사용
            if differences:
                for key, (orig, corr) in differences.items():
                    
                    # 1. 원본(orig)과 교정본(corr)의 공통 접두사(LCP)를 찾음
                    lcp = find_lcp(orig, corr)
                    
                    # 2. 공통 접두사를 제외한 나머지 '틀린 부분'을 추출
                    orig_part = orig[len(lcp):] # e.g., "되서"
                    corr_part = corr[len(lcp):] # e.g., "돼서"
                    
                    # 3. 이 '틀린 부분'을 고유 키(sub_key)로 생성
                    sub_key = f"{orig_part}→{corr_part}"
                    
                    # 하위 키(sub_key)를 기준으로 '이번 메시지' 횟수 집계
                    if sub_key:
                        mistake_counts_by_subkey[sub_key] = mistake_counts_by_subkey.get(sub_key, 0) + 1
                    
                    # 7. 최종 교정본 딕셔너리에 추가 및 다음 그룹을 위해 단어 목록 업데이트
                    final_differences[key] = (orig, corr)
                    corrected_word_list[key] = corr
    
    # --- 그룹별 루프 종료 ---


    # --- [수정] 메시지 전송 및 '총 누적 횟수' 저장/표시 로직 ---
    arrow_unicode = '\u2192'
    correction = []
    
    sorted_diff_keys = sorted(final_differences.keys())
    for key in sorted_diff_keys:
        orig, corr = final_differences[key]
        correction.append(f'{orig} {arrow_unicode} {corr}')
        print(f'교정 {key} : {orig} {arrow_unicode} {corr}')

    corrected_message = ' '.join(corrected_word_list) 

    if corrected_message != message.content and mistake_counts_by_subkey:
        user_id = str(message.author.id)
        
        # 1. '총 누적 횟수' 업데이트
        if user_id not in user_spell_counts:
            user_spell_counts[user_id] = {} 
        
        user_data = user_spell_counts[user_id]
        
        # 동적으로 생성된 '하위 키'를 그대로 user_data에 누적
        for sub_key, count_this_message in mistake_counts_by_subkey.items():
            user_data[sub_key] = user_data.get(sub_key, 0) + count_this_message
        
        # 2. 파일에 즉시 저장
        save_counts(user_spell_counts)
        
        # 3. [*** 수정 ***] '총 누적 횟수' 메시지 생성
        count_messages = []
        
        # '이번에 틀린' 키들의 '총 누적 횟수'를 표시
        for sub_key in mistake_counts_by_subkey.keys():
             # JSON 파일에 저장된 '총 누적 횟수'를 가져옴
             total_count = user_data.get(sub_key, 0)
             count_messages.append(f'{sub_key} {total_count}회')
        
        count_display = ", ".join(count_messages)

        # 4. 수정된 메시지 전송
        await message.channel.send(
            f'{message.author.mention} 님 틀림! {correction}\n'
            f'({count_display})' # (e.g., "되서→돼서 2회")
        )
            
    # [수정] 명령어 처리가 on_message 상단에서 처리되므로 이 줄은 필요 없음
    # await bot.process_commands(message)


# [*** 신규 ***] !통계 명령어
@bot.command(name="통계", aliases=["stats"])
async def stats(ctx, target_user: discord.Member = None): # [수정] User -> Member
    """
    지정한 유저(또는 자신)의 누적 맞춤법 오류 통계를 보여줍니다.
    사용법: !통계 @유저명
           !통계
    """
    
    # 1. 대상 유저가 지정되지 않았으면, 명령어를 쓴 사람으로 설정
    if target_user is None:
        target_user = ctx.author # ctx.author는 이미 Member 객체입니다.

    user_id = str(target_user.id)
    
    # 2. JSON 파일(user_spell_counts 변수)에서 유저 데이터 조회
    user_data = user_spell_counts.get(user_id)
    
    # 3. 데이터가 없는 경우
    if not user_data:
        # [수정] .name -> .display_name (닉네임 우선 표시)
        await ctx.send(f"**{target_user.display_name}** 님은 아직 맞춤법을 틀린 기록이 없습니다! 👍")
        return

    # 4. 데이터가 있는 경우, Embed로 예쁘게 만들기
    
    # 횟수가 많은 순서로 정렬
    sorted_stats = sorted(user_data.items(), key=lambda item: item[1], reverse=True)
    
    # Embed 메시지 생성
    embed = discord.Embed(
        # [수정] .name -> .display_name (닉네임 우선 표시)
        title=f"📊 {target_user.display_name} 님의 맞춤법 통계",
        color=discord.Color.blue()
    )
    
    # Description에 통계 목록 추가
    description_text = []
    for key, count in sorted_stats:
        description_text.append(f"• {key} **{count}회**")
    
    embed.description = "\n".join(description_text)
    
    await ctx.send(embed=embed)


bot.run(TOKEN)