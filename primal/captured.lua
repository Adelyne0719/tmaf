local occupant = nil
local button_state = "none" -- "none", "capture", "return"

function onLoad()
    self.clearButtons()
end

function getOwnerColor(obj)
    if not obj then return nil end
    for _, tag in ipairs(obj.getTags()) do
        if tag:sub(1,6) == "owner_" then
            return tag:sub(7)
        end
    end
    return nil
end

function onCollisionEnter(info)
    local obj = info.collision_object
    if obj.hasTag("actor_mini") then
        if not occupant or occupant == obj then
            occupant = obj
            if button_state == "none" then
                showCaptureButton()
            end
        end
    end
end

-- 폴링 루프를 통해 피규어가 타일을 벗어났는지 확인
function update()
    if occupant then
        if occupant.isDestroyed() then
            clearOccupant()
        else
            local tPos = self.getPosition()
            local oPos = occupant.getPosition()
            local distSq = (tPos.x - oPos.x)^2 + (tPos.z - oPos.z)^2
            if distSq > 9 then -- 타일을 벗어났다고 판단 (거리 조절 가능)
                clearOccupant()
            end
        end
    end
end

function onObjectPickUp(player_color, picked_up_object)
    if occupant == picked_up_object then
        clearOccupant()
    end
end

function clearOccupant()
    occupant = nil
    if button_state == "capture" then
        self.clearButtons()
        button_state = "none"
    end
end

function showCaptureButton()
    button_state = "capture"
    self.clearButtons()
    -- 남쪽(Z축 양수 방향), y축을 약간 높여서(0.5) 타일이나 바닥에 파묻히지 않게 함
    self.createButton({
        label="포획", click_function="onClickCapture", function_owner=self,
        position={0, 0.5, 1.5}, height=400, width=1000, font_size=300,
        color={0,0,0}, font_color={1,1,1}
    })
end

function showReturnButton()
    button_state = "return"
    self.clearButtons()
    self.createButton({
        label="복귀", click_function="onClickReturn", function_owner=self,
        position={0, 0.5, 1.5}, height=400, width=1000, font_size=300,
        color={0,0,0}, font_color={0,1,0}
    })
end

function getPlayerBoard(color)
    local activePlayers = Global.getTable("ActivePlayer")
    if activePlayers and activePlayers[color] then
        return getObjectFromGUID(activePlayers[color].boardGUID)
    end
    return nil
end

function setGlobalPhaseHUD(phase_num, active)
    if not active then
        Global.UI.setAttribute("PhaseHUD", "active", "false")
        return
    end

    local url = ""
    local text = ""
    if phase_num == 1 then
        url = "http://cloud-3.steamusercontent.com/ugc/2505775586675200388/C33DC1ACDA2F35F12D73CCB2A8D39EEFA7F015CE/"
        text = "Movement Phase"
    elseif phase_num == 2 then
        url = "http://cloud-3.steamusercontent.com/ugc/2505775586675204481/37482DA8A6FEA67AB55BEBB8B0E53B02052C8957/"
        text = "Action Phase"
    elseif phase_num == 3 then
        url = "http://cloud-3.steamusercontent.com/ugc/2505775586675206307/E868D96DF981E27581BCC6E70CDB255E2B961058/"
        text = "Attrition Phase"
    elseif phase_num == 4 then
        url = "https://steamusercontent-a.akamaihd.net/ugc/16465744318144975434/E48AF0CDCADD68E22EFD78EE062E8CBE0D2D5C00/"
        text = "End Turn"
    end

    if url ~= "" then
        Global.UI.setAttribute("PhaseHUD_Image", "image", url)
        Global.UI.setAttribute("PhaseHUD_Text", "text", text)
        Global.UI.setAttribute("PhaseHUD", "active", "true")
    end
end

