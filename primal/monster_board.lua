TOKENS = {
    ['Struggle']            = { tag = 'bag_struggle' },
    ['Acceleration']        = { tag = 'bag_acceleration' },
    ['Dust']                = { tag = 'bag_dust' },
    ['Vulnerable']          = { tag = 'bag_vulnerable' },
    ['Shard']               = { tag = 'bag_shard' },
    ['Confused']            = { tag = 'bag_confused' },
    ['Thornvine']           = { tag = 'bag_thornvine' },
    ['Stunned']             = { tag = 'bag_stunned' },
    ['Trigger']             = { tag = 'bag_trigger' },
    ['Blinded']             = { tag = 'bag_blinded' },
    ['BonusMonsterDamage']  = { tag = 'bag_bonus_m_damage' },
    ['Counter']             = { tag = 'bag_counter' },
    ['Slow']                = { tag = 'bag_slow' },
}

-- 체력, 경화, 충전 토큰 트래커 설정
local HEALTH_ROTATION_WORLD = {0, 135, 0}  -- 체력 토큰 회전값
local HARD_ROTATION_WORLD = {0, 225, 0}    -- 경화 토큰 회전값
local CHARGE_ROTATION_WORLD = {0, 135, 0}  -- 충전 토큰 회전값 (필요 시 따로 수정 가능)
local GLACIATION_ROTATION_WORLD = {0, 135, 0}  -- 빙결 토큰 회전값
local VIBRATION_ROTATION_WORLD = {0, 135, 0}  -- 진동 토큰 회전값
local CombatBoardGUIDs = {"cf5fc6", "7e2f97", "3d46a1", "e7e719", "822930", "0c1ffc", "20af28", "39cd16", "a25d70", "28124b", "21c822"}

-- 몬스터 표시값 (저장됨)
monster_damage = 0
monster_toughness = 0

-- 키보드 숫자 입력용 버퍼 및 상태 변수
damage_input_buffer = ''
damage_delay_started = false
toughness_input_buffer = ''
toughness_delay_started = false
current_hover_target = nil  -- XML UI에서 호버 감지된 타겟 ('damage' or 'toughness' or nil)
_currentStanceHasResistance = false
_currentStanceBaseToughness = -1
_currentStanceID = ""
_previousToughness = 0
_previousStanceHasResistance = false
_recentWoundToughness = 0
_lastToughnessUpdate = 0 

is_escalation_button_visible = false
is_escalating = false
escalation_btn_index = -1

is_struggle_btn_visible = false
is_struggle_reconstructing = false
struggle_btn_index = -1

_struggleBroadcastTimer = nil
_struggleBroadcastDiff = 0
_struggleBroadcastOldValue = nil

_accelBroadcastTimer = nil
_accelBroadcastDiff = 0
_accelBroadcastOldValue = nil

function queueStruggleBroadcast(diff)
    if _struggleBroadcastOldValue == nil then
        _struggleBroadcastOldValue = Global.call("getStruggleCount") or 0
    end
    _struggleBroadcastDiff = _struggleBroadcastDiff + diff
    if _struggleBroadcastTimer then Wait.stop(_struggleBroadcastTimer) end
    _struggleBroadcastTimer = Wait.time(function()
        if _struggleBroadcastDiff ~= 0 then
            local symbol = _struggleBroadcastDiff > 0 and '+' or ''
            local newValue = math.max(0, _struggleBroadcastOldValue + _struggleBroadcastDiff)
            printToAll(string.format('격앙 토큰: %d → %d (%s%d)', 
                _struggleBroadcastOldValue, newValue, symbol, _struggleBroadcastDiff), {0.2, 0.5, 1})
        end
        _struggleBroadcastDiff = 0
        _struggleBroadcastOldValue = nil
        _struggleBroadcastTimer = nil
    end, 0.5)
end

function queueAccelBroadcast(diff)
    if _accelBroadcastOldValue == nil then
        _accelBroadcastOldValue = Global.call("getAccelCount") or 0
    end
    _accelBroadcastDiff = _accelBroadcastDiff + diff
    if _accelBroadcastTimer then Wait.stop(_accelBroadcastTimer) end
    _accelBroadcastTimer = Wait.time(function()
        if _accelBroadcastDiff ~= 0 then
            local symbol = _accelBroadcastDiff > 0 and '+' or ''
            local newValue = math.max(0, _accelBroadcastOldValue + _accelBroadcastDiff)
            printToAll(string.format('가속 토큰: %d → %d (%s%d)', 
                _accelBroadcastOldValue, newValue, symbol, _accelBroadcastDiff), {0.2, 0.8, 1})
        end
        _accelBroadcastDiff = 0
        _accelBroadcastOldValue = nil
        _accelBroadcastTimer = nil
    end, 0.5)
end

function addSub(a, b, ButtonID)
    if ButtonID == "plusStr" then
        Global.call("addStruggle", 1)
        Global.call("ScheduleCheckEruption")
        queueStruggleBroadcast(1)
    elseif ButtonID == "minusStr" then
        local removed = Global.call("removeStruggle")
        if removed then
            queueStruggleBroadcast(-1)
        end
    elseif ButtonID == "plusAcc" then
        Global.call("addAccel", 1)
        queueAccelBroadcast(1)
    else
        local removed = Global.call("removeAccel")
        if removed then
            queueAccelBroadcast(-1)
        end
    end
end

function showEscalationButton()
    if is_escalation_button_visible then return end
    
    self.editButton({
        index = escalation_btn_index,
        label = '격화',
        width = 800,
        height = 1150,
    })
    is_escalation_button_visible = true
end

function hideEscalationButton()
    if not is_escalation_button_visible then return end
    self.editButton({
        index = escalation_btn_index,
        label = '',
        width = 0,
        height = 0,
    })
    is_escalation_button_visible = false
end

function checkEscalationButton()
    if is_escalating then return end
    
    local deckPos = {x=13.90, y=1.01, z=10.41}
    local discardPos = {x=28.09, y=0.86, z=10.33}
    local currentMonsterName = getMonsterName()
    if currentMonsterName == "Awakened" or currentMonsterName == "어웨이큰" then
        discardPos = {x=39.23, y=0.8, z=10.48}
    end
    
    local function getCardAt(pos)
        local hits = Physics.cast({
            origin       = {pos.x, pos.y + 1.5, pos.z},
            direction    = {0, -1, 0},
            type         = 3,
            size         = {2.5, 2, 2.5},
            max_distance = 3
        })
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            if obj.type == "Card" or obj.type == "Deck" then
                if not obj.held_by_color then
                    return obj
                end
            end
        end
        return nil
    end

    local deck = getCardAt(deckPos)
    if deck then
        hideEscalationButton()
    else
        local discard = getCardAt(discardPos)
        if discard then
            showEscalationButton()
        else
            hideEscalationButton()
        end
    end
end

function showStruggleButton()
    if is_struggle_btn_visible then return end
    
    self.editButton({
        index = struggle_btn_index,
        label = '마찰\n덱\n재구성',
        width = 440,
        height = 680,
    })
    is_struggle_btn_visible = true
end

