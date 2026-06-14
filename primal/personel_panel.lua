AGGRO_ON_URL = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111571390678/145B47FAD34C9279DB6464D8A4F9120AB333504B/'
AGGRO_OFF_URL = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111571389540/CA30F389ADD46B0FE9F0CFABD07C20615EFDE103/'

EXTENDED_MAT = 'https://steamusercontent-a.akamaihd.net/ugc/17133735590994085277/5D4E465740E30AE2734F6348B1196BED3D7DB93A/'
COLLAPSED_MAT = 'https://steamusercontent-a.akamaihd.net/ugc/15354677542493702953/A6AAB6B2F68FD88DCEAA579894CD8C93B11D84E1/'

THREATENED_URL = 'https://steamusercontent-a.akamaihd.net/ugc/16378673419954970639/6A21787DD6E4BCF729E1290F8944AF8EDC805E7A/'
TURN_END_MARKER_URL = 'https://steamusercontent-a.akamaihd.net/ugc/16465744318144975434/E48AF0CDCADD68E22EFD78EE062E8CBE0D2D5C00/'
SEQUENCE_SLOT_URL = 'https://steamusercontent-a.akamaihd.net/ugc/13577617259228275961/5A79E638EF06A34BF1F229FACBCE1024811DDEB3/'
WATER_BLOCKER_URL = 'https://steamusercontent-a.akamaihd.net/ugc/13111216766907417999/E5CC05C71904F5E28CAB5726F79702E3F9B66147/'

DAMAGE_BG_URL = 'https://steamusercontent-a.akamaihd.net/ugc/18178838673151729390/246BA89F9DF18B358EE363B4DAC073E2D387BEBC/'

EQUIPMENT_BG_URL = 'https://steamusercontent-a.akamaihd.net/ugc/10369557519346207521/3743AFB9AC46C17E287DF7B51A765CE69D7F4C45/'
EQUIPMENT_BG_HALF_URL = 'https://steamusercontent-a.akamaihd.net/ugc/16921441007728596820/BEB00D05C05A96CC786707FFCA3F6F1F63D722B0/'
EQUIPMENT_HIGHLIGHT_URL = 'https://steamusercontent-a.akamaihd.net/ugc/11661355341362006066/F81812AE973941EDC8E6EC4521B488101249548B/'
EQUIPMENT_HIGHLIGHT_HALF_URL = 'https://steamusercontent-a.akamaihd.net/ugc/13815737018645681549/57BBAFE5351D76F4CA81A5F12038898925C6EC29/'

STAMINA_URLS = {
    [1] = 'https://steamusercontent-a.akamaihd.net/ugc/11651281204409873210/7350360F4C6FD15753F79B76CA7D6DCC20B83429/',
    [2] = 'https://steamusercontent-a.akamaihd.net/ugc/15731883877263905782/E03FB7BCF80407569FB3957CDADDCBD00507552C/',
    [3] = 'https://steamusercontent-a.akamaihd.net/ugc/11542536937595298186/489C5808FD554EE50B54731005F76B9CDF6FFAE3/',
}

EQUIPMENT_TAGS = {
    'actor_armor',
    'actor_helm',
    'actor_accessory_1',
    'actor_accessory_2',
}

FIRST_PLAYER_URLS = {
    ['Blue']   = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535248821/110A9FFB2B665FE3139F44E22350F0CBF8A3D743/',
    ['Green']  = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535248971/E78FE186BBF1E42BD90AADF6A72B2C844BDDD8F5/',
    ['Yellow'] = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249223/DE77A57AEF52D95333974E82E1E642DA3E6D130D/',
    ['Orange'] = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249070/D878690B51AD96CBF2E542D21055F1A0EA01DB93/',
    ['Red']    = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249147/1A2CFA56B8E90764234D91CA0B220CCB1962EA8B/',
}

TOKENS = {
    ['Exhausted']   = { tag = 'bag_exhausted' },
    ['Dazed']       = { tag = 'bag_dazed' },
    ['Defensive']   = { tag = 'bag_defensive' },
    ['Disrupt']     = { tag = 'bag_disrupt' },
    ['Strain']      = { tag = 'bag_strain' },
    ['Depleted']    = { tag = 'bag_depleted' },
    ['BonusDamage'] = { tag = 'bag_bonus_damage' },
    ['Burned']      = { tag = 'bag_burned' },
    ['Threatened']  = { tag = 'bag_threatened' },
    ['Stamina']     = { tag = 'bag_stamina' },
    ['Counter']     = { tag = 'bag_counter' },
    ['KO']          = { tag = 'bag_ko' },
}

-- 시퀀스 슬롯 로컬 좌표
SEQUENCE_LOCAL_POSITIONS = {
    {x=0.635,  y=3.016, z=-0.981},
    {x=0.323,  y=3.015, z=-0.982},
    {x=0.011,  y=3.015, z=-0.981},
    {x=-0.312, y=3.015, z=-0.981},
    {x=-0.627, y=3.014, z=-0.976},
}

DISCARD_LOCAL_POS = {x=0.863, y=3.016, z=0.421}
DECK_LOCAL_POS = {x=0.863, y=2.247, z=-0.039}
HAND_SIZE_LIMIT_DEFAULT = 5

-- 데미지 버튼 위치 (createButton과 동일하게)
DAMAGE_BUTTON_LOCAL_POS = {-1.5, 1, -1.3}
DAMAGE_HOVER_RADIUS = 1.0

character_sheet_stats = {}
extended_slot_guids = {}

aggro_is_enabled = false
is_first_player = false
is_character_sheet_open = true
is_threatened = false
is_turn_ended = false
current_phase = 0
stamina_level = 0
hand_size_limit = 5
movement_phase_start_zone = nil
last_pickup_quadrant = nil

MOVEMENT_PHASE_MARKER_URL = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111559737310/4117293ACF34F339124FF95FC029613EEB4F8E01/'
ACTION_PHASE_MARKER_URL = 'https://steamusercontent-a.akamaihd.net/ugc/17335797285772214158/29D4DC3604244B67E68C73959F712E6FE1744243/'
ATTRITION_PHASE_MARKER_URL = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111559729521/EBF77250CBC0937ACE62E5CA5EE40B6894B108AE/'

after_play_hand_bonus = 0
damage_input_buffer = ''
damage_input_started = false

-- 장비 합계 관련 (저장 안 됨)
displayed_equipment_total = 0
equipment_exists = false
equipment_all_healthy = true
damage_counter = 0

is_discarding_sequence = false

reconstruct_deck_btn_index = -1
is_reconstruct_button_visible = false
is_reconstructing = false

function onLoad(script_state)
    local saveData = JSON.decode(script_state)

    for checkboxIndex = 1, 5 do
        for stepIndex = 1, 2 do
            disableCheckmark(character_sheet_stats, 'skilltree-' .. checkboxIndex .. '-' .. stepIndex)
        end
    end

    for matIndex = 1, 6 do
        self.UI.setAttribute('materials-' .. matIndex, 'color', getPastelColorFromTag() .. 'FF' or '#FFFFFFFF')
        self.UI.setAttribute('plants-' .. matIndex, 'color', getPastelColorFromTag() .. 'FF' or '#FFFFFFFF')
    end

    for elementIndex = 1, 9 do
        self.UI.setAttribute('elements-' .. elementIndex, 'color', getPastelColorFromTag() .. 'FF' or '#FFFFFFFF')
    end

    if saveData ~= nil then
        if saveData.aggro_is_enabled == true then enableAggro(true) end
        if saveData.is_first_player == true then enableFirstPlayer(true) end
        if saveData.is_threatened == true then enableThreatened() end

        if saveData.stamina_level ~= nil and saveData.stamina_level > 0 then
            stamina_level = saveData.stamina_level
            updateStaminaDecal()
        end

        if saveData.is_turn_ended == true then enableTurnEnd() end

        if saveData.hand_size_limit ~= nil then
            hand_size_limit = saveData.hand_size_limit
        end

        if saveData.is_character_sheet_open then
            openCharacterSheet()
        else
            closeCharacterSheet()
        end

        if saveData.character_sheet_stats ~= nil then
            character_sheet_stats = saveData.character_sheet_stats
            for id, value in pairs(character_sheet_stats) do
                if id:find('skilltree') then
                    if value == true then
                        enableCheckmark(character_sheet_stats, id)
                    else
                        disableCheckmark(character_sheet_stats, id)
                    end
                else
                    updateCounter(character_sheet_stats, id, value)
                end
            end
        end
    end

    local index = 1
    -- Left side tokens
    for _, tokenName in ipairs({ 'Exhausted', 'Dazed', 'Defensive', 'Disrupt', 'Strain', 'Depleted',
                                'BonusDamage', 'Burned' }) do
        local functionName = 'spawn' .. tokenName .. 'Token'
        self.setVar(functionName, function(_, color, alt_click)
            hoverWrapper(Player[color], spawnTokenOnButton, tokenName, alt_click == true and {0.00, 180.00, 180.00} or nil)
        end)

        self.createButton({
            click_function = functionName,
            function_owner = self,
            label          = '',
            position       = {(index%2==1 and -0.98 or -0.887), 1, -1.285 + (index-1) * 0.126},
            rotation       = {0, 180, 0},
            width          = 70,
            height         = 70,
            color          = {0.5, 0.5, 0.5, 0},
        })

        TOKENS[tokenName].button_index = index
        index = index + 1
    end

    -- Right side tokens
    for tokenName, details in pairs({
            ['Threatened'] = { position = {0.938, 1, -0.690}, width = 90, height = 90 },
            ['Stamina']    = { position = {0.938, 1, -0.492}, width = 90, height = 90 },
            ['Counter']    = { position = {0.786, 1, -0.315}, width = 70, height = 70 },
            ['KO']         = { position = {1.001, 1, -0.315}, width = 70, height = 70 }
    }) do
        local functionName = 'spawn' .. tokenName .. 'Token'

        if tokenName == 'Threatened' then
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], toggleThreatened)
            end)
        elseif tokenName == 'Stamina' then
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], alt_click and decrementStamina or incrementStamina)
            end)
        elseif tokenName == 'Counter' then
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], spawnTokenOnButton, tokenName, alt_click == true and {0.00, 225.00, 180.00} or {0.00, 225.00, 0.00})
            end)
        else
            self.setVar(functionName, function(_, color, alt_click)
                hoverWrapper(Player[color], spawnTokenOnButton, tokenName, alt_click == true and {0.00, 180.00, 180.00} or nil)
            end)
        end

        self.createButton({
            click_function = functionName,
            function_owner = self,
            label          = '',
            position       = details.position,
            rotation       = {0, 180, 0},
            width          = details.width,
            height         = details.height,
            font_size      = 5,
            color          = {0.5, 0.5, 0.5, 0},
        })

        TOKENS[tokenName].button_index = index
        index = index + 1
    end

    for i = 1, 3 do
        local id = "behave" .. i
        self.UI.setAttribute(id, "onClick", "ClickBehavior")
    end

    -- 장비 합계 클릭 영역 (좌클릭 +1, 우클릭 -1)
    self.setVar('handleEquipmentTotalClick', function(_, color, alt_click)
        hoverWrapper(Player[color], adjustEquipmentTotal, alt_click and -1 or 1)
    end)

    self.createButton({
        click_function = 'handleEquipmentTotalClick',
        function_owner = self,
        label          = '',
        position       = {-0.01, 1, -1.3},
        rotation       = {0, 180, 0},
        width          = 40,
        height         = 60,
        font_size      = 5,
        color          = {0.5, 0.5, 0.5, 0},
    })

    -- 데미지 카운터 클릭 영역 (좌클릭 +1, 우클릭 -1, 최대 = 장비값)
    self.setVar('handleDamageClick', function(_, color, alt_click)
        hoverWrapper(Player[color], adjustDamageCounter, alt_click and -1 or 1)
    end)

    self.createButton({
        click_function = 'handleDamageClick',
        function_owner = self,
        label          = '',
        position       = {-0.15, 1, -1.3},
        rotation       = {0, 180, 0},
        width          = 40,
        height         = 60,
        font_size      = 5,
        color          = {0.5, 0.5, 0.5, 0},
        tooltip        = '숫자 키를 입력하면 숫자가 바로 바뀝니다.',
    })

    self.setVar('handleReconstructDeck', function(_, color)
        if not is_reconstruct_button_visible or is_reconstructing then return end
        
        local matColor = getMatColorFromTag()
        local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
        local discard = findDeckAtWorldPos(discardWorldPos)
        
        if discard then
            is_reconstructing = true
            hideReconstructButton()
            startLuaCoroutine(self, 'reconstructDeckCoroutine')
        else
            broadcastToColor("버린 카드 더미가 없습니다.", color, Color.Red)
        end
    end)

    self.createButton({
        click_function = 'handleReconstructDeck',
        function_owner = self,
        label          = '',
        position       = {-0.863, 0.83, -0.039},
        rotation       = {0, 0, 0},
        scale          = {0.18, 1, 0.18},
        width          = 0,
        height         = 0,
        font_size      = 120,
        color          = {0, 0, 0, 1},
        font_color     = {1, 1, 1, 1},
        tooltip        = '버린 카드 더미를 섞어 덱을 재구성하고 탈진 피해를 받습니다.',
    })
    
    local buttons = self.getButtons()
    for _, btn in ipairs(buttons) do
        if btn.click_function == 'handleReconstructDeck' then
            reconstruct_deck_btn_index = btn.index
            break
        end
    end

    preloadDecalImages()
    addStaticBoardDecals()
    setEquipmentBgDecal(false)             -- 초기는 기본 BG
    Wait.time(updateEquipmentTotal, 2)     -- 2초 후 실제 상태로 갱신
    Wait.time(updateSequenceSlotDecals, 2)
    self.max_typed_number = 2
    Wait.time(function() startLuaCoroutine(self, "monitorHandSizeLoop") end, 3)
    Wait.time(checkDeckReconstructButton, 3)
end

_last_notified_hand_limit = nil
_pending_hand_limit = nil
_pending_limit_ticks = 0

function isHoldingHandSizeObject()
    for _, player in ipairs(Player.getPlayers()) do
        local holding = player.getHoldingObjects()
        if holding then
            for _, obj in ipairs(holding) do
                if obj.hasTag('hand_plus_1') 
                   or obj.hasTag('emergency_hand_plus_1') 
                   or obj.hasTag('pierce2_hand_plus_1') 
                   or obj.hasTag('after_play_hand_plus_1')
                   or obj.getName() == 'Pierce Token'
                   or obj.getName() == 'Strain'
                   or obj.hasTag('Strain') then
                    return true
                end
            end
        end
    end
    return false
end