function onClickCapture(obj, player_color, alt_click)
    if not occupant then return end
    local owner = getOwnerColor(occupant)
    if not owner then return end
    if player_color ~= owner then
        broadcastToColor("당신의 피규어가 아닙니다.", player_color, Color.Red)
        return
    end

    local board = getPlayerBoard(owner)
    if board then
        -- 1. 손패 버리기
        local handObjects = Player[owner].getHandObjects(1)
        if handObjects then
            local discardPosLocal = board.getVar("DISCARD_LOCAL_POS") or {1.319, 2.247, -0.038}
            local discardPos = board.positionToWorld(discardPosLocal)
            local boardRot = board.getRotation()
            for i, card in ipairs(handObjects) do
                pcall(function()
                    card.use_hands = false
                    card.setPositionSmooth({discardPos.x, discardPos.y + i*0.2, discardPos.z}, false, false)
                    card.setRotationSmooth({0, boardRot.y, 0}, false, false)
                    Wait.time(function() if card ~= nil and not card.isDestroyed() then card.use_hands = true end end, 1.0)
                end)
            end
        end

        -- 2. 시퀀스 버리기
        board.call("discardSequenceNoDrawWrapper")

        -- 3. End Turn 및 페이즈 변경 (턴은 넘기지 않음)
        board.setVar("current_phase", 4)
        board.call("disablePhaseDecals")
        if not board.getVar("is_turn_ended") then
            board.call("enableTurnEnd")
        end
        
        setGlobalPhaseHUD(4, true)
        broadcastToAll(owner .. " 플레이어가 포획되었습니다. 턴 종료 단계(End Turn)로 진입합니다.", Color[owner] or {1,1,1})
    end

    -- 4. 버튼 변경
    showReturnButton()
end

function getCombatBoard()
    local guid = Global.call("GetCombatBoardGUID")
    return getObjectFromGUID(guid)
end