function hideStruggleButton()
    if not is_struggle_btn_visible then return end
    self.editButton({
        index = struggle_btn_index,
        label = '',
        width = 0,
        height = 0,
    })
    is_struggle_btn_visible = false
end

function checkStruggleButton()
    if is_struggle_reconstructing then return end
    local deckPos = self.positionToWorld({1.2368, 0.2106, 0.8573})
    local discardPos = self.positionToWorld({1.0101, 0.2106, 0.8573})
    
    local function getCardAt(pos, name)
        local hits = Physics.cast({
            origin       = {pos.x, pos.y + 1.5, pos.z},
            direction    = {0, -1, 0},
            type         = 3,
            size         = {0.5, 2, 0.5},
            max_distance = 3
        })
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            if (obj.type == "Card" or obj.type == "Deck") and obj ~= self and obj.getGUID() ~= "c91f32" and obj.getGUID() ~= "fa932e" then
                if not obj.held_by_color then
                    return obj
                end
            end
        end
        return nil
    end

    local deck = getCardAt(deckPos, "DECK_POS")
    if deck then
        hideStruggleButton()
    else
        local discard = getCardAt(discardPos, "DISCARD_POS")
        if discard then
            showStruggleButton()
        else
            hideStruggleButton()
        end
    end
end

function onChat(message, player)
    if message:sub(1, 4) == "!btn" then
        local parts = {}
        for w in message:gmatch("%S+") do table.insert(parts, w) end
        if #parts == 4 then
            local x = tonumber(parts[2])
            local y = tonumber(parts[3])
            local z = tonumber(parts[4])
            if x and y and z then
                self.editButton({
                    index = struggle_btn_index,
                    position = {x, y, z}
                })
                printToAll("버튼 위치 변경: " .. x .. ", " .. y .. ", " .. z, {0,1,0})
            end
        end
        return false
    end
    
    if message == "!loc" then
        local pos = player.getPointerPosition()
        local localPos = self.positionToLocal(pos)
        printToAll("마우스 위치의 로컬 좌표: " .. string.format("%.4f, %.4f, %.4f", localPos.x, localPos.y, localPos.z), {0, 1, 0})
        return false
    end
end

function escalationCoroutine()
    local deckPos = {x=13.90, y=1.01, z=10.41}
    local discardPos = {x=28.09, y=0.86, z=10.33}
    local currentMonsterName = getMonsterName()
    if currentMonsterName == "Awakened" or currentMonsterName == "어웨이큰" then
        discardPos = {x=39.23, y=0.8, z=10.48}
    end
    
    local discardObj = nil
    local hits = Physics.cast({
        origin       = {discardPos.x, discardPos.y + 1.5, discardPos.z},
        direction    = {0, -1, 0},
        type         = 3,
        size         = {2.5, 2, 2.5},
        max_distance = 3
    })
    for _, hit in ipairs(hits) do
        local obj = hit.hit_object
        if obj.type == "Card" or obj.type == "Deck" then
            if not obj.held_by_color then
                discardObj = obj
                break
            end
        end
    end

    if discardObj then
        local struggleAmount = 1
        if currentMonsterName == "Awakened" or currentMonsterName == "어웨이큰" then
            struggleAmount = Global.call('getPlayersNb') or 1
        end

        broadcastToAll(currentMonsterName .. "이(가) 격화하여 격앙 토큰이 " .. struggleAmount .. "개 추가됩니다.", {r=1, g=0.5, b=0})

        discardObj.setPositionSmooth({x=deckPos.x, y=deckPos.y + 0.5, z=deckPos.z}, false, true)
        discardObj.setRotationSmooth({x=0, y=180, z=180}, false, true)
        
        -- 안착 대기
        for i=1, 90 do coroutine.yield(0) end

        if discardObj.type == "Deck" then discardObj.shuffle() end
        Global.call('addStruggle', struggleAmount)
        
        for i=1, 30 do coroutine.yield(0) end
        Global.call('ScheduleCheckEruption')
    end
    
    is_escalating = false
    checkEscalationButton()
    return 1
end

function struggleReconstructCoroutine()
    local deckPos = self.positionToWorld({1.2368, 0.2106, 0.8573})
    local discardPos = self.positionToWorld({1.0101, 0.2106, 0.8573})
    
    local discardObj = nil
    local hits = Physics.cast({
        origin       = {discardPos.x, discardPos.y + 1.5, discardPos.z},
        direction    = {0, -1, 0},
        type         = 3,
        size         = {0.5, 2, 0.5},
        max_distance = 3
    })
    for _, hit in ipairs(hits) do
        local obj = hit.hit_object
        if (obj.type == "Card" or obj.type == "Deck") and obj ~= self and obj.getGUID() ~= "c91f32" and obj.getGUID() ~= "fa932e" then
            if not obj.held_by_color then
                discardObj = obj
                break
            end
        end
    end

    if discardObj then
        broadcastToAll("마찰 덱을 재구성합니다.", {r=0.8, g=0.8, b=0.8})

        discardObj.setPositionSmooth({x=deckPos.x, y=deckPos.y + 0.5, z=deckPos.z}, false, true)
        discardObj.setRotationSmooth({x=0, y=180, z=180}, false, true)
        
        -- 안착 대기
        for i=1, 90 do coroutine.yield(0) end

        if discardObj.type == "Deck" then discardObj.shuffle() end
    end
    
    is_struggle_reconstructing = false
    checkStruggleButton()
    return 1
end

