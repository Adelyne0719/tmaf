--------------------------------------------------------------------------------
-- Terrain Card Automation
--------------------------------------------------------------------------------
active_terrain_cards = active_terrain_cards or {}

function getTerrainCardSnaps()
    local result = {}
    
    local function checkSnaps(snaps, obj)
        if not snaps then return end
        for i, snap in ipairs(snaps) do
            if snap.tags then
                for _, tag in ipairs(snap.tags) do
                    if string.lower(tag) == "terrain_card" then
                        local worldPos = snap.position
                        local worldRot = snap.rotation
                        if obj then
                            worldPos = obj.positionToWorld(snap.position)
                            local objRot = obj.getRotation()
                            worldRot = {
                                x = (objRot.x + snap.rotation.x) % 360,
                                y = (objRot.y + snap.rotation.y) % 360,
                                z = (objRot.z + snap.rotation.z) % 360
                            }
                        end
                        table.insert(result, { position = worldPos, rotation = worldRot })
                    end
                end
            end
        end
    end
    
    checkSnaps(Global.getSnapPoints(), nil)
    for _, obj in ipairs(getAllObjects()) do
        checkSnaps(obj.getSnapPoints(), obj)
    end
    
    table.sort(result, function(a, b) return a.position.x < b.position.x end)
    
    if #result == 0 then
        broadcastToAll("[지형 시스템] 에러: 'terrain_card' 태그가 지정된 스냅 포인트를 맵 전체에서 0개 찾았습니다!", "Red")
    end
    
    return result, nil
end

function isObjectTerrainType(obj)
    local t = obj.type
    if t == "Generic" or t == "Custom_Token" or t == "Custom_Model" or t == "Custom_Tile" or t == "Custom_Assetbundle" or t == "Figurine" or t == "RPG_Figurine" or t == "Tile" or t == "Token" or t == "Model" then
        local name = obj.getName()
        if name and name ~= "" then return true end
    end
    return false
end



--------------------------------------------------------------------------------
-- Terrain Card Automation
--------------------------------------------------------------------------------
active_terrain_cards = active_terrain_cards or {}

function getTerrainCardSnaps()
    local result = {}
    
    local function checkSnaps(snaps, obj)
        if not snaps then return end
        for i, snap in ipairs(snaps) do
            if snap.tags then
                for _, tag in ipairs(snap.tags) do
                    if string.lower(tag) == "terrain_card" then
                        local worldPos = snap.position
                        local worldRot = snap.rotation
                        if obj then
                            worldPos = obj.positionToWorld(snap.position)
                            local objRot = obj.getRotation()
                            worldRot = {
                                x = (objRot.x + snap.rotation.x) % 360,
                                y = (objRot.y + snap.rotation.y) % 360,
                                z = (objRot.z + snap.rotation.z) % 360
                            }
                        end
                        table.insert(result, { position = worldPos, rotation = worldRot })
                    end
                end
            end
        end
    end
    
    checkSnaps(Global.getSnapPoints(), nil)
    for _, obj in ipairs(getAllObjects()) do
        checkSnaps(obj.getSnapPoints(), obj)
    end
    
    table.sort(result, function(a, b) return a.position.x < b.position.x end)
    
    if #result == 0 then
        broadcastToAll("[지형 시스템] 에러: 'terrain_card' 태그가 지정된 스냅 포인트를 맵 전체에서 0개 찾았습니다!", "Red")
    end
    
    return result, nil
end

function isObjectTerrainType(obj)
    local t = obj.type
    if t == "Generic" or t == "Custom_Token" or t == "Custom_Model" or t == "Custom_Tile" or t == "Custom_Assetbundle" or t == "Figurine" or t == "RPG_Figurine" or t == "Tile" or t == "Token" or t == "Model" then
        local name = obj.getName()
        if name and name ~= "" then return true end
    end
    return false
end


function stripHex(str)
    return string.gsub(str, "%[.-%]", "")
end


local TerrainNameMap = {
    ["sand"] = "모래",
    ["water"] = "물",
    ["fire"] = "불",
    ["fog"] = "안개",
    ["ice"] = "얼음",
    ["rock"] = "바위",
    ["plateau"] = "고원",
    ["brush"] = "덤불",
    ["jungle brush"] = "정글덤불",
    ["baethanis"] = "배타니스",
    ["synaerea"] = "시내에라",
    ["wildmaw"] = "와일드마우",
    ["cyricae"] = "시리카",
    ["swamp"] = "늪"
}

local ReverseTerrainMap = {}
for k, v in pairs(TerrainNameMap) do
    ReverseTerrainMap[v] = k
end

