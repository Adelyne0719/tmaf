-- 보드 기준 로컬 좌표 (1단계에서 얻은 값 입력)
PIERCE_SNAP_LOCAL_POSITIONS = {
    [0] = {x=-0.263, y=5.395, z=0.493},
    [1] = {x=-0.354, y=5.395, z=0.493},
    [2] = {x=-0.447, y=5.395, z=0.493},
    [3] = {x=-0.540, y=5.395, z=0.493},
    [4] = {x=-0.631, y=5.395, z=0.493},
}
PIERCE_SNAP_DISTANCE = 0.3   -- 매치 거리 (조정 가능)

function onLoad()
    -- 초기 한 번 갱신 (게임 시작 시 위치 확인)
    Wait.time(updatePierceDescription, 1)
end

function onDrop(color)
    Wait.time(updatePierceDescription, 0.3)
end

function onPickUp(color)
    -- 들렸을 때는 description 비우기 (선택)
    self.setDescription('')
end

-- 현재 토큰이 올라간 플레이어 보드 찾기 (거리 기준 가장 가까운 보드)
function findCurrentBoard()
    local myPos = self.getPosition()
    local closestBoard = nil
    local minDistance = 999999
    
    for _, board in ipairs(getObjectsWithTag('player_board')) do
        local bPos = board.getPosition()
        local dx = myPos.x - bPos.x
        local dz = myPos.z - bPos.z
        local dist = math.sqrt(dx*dx + dz*dz)
        if dist < minDistance then
            minDistance = dist
            closestBoard = board
        end
    end
    
    -- 안전 장치: 가장 가까운 보드라 해도 일정 거리(예: 15) 이내여야 함
    if minDistance < 15 then
        return closestBoard
    end
    return nil
end

-- 토큰이 어느 자석 포인트에 있는지 (없으면 nil)
function findSnapValue()
    local board = findCurrentBoard()
    if not board then return nil end

    local lp = board.positionToLocal(self.getPosition())

    local closestIdx = nil
    local closestDist = PIERCE_SNAP_DISTANCE   -- 임계값

    for idx, snapPos in pairs(PIERCE_SNAP_LOCAL_POSITIONS) do
        local dx = snapPos.x - lp.x
        local dz = snapPos.z - lp.z
        local dist = math.sqrt(dx*dx + dz*dz)
        if dist < closestDist then
            closestDist = dist
            closestIdx = idx
        end
    end

    return closestIdx
end

-- description 갱신 및 owner 태그 동적 변경
function updatePierceDescription()
    local value = findSnapValue()
    if value ~= nil then
        self.setDescription(tostring(value))
    else
        self.setDescription('')
    end
    
    updateOwnerTag()
end

function updateOwnerTag()
    local board = findCurrentBoard()
    local targetTag = nil
    
    if board then
        local boardColor = nil
        if board.hasTag('color_blue') then boardColor = 'Blue'
        elseif board.hasTag('color_green') then boardColor = 'Green'
        elseif board.hasTag('color_yellow') then boardColor = 'Yellow'
        elseif board.hasTag('color_orange') then boardColor = 'Orange'
        elseif board.hasTag('color_red') then boardColor = 'Red'
        end
        
        if boardColor then
            targetTag = 'owner_' .. boardColor
        end
    end
    
    local tags = self.getTags()
    local newTags = {}
    for _, t in ipairs(tags) do
        -- 기존 owner_ 태그 제거
        if not t:find('owner_') then
            table.insert(newTags, t)
        end
    end
    
    -- 새로운 보드의 owner_ 태그 추가
    if targetTag then
        table.insert(newTags, targetTag)
    end
    
    self.setTags(newTags)
end