function monitorHandSizeLoop()
    local holdCooldown = 0
    while true do
        local matColor = getMatColorFromTag()
        if matColor and isThisBoardActive() then
            if isHoldingHandSizeObject() then
                holdCooldown = 4 -- 내려놓은 후 약 1초(0.25초 x 4) 대기
            end
            
            if holdCooldown > 0 then
                holdCooldown = holdCooldown - 1
            else
                local currentLimit, breakdown = calculateEffectiveHandSizeLimit()
                
                if _last_notified_hand_limit == nil then
                    _last_notified_hand_limit = currentLimit
                elseif _last_notified_hand_limit ~= currentLimit then
                    if _pending_hand_limit ~= currentLimit then
                        _pending_hand_limit = currentLimit
                        _pending_limit_ticks = 1
                    else
                        _pending_limit_ticks = _pending_limit_ticks + 1
                        if _pending_limit_ticks >= 2 then
                            local diff = currentLimit - _last_notified_hand_limit
                            local word = diff > 0 and "증가" or "감소"
                            local colorVal = Color[matColor] or Color.White
                            
                            printToAll(
                                string.format("%s: 손패 한도가 %d장으로 %s했습니다!\n  상세정보: %s", 
                                matColor, currentLimit, word, breakdown),
                                colorVal
                            )
                            
                            _last_notified_hand_limit = currentLimit
                            _pending_hand_limit = nil
                        end
                    end
                else
                    _pending_hand_limit = nil
                    _pending_limit_ticks = 0
                end
            end
        end
        for i = 1, 15 do coroutine.yield(0) end -- 0.25초 간격으로 확인하여 총 0.5초 대기
    end
    return 1
end

function ClickBehavior(player, value, id)
    local img = self.UI.getAttribute(id, "image")
    if img == nil or img == "" then return end

    local behaviorDescription = Global.getTable("BehaviorDescription")
    local msg = behaviorDescription[img]

    if msg then
        broadcastToAll(msg, {r=1, g=1, b=1})
    else
        broadcastToAll("No description found for image: " .. tostring(img), {r=1, g=1, b=1})
    end
end

-- global.lua에서 board.call()로 호출되는 함수
-- behave 버튼 위에 겹쳐진 데칼 오버레이의 투명도를 토글합니다.
function setBehaviorRing(params)
    local uiName = params.uiName  -- "behave1", "behave2", "behave3"
    local active = params.active
    local decalId = uiName .. "_decal"
    if active then
        self.UI.show(decalId)
        self.UI.setAttribute(decalId, "color", "#FFFFFFFF")
    else
        self.UI.hide(decalId)
        self.UI.setAttribute(decalId, "color", "#00000000")
    end
end

function onSave()
    local saveData = {}
    saveData.aggro_is_enabled        = aggro_is_enabled
    saveData.is_first_player         = is_first_player
    saveData.is_character_sheet_open = is_character_sheet_open
    saveData.is_threatened           = is_threatened
    saveData.character_sheet_stats   = character_sheet_stats
    saveData.stamina_level           = stamina_level
    saveData.is_turn_ended           = is_turn_ended
    saveData.hand_size_limit         = hand_size_limit
    return JSON.encode(saveData)
end

function hoverWrapper(player, callback, ...)
    if player ~= nil and player.getHoverObject() == self and callback ~= nil then
        callback(...)
    end
end

--------------------
-- Aggro UI
function toggleAggroWrapper(player)
    hoverWrapper(player, toggleAggro)
end

function toggleAggro()
    if not aggro_is_enabled then
        enableAggro()
        for _, object in ipairs(getObjectsWithTag('player_board')) do
            if object ~= self then object.call('disableAggro') end
        end
    else
        disableAggro()
    end
end

function enableAggro(params)
    local hideBroadcast = false
    if type(params) == "table" then
        hideBroadcast = params.hideBroadcast or params[1] or false
    else
        hideBroadcast = params or false
    end

    self.UI.setAttribute('aggro-button', 'image', AGGRO_ON_URL)
    aggro_is_enabled = true

    local matColor = getMatColorFromTag()
    if matColor then
        Global.call("SyncAggroFromBoard", {color = matColor, active = true})
        if not hideBroadcast then
            local playerName = Player[matColor].steam_name
            if playerName then
                broadcastToAll(playerName .. ' (' .. matColor .. ') has drawn aggro!', Color[matColor])
            else
                broadcastToAll(matColor .. ' has drawn aggro!', Color[matColor])
            end
        end
    else
        broadcastToAll('Object ' .. self.getGUID() .. ' is missing a color tag.', Color.Red)
    end
end

function disableAggro()
    self.UI.setAttribute('aggro-button', 'image', AGGRO_OFF_URL)
    aggro_is_enabled = false
    local matColor = getMatColorFromTag()
    if matColor then
        Global.call("SyncAggroFromBoard", {color = matColor, active = false})
    end
end

--------------------
-- First player UI
function toggleFirstPlayerWrapper(player)
    hoverWrapper(player, toggleFirstPlayer)
end

function toggleFirstPlayer()
    if not is_first_player then
        enableFirstPlayer()
        for _, object in ipairs(getObjectsWithTag('player_board')) do
            if object ~= self then object.call('disableFirstPlayer') end
        end
    else
        disableFirstPlayer()
    end
end

function enableFirstPlayer(hideBroadcast)
    hideBroadcast = hideBroadcast or false
    local matColor = getMatColorFromTag()
    if not matColor then
        broadcastToAll('Object ' .. self.getGUID() .. ' is missing a color tag.', Color.Red)
        matColor = 'Red'
    end

    self.UI.setAttribute('first-player-button', 'image', FIRST_PLAYER_URLS[getMatColorFromTag()])
    self.UI.setAttribute('first-player-button', 'color', '#FFFFFFFF')
    is_first_player = true

    if not hideBroadcast then
        local playerName = Player[matColor].steam_name
        if playerName then
            broadcastToAll(playerName .. ' (' .. matColor .. ') is the first player!', Color[matColor])
        else
            broadcastToAll(matColor .. ' is the first player!', Color[matColor])
        end
    end
    
    local isGameStarted = Global.getVar('is_game_started')
    Global.call('UpdateTurnOrder', {color = matColor})
    
    if not isGameStarted then
        enableAggro(hideBroadcast)
        for _, object in ipairs(getObjectsWithTag('player_board')) do
            if object ~= self then object.call('disableAggro') end
        end
    end
end

function disableFirstPlayer()
    self.UI.setAttribute('first-player-button', 'color', '#FFFFFF00')
    self.UI.setAttribute('first-player-button', 'image', '')
    is_first_player = false
    
    local matColor = getMatColorFromTag()
    if matColor and Global.call('GetCurrentFirstPlayer') == matColor then
        Global.call('ClearFirstPlayer')
    end
end

--------------------
-- Character sheet UI
function toggleCharacterSheetWrapper(player)
    hoverWrapper(player, toggleCharacterSheet)
end

function toggleCharacterSheet()
    if not is_character_sheet_open then
        openCharacterSheet()
    else
        closeCharacterSheet()
    end
end

function openCharacterSheet()
    self.setCustomObject({type = 1, face = EXTENDED_MAT, back = EXTENDED_MAT})
    self.UI.setAttribute('character-sheet-buttons', 'active', true)
    is_character_sheet_open = true
end

function closeCharacterSheet()
    self.setCustomObject({type = 1, face = COLLAPSED_MAT, back = COLLAPSED_MAT})
    self.UI.setAttribute('character-sheet-buttons', 'active', false)
    is_character_sheet_open = false
end

function toggleSkillTreeCheckmarkWrapper(player, _, id)
    hoverWrapper(player, toggleCheckmark, character_sheet_stats, id)
end

--------------------
-- Token spawn
function spawnTokenOnButton(tokenName, rotation)
    local spawnPosition = self.getButtons()[TOKENS[tokenName].button_index].position
    spawnPosition.x = -spawnPosition.x
    spawnPosition.y = spawnPosition.y + 3

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

----------------------
-- Utility functions
function toggleCheckmark(array, id)
    if not array then return end
    if array[id] then disableCheckmark(array, id) else enableCheckmark(array, id) end
end

function disableCheckmark(array, id)
    if not array then return end
    array[id] = false
    local color = getPastelColorFromTag() or '#FFFFFF'
    self.UI.setAttribute(id, 'colors', color .. '00|' .. color .. '99|' .. color .. 'BB|rgba(0.78,0.78,0.78,0.5)')
end

function enableCheckmark(array, id)
    if not array then return end
    array[id] = true
    local color = getPastelColorFromTag() or '#FFFFFF'
    self.UI.setAttribute(id, 'colors', color .. 'FF|' .. color .. '99|'.. color .. 'BB|rgba(0.78,0.78,0.78,0.5)')
end

function incrementCSCounterWrapper(player, _, id)
    hoverWrapper(player, incrementCounter, character_sheet_stats, id:gsub('%-plus', ''))
end

function decrementCSCounterWrapper(player, _, id)
    hoverWrapper(player, decrementCounter, character_sheet_stats, id:gsub('%-minus', ''), positiveClamp)
end

function incrementCounter(array, id, clamp)
    if not array or not id then return end
    local newValue = tonumber(array[id] or '0') + 1
    if clamp ~= nil and type(clamp) == 'function' then newValue = clamp(newValue) end
    updateCounter(array, id, newValue)
end

function decrementCounter(array, id, clamp)
    if not array or not id then return end
    local newValue = tonumber(array[id] or '0') - 1
    if clamp ~= nil and type(clamp) == 'function' then newValue = clamp(newValue) end
    updateCounter(array, id, newValue)
end

function updateCounter(array, id, value)
    if not array or not id or value == nil then return end
    array[id] = value
    self.UI.setAttribute(id, 'text', value)
end

function getPastelColorFromTag()
    local color = getMatColorFromTag()
    if color == 'Blue' then return '#4572cc'
    elseif color == 'Green' then return '#49b851'
    elseif color == 'Yellow' then return '#ebea57'
    elseif color == 'Orange' then return '#d4723d'
    elseif color == 'Red' then return '#d44333'
    else return nil end
end

function getMatColorFromTag()
    if self.hasTag('color_blue') then return 'Blue'
    elseif self.hasTag('color_green') then return 'Green'
    elseif self.hasTag('color_yellow') then return 'Yellow'
    elseif self.hasTag('color_orange') then return 'Orange'
    elseif self.hasTag('color_red') then return 'Red'
    else return nil end
end

function positiveClamp(value)
    if value < 0 then return 0 else return value end
end