function onLoad(saveState)
    -- 데칼 프리로드 (처음 불러올 때 흰색 네모박스 방지용)
    self.setDecals({
        {
            name     = "PreloadHealthStance",
            url      = "https://steamusercontent-a.akamaihd.net/ugc/10200152910888021012/203878BCE01CDE9E0F6847B606FF3A465D5A6DFB/",
            position = {0, 0, 0},
            rotation = {90, 180, 0},
            scale    = {0.001, 0.001, 0.001},
        }
    })

    self.max_typed_number = 3

    -- 저장 데이터 복원
    if saveState ~= nil and saveState ~= '' then
        local saveData = JSON.decode(saveState)
        if saveData then
            if saveData.monster_damage    ~= nil then monster_damage    = saveData.monster_damage end
            if saveData.monster_toughness ~= nil then monster_toughness = saveData.monster_toughness end
        end
    end

    -- 토큰 스폰 버튼 생성
    -- (XML UI 대신 createButton: XML 버튼 위 토큰 집어들 때 간섭 방지)
    local index = 1
    for tokenName, _ in pairs(TOKENS) do
        local functionName = 'spawn' .. tokenName .. 'Token'

        -- Counter는 세로 회전 스폰
        if tokenName == 'Counter' then
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], spawnTokenOnButton, tokenName,
                    alt_click == true and {0.00, 225.00, 180.00} or {0.00, 225.00, 0.00})
            end)
        else
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], spawnTokenOnButton, tokenName,
                    alt_click == true and {0.00, 180.00, 180.00} or nil)
            end)
        end

        self.createButton({
            click_function = functionName,
            function_owner = self,
            label          = '',
            position       = {-0.688 + (index-1) * 0.15975, 0.1, index%2==1 and 0.867 or 0.693},
            rotation       = {0, 180, 0},
            width          = 78,
            height         = 78,
            font_size      = 5,
            color          = {0.5, 0.5, 0.5, 0},
        })

        TOKENS[tokenName].button_index = index
        index = index + 1
    end

    self.createButton({
        click_function = 'noOp',
        function_owner = self,
        label          = '',
        position       = {-1.21, 0.1, -0.80},
        rotation       = {0, 180, 0},
        scale          = {0.05, 1, 0.05},
        width          = 400,
        height         = 400,
        font_size      = 5,
        color          = {0.5, 0.5, 0.5, 0},
        tooltip        = '숫자 키를 입력하면 숫자가 바로 바뀝니다.',
    })

    self.createButton({
        click_function = 'noOp',
        function_owner = self,
        label          = '',
        position       = {-1.05, 0.1, -0.80},
        rotation       = {0, 180, 0},
        scale          = {0.05, 1, 0.05},
        width          = 400,
        height         = 400,
        font_size      = 5,
        color          = {0.5, 0.5, 0.5, 0},
        tooltip        = '숫자 키를 입력하면 숫자가 바로 바뀝니다.',
    })

    self.setVar('handleEscalation', function(_, color)
        if is_escalating or not is_escalation_button_visible then return end
        
        local deckPos = {x=13.90, y=1.01, z=10.41}
        local discardPos = {x=28.09, y=0.86, z=10.33}
        local currentMonsterName = getMonsterName()
        if currentMonsterName == "Awakened" or currentMonsterName == "어웨이큰" then
            discardPos = {x=39.23, y=0.8, z=10.48}
        end
        
        local discardObj = nil
        local hits = Physics.cast({
            origin       = {discardPos.x, discardPos.y + 1.5, discardPos.z},
            direction    = {0, -1, 0},
            type         = 3,
            size         = {2.5, 2, 2.5},
            max_distance = 3
        })
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            if obj.type == "Card" or obj.type == "Deck" then
                if not obj.held_by_color then
                    discardObj = obj
                    break
                end
            end
        end

        if discardObj then
            is_escalating = true
            hideEscalationButton()
            startLuaCoroutine(self, 'escalationCoroutine')
        else
            broadcastToColor("버린 몬스터 행동 카드가 없습니다.", color, Color.Red)
        end
    end)

    self.createButton({
        click_function = 'handleEscalation',
        function_owner = self,
        label          = '',
        position       = {-1.1, 0.101, -0.25},
        rotation       = {0, 0, 0},
        scale          = {0.18, 1, 0.18},
        width          = 0,
        height         = 0,
        font_size      = 120,
        color          = {0, 0, 0, 1},
        font_color     = {1, 1, 1, 1},
        tooltip        = '버린 몬스터 행동 카드를 섞어 덱을 재구성하고 격화 효과(격앙 토큰 추가 등)를 적용합니다.',
    })

    self.setVar('handleStruggleReconstruct', function(_, color)
        if is_struggle_reconstructing or not is_struggle_btn_visible then return end
        
        local discardPos = self.positionToWorld({1.0101, 0.2106, 0.8573})
        
        local discardObj = nil
        local hits = Physics.cast({
            origin       = {discardPos.x, discardPos.y + 1.5, discardPos.z},
            direction    = {0, -1, 0},
            type         = 3,
            size         = {0.5, 2, 0.5},
            max_distance = 3
        })
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            if (obj.type == "Card" or obj.type == "Deck") and obj ~= self and obj.getGUID() ~= "c91f32" and obj.getGUID() ~= "fa932e" then
                if not obj.held_by_color then
                    discardObj = obj
                    break
                end
            end
        end

        if discardObj then
            is_struggle_reconstructing = true
            hideStruggleButton()
            startLuaCoroutine(self, 'struggleReconstructCoroutine')
        else
            broadcastToColor("버린 마찰 카드가 없습니다.", color, Color.Red)
        end
    end)

    self.createButton({
        click_function = 'handleStruggleReconstruct',
        function_owner = self,
        label          = '',
        position       = {-1.234, 0.101, 0.8573},
        rotation       = {0, 0, 0},
        scale          = {0.18, 1, 0.18},
        width          = 0,
        height         = 0,
        font_size      = 120,
        color          = {0, 0, 0, 1},
        font_color     = {1, 1, 1, 1},
        tooltip        = '버린 마찰 카드를 섞어 덱을 재구성합니다.',
    })

    local buttons = self.getButtons()
    if buttons then
        for _, btn in ipairs(buttons) do
            if btn.click_function == 'handleEscalation' then
                escalation_btn_index = btn.index
            elseif btn.click_function == 'handleStruggleReconstruct' then
                struggle_btn_index = btn.index
            end
        end
    end

    -- 텍스트 초기 표시 + actor_stance 카드 기반 강인함 갱신 (UI 로드 대기 후)
    Wait.time(function()
        refreshMonsterDisplay()
        updateMonsterToughnessFromActorStance()
    end, 0.5)

    -- 체력 토큰 버튼 설정
    Wait.time(function()
        for _, obj in ipairs(getObjectsWithTag('actor_health')) do
            setupHealthToken(obj)
        end
        for _, obj in ipairs(getObjectsWithTag('actor_hard')) do
            setupHealthToken(obj)
        end
    end, 1.0)
    
    Wait.time(function()
        checkEscalationButton()
        checkStruggleButton()
    end, 3)
end

function onSave()
    return JSON.encode({
        monster_damage    = monster_damage,
        monster_toughness = monster_toughness,
    })
end

--------------------
-- 텍스트 갱신
function refreshMonsterDisplay()
    -- 보드 위 actor_stance 카드 유무 직접 확인 (헬퍼 의존 없음)
    local hasStance = false

    if self and self.getBoundsNormalized then
        local cards = getObjectsWithTag('actor_stance')
        if cards and #cards > 0 then
            local bounds = self.getBoundsNormalized()
            local cx, cz = bounds.center.x, bounds.center.z
            local hx, hz = bounds.size.x / 2, bounds.size.z / 2
            local by = self.getPosition().y

            for _, c in ipairs(cards) do
                if c ~= nil then
                    local p = c.getPosition()
                    if math.abs(p.x - cx) <= hx
                    and math.abs(p.z - cz) <= hz
                    and p.y > by then
                        hasStance = true
                        break
                    end
                end
            end
        end
    end

    if hasStance then
        self.UI.setAttribute('monsterDamageText',    'active', 'true')
        self.UI.setAttribute('monsterToughnessText', 'active', 'true')
        self.UI.setAttribute('monsterDamageText',    'text', tostring(monster_damage))
        self.UI.setAttribute('monsterToughnessText', 'text', tostring(monster_toughness))
    else
        self.UI.setAttribute('monsterDamageText',    'active', 'false')
        self.UI.setAttribute('monsterToughnessText', 'active', 'false')
        -- 안전장치: active=false가 먹히지 않을 때를 대비해 텍스트를 0으로 초기화
        self.UI.setAttribute('monsterDamageText',    'text', "0")
        self.UI.setAttribute('monsterToughnessText', 'text', "0")
    end
    
    checkToughnessBreak(hasStance)
