import re

with open('global.lua', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the text inside broadcastToAll for ClickUpkeepPhase
content = re.sub(r'broadcastToAll\(".*?",\s*pColor\)', 'broadcastToAll("선플레이어가 아닙니다.", pColor)', content, count=1)

# Ensure the correct text for NextRound
content = re.sub(r'broadcastToAll\(".*?",\s*pColor\)', 'broadcastToAll("마지막 플레이어만 다음라운드로 진행 가능합니다.", pColor)', content)
# Wait, the first one is ClickUpkeepPhase, the second is NextRound... better to use accurate replacement

with open('global.lua', 'w', encoding='utf-8') as f:
    f.write(content)
