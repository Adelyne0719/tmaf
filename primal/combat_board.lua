
RoundNumber = 0

-- UI 위치 계산을 위한 상수
local BASE_X = -98
local BASE_Z = -40
local START_Y = -76
local ROUND_STEP_Y = 16
local RESET_Y = -82

function OnRoundClick(player, value, id)
    local nextRound = RoundNumber
    
    -- 우클릭(value == "-2")일 경우 라운드 감소, 그 외(좌클릭 등)일 경우 라운드 증가
    if value == "-2" then
        nextRound = nextRound - 1
        if nextRound < 1 then nextRound = 10 end
    else
        nextRound = nextRound + 1
        if nextRound > 10 then nextRound = 1 end
    end
    
    SetRound(nextRound)
end

function SetRound(n)
    local isChanged = (RoundNumber ~= n)
    RoundNumber = n

    local y = START_Y + (ROUND_STEP_Y * RoundNumber)

    -- 라운드별 좌표 보정
    if RoundNumber > 3 then
        y = y + 1
    end

    local poslocal = BASE_X .. " " .. y .. " " .. BASE_Z
    self.UI.setAttribute("btnNextContainer", "position", poslocal)
    
    if isChanged and RoundNumber > 0 then
        broadcastToAll("▶▶ Round " .. RoundNumber .. " ◀◀", {r=1, g=1, b=1})
        Global.setVar("CurrentRound", RoundNumber)
    end
end

function ResetTimer()
    RoundNumber = 0
    local poslocal = BASE_X .. " " .. RESET_Y .. " " .. BASE_Z
    self.UI.setAttribute("btnNextContainer", "position", poslocal)
end