end

function checkToughnessBreak(hasStance)
    local isBroken = (monster_toughness > 0 and monster_damage >= monster_toughness)
    
    -- 스탠스 카드의 기본 강인함(gm노트 첫번째 값)이 0인 경우 깨진 이미지로 변환하지 않음
    if _currentStanceBaseToughness == 0 then
        isBroken = false
    end
    
    -- XML에 작성된 두 이미지 태그의 active 속성을 토글하여 이미지를 교체
    self.UI.setAttribute("monsterToughness", "active", tostring(not isBroken))
    self.UI.setAttribute("monsterToughnessBroken", "active", tostring(isBroken))
end

--------------------
-- 데미지 조정 (0 ~ 999 클램프)
_damageBroadcastTimer = nil
_damageBroadcastOldValue = nil

function adjustMonsterDamage(delta, silent)
    local actualOldValue = monster_damage
    monster_damage = math.max(0, math.min(999, monster_damage + delta))
    refreshMonsterDisplay()

    if actualOldValue ~= monster_damage and not silent then
        if _damageBroadcastOldValue == nil then
            _damageBroadcastOldValue = actualOldValue
        end
        if _damageBroadcastTimer then Wait.stop(_damageBroadcastTimer) end
        _damageBroadcastTimer = Wait.time(function()
            local diff = monster_damage - _damageBroadcastOldValue
            if diff ~= 0 then
                local symbol = diff > 0 and '+' or ''
                printToAll(string.format(
                    '몬스터 데미지: %d → %d (%s%d)',
                    _damageBroadcastOldValue, monster_damage, symbol, diff
                ), {1, 1, 1})
            end
            _damageBroadcastOldValue = nil
            _damageBroadcastTimer = nil
        end, 0.5)
    end
end

-- 강인함 조정 (0 ~ 999 클램프)
_toughnessBroadcastTimer = nil
_toughnessBroadcastOldValue = nil

function adjustMonsterToughness(delta)
    local actualOldValue = monster_toughness
    monster_toughness = math.max(0, math.min(999, monster_toughness + delta))
    refreshMonsterDisplay()

    if actualOldValue ~= monster_toughness then
        if _toughnessBroadcastOldValue == nil then
            _toughnessBroadcastOldValue = actualOldValue
        end
        if _toughnessBroadcastTimer then Wait.stop(_toughnessBroadcastTimer) end
        _toughnessBroadcastTimer = Wait.time(function()
            local diff = monster_toughness - _toughnessBroadcastOldValue
            if diff ~= 0 then
                local symbol = diff > 0 and '+' or ''
                printToAll(string.format(
                    '몬스터 강인함: %d → %d (%s%d)',
                    _toughnessBroadcastOldValue, monster_toughness, symbol, diff
                ), {0.8, 0.8, 0.8})
            end
            _toughnessBroadcastOldValue = nil
            _toughnessBroadcastTimer = nil
        end, 0.5)
    end
end

-- 외부 호출용 절대값 설정
function setMonsterDamage(value)
    monster_damage = math.max(0, math.min(999, tonumber(value) or 0))
    refreshMonsterDisplay()
end

function setMonsterToughness(value)
    monster_toughness = math.max(0, math.min(999, tonumber(value) or 0))
    refreshMonsterDisplay()
end

--------------------
-- 데미지 1/5/10/50 
function adjustDmgPlus(player, value, id)
    local amount = tonumber(string.match(id, "(%d+)$"))
    if not amount then return end
    adjustMonsterDamage(amount)
end

-- 데미지 - 1/5/10/50 (좌클릭으로만 감소)
function adjustDmgMinus(player, value, id)
    local amount = tonumber(string.match(id, "(%d+)$"))
    if not amount then return end
    adjustMonsterDamage(-amount)   -- 음수로 전달 → 감소
end

--------------------
-- 토큰 스폰
function spawnTokenOnButton(tokenName, rotation)
    local spawnPosition = self.getButtons()[TOKENS[tokenName].button_index].position
    spawnPosition.x = -spawnPosition.x
    spawnPosition.y = spawnPosition.y + 0.25

    local tokenBags = getObjectsWithTag(TOKENS[tokenName].tag)
    if #tokenBags < 1 then
        broadcastToAll('Missing bag for token ' .. tokenName .. '.', Color.Red)
        return
    end

    tokenBags[1].takeObject({
        position = self.positionToWorld(spawnPosition),
        rotation = rotation or {0.00, 180.00, 0.00},
        smooth = false,
    })
end

function hoverWrapper(player, callback, ...)
    if player ~= nil and player.getHoverObject() == self and callback ~= nil then
        callback(...)
    end
end

-- 빈 클릭 핸들러 (createButton에 필수)
function noOp() end



function getClosestNumberButton(player)
    local pointerWorld = player.getPointerPosition()
    if not pointerWorld then return nil end

    local damageBtnPos = {-1.21, 0.1, -0.80}
    local toughnessBtnPos = {-1.05, 0.1, -0.80}

    local damageWorld = self.positionToWorld(damageBtnPos)
    local toughnessWorld = self.positionToWorld(toughnessBtnPos)

    local function isPointerNear(pw, bw)
        local dx = pw.x - bw.x
        local dz = pw.z - bw.z
        return math.sqrt(dx*dx + dz*dz) < 0.2
    end

    if isPointerNear(pointerWorld, damageWorld) then return 'damage' end
    if isPointerNear(pointerWorld, toughnessWorld) then return 'toughness' end

    return nil
end

function onScriptingButtonDown(index, color)
    local number = index
    if index == 10 then number = 0 end
    onNumberTyped(color, number)
end

-- 키보드 상단 숫자키(1~9, 0) 입력 이벤트
function onNumberTyped(color, number)
    local player = Player[color]
    if not player then return end
    if player.getHoverObject() ~= self then return end

    local target = getClosestNumberButton(player) or current_hover_target
    if not target then return end

    -- TTS는 0 키를 number=10으로 보내는 경우와 0으로 보내는 경우가 둘 다 있음
    local digit
    if number == 0 or number == 10 then
        digit = '0'
    else
        digit = tostring(number)
    end

    if target == 'damage' then
        damage_input_buffer = damage_input_buffer .. digit
        if not damage_delay_started then
            damage_delay_started = true
            startLuaCoroutine(self, "autoApplyDamageCoroutine")
        end
    elseif target == 'toughness' then
        toughness_input_buffer = toughness_input_buffer .. digit
        if not toughness_delay_started then
            toughness_delay_started = true
            startLuaCoroutine(self, "autoApplyToughnessCoroutine")
        end
    end

    return true
end

-- XML UI 호버 이벤트 핸들러
function hoverDamage(player, id)
    current_hover_target = 'damage'
end

function hoverToughness(player, id)
    current_hover_target = 'toughness'
end

function hoverExit(player, id)
    current_hover_target = nil
end

-- XML UI 클릭 이벤트 핸들러 (좌클릭 시 +1, 우클릭 시 -1)
function clickDamage(player, value, id)
    if value == "-1" then
        adjustMonsterDamage(1)
    elseif value == "-2" then
        adjustMonsterDamage(-1)
    end