local TerrainImageUrls = {
    ["모래"] = "https://steamusercontent-a.akamaihd.net/ugc/2514782313678838967/3FD2A277EAB8E27ADD5DF56BCFCA28874EB6587C/",
    ["물"] = "https://steamusercontent-a.akamaihd.net/ugc/2513648804729435560/5A1D850A3840A94DB6AF5DAEEC0719FB15F1ED74/",
    ["불1"] = "https://steamusercontent-a.akamaihd.net/ugc/2514782313678839078/D6E4F2F807643B90769A2798DBD4E838B8959FFC/",
    ["불2"] = "https://steamusercontent-a.akamaihd.net/ugc/2514782313678839153/D96D91EB2D0E3377CE71795B68CB1776C1DAD1E0/",
    ["안개"] = "https://steamusercontent-a.akamaihd.net/ugc/2513648804729430172/1CE006690D55C6318DEAE58BFCB8DF8CBAFCBA40/",
    ["얼음"] = "https://steamusercontent-a.akamaihd.net/ugc/2513648804729430572/BC43B89F49D34ED3CBCF4B209FD9405506FAF785/",
    ["바위"] = "https://steamusercontent-a.akamaihd.net/ugc/12796605896014872809/B374D3AF84F4FE9FFC45097333F7A75ABC5A95A0/",
    ["고원"] = "https://steamusercontent-a.akamaihd.net/ugc/16461813904938530072/7AFB155751B21BF6A8989D2DFE7244BA5CDAB3B0/",
    ["덤불"] = "https://steamusercontent-a.akamaihd.net/ugc/10227448999252428845/995C1479760EB4AB9F207DAE4EE9946700080398/",
    ["정글덤불"] = "https://steamusercontent-a.akamaihd.net/ugc/2513648804729435087/B6451318AFAE9AFF903049D6DD302742603B3CF8/",
    ["배타니스"] = "https://steamusercontent-a.akamaihd.net/ugc/13276293597751766092/FBEB5613CDCE13A5F6892EE9949F276A6F3724FF/",
    ["시내에라"] = "https://steamusercontent-a.akamaihd.net/ugc/14022280327567143827/BF17400DA52CA6D3045ADAAE6B2BA67045F9452C/",
    ["와일드마우"] = "https://steamusercontent-a.akamaihd.net/ugc/2514782313678838871/747C88A23044E4A00CB4A0DC5253F4F486041928/",
    ["시리카"] = "https://steamusercontent-a.akamaihd.net/ugc/12504717050239958294/815C845842552B7FD4FECF6524CD9DE8DAA5E735/",
    ["늪"] = "https://steamusercontent-a.akamaihd.net/ugc/2513648804729429149/F43FA544CAA140E97CF6397B1EBECAEC7F597652/",
}

function getTerrainQuadrant(terrainObj)
    if not terrainObj or terrainObj.isDestroyed() then return nil end
    local figPos = terrainObj.getPosition()
    local closestZone = nil
    local closestDist = math.huge
    local combatBoardGUID = GetCombatBoardGUID()
    if not combatBoardGUID then return nil end
    local terrains = Terrains
    if not terrains then return nil end
    
    for zoneName, snapTags in pairs(terrains) do
        for _, snapTag in ipairs(snapTags) do
            local snapPos = getWorldPosOfSnapOnObj({combatBoardGUID, snapTag})
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

function UpdateAllPlayerTerrainUI()
    local playerBoards = getObjectsWithTag("player_board")
    for _, board in ipairs(playerBoards) do
        local pColor = board.memo
        if not pColor or pColor == "" then
            if board.hasTag('color_blue') then pColor = 'Blue'
            elseif board.hasTag('color_green') then pColor = 'Green'
            elseif board.hasTag('color_yellow') then pColor = 'Yellow'
            elseif board.hasTag('color_orange') then pColor = 'Orange'
            elseif board.hasTag('color_red') then pColor = 'Red'
            else pColor = "White" end
        end
        local quadrant = getPlayerQuadrantGlobal(pColor)
        local urls = {}
        if quadrant then
            for _, data in ipairs(active_terrain_cards) do
                for _, t in ipairs(data.terrains) do
                    if not t.isDestroyed() and getTerrainQuadrant(t) == quadrant then
                        local rawName = t.getName()
                        if rawName and rawName ~= "" then
                            local name = stripHex(rawName)
                            local mapped = TerrainNameMap[string.lower(name)] or name
                            local url = TerrainImageUrls[mapped]
                            
                            -- 불 토큰 특수 처리 (앞/뒷면)
                            if mapped == "불" then
                                if t.is_face_down then
                                    url = TerrainImageUrls["불2"]
                                else
                                    url = TerrainImageUrls["불1"]
                                end
                            end
                            
                            if url then
                                table.insert(urls, url)
                            end
                        end
                        break -- 한 지형 종류당 하나만 추가
                    end
                end
            end
        end
        -- 최대 3개까지만 전송
        local finalUrls = {}
        for i=1, 3 do
            if urls[i] then table.insert(finalUrls, urls[i]) end
        end
        board.call("UpdateQuadrantTerrains", finalUrls)
    end