--------------------
-- Sequence Auto-Discard Logic
function countSequencePlusCards()
    local sequencePlusCount = 0
    local focusSequencePlusCount = 0
    local sequenceCardCount = 0

    local centerZ = SEQUENCE_LOCAL_POSITIONS[1].z
    local centerY = SEQUENCE_LOCAL_POSITIONS[1].y
    local centerWorld = self.positionToWorld({x=0, y=centerY, z=centerZ})

    local hitList = Physics.cast({
        origin       = centerWorld,
        direction    = {0, 1, 0},
        type         = 3,
        size         = {12, 1.5, 1.5},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if obj ~= self and not isHeld then
            if obj.type == "Card" or obj.type == "Deck" then
                sequenceCardCount = sequenceCardCount + 1
            end

            if not obj.is_face_down then
                if obj.hasTag('sequence_plus_1') then
                    sequencePlusCount = sequencePlusCount + 1
                end
                if obj.hasTag('focus_sequence_plus_1') then
                    focusSequencePlusCount = focusSequencePlusCount + 1
                end
            end
        end
    end

    local count = sequencePlusCount

    -- 시퀀스 영역의 focus 카드 + 보드 어딘가 뒤집힌 mastery
    if focusSequencePlusCount > 0 and hasFaceDownActorMastery() then
        count = count + focusSequencePlusCount
    end

    -- 추가: actor_mastery 자체가 focus 태그 있고 뒤집힌 경우 (각 카드당 +1)
    count = count + countFaceDownMasteryWithFocus()

    return count
end

-- 보드 전체에서 뒤집힌 actor_mastery 카드가 있는지 확인
function hasFaceDownActorMastery()
    for _, obj in ipairs(getObjectsWithTag('actor_mastery')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld and obj.is_face_down and isOnThisBoard(obj) then
            return true
        end
    end
    return false
end

function isPlayerAffectedByMist()
    local is_game_started = Global.getVar("is_game_started")
    if not is_game_started then return false end
    
    local inMist = false
    if _terrainNames then
        for i=1, 3 do
            if _terrainNames[i] == "안개" then
                inMist = true
                break
            end
        end
    end
    return inMist
end

function isPlayerAffectedByWater()
    local is_game_started = Global.getVar("is_game_started")
    if not is_game_started then return false end
    
    local matColor = getMatColorFromTag()
    if not matColor then return false end
    
    local inWater = false
    if _terrainNames then
        for i=1, 3 do
            if _terrainNames[i] == "물" then
                inWater = true
                break
            end
        end
    else
        inWater = Global.call("CheckPlayerInWater", matColor)
    end
    if not inWater then return false end
    
    for _, obj in ipairs(getObjectsWithTag('water_proof')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld and not obj.is_face_down and isOnThisBoard(obj) then
            return false
        end
    end
    
    return true
end

function getSequenceCapacity()
    local plusCount = countSequencePlusCards()
    local baseCapacity = 5
    
    if isPlayerAffectedByWater() then
        baseCapacity = 3
    end
    
    return baseCapacity + plusCount
end

function getEffectiveSequencePositions()
    local positions = {}
    local capacity = getSequenceCapacity()
    local spacing = SEQUENCE_LOCAL_POSITIONS[5].x - SEQUENCE_LOCAL_POSITIONS[4].x

    for i = 1, capacity do
        if i <= 5 then
            table.insert(positions, SEQUENCE_LOCAL_POSITIONS[i])
        else
            local extra = i - 5
            local lastSlot = SEQUENCE_LOCAL_POSITIONS[5]
            table.insert(positions, {
                x = lastSlot.x + (spacing * extra),
                y = lastSlot.y,
                z = lastSlot.z,
            })
        end
    end
    return positions
end

function updateSequenceSlotDecals()
    -- 1. 이 보드의 기존 확장 슬롯 모두 제거
    local slotTag = 'extension_slot_' .. self.getGUID()
    for _, obj in ipairs(getObjectsWithTag(slotTag)) do
        obj.destruct()
    end
    extended_slot_guids = {}

    -- 2. 기존 데칼 슬롯 정리 (맨 아래에서 세팅함)
    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if not (decal.name and decal.name:find('^sequence_slot_')) then
            table.insert(newDecals, decal)
        end
    end

    -- 3. 새 물리 슬롯 생성
    local capacity = getSequenceCapacity()
    local spacing = SEQUENCE_LOCAL_POSITIONS[5].x - SEQUENCE_LOCAL_POSITIONS[4].x
    local baseSlot = SEQUENCE_LOCAL_POSITIONS[5]
    local boardRot = self.getRotation()

    local extraCount = math.max(0, capacity - 5)
    
    -- 본인의 턴일 때만 물리적 추가 슬롯을 표시 (물지형 블로커는 capacity를 그대로 사용)
    local isMyTurn = (Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') == getMatColorFromTag())
    if not isMyTurn then
        extraCount = 0
    end

    for i = 1, extraCount do
        local newX = baseSlot.x + spacing * i
        local localPos = {x=newX, y=0.21, z=baseSlot.z}
        local worldPos = self.positionToWorld(localPos)

        local tile = spawnObjectData({
            data = {
                Name = 'Custom_Tile',
                Transform = {
                    posX = worldPos.x,
                    posY = worldPos.y,
                    posZ = worldPos.z,
                    rotX = 0,
                    rotY = boardRot.y,
                    rotZ = 0,
                    scaleX = 1.2,
                    scaleY = 0.1,
                    scaleZ = 1.2,
                },
                Nickname = 'Sequence Slot ' .. (5 + i),
                Locked = true,
                CustomImage = {
                    ImageURL = SEQUENCE_SLOT_URL,
                    ImageSecondaryURL = '',
                    ImageScalar = 1.0,
                    WidthScale = 0,
                    CustomTile = {
                        Type = 0,
                        Thickness = 0.1,
                        Stackable = false,
                        Stretch = true,
                    },
                },
            },
            callback_function = function(obj)
                obj.interactable = false
                obj.addTag(slotTag)

                -- 타일 가운데에 자석 포인트 추가
                obj.setSnapPoints({
                    {
                        position      = {0, 0.5, 0},
                        rotation      = {0, 0, 0},
                        rotation_snap = false,
                    }
                })
            end,
        })

        table.insert(extended_slot_guids, tile.getGUID())
    end

    -- 4. 물 지형 블로커 데칼 생성
    if isPlayerAffectedByWater() then
        local waterBlockerX
        if capacity == 3 then
            waterBlockerX = (SEQUENCE_LOCAL_POSITIONS[3].x + SEQUENCE_LOCAL_POSITIONS[4].x) / 2
        elseif capacity == 4 then
            waterBlockerX = (SEQUENCE_LOCAL_POSITIONS[4].x + SEQUENCE_LOCAL_POSITIONS[5].x) / 2
        elseif capacity == 5 then
            waterBlockerX = SEQUENCE_LOCAL_POSITIONS[5].x + (spacing / 2)
        end
        
        if waterBlockerX then
            table.insert(newDecals, {
                name     = 'sequence_slot_water_blocker',
                url      = WATER_BLOCKER_URL,
                position = {waterBlockerX, SEQUENCE_LOCAL_POSITIONS[3].y, SEQUENCE_LOCAL_POSITIONS[3].z},
                rotation = {90, 180, 0},
                scale    = {0.08, 0.5, 0.1},
            })
        end
    end

    self.setDecals(newDecals)

    checkSequenceAggro()
end

temporary_aggro_card_count = 0

function checkSequenceAggro()
    local CurrentMonster = Global.getVar("CurrentMonster")
    if CurrentMonster == "Xitheros" or CurrentMonster == "지테로스" then return end

    if is_discarding_sequence then return end

    local matColor = getMatColorFromTag()
    if not matColor then return end

    -- 현재 턴 플레이어의 보드가 아니며 임시 어그로 관련 카드가 전혀 없었다면 불필요한 연산 생략
    if Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') ~= matColor and temporary_aggro_card_count == 0 then
        return
    end

    local positions = getEffectiveSequencePositions()
    local currentAggroCardCount = 0

    for _, localPos in ipairs(positions) do
        local worldPos = self.positionToWorld(localPos)
        local card = findCardAtWorldPos(worldPos)
        if card and not card.is_face_down then
            if card.hasTag('Aggro') or card.hasTag('aggro') then
                currentAggroCardCount = currentAggroCardCount + 1
            end
        end
    end

    if currentAggroCardCount > temporary_aggro_card_count then
        if Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') == matColor then
            local diff = currentAggroCardCount - temporary_aggro_card_count
            for i = 1, diff do
                Global.call("SavePreviousAggro")
                enableAggro(false)
                for _, object in ipairs(getObjectsWithTag('player_board')) do
                    if object ~= self then object.call('disableAggro') end
                end
            end
            temporary_aggro_card_count = currentAggroCardCount
        end
    elseif currentAggroCardCount < temporary_aggro_card_count then
        local diff = temporary_aggro_card_count - currentAggroCardCount
        for i = 1, diff do
            disableAggro()
            Global.call("RevertAggro")
        end
        temporary_aggro_card_count = currentAggroCardCount
    end
end

function discardSequenceWrapper(player)
    startLuaCoroutine(self, "discardSequenceCoroutine")
end

function discardSequenceNoDrawWrapper()
    startLuaCoroutine(self, "discardSequenceNoDrawCoroutine")
end

function discardSequenceNoDrawCoroutine()
    discardSequenceCoroutine(true)
    return 1
end

function isPlayerKO()
    for _, obj in ipairs(getAllObjects()) do
        local name = obj.getName()
        if (name == "KO'D" or name == "KO'D Token" or obj.hasTag("KO'D")) and isOnThisBoard(obj) then
            return true
        end
    end
    return false
end

function discardSequenceCoroutine(skip_draw)
    if skip_draw == nil then
        skip_draw = isPlayerKO()
    end
    
    is_discarding_sequence = true
    
    -- 카드가 치워지기 전에 현재 시퀀스의 핸드 보너스를 저장해 둡니다.
    after_play_hand_bonus = countAfterPlayHandPlus1Cards()

    local boardRot = self.getRotation()
    local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
    local positions = getEffectiveSequencePositions()

    local movedCards = {}

    for i, localPos in ipairs(positions) do
        local worldPos = self.positionToWorld(localPos)
        local card = findCardAtWorldPos(worldPos)
        if card then
            pcall(function()
                card.use_hands = false
                card.setPositionSmooth(
                    {discardWorldPos.x, discardWorldPos.y + i * 0.4, discardWorldPos.z},
                    false, false
                )
                card.setRotationSmooth({0, boardRot.y, 0}, false, false)
                Wait.time(function() if card ~= nil then card.use_hands = true end end, 1.0)
            end)
            table.insert(movedCards, card)
        end
        for f=1, 5 do coroutine.yield(0) end
    end

    -- 모든 카드 이동 완료 대기 (상태 기반)
    local maxWait = 180
    local waitCount = 0
    while waitCount < maxWait do
        local anyMoving = false
        for _, card in ipairs(movedCards) do
            if card ~= nil and not card.isDestroyed() and card.isSmoothMoving() then
                anyMoving = true
                break
            end
        end
        if not anyMoving then break end
        coroutine.yield(0)
        waitCount = waitCount + 1
    end

    -- 약간의 정착 시간 (덱 합쳐지는 시간)
    for f=1, 30 do coroutine.yield(0) end

    local finalDiscard = findCardAtWorldPos(discardWorldPos)
    if finalDiscard then finalDiscard.use_hands = true end

    temporary_aggro_card_count = 0
    is_discarding_sequence = false

    Wait.time(updateSequenceSlotDecals, 0.3)
    if not skip_draw then
        Wait.time(drawToHandLimit, 0.3)
    end
    return 1
end

function findCardAtWorldPos(worldPos)
    local hitList = Physics.cast({
        origin       = {worldPos.x, worldPos.y + 2.0, worldPos.z},
        direction    = {0, -1, 0},
        type         = 3,
        size         = {0.8, 0.8, 0.8},
        max_distance = 4,
        debug        = false
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and (obj.tag == "Card" or obj.tag == "Deck") then
            if not obj.hasTag("player_board") and not obj.locked then
                return obj
            end
        end
    end
    return nil
end

--------------------
-- Threatened marker
function toggleThreatened()
    if not is_threatened then enableThreatened() else disableThreatened() end
end

function enableThreatened()
    local decals = self.getDecals() or {}
    table.insert(decals, {
        name     = 'threatened_marker',
        url      = THREATENED_URL,
        position = {-0.938, 0.21, -0.690},
        rotation = {90, 180, 0},
        scale    = {0.13, 0.13, 0.13},
    })
    self.setDecals(decals)
    is_threatened = true
    Global.call('TriggerBehaviorCheck', {type = "Threat", color = getMatColorFromTag()})
end

function disableThreatened()
    if isPlayerAffectedByMist() then
        local matColor = getMatColorFromTag()
        if matColor then
            broadcastToAll(matColor .. '는 안개 지형으로 인해 위협받습니다.', Color[matColor] or Color.White)
        end
        if not is_threatened then
            enableThreatened()
        end
        return false
    end

    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if decal.name ~= 'threatened_marker' then
            table.insert(newDecals, decal)
        end
    end
    self.setDecals(newDecals)
    is_threatened = false
    return true
end

--------------------
-- Stamina marker (4단계: 0~3)
function incrementStamina()
    if stamina_level < 3 then
        stamina_level = stamina_level + 1
        updateStaminaDecal()
    end
end

function decrementStamina()
    if stamina_level > 0 then
        stamina_level = stamina_level - 1
        updateStaminaDecal()
    end
end

function updateStaminaDecal()
    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if decal.name ~= 'stamina_marker' then
            table.insert(newDecals, decal)
        end
    end

    if stamina_level > 0 then
        table.insert(newDecals, {
            name     = 'stamina_marker',
            url      = STAMINA_URLS[stamina_level],
            position = {-0.938, 0.21, -0.492},
            rotation = {90, 180, 0},
            scale    = {0.13, 0.13, 0.13},
        })
    end
    self.setDecals(newDecals)
end

--------------------
-- Image Preloader
function preloadDecalImages()
    local decals = self.getDecals() or {}
    local existingUrls = {}
    for _, decal in ipairs(decals) do
        if decal.name and decal.name:find('^preload_') then
            existingUrls[decal.url] = true
        end
    end

    local urlsToPreload = {
        THREATENED_URL,
        STAMINA_URLS[1],
        STAMINA_URLS[2],
        STAMINA_URLS[3],
        TURN_END_MARKER_URL,
        SEQUENCE_SLOT_URL,
        DAMAGE_BG_URL,
        EQUIPMENT_BG_URL,
        EQUIPMENT_BG_HALF_URL,
        EQUIPMENT_HIGHLIGHT_URL,
        EQUIPMENT_HIGHLIGHT_HALF_URL,
    }

    local added = false
    for i, url in ipairs(urlsToPreload) do
        if not existingUrls[url] then
            table.insert(decals, {
                name     = 'preload_' .. i,
                url      = url,
                position = {0, -50, 0},
                rotation = {0, 0, 0},
                scale    = {0.01, 0.01, 0.01},
            })
            added = true
        end
    end

    if added then self.setDecals(decals) end
end

--------------------
-- Turn end button

function getPlayerQuadrant(color)
    local figures = getObjectsWithTag("owner_" .. color)
    local playerFig = nil
    for _, fig in ipairs(figures) do
        if fig.hasTag("actor_mini") then
            playerFig = fig
            break
        end
    end
    if not playerFig and #figures > 0 then playerFig = figures[1] end
    if not playerFig then return nil end
    
    local combatBoardGUID = Global.call('GetCombatBoardGUID')
    if not combatBoardGUID then return nil end
    
    local terrains = Global.getTable('Terrains')
    if not terrains then return nil end
    
    local figPos = playerFig.getPosition()
    local closestZone = nil
    local closestDist = math.huge
    
    for zoneName, snapTags in pairs(terrains) do
        for _, snapTag in ipairs(snapTags) do
            local snapPos = Global.call('getWorldPosOfSnapOnObj', {combatBoardGUID, snapTag})
            if snapPos then
                local dx = figPos.x - snapPos.x
                local dz = figPos.z - snapPos.z
                local dist = dx*dx + dz*dz
                if dist < closestDist then
                    closestDist = dist
                    closestZone = zoneName
                end
            end
        end
    end
    
    return closestZone
end

function onPlayerTurn(player, previous_player)
    local matColor = getMatColorFromTag()
    if Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') == matColor then
        -- KO'D 토큰 체크
        local kodToken = nil
        for _, obj in ipairs(getAllObjects()) do
            local name = obj.getName()
            if (name == "KO'D" or name == "KO'D Token" or obj.hasTag("KO'D")) and isOnThisBoard(obj) then
                local pos = obj.getPosition()
                local hitList = Physics.cast({
                    origin       = pos,
                    direction    = {0,-1,0},
                    type         = 1,
                    max_distance = 2.0,
                })
                local isActorBoard = false
                for _, hit in ipairs(hitList) do
                    if hit.hit_object == self or hit.hit_object.hasTag('actor_board') then
                        isActorBoard = true
                        break
                    end
                end
                if isActorBoard then
                    kodToken = obj
                    break
                end
            end
        end

        if kodToken then
            if not kodToken.is_face_down then
                -- 앞면인 경우: 뒤집기
                kodToken.flip()
            else
                -- 뒷면인 경우: KO'D 토큰 삭제 후 덱에서 5장 뽑기
                kodToken.destruct()
                
                local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
                local deck = findDeckAtWorldPos(deckWorldPos)
                if deck then
                    if Player[matColor].seated then
                        deck.deal(5, matColor, 1)
                    else
                        local startPos = {x=0.635, y=0.25, z=-0.45}
                        for i = 1, 5 do
                            local newX = startPos.x - ((i - 1) * 0.28)
                            local localTarget = {x=newX, y=startPos.y, z=startPos.z}
                            local worldTarget = self.positionToWorld(localTarget)
                            deck.takeObject({
                                position = worldTarget,
                                rotation = {0, 180, 0},
                                smooth = true
                            })
                        end
                    end
                end
            end

            -- 모든 페이즈 건너뛰고 End Turn 상태 대기 (클릭 시 턴 종료되도록 phase 3 유지)
            current_phase = 3
            disablePhaseDecals()
            broadcastToAll("KO 상태이므로 턴을 건너뜁니다.", Color[matColor] or {1,1,1})
            updateGlobalPhaseHUD(4, true)
            return
        end

        current_phase = 1
        disableTurnEnd()
        setPhaseDecal(1)
        broadcastToAll("Movement Phase", matColor)
        movement_phase_start_zone = getPlayerQuadrant(matColor)
    else
        current_phase = 0
        disablePhaseDecals()
    end
end

function updateGlobalPhaseHUD(phase_num, active)
    if not active then
        Global.UI.setAttribute("PhaseHUD", "active", "false")
        return
    end

    local url = ""
    local text = ""
    if phase_num == 1 then
        url = MOVEMENT_PHASE_MARKER_URL
        text = "Movement Phase"
    elseif phase_num == 2 then
        url = ACTION_PHASE_MARKER_URL
        text = "Action Phase"
    elseif phase_num == 3 then
        url = ATTRITION_PHASE_MARKER_URL
        text = "Attrition Phase"
    elseif phase_num == 4 then
        url = TURN_END_MARKER_URL
        text = "End Turn"
    end

    if url == "" then
        Global.UI.setAttribute("PhaseHUD", "active", "false")
    else
        Global.UI.setAttribute("PhaseHUD_Image", "image", url)
        Global.UI.setAttribute("PhaseHUD_Text", "text", text)
        
        local matColor = getMatColorFromTag() or ""
        Global.UI.setAttribute("PhaseHUD", "visibility", matColor)
        
        if matColor ~= "" and Color[matColor] then
            Global.UI.setAttribute("PhaseHUD", "outline", "#" .. Color[matColor]:toHex(false))
        else
            Global.UI.setAttribute("PhaseHUD", "outline", "none")
        end
        
        Global.UI.setAttribute("PhaseHUD", "active", "true")
    end
end

function toggleTurnEndFromGlobal(player)
    local boardColor = getMatColorFromTag()
    
    if not Global.call('GetTurnSystemActive') then
        if current_phase > 0 then
            current_phase = 0
            disablePhaseDecals()
            broadcastToAll("페이즈 초기화 완료", boardColor)
            return
        elseif is_turn_ended then
            disableTurnEnd()
            return
        else
            broadcastToAll("턴 시스템이 비활성화 되어있습니다.", boardColor)
            return
        end
    end
    
    if boardColor ~= Global.call('GetCurrentTurnColor') then
        broadcastToAll("현재 활성화 플레이어가 아닙니다.", boardColor)
        return
    end
    
    toggleTurnEnd()
end

function toggleTurnEndWrapper(player)
    local boardColor = getMatColorFromTag()
    
    -- 턴 시스템이 비활성화 상태일 때
    if not Global.call('GetTurnSystemActive') then
        if current_phase > 0 then
            current_phase = 0
            disablePhaseDecals()
            broadcastToAll("페이즈 초기화 완료", boardColor)
            return
        elseif is_turn_ended then
            hoverWrapper(player, disableTurnEnd)
            return
        else
            broadcastToAll("턴 시스템이 비활성화 되어있습니다.", boardColor)
            return
        end
    end
    
    -- 턴 시스템은 켜져있으나 본인 턴이 아닐 때
    if boardColor ~= Global.call('GetCurrentTurnColor') then
        broadcastToAll("현재 활성화 플레이어가 아닙니다.", boardColor)
        return
    end
    
    hoverWrapper(player, toggleTurnEnd)
end

function toggleTurnEnd()
    local matColor = getMatColorFromTag()
    if current_phase == 0 then
        current_phase = 1
        disableTurnEnd()
        setPhaseDecal(1)
        broadcastToAll("Movement Phase", matColor)
        movement_phase_start_zone = getPlayerQuadrant(matColor)
    elseif current_phase == 1 then
        current_phase = 2
        setPhaseDecal(2)
        broadcastToAll("Action Phase", matColor)
        
        local current_zone = getPlayerQuadrant(matColor)
        if movement_phase_start_zone and current_zone then
            if movement_phase_start_zone ~= current_zone then
                if is_threatened then
                    disableThreatened()
                    broadcastToAll(matColor .. '가 이동하여 위협을 받지 않습니다.', Color[matColor])
                end
            else
                if not is_threatened then
                    enableThreatened()
                    broadcastToAll(matColor .. '가 이동하지 않아 위협을 받습니다.', Color[matColor])
                else
                    Global.call('TriggerBehaviorCheck', {type = "Threat", color = matColor})
                    broadcastToAll(matColor .. '가 이동하지 않아 계속 위협을 받습니다.', Color[matColor])
                end
            end
        else
            if not is_threatened then 
                enableThreatened() 
            else
                Global.call('TriggerBehaviorCheck', {type = "Threat", color = matColor})
            end
        end
    elseif current_phase == 2 then
        local seqTags = getSequenceTagsSorted()
        local has_return = false
        for _, cTags in ipairs(seqTags) do
            if cTags.tags then
                for _, t in ipairs(cTags.tags) do
                    if t == "return_sequence" then
                        has_return = true
                        break
                    end
                end
            end
            if has_return then break end
        end

        if has_return then
            broadcastToAll("회수 효과(return_sequence)가 발동되었습니다. 회수할 시퀀스 카드를 클릭하거나 스킵하세요.", matColor)
            setupSequenceReturnUI(seqTags)
            return
        end

        proceedToActionPhaseEnd()
    elseif current_phase == 3 then
        local required_draws = 1
        if is_threatened then required_draws = 2 end
        
        local current_draws = drawn_attrition_count or 0
        if current_draws == 0 and has_drawn_attrition then
            current_draws = 1
        end

        if current_draws < required_draws then
            if Global.call("HasAttritionDeck") then
                if is_threatened and current_draws > 0 then
                    broadcastToAll("위협받고있습니다 마찰 카드를 한장 더 공개해 주세요", matColor)
                else
                    broadcastToAll("마찰 단계를 진행해 주세요.", matColor)
                end
            else
                broadcastToAll("마찰덱 재구성 후 마찰단계를 진행해 주세요.", matColor)
            end
            return
        end
        current_phase = 0
        disablePhaseDecals()
        broadcastToAll("End Turn", matColor)
        if not is_turn_ended then
            enableTurnEnd()
            startLuaCoroutine(self, "turnEndCoroutine")
        else
            disableTurnEnd()
        end
    elseif current_phase == 4 then
        current_phase = 0
        disablePhaseDecals()
        disableTurnEnd()
        Global.call('PassTurn')
    else
        -- 알 수 없는 상태일 경우 Movement Phase로 초기화
        current_phase = 1
        disableTurnEnd()
        setPhaseDecal(1)
        broadcastToAll("Movement Phase", matColor)
    end
end

function setPhaseDecal(phase_num)
    disablePhaseDecals()
    
    local url = ""
    if phase_num == 1 then url = MOVEMENT_PHASE_MARKER_URL
    elseif phase_num == 2 then url = ACTION_PHASE_MARKER_URL
    elseif phase_num == 3 then url = ATTRITION_PHASE_MARKER_URL
    end
    
    local decals = self.getDecals() or {}
    table.insert(decals, {
        name     = 'phase_marker',
        url      = url,
        position = {-0.972, 0.21, -1.353},
        rotation = {90, 180, 0},
        scale    = {0.132, 0.142, 0.132},
    })
    self.setDecals(decals)
    if Global.call('GetCurrentTurnColor') == getMatColorFromTag() then updateGlobalPhaseHUD(phase_num, true) end
end

function disablePhaseDecals()
    local decals = self.getDecals() or {}
    local newDecals = {}
    local changed = false
    for _, decal in ipairs(decals) do
        if decal.name ~= 'phase_marker' then
            table.insert(newDecals, decal)
        else
            changed = true
        end
    end
    if changed then
        self.setDecals(newDecals)
    end
    if Global.call('GetCurrentTurnColor') == getMatColorFromTag() then updateGlobalPhaseHUD(0, false) end
end

function turnEndCoroutine()
    discardSequenceCoroutine()
    
    -- Xitheros 방해(Disrupt) 토큰 자동 삭제
    for _, obj in ipairs(getObjects()) do
        if isOnThisBoard(obj) and obj.type ~= "Bag" then
            if obj.hasTag("Disrupt") or obj.getName() == "Disrupt Token" or obj.getName() == "Disrupt" or obj.hasTag("bag_disrupt") then
                destroyObject(obj)
            end
        end
    end

    
    Wait.time(function()
        Global.call('RotateMonsterToAggro')
        Global.call('PassTurn')
    end, 1.0)
    
    return 1
end

function enableTurnEnd()
    is_turn_ended = true
    if Global.call('GetCurrentTurnColor') == getMatColorFromTag() then updateGlobalPhaseHUD(0, false) end

    local matColor = getMatColorFromTag()
    if matColor then
        Global.call('SetGlobalTurnEndButton', {color = matColor, enabled = true})
    end
end

function disableTurnEnd()
    is_turn_ended = false
    if Global.call('GetCurrentTurnColor') == getMatColorFromTag() then updateGlobalPhaseHUD(0, false) end

    local matColor = getMatColorFromTag()
    if matColor then
        Global.call('SetGlobalTurnEndButton', {color = matColor, enabled = false})
    end
end

--------------------
-- Equipment total
_equipBroadcastTimer = nil
_equipBroadcastOldValue = nil

function refreshEquipmentDisplay()
    self.UI.setAttribute('equipment-total', 'text',
        equipment_exists and tostring(displayed_equipment_total) or '')
    self.UI.setAttribute('equipment-damage', 'text',
        equipment_exists and tostring(damage_counter) or '')
    
    setEquipmentBgDecal(equipment_exists and equipment_all_healthy)
end

function adjustEquipmentTotal(delta)
    if not equipment_exists then return end
    
    local oldEquip = displayed_equipment_total
    displayed_equipment_total = math.max(0, math.min(99, displayed_equipment_total + delta))
    damage_counter = math.min(damage_counter, displayed_equipment_total)

    if oldEquip ~= displayed_equipment_total then
        if _equipBroadcastOldValue == nil then
            _equipBroadcastOldValue = oldEquip
        end
        if _equipBroadcastTimer then Wait.stop(_equipBroadcastTimer) end
        _equipBroadcastTimer = Wait.time(function()
            local diff = displayed_equipment_total - _equipBroadcastOldValue
            if diff ~= 0 then
                local symbol = diff > 0 and '+' or ''
                local matColor = getMatColorFromTag()
                safeLog(string.format('%s: 체력 %d → %d (%s%d)', 
                    matColor or "Unknown", _equipBroadcastOldValue, displayed_equipment_total, symbol, diff), 
                    matColor)
            end
            _equipBroadcastOldValue = nil
            _equipBroadcastTimer = nil
        end, 0.5)
    end
    refreshEquipmentDisplay()
end

_damageBroadcastTimer = nil
_damageBroadcastOldValue = nil

function adjustDamageCounter(delta)
    if not equipment_exists then return end

    local oldDamage = damage_counter
    damage_counter = math.max(0, math.min(displayed_equipment_total, damage_counter + delta))

    if oldDamage ~= damage_counter then
        local matColor = getMatColorFromTag()

        if damage_counter == displayed_equipment_total
           and displayed_equipment_total > 0
           and oldDamage < damage_counter then
            checkKOState(matColor)
        end

        if _damageBroadcastOldValue == nil then
            _damageBroadcastOldValue = oldDamage
        end
        if _damageBroadcastTimer then Wait.stop(_damageBroadcastTimer) end
        _damageBroadcastTimer = Wait.time(function()
            local diff = damage_counter - _damageBroadcastOldValue
            if diff ~= 0 then
                local symbol = diff > 0 and '+' or ''
                safeLog(string.format('%s: 피해 %d → %d (%s%d)', 
                    matColor or "Unknown", _damageBroadcastOldValue, damage_counter, symbol, diff), 
                    matColor)
            end
            _damageBroadcastOldValue = nil
            _damageBroadcastTimer = nil
            
            Global.call('EvaluateXitherosAggro')
        end, 0.5)
    end

    refreshEquipmentDisplay()
end

function isEquipment(obj)
    for _, tag in ipairs(EQUIPMENT_TAGS) do
        if obj.hasTag(tag) then return true end
    end
    return false
end

function hasDepletedTokenOnTop(equipmentObj)
    local pos = equipmentObj.getPosition()
    local hitList = Physics.cast({
        origin       = {pos.x, pos.y + 0.3, pos.z},
        direction    = {0, 1, 0},
        type         = 3,
        size         = {1.5, 1, 2.2},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= equipmentObj and isDepletedToken(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld then
                return true
            end
        end
    end
    return false
end

function isDepletedToken(obj)
    return obj.getName() == 'Depleted'
        or obj.hasTag('token_depleted')
        or obj.hasTag('Depleted')
end

function isHelmetDepleted()
    local helmet = nil
    for _, o in ipairs(getAllObjects()) do
        if isOnThisBoard(o) and o.hasTag('actor_helm') then
            helmet = o
            break
        end
    end
    if helmet then
        return hasDepletedTokenOnTop(helmet)
    end
    return false
end

function isOnThisBoard(obj)
    return isOnThisBoardOBB(obj)
end

function isSequenceTriggerCard(obj)
    if obj.type == 'Card' or obj.type == 'Deck' then return true end
    return obj.hasTag('sequence_plus_1')
        or obj.hasTag('focus_sequence_plus_1')
        or obj.hasTag('actor_mastery')
end

--------------------
-- Equipment / Sequence events
function onObjectDrop(player_color, obj)
    -- Movement Phase 중 턴 플레이어가 카드를 시퀀스에 놓는 것 방지
    if obj.type == 'Card' and current_phase == 1 then
        local matColor = getMatColorFromTag()
        if matColor and Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') == matColor then
            local localPos = self.positionToLocal(obj.getPosition())
            local targetZ = SEQUENCE_LOCAL_POSITIONS[1].z
            -- 시퀀스 영역: z좌표가 targetZ 근처이고, x좌표가 슬롯 범위 내일 때
            if math.abs(localPos.z - targetZ) < 0.4 and math.abs(localPos.x) < 2.0 then
                broadcastToAll("Movement Phase 입니다. 이동여부를 결정해주세요.", Color[matColor] or matColor)
                obj.deal(1, player_color)
                return
            end
        end
    end
    local name = obj.getName()
    if name == "KO'D" or name == "KO'D Token" or obj.hasTag("KO'D") then
        if isOnThisBoard(obj) then
            -- 토큰 바로 아래에 actor_board 태그를 가진 보드가 있는지 확인
            local pos = obj.getPosition()
            local hitList = Physics.cast({
                origin       = pos,
                direction    = {0, -1, 0},
                type         = 3, -- Box
                size         = {2, 2, 2},
                max_distance = 4,
            })
            
            local isOnActorBoard = false
            for _, hit in ipairs(hitList) do
                if hit.hit_object.hasTag("actor_board") then
                    isOnActorBoard = true
                    break
                end
            end
            
            if isOnActorBoard then
                if not isHelmetDepleted() then
                    broadcastToAll(getMatColorFromTag() .. " 플레이어가 KO 되었습니다!", "Red")
                    startLuaCoroutine(self, "koCoroutine")
                end
            end
        end
    end

    if isEquipment(obj) or isDepletedToken(obj) then
        if obj.resting then
            Wait.time(updateEquipmentTotal, 0.5)
        else
            Wait.condition(
                function() updateEquipmentTotal() end,
                function() return obj == nil or obj.resting end,
                3
            )
        end
    end

    if isSequenceTriggerCard(obj) and isOnThisBoard(obj) then
        Wait.condition(
            function() updateSequenceSlotDecals() end,
            function() return obj == nil or obj.resting end,
            3
        )
        Wait.time(updateSequenceSlotDecals, 3.5)
    end

    if obj.type == 'Card' or obj.type == 'Deck' then
        Wait.condition(
            function() checkDeckReconstructButton() end,
            function() return obj == nil or obj.resting end,
            3
        )
        Wait.time(checkDeckReconstructButton, 3.5)
    end

    -- 본인 피규어가 사분면을 이동했다면 위협 토큰 업데이트
    local matColor = getMatColorFromTag()
    if matColor and obj.hasTag('owner_' .. matColor) and obj.hasTag('actor_mini') then
        local prevZone = last_pickup_quadrant
        last_pickup_quadrant = nil
        Wait.condition(
            function()
                local newZone = getPlayerQuadrant(matColor)
                if prevZone and newZone and prevZone ~= newZone and is_threatened then
                    -- Movement Phase(1) 중에는 페이즈 종료 시점에서 판단하므로 즉시 해제하지 않음
                    if current_phase ~= 1 then
                        disableThreatened()
                        broadcastToAll(matColor .. '가 이동하여 위협을 받지 않습니다.', Color[matColor])
                    end
                end
            end,
            function() return obj == nil or obj.resting end,
            3
        )
    end

    -- ==========================================================
    -- Behavior Auto-Trigger (Card Play)
    -- ==========================================================
    if obj.type == "Card" then
        Wait.condition(
            function()
                -- 플레이어가 시퀀스에 놓는 카드는 앞면이어야만 인식합니다. (뒷면은 발동 안함)
                if not obj.is_face_down and checkCardInSequence(obj) then
                    local tags = obj.getTags()
                    if tags and #tags > 0 then
                        local mColor = getMatColorFromTag()
                        if mColor then
                            local seqTags = getSequenceTagsSorted()
                            local is_stealthed = false
                            for _, st in ipairs(seqTags) do
                                if st.obj == obj then
                                    is_stealthed = st.is_stealthed
                                    break
                                end
                            end

                            if is_stealthed then
                                broadcastToAll("스텔스 효과로 인해 행동 발동이 무시되었습니다.", "Grey")
                            else
                                -- TTS 번역 충돌 방지를 위해 aa_ 접두사가 붙은 태그들을 사용합니다.
                                local valid_tags = {aa_attack=true, aa_maneuver=true, aa_evade=true, aa_defend=true, Aggro=true}
                                local _sent = {}
                                local tag_found = false
                                for _, t in ipairs(tags) do
                                    if valid_tags[t] and not _sent[t] then
                                        _sent[t] = true
                                        tag_found = true
                                        Global.call("TriggerBehaviorCheck", { type = "CardPlay", data = { tag = t }, color = mColor })
                                    end
                                end
                                if not tag_found then
                                    
                                end
                            end
                        end
                    end
                end
            end,
            function() return obj == nil or obj.resting end,
            3
        )
    end
end

function onObjectDestroy(obj)
    if isEquipment(obj) or isDepletedToken(obj) then
        Wait.time(updateEquipmentTotal, 0.1)
    end
    if isSequenceTriggerCard(obj) then
        Wait.time(updateSequenceSlotDecals, 0.1)
    end
    if obj.type == 'Card' or obj.type == 'Deck' then
        Wait.time(checkDeckReconstructButton, 0.1)
    end
end

function onObjectEnterContainer(container, obj)
    if isEquipment(obj) or isDepletedToken(obj) then
        Wait.time(updateEquipmentTotal, 0.1)
    end
    if isSequenceTriggerCard(obj) then
        Wait.time(updateSequenceSlotDecals, 0.1)
    end
    if container.type == 'Deck' or obj.type == 'Card' or obj.type == 'Deck' then
        Wait.time(checkDeckReconstructButton, 0.1)
    end
end

function onObjectLeaveContainer(container, obj)
    if container.type == 'Deck' or obj.type == 'Card' or obj.type == 'Deck' then
        Wait.time(checkDeckReconstructButton, 0.1)
    end
end

function onObjectSpawn(obj)
    if isSequenceTriggerCard(obj) and isOnThisBoard(obj) then
        Wait.condition(
            function() updateSequenceSlotDecals() end,
            function() return obj == nil or obj.resting end,
            3
        )
    end
end

function onObjectRotate(obj, spin, flip, player_color, old_spin, old_flip)
    -- 장비 뒤집힘
    if isEquipment(obj) and isOnThisBoard(obj) then
        local wasFaceDown = (old_flip > 90 and old_flip < 270)
        local isFaceDown  = (flip > 90 and flip < 270)
        if wasFaceDown ~= isFaceDown then
            Wait.time(updateEquipmentTotal, 0.3)
        end
    end

    -- actor_mastery 뒤집힘 → 슬롯 재계산
    if obj.hasTag('actor_mastery') and isOnThisBoard(obj) then
        local wasFaceDown = (old_flip > 90 and old_flip < 270)
        local isFaceDown  = (flip > 90 and flip < 270)
        if wasFaceDown ~= isFaceDown then
            Wait.time(updateSequenceSlotDecals, 0.5)
            Wait.time(updateSequenceSlotDecals, 1.5)
        end
    end

    -- 시퀀스 카드 뒤집힘 → 슬롯 재계산
    if (obj.hasTag('sequence_plus_1') or obj.hasTag('focus_sequence_plus_1'))
       and isOnThisBoard(obj) then
        local wasFaceDown = (old_flip > 90 and old_flip < 270)
        local isFaceDown  = (flip > 90 and flip < 270)
        if wasFaceDown ~= isFaceDown then
            Wait.time(updateSequenceSlotDecals, 0.5)
            Wait.time(updateSequenceSlotDecals, 1.5)
        end
    end
end

function countFaceDownMasteryWithFocus()
    local count = 0
    for _, obj in ipairs(getObjectsWithTag('actor_mastery')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and obj.is_face_down
           and obj.hasTag('focus_sequence_plus_1')
           and isOnThisBoard(obj) then
            count = count + 1
        end
    end
    return count
end

-- Hand Drawing
function startGameDraw()
    local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
    local deck = findDeckAtWorldPos(deckWorldPos)
    if deck and deck.type == 'Deck' then
        deck.shuffle()
    end
    -- 셔플 후 약간 대기한 다음 드로우 실행
    Wait.time(drawToHandLimit, 0.5)
end

function checkStaminaEndActionPhase()
    local matColor = getMatColorFromTag()
    if not matColor then return end

    if not isThisBoardActive() then return end

    local player = Player[matColor]
    if not player then return end

    -- 손패 잔여 카드로 스태미나 자동 설정 (장비 효과 반영)
    local totalHandCount = #(player.getHandObjects(1))
    local newStaminaLevel = calculateStaminaFromHand(totalHandCount)

    if newStaminaLevel > stamina_level then
        local oldLevel = stamina_level
        stamina_level = newStaminaLevel
        updateStaminaDecal()

        local _, displayLevel = getActiveBoneStaminaInfo()
        local source = ''
        if displayLevel then
            source = ' [척추뼈 갑옷 Lv' .. displayLevel .. ']'
        end

        safePrintToColor(
            matColor .. ': 손패 ' .. totalHandCount .. '장 → 스태미나 ' ..
            oldLevel .. ' → ' .. newStaminaLevel .. ' 획득' .. source,
            matColor, Color[matColor]
        )
    end
end

function drawToHandLimit()
    startLuaCoroutine(self, 'drawToHandLimitCoroutine')
end

function drawToHandLimitCoroutine()
    self.setVar("is_drawing_coroutine_running", true)
    local matColor = getMatColorFromTag()
    if not matColor then 
        self.setVar("is_drawing_coroutine_running", false)
        return 1 
    end

    if not isThisBoardActive() then
        self.setVar("is_drawing_coroutine_running", false)
        return 1
    end

    local player = Player[matColor]
    if not player then return 1 end

    local effectiveLimit, breakdown = calculateEffectiveHandSizeLimit()
    local startCount, startExcluded = countEffectiveHandSize(matColor)

    -- 손패 초과 체크
    if startCount > effectiveLimit then
        local msg = matColor .. ': 손패가 ' .. startCount .. '/' .. effectiveLimit .. '입니다.\n' ..
                    '손패를 ' .. effectiveLimit .. '장이 되도록 버려주세요.\n' ..
                    '  계산: ' .. breakdown
        if startExcluded > 0 then
            msg = msg .. '\n  끈기: ' .. startExcluded .. '장 (손패제한에서 제외됨)'
        end
        printToAll(msg, Color[matColor])
        disableTurnEnd()
        after_play_hand_bonus = 0
        self.setVar("is_drawing_coroutine_running", false)
        return 1
    end

    local initialNeeded = effectiveLimit - startCount

    if initialNeeded <= 0 then
        local msg = matColor .. ': 손패 ' .. startCount .. '/' .. effectiveLimit .. ' (드로우 불필요)\n  계산: ' .. breakdown
        if startExcluded > 0 then
            msg = msg .. '\n  끈기: ' .. startExcluded .. '장 (손패제한에서 제외됨)'
        end
        printToAll(msg, Color[matColor])
        after_play_hand_bonus = 0
        self.setVar("is_drawing_coroutine_running", false)
        return 1
    end

    local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
    local maxIterations = 30

    -- 드로우 루프 (필요 시 중간 셔플 = "탈진!!")
    for iteration = 1, maxIterations do
        local currentCount, _ = countEffectiveHandSize(matColor)
        local needed = effectiveLimit - currentCount

        if needed <= 0 then break end

        local deck = findDeckAtWorldPos(deckWorldPos)

        if not deck then
            local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
            local discard = findDeckAtWorldPos(discardWorldPos)

            if not discard then
                printToAll(
                    matColor .. ': 덱과 버림더미가 모두 비었습니다!',
                    Color.Red
                )
                self.setVar("is_drawing_coroutine_running", false)
                return 1
            end

            performShuffleAndForge(matColor, discard, deckWorldPos, '탈진!!')

            deck = findDeckAtWorldPos(deckWorldPos)
            if not deck then
                broadcastToAll('덱 회복 실패', Color.Red)
                self.setVar("is_drawing_coroutine_running", false)
                return 1
            end
        end

        local available = (deck.tag == 'Deck') and deck.getQuantity() or 1
        local toDraw = math.min(needed, available)
        
        if Player[matColor].seated then
            deck.deal(toDraw, matColor, 1)
            for f = 1, 30 do coroutine.yield(0) end
        else
            -- 플레이어가 자리에 없는 경우 (솔로 플레이), 보드의 PLAYER HAND 영역에 직접 펼쳐놓음
            local startPos = {x=0.635, y=0.25, z=-0.45}
            for i = 1, toDraw do
                local currentTotal = currentCount + (i - 1)
                local newX = startPos.x - (currentTotal * 0.28)
                local localTarget = {x=newX, y=startPos.y, z=startPos.z}
                local worldTarget = self.positionToWorld(localTarget)
                
                if deck.tag == 'Deck' then
                    deck.takeObject({
                        position = worldTarget,
                        rotation = self.getRotation(),
                        flip     = true,
                        smooth   = true
                    })
                else
                    deck.setPositionSmooth(worldTarget, false, false)
                    deck.setRotationSmooth(self.getRotation(), false, false)
                    if deck.is_face_down then deck.flip() end
                end
                for f = 1, 15 do coroutine.yield(0) end
            end
            break -- 보드 위에 놓으면 손패(hand) 매수로 즉각 인식되지 않으므로 무한루프 방지를 위해 종료
        end
    end

    -- 드로우 후 덱 비었으면 미리 셔플 (= "셔플 효과")
    local deckCheck = findDeckAtWorldPos(deckWorldPos)
    if not deckCheck then
        local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
        local discard = findDeckAtWorldPos(discardWorldPos)

        if discard then
            performShuffleAndForge(matColor, discard, deckWorldPos, '탈진!!')
        end
    end

    -- 최종 broadcast
    local newCount, newExcluded = countEffectiveHandSize(matColor)
    local msg = matColor .. ': 드로우 완료 (' .. startCount .. ' → ' .. newCount .. '/' .. effectiveLimit .. ')\n  계산: ' .. breakdown
    if newExcluded > 0 then
        msg = msg .. '\n  끈기: ' .. newExcluded .. '장 (손패크기에서 제외됨)'
    end
    printToAll(msg, Color[matColor])

    -- Strain 토큰 소비
    local strainCount = consumeStrainTokens()
    if strainCount > 0 then
        safeBroadcastToColor(
            matColor .. ': Strain ' .. strainCount .. '개 소멸 (손패 -' .. strainCount .. ' 적용 후 삭제)',
            matColor, Color[matColor]
        )
    end

    checkDeckReconstructButton()
    after_play_hand_bonus = 0
    self.setVar("is_drawing_coroutine_running", false)
    return 1
end

function findDeckAtWorldPos(worldPos)
    local hitList = Physics.cast({
        origin       = {worldPos.x, worldPos.y + 2.0, worldPos.z},
        direction    = {0, -1, 0},
        type         = 3,
        size         = {0.8, 0.8, 0.8},
        max_distance = 4,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and (obj.tag == 'Deck' or obj.tag == 'Card') then
            return obj
        end
    end
    return nil
end

-- 카드 효과로 기본 손패 한도 변경 (외부 스크립트에서 호출 가능)
function setHandSizeLimit(newLimit)
    if type(newLimit) ~= 'number' then return end
    hand_size_limit = math.max(0, math.floor(newLimit))
    local matColor = getMatColorFromTag()
    local colorVal = matColor and Color[matColor] or Color.White
    local prefix = matColor and (matColor .. ': ') or ''
    printToAll(prefix .. '기본 손패 한도가 ' .. hand_size_limit .. '장으로 설정되었습니다.', colorVal)
end

function modifyHandSizeLimit(delta)
    if type(delta) ~= 'number' then return end
    hand_size_limit = math.max(0, hand_size_limit + math.floor(delta))
    local matColor = getMatColorFromTag()
    local colorVal = matColor and Color[matColor] or Color.White
    local prefix = matColor and (matColor .. ': ') or ''
    printToAll(prefix .. '기본 손패 한도가 ' .. hand_size_limit .. '장으로 변경되었습니다.', colorVal)
end

-- 손패 한도 계산 (base + hand_plus_1 + emergency 조건)
function calculateEffectiveHandSizeLimit()
    local breakdown = {}
    local limit = hand_size_limit
    table.insert(breakdown, hand_size_limit .. '(기본)')

    -- hand_plus_1 카드
    local handPlusCount = 0
    local masteryHandPlusCount = 0
    for _, obj in ipairs(getObjectsWithTag('hand_plus_1')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld and isOnThisBoard(obj) then
            if obj.hasTag('actor_mastery') then
                if obj.is_face_down then masteryHandPlusCount = masteryHandPlusCount + 1 end
            else
                if not obj.is_face_down then handPlusCount = handPlusCount + 1 end
            end
        end
    end
    if handPlusCount > 0 then
        limit = limit + handPlusCount
        table.insert(breakdown, '+' .. handPlusCount .. '(손패+1 장비)')
    end
    if masteryHandPlusCount > 0 then
        limit = limit + masteryHandPlusCount
        table.insert(breakdown, '+' .. masteryHandPlusCount .. '(숙련도 뒤집음)')
    end

    -- emergency_hand_plus_1
    local threshold = math.floor(displayed_equipment_total / 2)
    if damage_counter >= threshold then
        local emergencyCount = 0
        for _, obj in ipairs(getObjectsWithTag('emergency_hand_plus_1')) do
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld and not obj.is_face_down and isOnThisBoard(obj) then
                emergencyCount = emergencyCount + 1
            end
        end
        if emergencyCount > 0 then
            limit = limit + emergencyCount
            table.insert(breakdown, '+' .. emergencyCount .. '(위급)')
        end
    end

    -- pierce2_hand_plus_1
    if hasPierce2HandPlus1Equipment() then
        local pierceValue = getPierceValueOnThisBoard()
        if pierceValue and pierceValue >= 2 then
            limit = limit + 1
            table.insert(breakdown, '+1(관통 ' .. pierceValue .. ')')
        end
    end

    -- after_play_hand_plus_1 보너스 (현재 시퀀스에 놓인 카드 + 턴 종료 시 저장된 보너스)
    local afterPlayHandBonus = countAfterPlayHandPlus1Cards() + after_play_hand_bonus
    if afterPlayHandBonus > 0 then
        limit = limit + afterPlayHandBonus
        table.insert(breakdown, '+' .. afterPlayHandBonus .. '(시퀀스 플레이)')
    end

    -- Strain 토큰
    local strainCount = countStrainTokensOnBoard()
    if strainCount > 0 then
        limit = limit - strainCount
        table.insert(breakdown, '-' .. strainCount .. '(피로)')
    end

    local clampedLimit = math.max(0, limit)
    if clampedLimit ~= limit then
        table.insert(breakdown, '(0 클램프)')
    end

    return clampedLimit, table.concat(breakdown, ' ')
end

function countEffectiveHandSize(matColor)
    local handObjects = Player[matColor].getHandObjects(1)
    local count = 0
    local excludedCount = 0
    for _, obj in ipairs(handObjects) do
        if obj.hasTag('hand_not_count') then
            excludedCount = excludedCount + 1
        else
            count = count + 1
        end
    end
    return count, excludedCount
end

function getSoloHandCards()
    local cards = {}
    for _, obj in ipairs(getAllObjects()) do
        if (obj.type == 'Card' or obj.type == 'Deck') and isOnThisBoard(obj) and not obj.locked then
            local localPos = self.positionToLocal(obj.getPosition())
            if localPos.z > -0.7 and localPos.z < -0.2 and localPos.x > -1.5 and localPos.x < 1.0 then
                table.insert(cards, obj)
            end
        end
    end
    return cards
end

-- 이 보드에 pierce2_hand_plus_1 태그 장비가 있는지 (face up, Depleted 없음)
function hasPierce2HandPlus1Equipment()
    for _, obj in ipairs(getObjectsWithTag('pierce2_hand_plus_1')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and isOnThisBoard(obj)
           and not obj.is_face_down
           and not hasDepletedTokenOnTop(obj) then
            return true
        end
    end
    return false
end

-- 이 보드 위의 Pierce Token description 값 (없거나 숫자 아니면 nil)
function getPierceValueOnThisBoard()
    local matColor = getMatColorFromTag()
    if not matColor then return nil end

    local ownerTag = 'owner_' .. matColor

    for _, obj in ipairs(getAllObjects()) do
        if obj.getName() == 'Pierce Token' and obj.hasTag(ownerTag) then
            return tonumber(obj.getDescription())
        end
    end
    return nil
end

function countAfterPlayHandPlus1Cards()
    local count = 0
    local centerZ = SEQUENCE_LOCAL_POSITIONS[1].z
    local centerY = SEQUENCE_LOCAL_POSITIONS[1].y
    local centerWorld = self.positionToWorld({x=0, y=centerY, z=centerZ})

    local hitList = Physics.cast({
        origin       = centerWorld,
        direction    = {0, 1, 0},
        type         = 3,
        size         = {12, 1.5, 1.5},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if obj ~= self and not isHeld and not obj.is_face_down then
            if obj.hasTag('after_play_hand_plus_1') then
                count = count + 1
            end
        end
    end
    return count
end

function countStrainTokensOnBoard()
    local count = 0
    for _, obj in ipairs(getAllObjects()) do
        if obj ~= self and isStrainToken(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld and isOnThisBoardOBB(obj) then
                count = count + 1
            end
        end
    end
    return count
end

function isStrainToken(obj)
    return obj.getName() == 'Strain'
        or obj.hasTag('token_strain')
        or obj.hasTag('Strain')
end

-- 보드의 실제 크기와 회전에 맞춰 정확하게 판정
function isOnThisBoardOBB(obj)
    local bounds = self.getBoundsNormalized()
    local boardPos = self.getPosition()
    local boardRight = self.getTransformRight()
    local boardForward = self.getTransformForward()

    local objPos = obj.getPosition()
    local dx = objPos.x - boardPos.x
    local dz = objPos.z - boardPos.z

    local rightDist = math.abs(dx * boardRight.x + dz * boardRight.z)
    local forwardDist = math.abs(dx * boardForward.x + dz * boardForward.z)

    return rightDist < bounds.size.x / 2 and forwardDist < bounds.size.z / 2
end

-- 보드 위의 actor_weapon 장비에서 forge_level 보너스 합계
-- 레벨은 오브젝트 이름 어딘가의 "Level N"에서 추출 (N = 1/2/3)
function getWeaponForgeBonus()
    local totalBonus = 0

    local hitList = Physics.cast({
        origin       = self.getPosition() + Vector(0, 0.5, 0),
        direction    = {0, 1, 0},
        type         = 3,
        size         = {6, 2, 10},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and obj.hasTag('actor_weapon') then
            local name = obj.getName() or ''
            local lvl = tonumber(name:match('Level%s+([123])'))
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            local faceDown = obj.is_face_down
            local depleted = hasDepletedTokenOnTop(obj)

            if not isHeld and not faceDown and not depleted and lvl then
                totalBonus = totalBonus + lvl
            end
        end
    end

    return totalBonus
end

function performShuffleAndForge(matColor, discard, deckWorldPos, shuffleMsg, forgeLabel)
    shuffleMsg = shuffleMsg or '버림더미 → 덱 (재구성 중...)'
    forgeLabel = forgeLabel or '재구성 효과'

    printToAll(matColor .. ': ' .. shuffleMsg, Color[matColor])

    discard.setPositionSmooth(deckWorldPos, false, false)
    coroutine.yield(0) -- 상태 업데이트를 위해 1프레임 대기
    local timeout = os.clock() + 2.0
    while discard.isSmoothMoving() and os.clock() < timeout do
        coroutine.yield(0)
    end

    discard.flip()
    coroutine.yield(0)
    timeout = os.clock() + 1.0
    while discard.isSmoothMoving() and os.clock() < timeout do
        coroutine.yield(0)
    end

    if discard.tag == 'Deck' then
        discard.shuffle()
        for f = 1, 15 do coroutine.yield(0) end
    end

    local forgeBonus = getWeaponForgeBonus()
    local oldDamage = damage_counter
    local noExhaustion = hasFaceDownNoExhaustionMastery()
    local rhythm3Exhaustion = isGlobalRhythm3Active()

    -- 탈진 데미지 (forge_level, no_exhaustion일 때 차단)
    local exhaustionDamage = 0
    if not noExhaustion and not rhythm3Exhaustion and forgeBonus > 0 then
        exhaustionDamage = forgeBonus
    end

    -- Burning 화상 데미지 (별개, no_exhaustion 영향 X)
    local burningCount = consumeBurningTokens()
    local burningDamage = 0
    if burningCount > 0 and forgeBonus > 0 then
        burningDamage = forgeBonus
    end

    -- 총 데미지 적용
    local totalDamage = exhaustionDamage + burningDamage
    if totalDamage > 0 then
        damage_counter = math.min(displayed_equipment_total, damage_counter + totalDamage)
        refreshEquipmentDisplay()

        -- KO 체크: 데미지가 장비값과 같아지고, 이번에 그 값에 도달한 경우
        if damage_counter == displayed_equipment_total
           and displayed_equipment_total > 0
           and oldDamage < damage_counter then
            checkKOState(matColor)
        end
        
        Global.call('EvaluateXitherosAggro')
    end

    -- 로그 메시지 (효과별로 분리해서 표시)
    local logParts = {}
    if rhythm3Exhaustion then
        table.insert(logParts, '탈진의 송가 리듬 3단계! 탈진피해를 무시합니다.')
    elseif noExhaustion then
        table.insert(logParts, '탈진 피해 무시')
    elseif exhaustionDamage > 0 then
        table.insert(logParts, '탈진!! +' .. exhaustionDamage)
    end

    if burningCount > 0 then
        if burningDamage > 0 then
            table.insert(logParts, '화상!! +' .. burningDamage)
        else
            table.insert(logParts, '화상 소멸(forge 무기 없음)')
        end
    end

    if #logParts > 0 then
        printToAll(
            matColor .. ': ' .. forgeLabel .. ' - 데미지 ' .. oldDamage .. ' → ' .. damage_counter ..
            ' [' .. table.concat(logParts, ', ') .. ']',
            Color[matColor]
        )
    end
end

-- 글로벌 버튼 클릭 → 보드 이미지만 토글 (실제 동작 안 함)
function setTurnEndVisualOnly(params)
    local enabled = params.enabled
    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if decal.name ~= 'turn_end_marker' then
            table.insert(newDecals, decal)
        end
    end

    if enabled then
        table.insert(newDecals, {
            name     = 'turn_end_marker',
            url      = TURN_END_MARKER_URL,
            position = {-0.972, 0.21, -1.353},
            rotation = {90, 180, 0},
            scale    = {0.132, 0.142, 0.132},
        })
    end

    self.setDecals(newDecals)
    is_turn_ended = enabled
end

function hasFaceDownNoExhaustionMastery()
    for _, obj in ipairs(getObjectsWithTag('actor_mastery')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and obj.is_face_down
           and obj.hasTag('focus_no_exhaustion')
           and isOnThisBoard(obj) then
            return true
        end
    end
    return false
end

function isStealthFocusMasteryActive()
    for _, obj in ipairs(getObjectsWithTag('actor_mastery')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and obj.is_face_down
           and obj.hasTag('aa_stealth_focus_am')
           and isOnThisBoard(obj) then
            return true
        end
    end
    return false
end

function isOnTargetBoardOBB(board, obj)
    local bounds = board.getBoundsNormalized()
    local boardPos = board.getPosition()
    local boardRight = board.getTransformRight()
    local boardForward = board.getTransformForward()

    local objPos = obj.getPosition()
    local dx = objPos.x - boardPos.x
    local dz = objPos.z - boardPos.z

    local rightDist = math.abs(dx * boardRight.x + dz * boardRight.z)
    local forwardDist = math.abs(dx * boardForward.x + dz * boardForward.z)

    return rightDist < bounds.size.x / 2 and forwardDist < bounds.size.z / 2
end

function isGlobalRhythm3Active()
    local boards = getObjectsWithTag('player_board')
    
    for _, mastery in ipairs(getObjectsWithTag('actor_mastery')) do
        local isHeld = mastery.held_by_color ~= nil and mastery.held_by_color ~= ''
        
        if not isHeld and mastery.is_face_down and mastery.hasTag('focus_rhythm_3') then
            -- 이 마스터리가 올려져 있는 정확한 보드(OBB 기반) 찾기
            local targetBoard = nil
            for _, board in ipairs(boards) do
                if isOnTargetBoardOBB(board, mastery) then
                    targetBoard = board
                    break
                end
            end
            
            if targetBoard then
                -- 해당 보드 위에 있는 리듬 토큰을 찾음
                for _, obj in ipairs(getAllObjects()) do
                    -- 스크립트 변수 확인 또는 이름 확인으로 강력하게 토큰 식별
                    local isRhythm = (obj.getVar('RHYTHM_SNAP_DISTANCE') ~= nil)
                    local name = obj.getName() or ''
                    if not isRhythm and name:lower():match('rhythm') then
                        isRhythm = true
                    end
                    
                    if isRhythm then
                        -- 토큰이 마스터리 카드와 완벽히 동일한 보드 위에 있는지 OBB로 확인
                        if isOnTargetBoardOBB(targetBoard, obj) then
                            -- 설명에 '3'이 포함되어 있는지 유연하게 확인 (공백, 줄바꿈 무시)
                            local desc = tostring(obj.getDescription() or '')
                            if desc:match('3') then
                                return true
                            end
                        end
                    end
                end
            end
        end
    end
    return false
end

function isThisBoardActive()
    local matColor = getMatColorFromTag()
    if not matColor then return false end

    local objs = getObjectsWithTag('owner_' .. matColor)
    if #objs == 0 then return false end

    local bp = self.getPosition()
    for _, obj in ipairs(objs) do
        local op = obj.getPosition()
        if math.abs(op.x - bp.x) < 9 then
            return true
        end
    end
    return false
end

-- broadcastToColor가 안전하게 작동하도록 (seated 체크 + 폴백)
function safeBroadcastToColor(message, matColor, msgColor)
    broadcastToAll(message, msgColor)
end

function isBurningToken(obj)
    return obj.getName() == 'Burning'
        or obj.hasTag('token_burning')
        or obj.hasTag('Burning')
end

-- Strain 토큰 소비 (보드 위, 들고 있지 않음) → 삭제하고 개수 반환
function consumeStrainTokens()
    local tokens = {}
    for _, obj in ipairs(getAllObjects()) do
        if obj ~= self and isStrainToken(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld and isOnThisBoardOBB(obj) then
                table.insert(tokens, obj)
            end
        end
    end

    local count = #tokens
    for _, token in ipairs(tokens) do
        token.destruct()
    end
    return count
end

-- Burning 토큰 소비 → 삭제하고 개수 반환
function consumeBurningTokens()
    local tokens = {}
    for _, obj in ipairs(getAllObjects()) do
        if obj ~= self and isBurningToken(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld and isOnThisBoardOBB(obj) then
                table.insert(tokens, obj)
            end
        end
    end

    local count = #tokens
    for _, token in ipairs(tokens) do
        token.destruct()
    end
    return count
end

function checkKOState(matColor)
    if hasDepletedOrFlippedEquipment() then
        broadcastToAll(
            matColor .. ': KO!! 전투 불능 상태가 되었습니다',
            Color.Red
        )
    else
        broadcastToAll(
            matColor .. ': KO!! 상태처리를 진행하세요',
            Color.Yellow
        )
    end
end

function hasDepletedOrFlippedEquipment()
    local hitList = Physics.cast({
        origin       = self.getPosition() + Vector(0, 0.5, 0),
        direction    = {0, 1, 0},
        type         = 3,
        size         = {6, 2, 10},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and isEquipment(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld then
                if obj.hasTag('actor_helm') or obj.hasTag('actor_armor') then
                    if obj.is_face_down or hasDepletedTokenOnTop(obj) then
                        return true
                    end
                end
            end
        end
    end
    return false
end

-- 채팅 로그에만 표시 (전체 출력)
function safeLog(message, matColor)
    if matColor then
        printToAll(message, Color[matColor] or Color.White)
    else
        printToAll(message, Color.White)
    end
end

function applyDamageBuffer()
    if damage_input_buffer == '' then return end

    local newDamage = tonumber(damage_input_buffer)
    damage_input_buffer = ''
    damage_input_timer_id = nil

    if not newDamage then return end
    if not equipment_exists then return end

    local oldDamage = damage_counter
    damage_counter = math.max(0, math.min(displayed_equipment_total, newDamage))

    if oldDamage ~= damage_counter then
        local matColor = getMatColorFromTag()
        local diff = damage_counter - oldDamage
        local symbol = diff > 0 and '+' or ''

        safePrintToColor(
            matColor .. ': 피해 ' .. oldDamage .. ' → ' .. damage_counter ..
            ' (' .. symbol .. diff .. ', 키 입력: ' .. newDamage .. ')',
            matColor, Color[matColor]
        )

        if damage_counter == displayed_equipment_total
           and displayed_equipment_total > 0
           and oldDamage < damage_counter then
            checkKOState(matColor)
        end
        
        Global.call('EvaluateXitherosAggro')
    end

    refreshEquipmentDisplay()
end

function isPointerNearDamageButton(player)
    if type(player) == 'string' then
        player = Player[player]
    end
    if not player then return false end

    local pointerWorld = player.getPointerPosition()
    if not pointerWorld then return false end

    local buttons = self.getButtons()
    local damageButton = nil
    for _, btn in ipairs(buttons) do
        if btn.click_function == 'handleDamageClick' then
            damageButton = btn
            break
        end
    end
    if not damageButton then return false end

    -- createButton 좌표는 X 반전 필요
    local localPos = {
        -damageButton.position.x,
        damageButton.position.y,
        damageButton.position.z
    }
    local buttonWorld = self.positionToWorld(localPos)

    local dx = pointerWorld.x - buttonWorld.x
    local dz = pointerWorld.z - buttonWorld.z
    local dist = math.sqrt(dx*dx + dz*dz)

    return dist < DAMAGE_HOVER_RADIUS
end

equipment_input_buffer = ''
equipment_input_timer_id = nil

function onNumberTyped(color, number)
    if not equipment_exists then return end

    local player = Player[color]
    if not player then return end

    if player.getHoverObject() ~= self then return end

    local target_btn = getClosestNumberButton(player)
    if not target_btn then return end

    local digit = (number == 10) and '0' or tostring(number)

    if target_btn == 'damage' then
        handleDamageDigit(digit)
    elseif target_btn == 'equipment' then
        handleEquipmentDigit(digit)
    end

    return true
end

function onScriptingButtonDown(index, color)
    local number = index
    if index == 10 then number = 0 end
    onNumberTyped(color, number)
end

function getClosestNumberButton(player)
    if type(player) == 'string' then
        player = Player[player]
    end
    if not player then return nil end

    local pointerWorld = player.getPointerPosition()
    if not pointerWorld then return nil end

    local buttons = self.getButtons()
    local damageBtn = nil
    local equipBtn = nil
    for _, btn in ipairs(buttons) do
        if btn.click_function == 'handleDamageClick' then
            damageBtn = btn
        elseif btn.click_function == 'handleEquipmentTotalClick' then
            equipBtn = btn
        end
    end

    local min_dist = DAMAGE_HOVER_RADIUS or 1.0
    local target_btn = nil

    if damageBtn then
        local d_pos = {-damageBtn.position.x, damageBtn.position.y, damageBtn.position.z}
        local d_world = self.positionToWorld(d_pos)
        local dx = pointerWorld.x - d_world.x
        local dz = pointerWorld.z - d_world.z
        local dist = math.sqrt(dx*dx + dz*dz)
        if dist < min_dist then
            min_dist = dist
            target_btn = 'damage'
        end
    end

    if equipBtn then
        local e_pos = {-equipBtn.position.x, equipBtn.position.y, equipBtn.position.z}
        local e_world = self.positionToWorld(e_pos)
        local dx = pointerWorld.x - e_world.x
        local dz = pointerWorld.z - e_world.z
        local dist = math.sqrt(dx*dx + dz*dz)
        if dist < min_dist then
            min_dist = dist
            target_btn = 'equipment'
        end
    end

    return target_btn
end

function handleEquipmentDigit(digit)
    if equipment_input_timer_id then
        Wait.stop(equipment_input_timer_id)
        equipment_input_timer_id = nil
    end

    equipment_input_buffer = equipment_input_buffer .. digit

    if #equipment_input_buffer >= 2 then
        applyEquipmentBuffer()
    else
        equipment_input_timer_id = Wait.time(applyEquipmentBuffer, 1)
    end
end

function applyEquipmentBuffer()
    if equipment_input_buffer == '' then return end

    local newEquip = tonumber(equipment_input_buffer)
    equipment_input_buffer = ''
    equipment_input_timer_id = nil

    if not newEquip then return end
    if not equipment_exists then return end

    local oldEquip = displayed_equipment_total
    displayed_equipment_total = math.max(0, math.min(99, newEquip))
    damage_counter = math.min(damage_counter, displayed_equipment_total)

    if oldEquip ~= displayed_equipment_total then
        local matColor = getMatColorFromTag()
        local diff = displayed_equipment_total - oldEquip
        local symbol = diff > 0 and '+' or ''

        safePrintToColor(
            matColor .. ': 장비 ' .. oldEquip .. ' → ' .. displayed_equipment_total ..
            ' (' .. symbol .. diff .. ', 키 입력: ' .. newEquip .. ')',
            matColor, Color[matColor]
        )
    end

    refreshEquipmentDisplay()
end

function handleDamageDigit(digit)
    if damage_input_timer_id then
        Wait.stop(damage_input_timer_id)
        damage_input_timer_id = nil
    end

    damage_input_buffer = damage_input_buffer .. digit

    if #damage_input_buffer >= 2 then
        applyDamageBuffer()
    else
        damage_input_timer_id = Wait.time(applyDamageBuffer, 1)
    end
end

function safePrintToColor(message, matColor, msgColor)
    printToAll(message, msgColor)
end

-- 활성화된 bone_stamina 장비 체크 (앞면, 고갈 안 됨, 들고 있지 않음)
function hasActiveBoneStaminaEquipment(tag)
    for _, obj in ipairs(getObjectsWithTag(tag)) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and not obj.is_face_down
           and isOnThisBoard(obj)
           and not hasDepletedTokenOnTop(obj) then
            return true
        end
    end
    return false
end

function calculateStaminaFromHand(handCount)
    local staminaType, _ = getActiveBoneStaminaInfo()

    if staminaType == 3 then
        -- 척추뼈 갑옷 Lv2/Lv3: 1→1, 2→2, 3+→3
        if handCount >= 3 then return 3
        elseif handCount == 2 then return 2
        elseif handCount == 1 then return 1
        else return 0 end
    elseif staminaType == 2 then
        -- 척추뼈 갑옷 Lv1: 2+→2
        if handCount >= 2 then return 2
        else return 0 end
    else
        -- 기본: 2+→1
        if handCount >= 2 then return 1
        else return 0 end
    end
end

-- 활성 척추뼈 갑옷 정보 반환
-- returns: staminaType (2 or 3), displayLevel (1~3), 없으면 nil, nil
function getActiveBoneStaminaInfo()
    -- bone_stamina_3 우선 체크 (더 강한 효과)
    for _, obj in ipairs(getObjectsWithTag('bone_stamina_3')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and not obj.is_face_down
           and isOnThisBoard(obj)
           and not hasDepletedTokenOnTop(obj) then
            local displayLevel = getForgeLevelFromName(obj) or 2
            return 3, displayLevel
        end
    end

    -- bone_stamina_2
    for _, obj in ipairs(getObjectsWithTag('bone_stamina_2')) do
        local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
        if not isHeld
           and not obj.is_face_down
           and isOnThisBoard(obj)
           and not hasDepletedTokenOnTop(obj) then
            return 2, 1
        end
    end

    return nil, nil
end

function addStaticBoardDecals()
    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if decal.name ~= 'damage_bg' then
            table.insert(newDecals, decal)
        end
    end

    -- 데미지 버튼 위치 데칼 (createButton 좌표 X 반전)
    table.insert(newDecals, {
        name     = 'damage_bg',
        url      = DAMAGE_BG_URL,
        position = {0.155, 0.21, -1.29},
        rotation = {90, 180, 0},
        scale    = {0.08, 0.1, 0.08},
    })

    self.setDecals(newDecals)
end

function updateEquipmentTotal()
    local total = 0
    local exists = false
    local allHealthy = true   -- 모든 장비가 앞면 + 비-고갈

    local hitList = Physics.cast({
        origin       = self.getPosition() + Vector(0, 0.5, 0),
        direction    = {0, 1, 0},
        type         = 3,
        size         = {6, 2, 10},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and isEquipment(obj) then
            local isHeld = obj.held_by_color ~= nil and obj.held_by_color ~= ''
            if not isHeld then
                exists = true
                local faceUp = not obj.is_face_down
                local notDepleted = not hasDepletedTokenOnTop(obj)

                if obj.hasTag('actor_helm') or obj.hasTag('actor_armor') then
                    if not faceUp or not notDepleted then
                        allHealthy = false
                    end
                end

                if faceUp and notDepleted then
                    local num = tonumber(obj.getGMNotes())
                    if num then total = total + num end
                end
            end
        end
    end

    displayed_equipment_total = math.max(0, math.min(99, total))
    equipment_exists = exists
    equipment_all_healthy = allHealthy
    damage_counter = math.min(damage_counter, displayed_equipment_total)
    refreshEquipmentDisplay()
    
    Wait.time(updateSequenceSlotDecals, 0.1)
end

function onObjectPickUp(player_color, obj)
    if isEquipment(obj) or isDepletedToken(obj) then
        Wait.time(updateEquipmentTotal, 0.1)
    end
    if isSequenceTriggerCard(obj) then
        Wait.time(updateSequenceSlotDecals, 0.1)
    end
    if obj.type == 'Card' or obj.type == 'Deck' then
        Wait.time(checkDeckReconstructButton, 0.1)
    end
    
    -- 시퀀스에서 카드를 들어올렸을 때 발동된 행동 트리거 초기화
    if obj.type == 'Card' then
        if checkCardInSequence(obj) then
            Global.call("ClearBehaviorTriggers")
        end
    end

    -- 본인 피규어가 들리면 현재 사분면을 기록
    local matColor = getMatColorFromTag()
    if matColor and obj.hasTag('owner_' .. matColor) and obj.hasTag('actor_mini') then
        last_pickup_quadrant = getPlayerQuadrant(matColor)
    end
end

function setEquipmentBgDecal(useHighlight)
    local isHalfDamage = equipment_exists and displayed_equipment_total > 0 and damage_counter >= (displayed_equipment_total / 2)
    local url
    
    if useHighlight then
        url = isHalfDamage and EQUIPMENT_HIGHLIGHT_HALF_URL or EQUIPMENT_HIGHLIGHT_URL
    else
        url = isHalfDamage and EQUIPMENT_BG_HALF_URL or EQUIPMENT_BG_URL
    end

    local decals = self.getDecals() or {}
    local newDecals = {}
    for _, decal in ipairs(decals) do
        if decal.name ~= 'equipment_bg' then
            table.insert(newDecals, decal)
        end
    end

    table.insert(newDecals, {
        name     = 'equipment_bg',
        url      = url,
        position = {0.01, 0.21, -1.29},
        rotation = {90, 180, 0},
        scale    = {0.075, 0.1, 0.05},
    })

    self.setDecals(newDecals)
end

-- 오브젝트 이름의 "Level N"에서 N(1/2/3) 추출. 없으면 nil.
function getForgeLevelFromName(obj)
    if not obj then return nil end
    local name = obj.getName() or ''
    return tonumber(name:match('Level%s+([123])'))
end

function showReconstructButton()
    if is_reconstruct_button_visible then return end
    self.editButton({
        index = reconstruct_deck_btn_index,
        label = '액션\n덱\n재구성',
        width = 800,
        height = 1150,
    })
    is_reconstruct_button_visible = true
end

function hideReconstructButton()
    if not is_reconstruct_button_visible then return end
    self.editButton({
        index = reconstruct_deck_btn_index,
        label = '',
        width = 0,
        height = 0,
    })
    is_reconstruct_button_visible = false
end

function checkDeckReconstructButton()
    if is_reconstructing then return end
    
    local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
    local deck = findDeckAtWorldPos(deckWorldPos)
    
    if deck then
        hideReconstructButton()
    else
        local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
        local discard = findDeckAtWorldPos(discardWorldPos)
        if discard then
            showReconstructButton()
        else
            hideReconstructButton()
        end
    end
end

function reconstructDeckCoroutine()
    local matColor = getMatColorFromTag()
    local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
    local discard = findDeckAtWorldPos(discardWorldPos)
    
    if discard then
        local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
        performShuffleAndForge(matColor, discard, deckWorldPos, '덱 재구성 (탈진!!)', '재구성 효과')
    end
    is_reconstructing = false
    checkDeckReconstructButton()
    return 1
end

--------------------------------------------------------------------------------
-- KO Automation
--------------------------------------------------------------------------------
function koCoroutine()
    local matColor = getMatColorFromTag()
    local discardWorldPos = self.positionToWorld(DISCARD_LOCAL_POS)
    local deckWorldPos = self.positionToWorld(DECK_LOCAL_POS)
    
    -- 승패 조건 확인
    Global.call('CheckDefeatCondition')
    
    -- 1. 턴 & 어그로 넘기기
    local hadAggro = aggro_is_enabled
    
    if Global.call('GetTurnSystemActive') and Global.call('GetCurrentTurnColor') == matColor then
        current_phase = 0
        disablePhaseDecals()
        broadcastToAll("End Turn", matColor)
        if not is_turn_ended then enableTurnEnd() end
        disableAggro()
        Global.call('PassTurn')
    else
        disableAggro()
    end
    
    if hadAggro then
        local nextPlayer = Global.call('GetNextAlivePlayer', matColor)
        if nextPlayer then
            Global.call('SetAggroTarget', nextPlayer)
            Wait.time(function() Global.call('RotateMonsterToAggro', nextPlayer) end, 0.5)
        end
    end
    
    -- 2. 손패 버리기 (앉은 플레이어 손패 + 보드 위 솔로 손패 모두 포함)
    local allHandCards = {}
    local handObjects = Player[matColor].getHandObjects(1)
    if handObjects then
        for _, card in ipairs(handObjects) do
            table.insert(allHandCards, card)
        end
    end
    local soloHandCards = getSoloHandCards()
    for _, card in ipairs(soloHandCards) do
        table.insert(allHandCards, card)
    end
    
    local boardRot = self.getRotation()
    for i, card in ipairs(allHandCards) do
        pcall(function()
            card.use_hands = false
            card.setPositionSmooth(
                {discardWorldPos.x, discardWorldPos.y + i * 0.2, discardWorldPos.z},
                false, false
            )
            card.setRotationSmooth({0, boardRot.y, 180}, false, false)
            Wait.time(function() if card ~= nil then card.use_hands = true end end, 1.0)
        end)
    end
    
    for f=1, 30 do coroutine.yield(0) end -- 0.5초 대기
    
    -- 3. 시퀀스 카드 파기
    discardSequenceCoroutine(true)
    after_play_hand_bonus = 0
    
    -- 손패 이동 완료 대기 (상태 기반)
    if #allHandCards > 0 then
        local maxWait = 180
        local waitCount = 0
        while waitCount < maxWait do
            local anyMoving = false
            for _, card in ipairs(allHandCards) do
                if card ~= nil and not card.isDestroyed() and card.isSmoothMoving() then
                    anyMoving = true
                    break
                end
            end
            if not anyMoving then break end
            coroutine.yield(0)
            waitCount = waitCount + 1
        end
    end
    
    -- 약간의 정착 시간 (덱 합쳐지는 시간)
    for f=1, 30 do coroutine.yield(0) end
    
    -- 3.5 버린 더미에서 합쳐진 덱 뒤집기
    local mergedDiscard = findDeckAtWorldPos(discardWorldPos)
    if mergedDiscard then
        if not mergedDiscard.is_face_down then 
            mergedDiscard.flip() 
            for f=1, 30 do coroutine.yield(0) end -- 뒤집히는 시간 대기
        end
    end
    
    -- 4. 버린 더미를 액션 덱으로 가져오기
    for f=1, 30 do coroutine.yield(0) end -- 0.5초 대기
    
    local hitList = Physics.cast({
        origin       = {discardWorldPos.x, discardWorldPos.y + 2.0, discardWorldPos.z},
        direction    = {0, -1, 0},
        type         = 3,
        size         = {1.5, 3.0, 1.5},
        max_distance = 4,
    })
    
    local faceDownRot = {0, self.getRotation().y, 180}
    
    local movedDiscards = {}
    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj ~= self and (obj.type == 'Deck' or obj.type == 'Card') then
            obj.setPositionSmooth(deckWorldPos, false, false)
            obj.setRotationSmooth(faceDownRot, false, false)
            table.insert(movedDiscards, obj)
        end
    end
    
    -- 5. 상처카드(actor_wounds & owner_color) 1장 가져오기 (거리 35 이내)
    for f=1, 30 do coroutine.yield(0) end -- 0.5초 대기
    
    local myPos = self.getPosition()
    local objs = getObjects()
    local foundWound = false
    local targetTag = "owner_" .. string.lower(matColor)
    local targetTag2 = "owner_" .. matColor
    local woundObj = nil
    
    for _, o in ipairs(objs) do
        if o.hasTag("actor_wounds") and (o.hasTag(targetTag) or o.hasTag(targetTag2)) then
            local oPos = o.getPosition()
            local dist = math.sqrt((oPos.x - myPos.x)^2 + (oPos.z - myPos.z)^2)
            local distToDeck = math.sqrt((oPos.x - deckWorldPos.x)^2 + (oPos.z - deckWorldPos.z)^2)
            
            -- 이미 합쳐진 액션 덱이 상처 태그를 상속받은 경우를 무시하기 위함
            if dist <= 40 and distToDeck > 5 then
                if o.type == 'Deck' then
                    local deckTags = o.getTags()
                    woundObj = o.takeObject({
                        position = {deckWorldPos.x, deckWorldPos.y + 2.0, deckWorldPos.z},
                        rotation = faceDownRot,
                        smooth = true
                    })
                    if deckTags then
                        for _, tag in ipairs(deckTags) do
                            woundObj.addTag(tag)
                        end
                    end
                    foundWound = true
                    break
                elseif o.type == 'Card' then
                    woundObj = o
                    o.setPositionSmooth({deckWorldPos.x, deckWorldPos.y + 2.0, deckWorldPos.z}, false, false)
                    o.setRotationSmooth(faceDownRot, false, false)
                    foundWound = true
                    break
                end
            end
        end
    end
    
    if not foundWound then
        broadcastToAll("경고: 범위 내에 상처 카드(actor_wounds & " .. targetTag2 .. ")를 찾을 수 없습니다.", "Orange")
    end
    
    -- 버린 더미와 상처 카드 이동 완료 대기
    local maxWaitMerge = 180
    local waitMergeCount = 0
    while waitMergeCount < maxWaitMerge do
        local anyMoving = false
        for _, obj in ipairs(movedDiscards) do
            if obj ~= nil and not obj.isDestroyed() and obj.isSmoothMoving() then
                anyMoving = true
                break
            end
        end
        if woundObj ~= nil and not woundObj.isDestroyed() and woundObj.isSmoothMoving() then 
            anyMoving = true 
        end
        
        if not anyMoving then break end
        coroutine.yield(0)
        waitMergeCount = waitMergeCount + 1
    end
    
    -- 덱 결합 정착 대기
    for f=1, 45 do coroutine.yield(0) end
    
    -- 6. 액션 덱 섞기
    for f=1, 30 do coroutine.yield(0) end -- 0.5초 대기
    local deck = findDeckAtWorldPos(deckWorldPos)
    if deck and deck.type == 'Deck' then 
        deck.shuffle()
        for f=1, 15 do coroutine.yield(0) end
    end
    
    -- 7. 보드 위 토큰 삭제
    for f=1, 30 do coroutine.yield(0) end -- 0.5초 대기
    for _, o in ipairs(getObjects()) do
        if isOnThisBoard(o) then
            local name = o.getName() or ""
            local shouldDestroy = false
            
            if string.match(name, "Exhausted") or string.match(name, "Dazed") or
               string.match(name, "Defensive") or string.match(name, "Disrupt") or
               string.match(name, "Strain") or string.match(name, "Burned") or
               string.match(name, "Burning") or string.match(name, "Bonus") or
               string.match(name, "Threatened") then
                shouldDestroy = true
            elseif o.hasTag("Exhausted") or o.hasTag("Dazed") or 
               o.hasTag("Defensive") or o.hasTag("Disrupt") or o.hasTag("Strain") or 
               o.hasTag("Burned") or o.hasTag("Burning") or o.hasTag("BonusDamage") or 
               o.hasTag("Threatened") or o.hasTag("token_exhausted") or o.hasTag("token_dazed") then
                shouldDestroy = true
            end
            
            if shouldDestroy then
                o.destruct()
            end
        end
    end
    
    -- 8. 스태미나, 위협 데칼 초기화
    if stamina_level > 0 then
        stamina_level = 0
        updateStaminaDecal()
    end
    if is_threatened then
        disableThreatened()
    end
    
    -- 9. 피해 텍스트 0으로 초기화
    if damage_counter > 0 then
        damage_counter = 0
        refreshEquipmentDisplay()
    end
    
    -- 10. 투구(actor_helm) 장비 위에 Depleted 토큰 생성
    local function spawnDepletedOnHelmet()
        local helmet = nil
        for _, o in ipairs(getObjects()) do
            if isOnThisBoard(o) and o.hasTag('actor_helm') then
                helmet = o
                break
            end
        end
        
        if helmet then
            local depletedBags = getObjectsWithTag('bag_depleted')
            if #depletedBags > 0 then
                local bag = depletedBags[1]
                local spawnPos = helmet.getPosition()
                spawnPos.y = spawnPos.y + 0.5
                local spawnedToken = bag.takeObject({
                    position = spawnPos,
                    rotation = helmet.getRotation()
                })
                
                -- 스크립트로 생성한 오브젝트는 onObjectDrop을 발생시키지 않으므로 수동으로 장비 갱신 함수를 호출합니다.
                Wait.condition(
                    function() updateEquipmentTotal() end,
                    function() return spawnedToken == nil or spawnedToken.resting end,
                    3
                )
            else
                broadcastToAll("경고: bag_depleted 태그를 가진 가방을 찾을 수 없습니다.", "Orange")
            end
        else
            broadcastToAll("안내: 장착 중인 투구(actor_helm) 장비를 찾을 수 없어 고갈 토큰을 놓지 않았습니다.", "Orange")
        end
    end
    spawnDepletedOnHelmet()
    
    return 1
end

function checkCardInSequence(card)
    local capacity = getSequenceCapacity()
    local spacing = SEQUENCE_LOCAL_POSITIONS[5].x - SEQUENCE_LOCAL_POSITIONS[4].x
    
    local maxX = SEQUENCE_LOCAL_POSITIONS[1].x + 0.20
    local minX
    if capacity <= 5 then
        minX = SEQUENCE_LOCAL_POSITIONS[capacity].x - 0.20
    else
        minX = SEQUENCE_LOCAL_POSITIONS[5].x + ((capacity - 5) * spacing) - 0.20
    end
    
    local centerX = (maxX + minX) / 2
    -- 보드의 X 스케일을 곱해서 물리적 상자의 정확한 월드 크기를 구합니다.
    local width = (maxX - minX) * self.getScale().x
    
    local centerZ = SEQUENCE_LOCAL_POSITIONS[1].z
    local centerY = SEQUENCE_LOCAL_POSITIONS[1].y
    local centerWorld = self.positionToWorld({x=centerX, y=centerY, z=centerZ})

    local hitList = Physics.cast({
        origin       = centerWorld,
        direction    = {0, 1, 0},
        type         = 3,
        size         = {width, 1.5, 1.5},
        max_distance = 0,
    })

    for _, hit in ipairs(hitList) do
        if hit.hit_object == card then
            return true
        end
    end
    return false
end

function getSequenceTagsSorted()
    local capacity = getSequenceCapacity()
    local spacing = SEQUENCE_LOCAL_POSITIONS[5].x - SEQUENCE_LOCAL_POSITIONS[4].x
    
    local maxX = SEQUENCE_LOCAL_POSITIONS[1].x + 0.20
    local minX
    if capacity <= 5 then
        minX = SEQUENCE_LOCAL_POSITIONS[capacity].x - 0.20
    else
        minX = SEQUENCE_LOCAL_POSITIONS[5].x + ((capacity - 5) * spacing) - 0.20
    end
    
    local centerX = (maxX + minX) / 2
    local width = (maxX - minX) * self.getScale().x
    
    local centerZ = SEQUENCE_LOCAL_POSITIONS[1].z
    local centerY = SEQUENCE_LOCAL_POSITIONS[1].y
    local centerWorld = self.positionToWorld({x=centerX, y=centerY, z=centerZ})

    local hitList = Physics.cast({
        origin       = centerWorld,
        direction    = {0, 1, 0},
        type         = 3,
        size         = {width, 1.5, 1.5},
        max_distance = 0,
    })

    local cards = {}
    for _, hit in ipairs(hitList) do
        local obj = hit.hit_object
        if obj.type == "Card" and not obj.is_face_down then
            local lPos = self.positionToLocal(obj.getPosition())
            -- 확실히 영역 내부의 카드만 정렬에 포함하도록 이중 검사
            if lPos.x <= maxX and lPos.x >= minX and math.abs(lPos.z - centerZ) < 0.4 then
                table.insert(cards, {obj = obj, x = lPos.x})
            end
        end
    end
    -- Sequence builds left to right. x is positive on right (slot 1) and negative on left.
    -- Descending order of x means rightmost (slot 1) first, leftmost last.
    table.sort(cards, function(a, b) return a.x > b.x end)
    
    local sortedTags = {}
    local stealth_next_any = false
    local stealth_next_attack = false
    local stealth_all = false
    
    for _, c in ipairs(cards) do
        local tags = c.obj.getTags()
        local tList = {}
        local has_stealth = false
        local has_stealth_next_any = false
        local has_stealth_next_attack = false
        local has_stealth_next_all = false
        local has_attack = false
        local has_maneuver = false
        
        if tags then
            for _, t in ipairs(tags) do
                table.insert(tList, t)
                if t == "aa_stealth" then has_stealth = true end
                if t == "aa_stealth_next_any" then has_stealth_next_any = true end
                if t == "aa_stealth_next_attack" then has_stealth_next_attack = true end
                if t == "aa_stealth_next_all" then has_stealth_next_all = true end
                if t == "aa_attack" then has_attack = true end
                if t == "aa_maneuver" then has_maneuver = true end
            end
        end
        
        local is_stealthed = false
        if stealth_all then is_stealthed = true end
        if has_stealth_next_all then is_stealthed = true; stealth_all = true end
        if has_stealth then is_stealthed = true end
        if stealth_next_any then is_stealthed = true end
        if stealth_next_attack and has_attack then is_stealthed = true end
        
        -- aa_stealth_focus_am 마스터리 처리
        if (has_attack or has_maneuver) and isStealthFocusMasteryActive() then
            is_stealthed = true
        end
        
        -- Reset next triggers
        stealth_next_any = has_stealth_next_any
        stealth_next_attack = has_stealth_next_attack
        
        table.insert(sortedTags, { tags = tList, is_stealthed = is_stealthed, obj = c.obj })
    end
    return sortedTags
end

function proceedToActionPhaseEnd()
    checkStaminaEndActionPhase()
    local matColor = getMatColorFromTag()
    current_phase = 3
    has_drawn_attrition = false
    drawn_attrition_count = 0
    setPhaseDecal(3)
    broadcastToAll("Attrition Phase", matColor)
    
    local seqTags = getSequenceTagsSorted()
    local hasAttack = false
    for _, cTags in ipairs(seqTags) do
        if cTags.tags then
            for _, t in ipairs(cTags.tags) do
                if t == "aa_attack" then hasAttack = true break end
            end
        end
        if hasAttack then break end
    end
    if hasAttack and Global.getVar('is_game_started') then
        Global.call('TriggerBehaviorCheck', {type = "ActionEndWithAttack", color = matColor})
    end
    
    local CurrentMonster = Global.getVar("CurrentMonster")
    if (CurrentMonster == "Xitheros" or CurrentMonster == "지테로스" or CurrentMonster == "자이테로스") and aggro_is_enabled then
        local defensiveBags = getObjectsWithTag('bag_disrupt')
        if #defensiveBags > 0 then
            local bag = defensiveBags[1]
            -- 데미지 버튼 근처 보드 위에 방해 토큰 생성 (X 좌표 교정)
            local spawnPos = self.positionToWorld({0.25, 1, -1.3}) 
            bag.takeObject({
                position = spawnPos,
                rotation = self.getRotation()
            })
            broadcastToAll(matColor .. " 플레이어는 Xitheros 효과로 방해(Disrupt) 토큰을 받습니다.", Color[matColor])
        end
    end
end

function setupSequenceReturnUI(seqTags)
    _sequenceReturnCards = seqTags
    for i, c in ipairs(seqTags) do
        local obj = c.obj
        if obj and not obj.isDestroyed() then
            obj.createButton({
                label="회수",
                click_function="onClickReturnSequenceCard",
                function_owner=self,
                position={0, 0.5, 0},
                width=800, height=300, font_size=150,
                color={0, 0, 0}, font_color={1, 1, 1},
                tooltip="이 카드를 패로 되돌립니다",
            })
        end
    end
    
    self.createButton({
        click_function = "onSkipReturnSequence",
        function_owner = self,
        label = "회수 스킵",
        position = {-0.5, 0.21, -1.45}, 
        width = 800, height = 300, font_size = 150,
        scale = {0.15, 1, 0.2},
        color = {0, 0, 0}, font_color = {1, 1, 1}
    })
end

function onClickReturnSequenceCard(clicked_card, player_color)
    local matColor = getMatColorFromTag()
    if player_color ~= matColor then
        broadcastToAll("현재 턴 플레이어만 카드를 회수할 수 있습니다.", player_color)
        return
    end
    
    if clicked_card.hasTag('Aggro') or clicked_card.hasTag('aggro') then
        if temporary_aggro_card_count > 0 then
            temporary_aggro_card_count = temporary_aggro_card_count - 1
        end
    end

    cleanupSequenceReturnUI()
    clicked_card.deal(1, matColor, 1)
    
    -- 초 단위 대기 대신, 카드가 손패 존에 물리적으로 진입했는지 조건 확인
    Wait.condition(
        function() proceedToActionPhaseEnd() end,
        function()
            if not clicked_card or clicked_card.isDestroyed() then return true end
            local player = Player[matColor]
            if player then
                local handObjs = player.getHandObjects(1)
                if handObjs then
                    for _, obj in ipairs(handObjs) do
                        if obj == clicked_card then return true end
                    end
                end
            end
            return false
        end,
        3.0, -- 3초 타임아웃
        function() proceedToActionPhaseEnd() end
    )
end

function onSkipReturnSequence(obj, player_color)
    if player_color ~= getMatColorFromTag() then return end
    cleanupSequenceReturnUI()
    proceedToActionPhaseEnd()
end

function cleanupSequenceReturnUI()
    if _sequenceReturnCards then
        for _, c in ipairs(_sequenceReturnCards) do
            if c.obj and not c.obj.isDestroyed() then
                c.obj.clearButtons()
            end
        end
    end
    _sequenceReturnCards = nil
    
    local btns = self.getButtons()
    if btns then
        for _, btn in ipairs(btns) do
            if btn.click_function == "onSkipReturnSequence" then
                self.removeButton(btn.index)
            end
        end
    end
end

_terrainNames = _terrainNames or {"", "", ""}

function UpdateQuadrantTerrains(dataList)
    local wasInMist = isPlayerAffectedByMist()

    for i=1, 3 do
        local data = dataList[i]
        if type(data) == "string" then
            self.UI.setAttribute('quadrant-terrain-'..i, 'image', data)
            _terrainNames[i] = ""
            self.UI.show('quadrant-terrain-'..i)
        elseif type(data) == "table" and data.url then
            self.UI.setAttribute('quadrant-terrain-'..i, 'image', data.url)
            _terrainNames[i] = data.name or ""
            self.UI.show('quadrant-terrain-'..i)
        else
            self.UI.hide('quadrant-terrain-'..i)
            _terrainNames[i] = ""
        end
    end

    local isInMist = isPlayerAffectedByMist()
    if isInMist and not wasInMist then
        local matColor = getMatColorFromTag()
        if matColor then
            broadcastToAll(matColor .. '는 안개 지형으로 인해 위협받습니다.', Color[matColor] or Color.White)
        end
        if not is_threatened then
            enableThreatened()
        end
    end
    
    updateSequenceSlotDecals()
end

function onTerrainEnter1(player, value, id) showTerrainTooltip(1) end
function onTerrainEnter2(player, value, id) showTerrainTooltip(2) end
function onTerrainEnter3(player, value, id) showTerrainTooltip(3) end

function showTerrainTooltip(idx)
    if _terrainNames[idx] and _terrainNames[idx] ~= "" then
        self.UI.setAttribute('terrain-tooltip', 'text', _terrainNames[idx])
        self.UI.show('terrain-tooltip')
    end
end

function onTerrainExit(player, value, id)
    self.UI.hide('terrain-tooltip')
end