end

function clickToughness(player, value, id)
    if value == "-1" then
        adjustMonsterToughness(1)
    elseif value == "-2" then
        adjustMonsterToughness(-1)
    end
end

--------------------
-- 프레임 딜레이 후 자동 실행 (데미지)
function autoApplyDamageCoroutine()
    -- 60프레임 대기 (~1.0초)
    for i = 1, 60 do coroutine.yield(0) end

    applyDamageBuffer()
    damage_delay_started = false
    return 1
end

function applyDamageBuffer()
    if damage_input_buffer == '' then return end

    local newValue = tonumber(damage_input_buffer)
    damage_input_buffer = ''

    if not newValue then return end

    local oldValue = monster_damage
    setMonsterDamage(newValue)   -- 내부에서 0~monster_toughness 클램프

    if oldValue ~= monster_damage then
        local diff = monster_damage - oldValue
        local symbol = diff > 0 and '+' or ''
        print(string.format(
            '몬스터 데미지: %d → %d (%s%d, 키 입력 %d)',
            oldValue, monster_damage, symbol, diff, newValue
        ))
    end
end

--------------------
-- 프레임 딜레이 후 자동 실행 (강인함)
function autoApplyToughnessCoroutine()
    -- 60프레임 대기 (~1.0초)
    for i = 1, 60 do coroutine.yield(0) end

    applyToughnessBuffer()
    toughness_delay_started = false
    return 1
end

function applyToughnessBuffer()
    if toughness_input_buffer == '' then return end

    local newValue = tonumber(toughness_input_buffer)
    toughness_input_buffer = ''

    if not newValue then return end

    local oldValue = monster_toughness
    setMonsterToughness(newValue)   -- 내부에서 0~999 클램프 + 데미지 동기화

    if oldValue ~= monster_toughness then
        local diff = monster_toughness - oldValue
        local symbol = diff > 0 and '+' or ''
        print(string.format(
            '몬스터 강인함: %d → %d (%s%d, 키 입력 %d)',
            oldValue, monster_toughness, symbol, diff, newValue
        ))
    end
end

-- GM 노트의 콤마 구분 값에서 N번째 숫자 추출
-- 예) parseGMNotesField("10,6,1", 1) → 10
--     parseGMNotesField("10,6,1", 2) → 6
function parseGMNotesField(notes, index)
    notes = notes or ''
    index = index or 1

    local i = 0
    for part in string.gmatch(notes, '([^,]+)') do
        i = i + 1
        if i == index then
            return tonumber((part:gsub('^%s*(.-)%s*$', '%1')))
        end
    end
    return nil
end

function getActiveStanceCard()
    if not self or not self.getBoundsNormalized then return nil end
    local cards = getObjectsWithTag('actor_stance')
    if not cards or #cards == 0 then return nil end

    local bounds = self.getBoundsNormalized()
    local cx, cz = bounds.center.x, bounds.center.z
    local hx, hz = bounds.size.x / 2, bounds.size.z / 2
    local by = self.getPosition().y

    for _, c in ipairs(cards) do
        if c ~= nil then
            local p = c.getPosition()
            if math.abs(p.x - cx) <= hx
            and math.abs(p.z - cz) <= hz
            and p.y > by then
                return c
            end
        end
    end
    return nil
end

function getMonsterName()
    local globalName = Global.getVar("CurrentMonster")
    if globalName and type(globalName) == "string" and globalName ~= "" then
        return globalName
    end

    if not self or not self.getBoundsNormalized then return "몬스터" end
    local bounds = self.getBoundsNormalized()
    local cx, cz = bounds.center.x, bounds.center.z
    local hx, hz = bounds.size.x / 2, bounds.size.z / 2
    local by = self.getPosition().y

    for _, guid in ipairs(CombatBoardGUIDs) do
        local obj = getObjectFromGUID(guid)
        if obj ~= nil then
            local p = obj.getPosition()
            if math.abs(p.x - cx) <= hx and math.abs(p.z - cz) <= hz and p.y > by then
                local name = obj.getName()
                if name and name ~= "" then
                    return name
                end
            end
        end
    end
    return "몬스터"
end

--------------------
-- GM 노트를 기반으로 체력 트랙 스냅포인트에 붉은 동그라미 표시
function updateHealthTrackCircles(notes)
    self.setVectorLines({})
    self.setDecals({})  -- 이전 스탠스 카드가 남긴 쓰레쉬홀드 데칼 초기화
    
    if not notes or notes == '' then
        return
    end

    local health_token = nil
    for _, obj in ipairs(getObjectsWithTag('actor_health')) do
        local p = obj.getPosition()
        local lPos = self.positionToLocal(p)
        if math.abs(lPos.x) <= 20 and math.abs(lPos.z) <= 20 and lPos.y > -2 then
            health_token = obj
            break
        end
    end

    if not health_token then 
        return 
    end

    local sorted_snaps = getSortedSnapPoints(health_token)
    if not sorted_snaps or #sorted_snaps == 0 then
        return
    end

    local N = #sorted_snaps
    local threshold = parseGMNotesField(notes, 2)
    if threshold and threshold > 0 then
        local target_idx = threshold + 1
        if target_idx >= 1 and target_idx <= N then
            local sp_world = sorted_snaps[target_idx]
            local sp_local = self.positionToLocal(sp_world)
            
            -- 이미지 주소를 사용하여 데칼로 스냅포인트에 표시
            self.setDecals({
                {
                    name     = "HealthThreshold",
                    url      = "https://steamusercontent-a.akamaihd.net/ugc/10200152910888021012/203878BCE01CDE9E0F6847B606FF3A465D5A6DFB/",
                    position = {sp_local.x, sp_local.y + 0.01, sp_local.z},
                    rotation = {90, 180, 0},
                    scale    = {0.048, 0.065, 0.3},
                }
            })
        end
    end
end

function updateMonsterToughnessFromActorStance()
    if _toughnessUpdateTimerID then
        Wait.stop(_toughnessUpdateTimerID)
    end
    _toughnessUpdateTimerID = Wait.time(_doUpdateMonsterToughnessFromActorStance, 0.5)
end

function _doUpdateMonsterToughnessFromActorStance()
    local card = getActiveStanceCard()
    if not card then 
        _currentStanceBaseToughness = -1
        setMonsterDamage(0)
        setMonsterToughness(0)
        self.setVectorLines({})
        self.setDecals({}) -- 스탠스 카드가 완전히 없어졌을 때 데칼도 지움
        return 
    end

    local notes = card.getGMNotes() or ''
    updateHealthTrackCircles(notes)

    local base = parseGMNotesField(notes, 1)
    if not base then return end

    local stateId = card.getStateId() or -1
    local currentID = card.getGUID() .. "_" .. tostring(stateId)

    -- 백업 로직은 checkStanceTransition에서 명시적으로 수행하므로 여기서는 강인함 갱신만 처리합니다.
    _currentStanceID = currentID

    _currentStanceBaseToughness = base

    local playerCount = Global.call('getPlayersNb')
    if type(playerCount) ~= 'number' or playerCount < 1 then
        _currentStanceHasResistance = card.hasTag('resistance')
        return
    end

    local total = base * playerCount
    setMonsterToughness(total)
    _currentStanceHasResistance = card.hasTag('resistance')