function findSnapInFrontZone()
    local combatBoardGUID = Global.call("GetCombatBoardGUID")
    if not combatBoardGUID then return nil end

    local frontZoneName = Global.call("getMonsterFrontZone")
    local emptySnaps = {}
    local occupiedSnaps = {}
    local validSnapsPos = {}

    local combatBoard = getObjectFromGUID(combatBoardGUID)

    local allSnaps = {}
    local cSnaps = combatBoard.getSnapPoints()
    if cSnaps then
        for _, s in ipairs(cSnaps) do
            table.insert(allSnaps, { snap = s, isGlobal = false })
        end
    end
    
    local gSnaps = Global.getSnapPoints()
    if gSnaps then
        for _, s in ipairs(gSnaps) do
            table.insert(allSnaps, { snap = s, isGlobal = true })
        end
    end

    for _, item in ipairs(allSnaps) do
        local snap = item.snap
        local isFigureSnap = false
        if snap.tags then
            for _, tag in ipairs(snap.tags) do
                if string.match(tag, "^figure_") then
                    isFigureSnap = true
                    break
                end
            end
        end

        if isFigureSnap then
            local worldPos = item.isGlobal and snap.position or combatBoard.positionToWorld(snap.position)
            
            local center = Global.call("getTrueBoardCenter", combatBoardGUID)
            if not center then center = combatBoard.getPosition() end
            
            local dx = worldPos.x - center.x
            local dz = worldPos.z - center.z
            
            local boardRot = Global.call("getTrueBoardRotation", combatBoardGUID)
            if not boardRot then boardRot = combatBoard.getRotation().y end
            
            local rad = math.rad(-boardRot)
            local localX = dx * math.cos(rad) - dz * math.sin(rad)
            local localZ = dx * math.sin(rad) + dz * math.cos(rad)
            
            local absX = math.abs(localX)
            local absZ = math.abs(localZ)
            
            local zone = nil
            if localZ > absX then zone = "back"
            elseif localZ < -absX then zone = "front"
            elseif localX > absZ then zone = "right"
            else zone = "left" end

            if zone == frontZoneName then
                table.insert(validSnapsPos, worldPos)
            end
        end
    end

    for _, worldPos in ipairs(validSnapsPos) do
        local hitList = Physics.cast({
            origin={worldPos.x, worldPos.y + 2, worldPos.z}, direction={0,-1,0}, type=3, size={1.5,2,1.5}, max_distance=4
        })
        local hasObj = false
        for _, hit in ipairs(hitList) do
            local hObj = hit.hit_object
            if hObj.guid ~= combatBoardGUID and hObj.type ~= "Surface" and hObj.type ~= "Board" and not hObj.hasTag("Monster") then
                hasObj = true
                break
            end
        end
        if not hasObj then
            table.insert(emptySnaps, worldPos)
        else
            table.insert(occupiedSnaps, worldPos)
        end
    end

    if #emptySnaps > 0 then
        return emptySnaps[math.random(#emptySnaps)]
    elseif #occupiedSnaps > 0 then
        local pos = occupiedSnaps[math.random(#occupiedSnaps)]
        pos.y = pos.y + 1
        return pos
    elseif #validSnapsPos > 0 then
        local pos = validSnapsPos[1]
        pos.y = pos.y + 1
        return pos
    end
    
    if combatBoard then return combatBoard.getPosition() end
    return nil
end

function onClickReturn(obj, player_color, alt_click)
    if not occupant then return end
    local owner = getOwnerColor(occupant)
    if not owner then return end
    if player_color ~= owner then
        broadcastToColor("당신의 피규어가 아닙니다.", player_color, Color.Red)
        return
    end

    local board = getPlayerBoard(owner)
    local combatBoard = getCombatBoard()

    -- 1. 정면 구역 배치
    local targetPos = findSnapInFrontZone()
    if targetPos then
        occupant.setPositionSmooth(targetPos, false, false)
    end

    if board then
        -- 2. 손패 제한까지 뽑기
        board.call("drawToHandLimit")
        
        -- 3. 무기 레벨 피해
        local forgeBonus = board.call("getWeaponForgeBonus") or 0
        if forgeBonus > 0 then
            -- adjustDamageCounter 함수는 데미지를 추가하므로 그냥 양수를 넘김
            board.call("adjustDamageCounter", forgeBonus)
            broadcastToAll(owner .. " 플레이어가 무기 레벨(" .. forgeBonus .. ")만큼 피해를 받았습니다.", Color[owner] or {1,1,1})
        end

        -- 4. 덱에서 2장 버리며 체크 코루틴 실행
        _G.returnOwner = owner
        startLuaCoroutine(self, "returnCardCheckCoroutine")
    end

    self.clearButtons()
    button_state = "none"
end

function returnCardCheckCoroutine()
    local owner = _G.returnOwner
    local board = getPlayerBoard(owner)
    if not board then return 1 end

    local deckPosLocal = board.getVar("DECK_LOCAL_POS") or {0.863, 2.247, -0.039}
    local discardPosLocal = board.getVar("DISCARD_LOCAL_POS") or {1.319, 2.247, -0.038}
    local deckPos = board.positionToWorld(deckPosLocal)
    local discardPos = board.positionToWorld(discardPosLocal)

    -- 손패 제한 드로우 코루틴이 끝날 때까지 대기
    while board.getVar("is_drawing_coroutine_running") do
        coroutine.yield(0)
    end

    local hasAttackOrManeuver = false

    for i=1, 2 do
        local hits = Physics.cast({
            origin={deckPos.x, deckPos.y + 1, deckPos.z}, direction={0, -1, 0}, type=3, size={2, 5, 2}, max_distance=0
        })
        local deck = nil
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            if obj.type == "Deck" or obj.type == "Card" then
                deck = obj
                break
            end
        end

        if deck then
            local cardObj = nil
            if deck.type == "Deck" then
                cardObj = deck.takeObject({
                    position = {discardPos.x, discardPos.y + 1 + (i*0.2), discardPos.z},
                    flip = true,
                    smooth = true
                })
            else
                cardObj = deck
                cardObj.setPositionSmooth({discardPos.x, discardPos.y + 1 + (i*0.2), discardPos.z}, false, false)
                cardObj.setRotationSmooth({0, board.getRotation().y, 180}, false, false)
            end

            -- 카드가 움직이고 태그를 읽을 수 있을 때까지 대기
            for _=1, 50 do coroutine.yield(0) end

            if cardObj and not cardObj.isDestroyed() then
                local foundCardType = "알 수 없음"
                for _, tag in ipairs(cardObj.getTags()) do
                    if tag == "aa_attack" then
                        foundCardType = "공격"
                        hasAttackOrManeuver = true
                    elseif tag == "aa_maneuver" then
                        foundCardType = "기동"
                        hasAttackOrManeuver = true
                    elseif tag == "aa_evade" then
                        foundCardType = "회피"
                    elseif tag == "aa_defend" then
                        foundCardType = "방어"
                    end
                end
                if foundCardType ~= "알 수 없음" then
                    broadcastToAll(owner .. " 플레이어가 [" .. foundCardType .. "] 카드를 뽑았습니다.", Color[owner] or {1,1,1})
                end
            end
            
            -- 다음 카드 뽑기 전 0.5초 간격 대기
            for _=1, 30 do coroutine.yield(0) end
        end
    end

    if hasAttackOrManeuver then
        board.setVar("current_phase", 1)
        setGlobalPhaseHUD(1, true)
        broadcastToAll(owner .. " 플레이어가 포획에서 복귀하며 Movement Phase를 진행합니다.", Color[owner] or {1,1,1})
    else
        board.setVar("current_phase", 4)
        board.call("disablePhaseDecals")
        if not board.getVar("is_turn_ended") then
            board.call("enableTurnEnd")
        end
        setGlobalPhaseHUD(4, true)
        broadcastToAll(owner .. " 플레이어가 포획에서 복귀했으나 행동 카드를 뽑지 못해 턴을 종료합니다. End Turn 버튼을 눌러 턴을 넘기세요.", Color[owner] or {1,1,1})
    end

    return 1
end