end

local TerrainNameMap = {
function handleTerrainAdded(terrainObj)
    if not terrainObj or terrainObj.isDestroyed() then
        return
    end
    if terrainObj.hasTag("terrain_card_handled") then
        return
    end
    if not isObjectTerrainType(terrainObj) then
        return
    end
    
    local rawName = terrainObj.getName()
    if not rawName or rawName == "" then return end
    local name = stripHex(rawName)
    if name == "" then return end
    
    local lowerName = string.lower(name)
    local mappedName = TerrainNameMap[lowerName] or ReverseTerrainMap[lowerName]
    
    local searchNames = {name}
    if mappedName and mappedName ~= name then
        table.insert(searchNames, mappedName)
    end
    
    -- 이미 나와 있는 지형 카드인지 확인 (중복된 카드가 나오지 않게 함)
    for _, data in ipairs(active_terrain_cards) do
        if data.card and not data.card.isDestroyed() then
            local cname = data.card.getName()
            if cname then
                local lcname = string.lower(string.gsub(cname, "^%s*(.-)%s*$", "%1"))
                for _, sName in ipairs(searchNames) do
                    if lcname == string.lower(sName) then
                        -- 기존 카드에 토큰만 추가
                        terrainObj.addTag("terrain_card_handled")
                        table.insert(data.terrains, terrainObj)
                        Wait.frames(function() UpdateAllPlayerTerrainUI() end, 1)
                        return
                    end
                end
            end
        end
    end
    
    local snaps, board = getTerrainCardSnaps()
    local nextIndex = #active_terrain_cards + 1
    local targetPos = {-19.21, 5, 21.72}
    local targetRot = {0, 180, 180}
    
    if snaps and nextIndex <= #snaps then
        local snap = snaps[nextIndex]
        targetPos = {x=snap.position.x, y=snap.position.y + 1, z=snap.position.z}
        targetRot = snap.rotation
        if board then
            targetPos = board.positionToWorld(snap.position)
            targetPos.y = targetPos.y + 1
            local brot = board.getRotation()
            targetRot = {
                x = (brot.x + snap.rotation.x) % 360,
                y = (brot.y + snap.rotation.y) % 360,
                z = (brot.z + snap.rotation.z) % 360
            }
        end
    end
    
    local matchCard = takeTerrainCard(searchNames, targetPos, targetRot)
    if not matchCard then return end
    
    terrainObj.addTag("terrain_card_handled")
    
    table.insert(active_terrain_cards, {
        card = matchCard,
        terrains = {terrainObj},
        snap_index = (nextIndex <= #snaps) and nextIndex or -1
    })
    Wait.frames(function() UpdateAllPlayerTerrainUI() end, 1)
end

function handleTerrainRemoved(terrainObj)
    if not terrainObj.hasTag("terrain_card_handled") then return end
    
    for i, data in ipairs(active_terrain_cards) do
        for j, t in ipairs(data.terrains) do
            if t == terrainObj then
                table.remove(data.terrains, j)
                Wait.frames(function() UpdateAllPlayerTerrainUI() end, 1)
                if #data.terrains == 0 then
                    if data.card and not data.card.isDestroyed() then
                        -- Return to original deck position
                        data.card.setPositionSmooth({-19.21, 2, 21.72}, false, true)
                        data.card.setRotationSmooth({0, 180, 180}, false, true)
                    end
                    table.remove(active_terrain_cards, i)
                    realignTerrainCards()
                end
                return
            end
        end
    end
end

function realignTerrainCards()
    local snaps, board = getTerrainCardSnaps()
    local currentSnapIndex = 1
    
    for _, data in ipairs(active_terrain_cards) do
        if data.card and not data.card.isDestroyed() then
            if currentSnapIndex <= #snaps then
                local snap = snaps[currentSnapIndex]
                local targetPos = {x=snap.position.x, y=snap.position.y + 1, z=snap.position.z}
                local targetRot = snap.rotation
                
                data.snap_index = currentSnapIndex
                data.card.setPositionSmooth(targetPos, false, true)
                data.card.setRotationSmooth(targetRot, false, true)
                currentSnapIndex = currentSnapIndex + 1
            else
                data.snap_index = -1
            end
        end
    end
end

function onObjectSpawn(spawned_object)
    if spawned_object == nil or spawned_object.isDestroyed() then return end
    Wait.time(function() 
        if spawned_object and not spawned_object.isDestroyed() then
            handleTerrainAdded(spawned_object) 
        end
    end, 0.5)
end

function onObjectDestroy(destroyed_object)
    if destroyed_object == nil then return end
    handleTerrainRemoved(destroyed_object)
end