end

-- 카드가 보드에 떨어졌을 때 / 들렸을 때 재계산
function onCollisionEnter(info)
    local obj = info.collision_object
    if obj and obj.hasTag and obj.hasTag('actor_stance') then
        Wait.frames(updateMonsterToughnessFromActorStance, 2)
        Wait.frames(refreshMonsterDisplay, 5)   -- ← 카드 도착 시 visibility 강제 갱신
    end
end

function onCollisionExit(info)
    local obj = info.collision_object
    if obj and obj.hasTag and obj.hasTag('actor_stance') then
        Wait.frames(updateMonsterToughnessFromActorStance, 2)
        Wait.frames(refreshMonsterDisplay, 5)   -- ← 카드 떠난 후 visibility 갱신
    end
end

-- 스탠스 카드가 Delete(삭제)되었을 때 감지
function onObjectDestroy(destroyed_object)
    if destroyed_object.hasTag and destroyed_object.hasTag('actor_stance') then
        Wait.frames(updateMonsterToughnessFromActorStance, 2)
        Wait.frames(refreshMonsterDisplay, 5)
    end
    if destroyed_object.type == 'Card' or destroyed_object.type == 'Deck' then
        Wait.time(checkEscalationButton, 0.1)
        Wait.time(checkStruggleButton, 0.1)
    end
end

-- 스탠스 카드가 가방이나 덱으로 들어갔을 때 감지
function onObjectEnterContainer(container, object)
    if object.hasTag and object.hasTag('actor_stance') then
        Wait.frames(updateMonsterToughnessFromActorStance, 2)
        Wait.frames(refreshMonsterDisplay, 5)
    end
    if object.type == 'Card' or object.type == 'Deck' or container.type == 'Deck' then
        Wait.time(checkEscalationButton, 0.1)
        Wait.time(checkStruggleButton, 0.1)
    end
end

function applyStanceBreakthrough()
    -- 백업된 이전 스탠스 정보가 있다면 우선 사용, 없다면 현재 값(아직 카드를 안 바꿨을 때) 사용
    local hadResistance = _previousStanceHasResistance
    local oldToughness = _previousToughness

    if not oldToughness or oldToughness == 0 then
        hadResistance = _currentStanceHasResistance
        oldToughness = monster_toughness
    end

    if hadResistance then
        if monster_damage > 0 then
            local oldDamage = monster_damage
            setMonsterDamage(0)
            broadcastToAll(
                string.format('저항: 데미지 %d → 0 초기화', oldDamage),
                {1, 0.3, 0.3}
            )
        end
    elseif oldToughness > 0 and _recentWoundToughness ~= oldToughness then
        local oldDamage = monster_damage
        adjustMonsterDamage(-oldToughness, true)
        local newDamage = monster_damage
        broadcastToAll(
            string.format('스탠스 변경: 데미지 %d → %d (이전 강인함 %d 차감)', oldDamage, newDamage, oldToughness),
            {1, 0.8, 0}
        )
    end

    -- 처리 후 백업된 이전 정보를 초기화하여 중복 적용 방지
    _previousToughness = 0
    _previousStanceHasResistance = false
    _recentWoundToughness = 0

    -- 새 스탠스 카드로 강인함 + resistance 플래그 갱신
    Wait.frames(updateMonsterToughnessFromActorStance, 5)
end

-- 몬스터 완전 리셋용 호출: 데미지 초기화 + 텍스트 업데이트
function onMonsterCleanup()
    self.setVectorLines({})
    monster_damage = 0
    monster_toughness = 0
    _currentStanceHasResistance = false
    _lastToughnessUpdate = 0
    _recentWoundToughness = 0
    refreshMonsterDisplay()   -- 보드에 카드 없음 → 두 텍스트 자동 숨김
    
    Global.call("ResetGameToInitial")
end

--------------------
-- 체력(Health) 토큰 트래커 관련 함수
function getSortedSnapPoints(obj)
    local pos = obj.getPosition()
    local target_board = nil
    
    local hits = Physics.cast({
        origin       = {pos.x, pos.y + 0.5, pos.z},
        direction    = {0, -1, 0},
        type         = 1,
        max_distance = 5,
    })
    
    local snaps = nil
    for _, hit in ipairs(hits) do
        if hit.hit_object ~= obj and hit.hit_object ~= self then
            snaps = hit.hit_object.getSnapPoints()
            target_board = hit.hit_object
            if snaps and #snaps > 0 then
                break
            end
        end
    end

    if not target_board then
        snaps = self.getSnapPoints()
        target_board = self
    end

    if not snaps or #snaps == 0 then return {} end

    local world_snaps = {}
    local token_pos = obj.getPosition()
    
    local token_local = target_board.positionToLocal(token_pos)
    local closest_local_z = nil
    local min_z_diff = math.huge
    for _, snap in ipairs(snaps) do
        local diff = math.abs(snap.position.z - token_local.z)
        if diff < min_z_diff then
            min_z_diff = diff
            closest_local_z = snap.position.z
        end
    end

    for i, snap in ipairs(snaps) do
        if math.abs(snap.position.z - closest_local_z) < 0.1 then
            local wp = target_board.positionToWorld(snap.position)
            table.insert(world_snaps, wp)
        end
    end
    
    table.sort(world_snaps, function(a, b) 
        return a.x < b.x 
    end)
    
    return world_snaps
end

local function hasTargetTag(obj, targetTag)
    local tags = obj.getTags()
    if not tags then return false end
    targetTag = string.lower(targetTag)
    for _, t in ipairs(tags) do
        local lower_t = string.lower(t)
        lower_t = string.gsub(lower_t, "%s+", "") -- 공백 제거
        if lower_t == targetTag then return true end
    end
    return false
end

local function isHardToken(obj)
    if not obj then return false end
    if hasTargetTag(obj, 'actor_hard') then return true end
    local name = obj.getName()
    if not name or name == "" then return false end
    
    local lower_n = string.lower(name)
    lower_n = string.gsub(lower_n, "%s+", "") -- 공백 제거
    if lower_n == "vibrationmarker" or lower_n == "chargemarker" or lower_n == "glaciation" then return true end
    
    return false
end

local function isTrackerToken(obj)
    if not obj then return false end
    if hasTargetTag(obj, 'actor_health') then return true end
    return isHardToken(obj)
end

function onObjectSpawn(obj)
    if isTrackerToken(obj) then
        Wait.frames(function() setupHealthToken(obj) end, 5)
    end
end

function onObjectLeaveContainer(container, obj)
    if isTrackerToken(obj) then
        Wait.frames(function() setupHealthToken(obj) end, 5)
    end
    if obj.type == 'Card' or obj.type == 'Deck' or container.type == 'Deck' then
        Wait.time(checkEscalationButton, 0.1)
        Wait.time(checkStruggleButton, 0.1)
    end
end

function onObjectDrop(player_color, dropped_object)
    if isTrackerToken(dropped_object) then
        Wait.frames(function() setupHealthToken(dropped_object) end, 5)
    end
    if dropped_object.type == 'Card' or dropped_object.type == 'Deck' then
        Wait.time(checkEscalationButton, 0.1)
        Wait.time(checkStruggleButton, 0.1)
    end
end

function onObjectPickUp(player_color, obj)
    if obj.type == 'Card' or obj.type == 'Deck' then
        Wait.time(checkEscalationButton, 0.1)
        Wait.time(checkStruggleButton, 0.1)
    end
end

local function isTokenOnTrack(obj)
    local sorted = getSortedSnapPoints(obj)
    if not sorted or #sorted == 0 then return false end
    
    local pos = obj.getPosition()
    local min_dist = math.huge
    for _, sp in ipairs(sorted) do
        -- X, Z 평면 상의 거리 제곱 측정
        local dist = (pos.x - sp.x)^2 + (pos.z - sp.z)^2
        if dist < min_dist then
            min_dist = dist
        end
    end
    
    -- 가장 가까운 자석 지점과의 거리가 4.0(약 2칸) 이상이라면 트랙 밖으로 간주
    if min_dist > 4.0 then 
        return false 
    end
    
    return true
end

function setupHealthToken(obj)
    local function doSetup()
        if not obj or obj.isDestroyed() then return end
        
        -- 잠금을 하지 않고 물리엔진(중력)에 맡김으로써 콜라이더 버그로 인한 공중부양 원천 차단
        obj.setLock(false)
        
        -- 뒤집혀서 스폰되거나 각도가 비뚤어지는 것을 방지하기 위해 안착 즉시 정방향으로 회전 정렬
        if isHardToken(obj) then
            if obj.getName() == "Charge Marker" then
                obj.setRotationSmooth(CHARGE_ROTATION_WORLD)
            elseif obj.getName() == "Glaciation" then
                obj.setRotationSmooth(GLACIATION_ROTATION_WORLD)
            elseif obj.getName() == "Vibration Marker" then
                obj.setRotationSmooth(VIBRATION_ROTATION_WORLD)
            else
                obj.setRotationSmooth(HARD_ROTATION_WORLD)
            end
        else
            obj.setRotationSmooth(HEALTH_ROTATION_WORLD)
        end

        
        -- 안착 즉시 가장 가까운 자석 지점으로 자동 정렬 및 공중부양(높이) 보정
        local sorted_snaps = getSortedSnapPoints(obj)
        if sorted_snaps and #sorted_snaps > 0 then
            local current_world = obj.getPosition()
            local closest_index = 1
            local min_dist = math.huge
            for i, sp in ipairs(sorted_snaps) do
                local dist = (current_world.x - sp.x)^2 + (current_world.z - sp.z)^2
                if dist < min_dist then
                    min_dist = dist
                    closest_index = i
                end
            end
            local target_world = sorted_snaps[closest_index]

            -- Glaciation 자동 셋업 로직
            if obj.getName() == "Glaciation" then
                local card = getActiveStanceCard()
                if card then
                    local st = card.getStateId()
                    if st and st >= 1 and st <= 3 then
                        local target_idx = st + 1
                        if target_idx <= #sorted_snaps then
                            closest_index = target_idx
                            target_world = sorted_snaps[closest_index]
                            broadcastToAll("빙결: 스탠스 레벨(" .. st .. ")에 맞춰 자동 이동되었습니다.", {0.6, 0.8, 1.0})
                        end
                    end
                end
            end

            target_world.y = current_world.y + 0.2 -- 잠금이 풀려있으므로 살짝 위로 띄워주면 중력이 완벽한 바닥까지 끌어내림
            obj.setPositionSmooth(target_world)
        end

        local btns = obj.getButtons()
        if btns ~= nil then
            for _, b in ipairs(btns) do
                if b.click_function == 'onClickHealthToken' then return end
            end
        end

        obj.createButton({
            click_function = 'onClickHealthToken',
            function_owner = self,
            label          = '',
            position       = {0, 0.2, 0}, -- 커스텀 타일 바로 위에 얇게 붙도록 적절한 높이 설정
            width          = 1200,
            height         = 1200,
            color          = {0,0,0,0},
            tooltip        = '좌클릭: 왼쪽으로 1칸 (-1)\n우클릭: 오른쪽으로 1칸 (+1)',
        })

        local t_name = "체력"
        if isHardToken(obj) then
            if obj.getName() == "Charge Marker" then
                t_name = "충전"
            elseif obj.getName() == "Glaciation" then
                t_name = "빙결"
            elseif obj.getName() == "Vibration Marker" then
                t_name = "진동"
            else
                t_name = "경화"
            end
        end
        broadcastToAll(t_name .. " 토큰 버튼 설정 완료!", {0, 1, 0})
    end

    local function checkResting()
        if obj and not obj.isDestroyed() then
            -- 토큰이 트랙 주변에 있는지 검사
            if not isTokenOnTrack(obj) then
                return -- 보드 밖이나 트랙이 아닌 곳에 있다면 설정(잠금 등) 무시
            end

            -- 플레이어가 들고 있지 않고 바닥에 완벽히 떨어져 물리적으로 멈췄는지 확인
            if obj.resting and obj.held_by_color == nil then
                doSetup()
            else
                Wait.frames(checkResting, 10)
            end
        end
    end

    -- 스폰 직후 물리엔진이 작동하기 전의 일시적인 resting=true 상태를 우회하기 위해 0.5초 대기 후 검사 시작
    Wait.time(checkResting, 0.5)
end

function checkStanceTransition(target_index)
    local card = getActiveStanceCard()
    if not card then return end

    local threshold = parseGMNotesField(card.getGMNotes(), 2)
    if not threshold then return end
    
    if target_index == 1 then
        -- 체력이 0에 도달
        local monster_name = getMonsterName()
        Wait.time(function()
            broadcastToAll(monster_name .. " 토벌에 성공하였습니다!", {0, 1, 0})
        end, 0.5)
        
        -- 만약 0이 임계치이기도 하다면 상태 변환도 같이 수행
        if target_index == (threshold + 1) then
            local current_state = card.getStateId()
            if current_state and current_state > 0 then
                _previousToughness = monster_toughness
                _previousStanceHasResistance = _currentStanceHasResistance
                card.setState(current_state + 1)
                Wait.time(applyStanceBreakthrough, 1.5)
            end
        end
    elseif target_index == (threshold + 1) then
        -- 0이 아니면서 임계치에 도달
        local current_state = card.getStateId()
        if current_state and current_state > 0 then
            _previousToughness = monster_toughness
            _previousStanceHasResistance = _currentStanceHasResistance
            card.setState(current_state + 1)
            Wait.time(function()
                broadcastToAll("체력이 임계치에 도달하여 스탠스가 다음 상태로 변환되었습니다!", {1, 0.8, 0})
            end, 0.5)
            Wait.time(applyStanceBreakthrough, 1.5)
        end
    end
end

function onClickHealthToken(obj, player_color, alt_click)
    local sorted_snaps = getSortedSnapPoints(obj)
    if not sorted_snaps or #sorted_snaps == 0 then return end

    -- 현재 위치와 가장 가까운 지점(인덱스) 찾기
    local current_world = obj.getPosition()
    local closest_index = 1
    local min_dist = math.huge

    for i, sp in ipairs(sorted_snaps) do
        local dist = (current_world.x - sp.x)^2 + (current_world.z - sp.z)^2
        if dist < min_dist then
            min_dist = dist
            closest_index = i
        end
    end

    local target_index = closest_index
    if not alt_click then
        target_index = target_index - 1  -- 좌클릭 (왼쪽)
    else
        target_index = target_index + 1  -- 우클릭 (오른쪽)
    end

    -- 인덱스 범위 클램프 (1 ~ 자석지점 개수)
    if target_index < 1 then
        target_index = 1
    elseif target_index > #sorted_snaps then
        target_index = #sorted_snaps
    end

    -- 이동
    if target_index ~= closest_index then
        local target_world = sorted_snaps[target_index]
        target_world.y = current_world.y + 0.2 -- 바닥에 긁히지 않도록 이동 시 살짝 띄우고 중력에 맡김
        obj.setPositionSmooth(target_world)
        
        if hasTargetTag(obj, 'actor_hard') then
            if obj.getName() == "Charge Marker" then
                obj.setRotationSmooth(CHARGE_ROTATION_WORLD)
            elseif obj.getName() == "Glaciation" then
                obj.setRotationSmooth(GLACIATION_ROTATION_WORLD)
            elseif obj.getName() == "Vibration Marker" then
                obj.setRotationSmooth(VIBRATION_ROTATION_WORLD)
            else
                obj.setRotationSmooth(HARD_ROTATION_WORLD)
            end
        else
            obj.setRotationSmooth(HEALTH_ROTATION_WORLD)
        end
        
        local current_val = target_index - 1
        
        if hasTargetTag(obj, 'actor_health') then
            -- 스탠스 전환 체크를 상처 체크보다 먼저 수행
            checkStanceTransition(target_index)

            if target_index < closest_index then
                broadcastToAll("상처! 현재체력 " .. current_val, {1, 0.2, 0.2})
                
                -- 경화 상태 확인 (Charge Marker는 제외)
                local isHardened = false
                local hard_tokens = {}
                for _, o in ipairs(getAllObjects()) do
                    if isHardToken(o) and o.getName() ~= "Charge Marker" and o.getName() ~= "Vibration Marker" and o.getName() ~= "Glaciation" then
                        table.insert(hard_tokens, o)
                    end
                end
                if hard_tokens and #hard_tokens > 0 then
                    local hard_token = hard_tokens[1]
                    local sorted = getSortedSnapPoints(hard_token)
                    if sorted and #sorted > 0 then
                        local cp = hard_token.getPosition()
                        local hard_closest = 1
                        local min_d = math.huge
                        for i, sp in ipairs(sorted) do
                            local d = (cp.x - sp.x)^2 + (cp.z - sp.z)^2
                            if d < min_d then
                                min_d = d
                                hard_closest = i
                            end
                        end
                        -- 4번째 자석 지점이 값 3(경화)이므로 4 이상인지 체크
                        if hard_closest >= 4 then
                            isHardened = true
                        end
                    end
                end

                if monster_toughness > 0 then
                    _recentWoundToughness = monster_toughness
                    -- 상처 로직과 스탠스 변경 로직 사이의 시차(약 2초)를 고려하여 4초 뒤에 리셋
                    Wait.time(function() _recentWoundToughness = 0 end, 4)
                    
                    if isHardened then
                        local old = monster_damage
                        setMonsterDamage(0)
                        broadcastToAll(
                            string.format('경화(Hardened) 상태! 누적 데미지 %d → 0 으로 초기화', old),
                            {1, 0.3, 0.3}
                        )
                    else
                        local oldDamage = monster_damage
                        adjustMonsterDamage(-monster_toughness, true)
                        local newDamage = monster_damage
                        broadcastToAll(
                            string.format('상처 적용: 데미지 %d → %d (강인함 %d 차감)', oldDamage, newDamage, monster_toughness),
                            {1, 0.8, 0}
                        )
                    end
                end
            else
                broadcastToAll("몬스터가 회복했습니다! 현재체력 " .. current_val, {0.4, 0.8, 1.0})
            end

        elseif isHardToken(obj) then
            if obj.getName() == "Charge Marker" then
                if target_index < closest_index then
                    broadcastToAll("충전 감소! " .. current_val, {0.8, 0.8, 0.8})
                else
                    broadcastToAll("충전 증가! " .. current_val, {0.8, 0.8, 0.8})
                    if current_val == 3 then
                        broadcastToAll("충전되었습니다!", {1, 0.5, 0})
                        
                        -- 스탠스 카드 상태 변화 처리
                        local card = getActiveStanceCard()
                        if card then
                            local st = card.getStateId()
                            if st == 1 or st == 2 then
                                _previousToughness = monster_toughness
                                _previousStanceHasResistance = _currentStanceHasResistance
                                card.setState(st + 1)
                                Wait.time(applyStanceBreakthrough, 1.5)
                                -- 0.8초 후 자동으로 0위치(첫 번째 칸)로 되돌아감
                                Wait.time(function()
                                    if obj and not obj.isDestroyed() then
                                        local reset_target = sorted_snaps[1]
                                        reset_target.y = obj.getPosition().y + 0.2 -- 초기화 이동 시에도 살짝 띄움
                                        obj.setPositionSmooth(reset_target)
                                        broadcastToAll("충전도가 0으로 초기화되었습니다.", {0.8, 0.8, 0.8})
                                    end
                                end, 0.8)
                            elseif st == 3 then
                                Wait.time(function()
                                    broadcastToAll("제코로스의 뇌전이 폭발합니다! 모든 플레이어는 KO 되었습니다.", {1, 0, 0})
                                end, 0.5)
                            end
                        end
                    end
                end
            elseif obj.getName() == "Glaciation" then
                if target_index < closest_index then
                    broadcastToAll("빙결 수치 감소! " .. current_val, {0.6, 0.8, 1.0})
                else
                    broadcastToAll("빙결 수치 증가! " .. current_val, {0.6, 0.8, 1.0})
                end
            elseif obj.getName() == "Vibration Marker" then
                if target_index < closest_index then
                    broadcastToAll("진동 수치 감소! " .. current_val, {0.9, 0.7, 0.1})
                else
                    broadcastToAll("진동 수치 증가! " .. current_val, {0.9, 0.7, 0.1})
                    if current_val == 3 then
                        broadcastToAll("진동 수치가 최대로 도달했습니다!", {1, 0.5, 0})
                    end
                end
            else
                if target_index < closest_index then
                    broadcastToAll("경화 수치 감소! " .. current_val, {0.8, 0.8, 0.8})
                else
                    broadcastToAll("경화 수치 증가! " .. current_val, {0.8, 0.8, 0.8})
                    if current_val == 3 then
                        broadcastToAll("몬스터가 경화 상태가 되었습니다!", {1, 0.3, 0.3})
                    end
                end
            end
        end
    end
end