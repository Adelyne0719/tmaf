--몬스터별 빨간 테두리(XML UI) 회전 보정 값
MonsterUIOffsets = {
    ["da7685"] = 150,
    ["52ca56"] = 135,
    ["5e8dd4"] = -45,
    ["29f00d"] = -45,
    ["e4a59c"] = 45,
    ["e2684e"] = 30,
    ["94fc1a"] = 30,
    ["cfafe2"] = 45,
    ["2bc51e"] = 60,
    ["56f215"] = 45,
    ["426541"] = -30
}

-- 몬스터 회전 4가지 케이스
-- 각 case 의 front/right/back/left 는 그 zone 에 어그로 플레이어가 있을 때 몬스터의 절대 Y 회전값
MonsterRotationCases = {
    -- 케이스 1: 정면 Y=180, 표준 회전 (front→right→back→left = 시계 반대)
    case1 = { front = 180, right = 90,  back = 0,   left = 270 },

    -- 케이스 2: 정면 Y=180, 좌우 반전 (front→right→back→left = 시계)
    case2 = { front = 180, right = 270, back = 0,   left = 90 },

    -- 케이스 3: 정면 Y=0, 표준 회전
    case3 = { front = 0,   right = 270, back = 180, left = 90 },

    -- 케이스 4: 정면 Y=0, 좌우 반전
    case4 = { front = 0,   right = 90,  back = 180, left = 270 },

    -- 케이스 5: 90도 반시계방향 전위
    case5 = { front = 270, right = 180, back = 90,  left = 0 },

    -- 케이스 6: 90도 시계방향 전위
    case6 = { front = 90, right = 0, back = 270, left = 180 }
}


-- 각 케이스에 해당하는 몬스터 이름만 추가하면 자동 매핑됨
MonsterCases = {
    case1 = {

        -- 예: "MonsterA",
    },
    case2 = {

        -- 예: "MonsterB",
    },
    case3 = {
        "Felaxir",
        -- 예: "MonsterC",
    },
    case4 = {

        -- 예: "MonsterD",
    },
    case5 = {
        "Xitheros",
    },
    case6 = {
        "Awakened",
    }
}

-- 등록되지 않은 몬스터용 기본 케이스
MONSTER_DEFAULT_CASE = "case1"

--game static variable
TurnOrderUIisHidden = true
CampaignUIisHidden = true
MonsterBookGUID = "732918"
CampaignSheetGUID = "9c5742"
CombatBoardGUIDs = {"cf5fc6", "7e2f97", "3d46a1", "e7e719", "822930", "0c1ffc", "20af28", "39cd16", "a25d70", "28124b", "21c822"}

function GetCombatBoardGUID()
    for _, guid in ipairs(CombatBoardGUIDs) do
        if getObjectFromGUID(guid) then return guid end
    end
    return CombatBoardGUIDs[1]
end

ZoneBehave = {"f1a17b", "08c643","e76a94"}
RuleBookPDF = "5b5068"
disableSave=false

-- 어그로 마크 URL (개인 보드와 Global UI 공용)
URL_AGGRO_ON = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111571390678/145B47FAD34C9279DB6464D8A4F9120AB333504B/'
URL_AGGRO_OFF = 'https://steamusercontent-a.akamaihd.net/ugc/2452852111571389540/CA30F389ADD46B0FE9F0CFABD07C20615EFDE103/'

-- 플레이어별 시퀀스 구역 좌표
local SequenceZones = {
    Blue   = { min_x = -43.5, max_x = -32.5, min_z = -6.0, max_z = -2.5 },
    Green  = { min_x = -24.5, max_x = -13.5, min_z = -6.0, max_z = -2.5 },
    Yellow = { min_x = -5.8,  max_x = 5.9,   min_z = -6.0, max_z = -2.5 },
    Orange = { min_x = 13.5,  max_x = 24.5,  min_z = -6.0, max_z = -2.5 },
    Red    = { min_x = 32.5,  max_x = 43.5,  min_z = -6.0, max_z = -2.5 }
}

--current combat/Campaign variable
CurrentMonster= "Vyraxen"
CurrentRound = 0
FightLevel = "0"
MonsterData = {	}

--static Dictionnaries/arrays
Terrains={
front = {"terrain_1","terrain_2","terrain_3", },
right = {"terrain_4","terrain_5","terrain_6", },
back = {"terrain_7","terrain_8","terrain_9", },
left = {"terrain_10","terrain_11","terrain_12", },
}

Dictionnary = {
	{"Acceleration token", pdf = RuleBookPDF, page=107},
	{"Acheivement", pdf = RuleBookPDF, page=62},
	{"Acheivement system", pdf = RuleBookPDF, page=57},
	{"Action card", pdf = RuleBookPDF, page=10},
	{"Playing Action card", pdf = RuleBookPDF, page=22},
	{"Action card ID", pdf = RuleBookPDF, page=50},
	{"Action phase", pdf = RuleBookPDF, page=20},
	{"Action keyword", pdf = RuleBookPDF, page=106},
	{"Active Player", pdf = RuleBookPDF, page=18},
	{"Adjacent sector", pdf = RuleBookPDF, page=107},
}

allZone = {
AccelData = {tag="Accel", zoneGUID="2a98da", textGUID="19b372"},
StruggleData = {tag="Struggle", zoneGUID="428ead", textGUID="b32e80"},
	behaviorUI1Data = {tag="Behavior", zoneGUID = "f1a17b", UIname = "behave1"},
	behaviorUI2Data = {tag="Behavior", zoneGUID = "08c643", UIname = "behave2"},
	behaviorUI3Data = {tag="Behavior", zoneGUID = "e76a94", UIname = "behave3"},
}

BehaviorDescription = {
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111556058232/617203190F2145AEE18455891FB5B41209E6BD94/"] = "플레이어가 시퀸스에서 공격 (빨강) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559736514/8DE2F02F366A0D2CB1264A35E0A98A820DDCD036/"] = "플레이어가 시퀸스에서 기동 (파랑) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559724451/0FDA53FFF2BFF38EAFDAEFABC30B4BD9522EA1B2/"] = "플레이어가 시퀸스에서 회피 (초록) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559738675/A0C90AAF5A5160DEDDFBC02E9FDBF7E18200937E/"] = "플레이어가 시퀸스에서 방어 (노랑) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559722258/60A67E00A895B42BB39FD2319C9D1470797F3A9B/"] = "플레이어가 시퀸스에서 어그로 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559737991/D6A43F7E0DAF187B944A040BF84A0D5B3BC41C68/"] = "플레이어가 시퀸스에서 공격형(빨강/파랑) 카드를 플레이한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559727035/F4AB07C543E2813FBF3B259E5EFDB137CD8770A9/"] = "플레이어가 시퀸스에서 공격형(빨강/파랑) 카드를 두장 연속으로 플레이한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559723262/11B6814A51F5474342C43023EA0FB57F64545F26/"] = "플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 플레이한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559726274/A555F886EBDDCB1B0E6CF5EC0B369D426E9D6746/"] = "플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 두장 연속으로 플레이한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559728634/D1BAD234BF2812CA30C2923D5AC7E4DE49A52AB8/"] = "라운드가 끝날 때 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559733007/C9578229C5D3B0C7EB431B40DD4D9302EF0CCB50/"] = "이 카드가 게임에 들어온 즉시 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559745713/7E46CE2DD23CF4CA89C18946CAFDE5E7EE5CF6A1/"] = "몬스터가 다른 구역을 향해 방향을 바꾼 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559730908/45AF0AB5D6E2FC61AA62EEEC1D1C003465C957D6/"] = "플레이어가 정면 구역에서 턴을 시작할 때 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559737310/4117293ACF34F339124FF95FC029613EEB4F8E01/"] = "플레이어가 이동한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559735346/68371C9A4105F64B3C1651E9EBC72B4551B1FBE4/"] = "플레이어가 물 지형이 있는 구역으로 이동한 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559732177/EAEC1B8619BB25D425DB54E16200E7698479C960/"] = "플레이어가 손패를 비운 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559729521/EBF77250CBC0937ACE62E5CA5EE40B6894B108AE/"] = "마찰 단계가 끝난 후 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2499015733551843140/89B11196A6A96F74CB856B8FDA9DDE5371C03601/"] = "행동 카드가 비어 있습니다. 행동 카드가 있는 경우 해당 행동 카드의 발동 조건이 표시됩니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559427251/DBC558D9044F317A8D6C70ABC23374C9C9C37D66/"] = "다른 카드가 발동할 때 같이 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559730265/68C05667939A937D5723F33FF980EB661A8977A2/"] = "플레이어가 측면 구역에서 턴을 시작할 때 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559731494/5FA45BDB091EB12421C731327E3A61FF36495116/"] = "플레이어가 턴 시작시 측면 구역에 플레이어가 한 명이라도 있다면 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559741580/D5BAD0FFE9E8E019A8F00B5B68ED1FF67FCF583C/"] = "플레이어가 턴 시작시 후면 구역에 플레이어가 한 명이라도 있다면 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559746355/98CA1BDA3D617C3D4D876B1A4170A3274CF6DE3B/"] = "플레이어가 물 지형이 있는 구역에서 턴을 시작할 때 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2452852111559740769/85B163EF2C8F02CED3E55C3B71C2E29E4C50FC03/"] = "플레이어가 후면 구역에서 턴을 시작할 때 발동합니다." ,
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797939246/E37B30E0FCE7C2E26C24DA2E52FB8BAA97314F9B/"] = "플레이어가 손패를 비웠거나 플레이어가 시퀸스에서 회피 (초록) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797926049/899D5957BD9DA1D22EC1DA735B27DFDE776247B9/"] = "플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 정면 구역에서 턴을 시작할 때 발동합니다..",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782313707938763/A35216A32C62594408CE625CF00091A6A6C333A2/"] = "플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 손패를 비운 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782948727284265/F26FC15B3213217809FA164E50B91C113511F0AA/"] = "플레이어가 위협 상태가 되었거나 플레이어가 측면 구역에서 턴을 시작할 때 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797932158/3BBF71B0FB754355A0B19FD5071CD12A4976B806/"] = "플레이어가 위협 상태가 되었거나 플레이어가 후면 구역에서 턴을 시작할 때 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782313707940714/FE3F3F0C8FED4C16936FBEC687331AB3155A0C1B/"] = "플레이어가 위협 상태가 되었거나 플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797947019/F968EA586683C55CB46A1B893F8C4E0A99DB7ED4/"] = "플레이어의 행동 단계가 끝날 때 공격(빨강) 카드가 시퀸스에 있는 경우 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039798556808/DE98B5A807CDBEDE7268489F04B7688263909B39/"] = "플레이어가 시퀸스에서 공격(빨강) 카드를 두장 연속으로 플레이한 후 발동합니다.",
  ["https://steamusercontent-a.akamaihd.net/ugc/2452852111559744720/907FB13C73B2FC99684AC4CD91DF9337AFE5A288/"] = "플레이어가 위협 상태가 된 후 발동합니다.",
  ["Question"] = "행동 카드가 비어 있습니다. 행동 카드가 있는 경우 해당 행동 카드의 발동 조건이 표시됩니다.",
}

levelsTag = {
	["0"] = "_p",
	["1"] = "_1",
	["2"] = "_2",
	["3"] = "_3",
}

featuresData = {
  {
    actor_tag = "actor_board",
    type = "board",
    		position = {20.99, 0.95, 11.05},
    		rotation = {0, 180, 0},
    		locked = true,
  },{
    actor_tag = "actor_board2",
    type = "board2",
    position = {32.15, 1.2, 11.10},
    rotation = {0, 180, 0},
    locked = true
  },
  {
    actor_tag = "actor_mini",
    type = "mini",
    position = {-1.52, 0.88, 10.38},
    rotation = {0.00, 135.00, 0.00}
  },
  {
    actor_tag = "actor_hard",
    type = "spawn",
    position = {23.80, 4, 13.13},
    rotation = {0.00, 226.21, 180.00}
  },
  {
    actor_tag = "actor_vibration",
    type = "spawn",
    position = {23.80, 4, 13.13},
    rotation = {0.00, 136.21, 180.00}
  },
  {
    actor_tag = "actor_nightmare",
    type = "spawn",
    position = {27.92, 0.69, 3.86}
  },
  {
    actor_tag = "actor_stand",
    type = "spawn",
    position = {0, 1.9, 27.71}
  },
  {
    actor_tag = "actor_debility",
    type = "spawn",
    position = {31.60, 0.89, 3.70},
    rotation = {0, 180, 180}
  },
  {
    actor_tag = "actor_blast",
    type = "spawn",
    position = {31.17, 1.45, 14.05},
    rotation = {0.00, 134.97, 0.00}
  },
  {
    actor_tag = "actor_objective",
    type = "spawn",
    position = {24.68, 1.2, 6.46},
    rotation = {0.00, 180.00, 0.00}
  },
  {
    actor_tag = "actor_threat",
    type = "spawn",
    position = {20.97, 0.99, 6.44},
    rotation = {0.00, 180.00, 0.00}
  },
  {
    type = "stances",
    position = {17.31, 1.3, 6.47},
    rotation = {0.00, 180.00, 0.00}
  },
  {
    type = "behaviors",
    position = {13.9, 1.2, 10.41},
    rotation = {0, 180, 180}
  },
  {
    type = "attrition",
    position = {0,0,0},
    rotation = {0, 180, 180}
  },
  {
    type = "behavior_special",
  },
}

--current combat/Campaign Dictionnaries
ActivePlayer= {
	Blue   = {isActive = false, boardGUID = "8cbb53", color = "Blue",   button = "btn1", isDone = false},
	Green  = {isActive = false, boardGUID = "3954b5", color = "Green",  button = "btn2", isDone = false},
	Yellow = {isActive = false, boardGUID = "c38413", color = "Yellow", button = "btn3", isDone = false},
	Orange = {isActive = false, boardGUID = "2194d4", color = "Orange", button = "btn4", isDone = false},
	Red    = {isActive = false, boardGUID = "2f7792", color = "Red",    button = "btn5", isDone = false},
}

-- 색상 ↔ 버튼 ID 매핑
COLOR_TO_BUTTON = {
    Blue   = 'btn1',
    Green  = 'btn2',
    Yellow = 'btn3',
    Orange = 'btn4',
    Red    = 'btn5',
}

BUTTON_TO_COLOR = {
    btn1 = 'Blue',
    btn2 = 'Green',
    btn3 = 'Yellow',
    btn4 = 'Orange',
    btn5 = 'Red',
}

----- Search Bar for Rules / Glossary -----

function searchdone()
    res = Global.UI.getAttribute("searchfield", "text")
end

function FilterResult(player, value, id)
    local results = {}

	if value == "" or value == nil then
		results = {}
	else
		for _, entry in ipairs(Dictionnary) do
			local term = entry[1]

			if string.find(term:lower(), value:lower(), 1, true) then
				table.insert(results, entry)
				if #results > 4 then
					break
				end
			end
		end
	end

	for i=1,5,1 do
		if results[i] then
			Global.UI.setAttribute("result" .. i, "active" , true)
			Global.UI.setAttribute("result" .. i, "text" , results[i][1])
		else
			Global.UI.setAttribute("result" .. i, "active" , false)
			Global.UI.setAttribute("result" .. i, "text" , "")
		end
	end
end

--- player setup ---

function SetActivePlayer(pColor)
    ActivePlayer[pColor].isActive = true
	StartTurnUI()
end


--- monster setups related functions

function CleanMonster()
	MonsterData = {}
	CurrentMonster= ""
	FightLevel = "0"
	CurrentRound = 0

  local objs = getAllObjects()
  for i,v in ipairs(objs) do
    if v.hasTag("monster_spawn") then
      v.destruct()
    end
  end

    for _, guid in ipairs(CombatBoardGUIDs) do
        local board = getObjectFromGUID(guid)
        if board then
            board.call("ResetTimer")
        end
    end
end

function SetupMonster(params)
    local nb = getPlayersNb()
    getObjectFromGUID(MonsterBookGUID).call("setPlayers",nb)

    CurrentMonster = params[1]
    FightLevel= params[2]
    explevel = params[3] or ""
    questlevel = params[4] or ""
    isNightmare = params[5] or false

    myparams = {CurrentMonster,	FightLevel,explevel,questlevel,isNightmare}

    SpawnMonster(myparams)
end

function SpawnMonster(params)
    local wantedname = params[1]
    local currentLevel = params[2]
    local MonsterBook = getObjectFromGUID(MonsterBookGUID)

			MonsterBook.takeObject({smooth = false,position={100,100,100},
        callback_function= function(MainBag)
            MainBag.setLock(true)
            for _,mbag in pairs(MainBag.getObjects()) do
                if mbag.name == wantedname then
                    MainBag.takeObject({guid = mbag.guid, position={27.13, 0.57, 16.99},
                        smooth = false,
                        callback_function= function(storebag)
                            storebag.addTag("monster_spawn")
							spawnMonsterFromBag(storebag, tonumber(currentLevel), params)
                            SetMonsterData(params, storebag)
                        end
                    })
                    break
                end
            end

            MainBag.destruct()
        end
    })

   UpdateRoundState(1)

    local infinityBag = getObjectFromGUID("f814f5")
    if infinityBag then
        infinityBag.takeObject({
            position = {26.05, 1.15, 14.04},
            rotation = {0, 135, 0},
            smooth = false
        })
    end

    local attrBag = getObjectFromGUID("3d7a5b")
    if attrBag then
        attrBag.takeObject({
            position = {13.05, 0.92, 3.08},
            rotation = {0, 180, 180},
            smooth = false,
            callback_function = function(obj)
                obj.shuffle()
            end
        })
    end
end

function SetMonsterData(params, storebag)
	local AllData = getObjectFromGUID(MonsterBookGUID).getTable("Data")
    MonsterData = AllData["Monsters"][params[1]]

	local level = params[2]
	local ExpeditionType = params[3] or ""
	local QuestNumber = params[4] or ""
	local isNightmare =  params[5] or false

    if ExpeditionType ~= "" then
		if MonsterData[ExpeditionType]["Terrain"] then
			for i, terrain in pairs(MonsterData[ExpeditionType]["Terrain"]) do
				Wait.time(function() addTerrainInZone(terrain) end, i)
			end
		end

        if MonsterData[ExpeditionType]["Ballistas"] and storebag then
            local bBagData = getObjectDataByTag(storebag, "Ballista")
            if not bBagData then bBagData = getObjectDataByTag(storebag, "Ballist") end

            if bBagData then
                storebag.takeObject({
                    guid = bBagData.guid,
                    position = {32.0, 1.2, 16.0},
                    smooth = false,
                    callback_function = function(infBag)
                        infBag.addTag("monster_spawn")
                        infBag.setLock(true)

                        for _, bData in pairs(MonsterData[ExpeditionType]["Ballistas"]) do
                            infBag.takeObject({
                                position = bData.pos,
                                rotation = bData.rot,
                                smooth = false,
                                callback_function = function(obj)
                                    obj.addTag("monster_spawn")
                                end
                            })
                        end
                    end
                })
            else
                broadcastToAll("System Error: 어웨이큰 가방 안에 'Ballista' 태그를 가진 무한 주머니가 없습니다.", Color.Red)
            end
        end
	else
		local QuestData = AllData["Quests"][tostring(QuestNumber)]

		for i, terrain in pairs(QuestData["Terrain"]) do
			Wait.time(function() addTerrainInZone(terrain) end, i)
		end
	end

    if params[1] == "Awakened" and storebag then
        storebag.takeObject({
            guid = "5caaef",
            position = {32.17, 1.41, 10.48},
            rotation = {0.0, 179.99, 180.0},
            smooth = false,
            callback_function = function(obj) obj.addTag("monster_spawn") end
        })
        storebag.takeObject({
            guid = "b950e8",
            position = {35.82, 1.41, 10.47},
            rotation = {0.0, 179.99, 180.0},
            smooth = false,
            callback_function = function(obj) obj.addTag("monster_spawn") end
        })
    end
end

function flipSpawnObject(obj)
    if obj == nil then
        return
    end

    if obj.type == "Card" then
        obj.flip()
        return
    end

    if obj.type ~= "Deck" then
        return
    end

    local cards = obj.getObjects()
    local total = #cards

    if total == 0 then
        return
    end

    local pos = obj.getPosition()
    local rot = obj.getRotation()

    local gap = 3
    local order = 1

    local function takeNext()
        local currentCards = obj.getObjects()
        local count = #currentCards

        if count == 2 then
            local cardInfo = currentCards[1]
            local lastCard = nil

            obj.takeObject({
                index = cardInfo.index,
                position = {
                    pos[1],
                    pos[2] + gap * (order - 1),
                    pos[3]
                },
                rotation = rot,
                smooth = false,
                callback_function = function(card)
                    card.addTag("monster_spawn")
                    card.flip()

                    order = order + 1

                    if lastCard ~= nil then
                        lastCard.addTag("monster_spawn")
                        lastCard.setPosition({
                            pos[1],
                            pos[2] + gap * (order - 1),
                            pos[3]
                        })
                        lastCard.setRotation(rot)
                        lastCard.flip()
                    else
                        print("flipSpawnObject: remainder is nil")
                    end
                end
            })

            lastCard = obj.remainder
            return
        end

        if count > 2 then
            local cardInfo = currentCards[1]

            obj.takeObject({
                index = cardInfo.index,
                position = {
                    pos[1],
                    pos[2] + gap * (order - 1),
                    pos[3]
                },
                rotation = rot,
                smooth = false,
                callback_function = function(card)
                    card.addTag("monster_spawn")
                    card.flip()

                    order = order + 1
                    takeNext()
                end
            })
        end
    end

    takeNext()
end

function spawnMonsterFromBag(bag, level, params)
    for i,data in ipairs(featuresData) do
		if data.type == "mini" then
            spawnMiniFromBag(data, bag)
        elseif data.type == "board" then
            spawnActorFromBag(data, bag)
        elseif data.type == "board2" then
			spawnActorFromBag(data, bag)
        elseif data.type == "spawn" then
          local monsterName = params and params[1] or nil

          local needFlipSetup =
            (data.actor_tag == "actor_objective" or data.actor_tag == "actor_threat")
            and level == 3
            and monsterName ~= "Awakened"

            if needFlipSetup then
              spawnActorFromBag(data, bag, function(obj)
              flipSpawnObject(obj)
            end)
            else
              spawnActorFromBag(data, bag)
            end
        elseif data.type == "stances" then
            spawnStance(data, bag, level)
        elseif data.type == "behaviors" then
            spawnBehaviors(data, bag, level)
        elseif data.type == "attrition" then
            spawnAttrition(data, bag, level)
        elseif data.type == "behavior_special" then
            spawnSpecBehavior(data, bag, level)
        end
    end
end

function spawnMiniFromBag(actorData, bag)
	local objectData = getObjectDataByTag(bag, actorData.actor_tag, actorData.OtherTag)
	if objectData == nil then
		return
	end
	local rot = nil

	if objectData.gm_notes and objectData.gm_notes ~= "" then
		rot = tonumber(objectData.gm_notes)
	end

	local lrotation = actorData.rotation or {0, 0, 0}
	if rot ~= nil then
		lrotation = {0, rot, 0}
	end
  bag.takeObject({
    position = actorData.position,
    rotation = lrotation,
    smooth = false,
    guid = objectData.guid,
    callback_function = function(actor)
      actor.addTag("monster_spawn")
      if actorData.locked then
        actor.setLock(actorData.locked)
      end
    end
  })
end

function spawnSpecBehavior(data, bag, level)
  local objectData = getObjectDataByTag(bag, "actor_behavior_special_1")
  local object2Data = getObjectDataByTag(bag, "actor_behavior_special_2")

    if objectData ~= nil then
  bag.takeObject({
    position = getSnapPos("actor_behavior_special_1"),
    rotation = {0, 0, 0},
    smooth = false,
    guid = objectData.guid,
    callback_function = function(actor)
      actor.addTag("monster_spawn")
    end
  })
    end

     if object2Data ~= nil then
  bag.takeObject({
    position = getSnapPos("actor_behavior_special_2"),
    rotation = {0, 0, 0},
    smooth = false,
    guid = object2Data.guid,
    callback_function = function(actor)
      actor.addTag("monster_spawn")
    end
  })
    end
end

function spawnAttrition(featureData, bag, level)
	local attpos = getWorldPosOfSnapOnObj({"a323b1", "actor_attrition"})
	local actorData = {
    position = attpos,
    rotation = featureData.rotation,
    actor_tag = "actor_attrition",
  }

  spawnActorFromBag(actorData, bag, function(actor)
	actor.shuffle()
  end)
end

function spawnBehaviors(featureData, bag, level)
	spawnActorFromBag(
	{
		position = featureData.position,
		rotation = featureData.rotation,
		actor_tag = "actor_behavior",
		OtherTag = levelsTag[tostring(level)],
	}
	, bag
	, function(deck)
		deck.shuffle()

		for _, zoneGUID in pairs(ZoneBehave) do
			local zpos = getObjectFromGUID(zoneGUID).getPosition()
			zpos[2] = zpos[2]+4
			deck.takeObject({smooth = false, position = zpos})
		end
	end
	)
end

function spawnStance(featureData, bag, level)
  local actorData = {
    position = featureData.position,
    rotation = featureData.rotation,
    actor_tag = "actor_stance",
    	OtherTag = levelsTag[tostring(level)],
  }

  spawnActorFromBag(actorData, bag, function(actor)
    Wait.time(function() OnStateChange(actor.getStateId()) end, 1)
  end)
end

function spawnActorFromBag(actorData, bag, callback)
  local objectData = getObjectDataByTag(bag, actorData.actor_tag, actorData.OtherTag)
  if objectData == nil then
    return
  end

  bag.takeObject({
    position = actorData.position,
    rotation = actorData.rotation or {0, 0, 0},
    smooth = false,
    guid = objectData.guid,
    callback_function = function(actor)
      actor.addTag("monster_spawn")
      if actorData.locked then
        Wait.time(function() actor.setLock(true) end, 5)
      end
      if callback ~= nil then
        callback(actor)
      end
    end
  })
end

function getObjectDataByTag(bag, tag, otherTag)
	local other = otherTag or false
	local data = bag.getObjects()
	local maybe = ""

	for i,v in ipairs(data) do
		for _, t in ipairs(v.tags) do
			if t == tag then
				if other then
					maybe = v
					for c,tagtwo in ipairs(maybe.tags) do
						if tagtwo == other then
							return v
						end
					end
				else
					return v
				end
			end
		end
	end
end


----- utility fonction -----

local lastClickTime = 0

function NextRound()
    if os.clock() - lastClickTime < 0.2 then return end
    lastClickTime = os.clock()

    local activeBoard = nil
    local currentPos = 0

    for _, guid in ipairs(CombatBoardGUIDs) do
        local b = getObjectFromGUID(guid)
        if b then
            activeBoard = b
            currentPos = b.getVar("RoundNumber") or CurrentRound
            break
        end
    end

    UpdateRoundState(currentPos + 1)
    SetFirstPlayerToAggro()
    ProcessFireTokens()
    ProcessDustTokens()
    ProcessMonsterStatusTokens()
    clearAllTurnEndDecals()
end

function UpdateRoundState(round)
    CurrentRound = round
    if CurrentRound > 10 then CurrentRound = 1 end

    for _, guid in ipairs(CombatBoardGUIDs) do
        local board = getObjectFromGUID(guid)
        if board then
            board.call("SetRound", CurrentRound)
        end
    end

    for i=1, 5 do
        Global.UI.setAttribute("btn" .. i, "color", "white")
    end

    local tokens = getObjectsWithTag("ON_OFF_Token")
    for _, token in ipairs(tokens) do
        if token.is_face_down then
            token.flip()
        end
    end

    CheckMonsterStanceAutomation()
end

function CheckMonsterStanceAutomation()
    if CurrentMonster == "Taraska" and CurrentRound == 2 then
        for _, obj in ipairs(getObjectsWithTag("actor_stance")) do
            if obj.getStateId() == 1 then
                obj.setState(2)
            end
        end
    end
end

function ProcessFireTokens()
    -- 불 토큰 가능한 태그들
    local possibleTags = {"Fire", "fire", "불", "Burned", "burned", "bag_fire", "FireToken", "fire_token"}
    local foundTokens = {}

    for _, tag in ipairs(possibleTags) do
        for _, t in ipairs(getObjectsWithTag(tag)) do
            foundTokens[t.getGUID()] = t
        end
    end

    if next(foundTokens) == nil then return end

    local tokensToFlip = {}
    local tokensToDestroy = {}

    for _, token in pairs(foundTokens) do
        local tokenPos = token.getPosition()
        local hits = Physics.cast({
            origin = {tokenPos.x, tokenPos.y + 0.5, tokenPos.z},
            direction = {0, -1, 0},
            type = 1,
            max_distance = 10
        })

        local onBoard = false
        for _, hit in ipairs(hits) do
            if hit.hit_object and hit.hit_object.getGUID() == GetCombatBoardGUID() then
                onBoard = true
                break
            end
        end

        if onBoard then
            if token.is_face_down then
                table.insert(tokensToDestroy, token)
            else
                table.insert(tokensToFlip, token)
            end
        end
    end

    for _, token in ipairs(tokensToFlip) do token.flip() end
    for _, token in ipairs(tokensToDestroy) do token.destruct() end

    if #tokensToFlip > 0 or #tokensToDestroy > 0 then
        print(string.format("불 토큰 처리: %d개 뒤집기, %d개 삭제",
            #tokensToFlip, #tokensToDestroy))
    end
end

function ProcessDustTokens()
    local dustTokens = getObjectsWithTag("Dust")
    if #dustTokens == 0 then return end

    local tokensToDestroy = {}

    for _, token in ipairs(dustTokens) do
        local tokenPos = token.getPosition()
        local hits = Physics.cast({
            origin = {tokenPos.x, tokenPos.y + 0.5, tokenPos.z},
            direction = {0, -1, 0},
            type = 1,
            max_distance = 10
        })

        local onBoard = false
        for _, hit in ipairs(hits) do
            if hit.hit_object and hit.hit_object.getGUID() == GetCombatBoardGUID() then
                onBoard = true
                break
            end
        end

        if onBoard then
            table.insert(tokensToDestroy, token)
        end
    end

    for _, token in ipairs(tokensToDestroy) do token.destruct() end

    if #tokensToDestroy > 0 then
        print(string.format("Dust 토큰 처리: %d개 삭제", #tokensToDestroy))
    end
end

function ProcessMonsterStatusTokens()
    local monsterBoardGUID = "fa932e"
    local tagsToRemove = {"Vulnerable", "Confused", "Stunned", "Monster_Bonus_Damage"}

    local foundTokens = {}
    for _, tag in ipairs(tagsToRemove) do
        for _, t in ipairs(getObjectsWithTag(tag)) do
            foundTokens[t.getGUID()] = t
        end
    end

    if next(foundTokens) == nil then return end

    local tokensToDestroy = {}

    for _, token in pairs(foundTokens) do
        local tokenPos = token.getPosition()
        local hits = Physics.cast({
            origin = {tokenPos.x, tokenPos.y + 0.5, tokenPos.z},
            direction = {0, -1, 0},
            type = 1,
            max_distance = 10
        })

        local onBoard = false
        for _, hit in ipairs(hits) do
            if hit.hit_object and hit.hit_object.getGUID() == monsterBoardGUID then
                onBoard = true
                break
            end
        end

        if onBoard then
            table.insert(tokensToDestroy, token)
        end
    end

    for _, token in ipairs(tokensToDestroy) do token.destruct() end

    if #tokensToDestroy > 0 then
        print(string.format("몬스터 보드 상태이상 토큰 처리: %d개 삭제", #tokensToDestroy))
    end
end

function addTerrainInZone(params)
    for _,zonesnap in pairs(Terrains[params[2]]) do
        local pos = getWorldPosOfSnapOnObj({GetCombatBoardGUID(), zonesnap})
		local isEmpty = true
		local objs = GetObjOnPos({pos})

		for _, obj in pairs(objs) do
			if obj.hit_object.getLock() then
				-- ignore
			else
				isEmpty = false
				break
			end
		end

        if isEmpty then
			addTokensOnPos(1, params[1], pos)
			break
        end
    end
end

function OnRotateButtonClick(player, value, id)
    -- 클릭 피드백: 글씨를 어둡게
    Global.UI.setAttribute("rotateMonsterBtn", "textColor", "#888888")

    -- 실제 회전 실행
    RotateMonsterToAggro()

    -- 잠시 후 글씨 원래 색으로 복원
    Wait.time(function()
        Global.UI.setAttribute("rotateMonsterBtn", "textColor", "#ffffff")
    end, 0.15)
end

function RotateMonsterToAggro()
    local aggroColor = nil
    for color, _ in pairs(ActivePlayer) do
        local img = Global.UI.getAttribute("aggro_" .. color, "image")
        if img == URL_AGGRO_ON then aggroColor = color; break end
    end
    if aggroColor == nil then return end

    local figures = getObjectsWithTag("owner_" .. aggroColor)
    local playerFig = nil
    local activeBoardGUID = nil

    -- 어그로 플레이어 피규어가 어떤 보드 위에 있는지 탐색
    for _, guid in ipairs(CombatBoardGUIDs) do
        local combatBoard = getObjectFromGUID(guid)
        if combatBoard then
            local boardPos = combatBoard.getPosition()
            local boardBounds = combatBoard.getBounds()
            local halfX = boardBounds.size.x / 2
            local halfZ = boardBounds.size.z / 2

            for _, fig in ipairs(figures) do
                if fig.hasTag("actor_mini") then
                    local p = fig.getPosition()
                    if math.abs(p.x - boardPos.x) < halfX and math.abs(p.z - boardPos.z) < halfZ then
                        playerFig = fig
                        activeBoardGUID = guid
                        break
                    end
                end
            end

            if not playerFig then
                for _, fig in ipairs(figures) do
                    local p = fig.getPosition()
                    if math.abs(p.x - boardPos.x) < halfX and math.abs(p.z - boardPos.z) < halfZ then
                        playerFig = fig
                        activeBoardGUID = guid
                        break
                    end
                end
            end

            if playerFig and activeBoardGUID then break end
        end
    end

    if not playerFig or not activeBoardGUID then return end

    local figPos = playerFig.getPosition()
    local closestZone = nil; local closestDist = math.huge
    for zoneName, snapTags in pairs(Terrains) do
        for _, snapTag in ipairs(snapTags) do
            -- 발견된 보드(activeBoardGUID)를 기준으로 스냅 포인트 탐색
            local snapPos = getWorldPosOfSnapOnObj({activeBoardGUID, snapTag})
            if snapPos then
                local dx = figPos.x - snapPos.x; local dz = figPos.z - snapPos.z
                local dist = dx*dx + dz*dz
                if dist < closestDist then closestDist = dist; closestZone = zoneName end
            end
        end
    end
    if not closestZone then return end

    local monsterCase = nil
    for caseName, monsterList in pairs(MonsterCases) do
        for _, name in ipairs(monsterList) do
            if name == CurrentMonster then monsterCase = caseName; break end
        end
        if monsterCase then break end
    end
    if not monsterCase then monsterCase = MONSTER_DEFAULT_CASE end
    local cfg = MonsterRotationCases[monsterCase]
    if not cfg then return end
    local targetRotY = cfg[closestZone]

    -- 발견된 보드(activeBoardGUID)를 기준으로 몬스터 탐색
    local monsterPos = getWorldPosOfSnapOnObj({activeBoardGUID, "actor_mini"})
    if not monsterPos then return end
    local monster = GetObjOnPos({monsterPos, CurrentMonster})
    if not monster then return end

    local currentRot = monster.getRotation()
    monster.setRotationSmooth({currentRot.x, targetRotY, currentRot.z}, false, false)

    broadcastToAll(
        string.format("몬스터가 (%s)(%s) 을 향해 회전하였습니다.", aggroColor, playerFig.getName()),
        Color[aggroColor]
    )
end

function getCampaignLevel()
	lvl = getObjectFromGUID(CampaignSheetGUID).call("getLevel")
    return lvl
end

function addStruggle(nbr)
    local nb = getPlayersNb()
    if type(nbr) == "string" then
        if nbr == "nbr" then nbr = nb
        elseif nbr == "nbr-1" then nbr = math.max(0, nb - 1)
        else nbr = tonumber(nbr) or 1 end
    end
    if not nbr then nbr = 1 end
	addTokensInGrid(nbr, "bag_struggle", allZone.StruggleData.zoneGUID, "Struggle")
    ScheduleCheckEruption()
end

function addAccel(nbr)
    addTokensInGrid(nbr or 1, "bag_accel", allZone.AccelData.zoneGUID, "Accel")
end

-- 하위 호환용 별칭 (기존에 addAcceleration 을 호출하던 코드가 있을 수 있음)
function addAcceleration(nbr)
    addAccel(nbr)
end

function addTokensInGrid(nbr, bagTag, zoneGUID, tokenTag)
    local zone = getObjectFromGUID(zoneGUID)
    local bag = getObjectsWithTag(bagTag)[1]
    if not bag or not zone then
        broadcastToAll('Error: Missing bag (' .. bagTag .. ') or zone (' .. zoneGUID .. ')', Color.Red)
        return
    end

    local existingTokens = {}
    for _, obj in ipairs(zone.getObjects()) do
        if obj.hasTag(tokenTag) then
            table.insert(existingTokens, obj)
        end
    end

    local count = #existingTokens
    local rowSize = 5
    local maxRows = 2
    local layerSize = rowSize * maxRows
    local spacing = 0.6

    local basePos = zone.getPosition()
    local rotY = zone.getRotation().y

    for i = 1, nbr do
        local currentCount = count + i - 1
        local layer = math.floor(currentCount / layerSize)
        local indexInLayer = currentCount % layerSize

        local col = indexInLayer % rowSize
        local row = math.floor(indexInLayer / rowSize)

        local xOffset = (col - (rowSize - 1) / 2) * spacing
        local zOffset = (0.5 - row) * spacing

        local yOffset = 0.4 + (layer * 0.2)

        local offset = Vector(xOffset, yOffset, zOffset)
        offset:rotateOver('y', rotY)
        local worldPos = basePos + offset

        bag.takeObject({
            position = worldPos,
            rotation = {0, 180, 0},
            smooth = false
        })
    end
end

function removeStruggle()
    return removeLastTokenInGrid(allZone.StruggleData.zoneGUID, "Struggle")
end

function removeAccel()
    return removeLastTokenInGrid(allZone.AccelData.zoneGUID, "Accel")
end

function getStruggleCount()
    local zone = getObjectFromGUID(allZone.StruggleData.zoneGUID)
    local count = 0
    if zone then
        for _, obj in ipairs(zone.getObjects()) do
            if obj.hasTag("Struggle") then count = count + 1 end
        end
    end
    return count
end

function getAccelCount()
    local zone = getObjectFromGUID(allZone.AccelData.zoneGUID)
    local count = 0
    if zone then
        for _, obj in ipairs(zone.getObjects()) do
            if obj.hasTag("Accel") then count = count + 1 end
        end
    end
    return count
end

-- addTokensInGrid 가 놓는 순서(왼위→오위→왼아래→오아래→다음 레이어)의 역순으로
-- 가장 마지막에 놓인 토큰 하나만 제거한다.
function removeLastTokenInGrid(zoneGUID, tokenTag)
    local zone = getObjectFromGUID(zoneGUID)
    if not zone then return false end

    local basePos = zone.getPosition()
    local rotY = zone.getRotation().y

    local tokens = {}
    for _, tok in pairs(zone.getObjects()) do
        if tok.hasTag(tokenTag) then
            local p = tok.getPosition()
            local off = Vector(p.x - basePos.x, p.y - basePos.y, p.z - basePos.z)
            off:rotateOver('y', -rotY)
            table.insert(tokens, {obj = tok, x = off.x, y = off.y, z = off.z})
        end
    end

    if #tokens == 0 then return false end

    -- 우선순위: 위층(y 큼) → 아래 줄(z 작음) → 오른쪽 칸(x 큼)
    table.sort(tokens, function(a, b)
        if math.abs(a.y - b.y) > 0.05 then return a.y > b.y end
        if math.abs(a.z - b.z) > 0.05 then return a.z < b.z end
        return a.x > b.x
    end)

    tokens[1].obj.destruct()
    return true
end

function addTokensOnPos(nbr, tokenbagtag, tokenpos)
	local tokenBags = getObjectsWithTag(tokenbagtag)
	if #tokenBags ~= 1 then
		broadcastToAll('Error : Missing bag or duplicate tag for ' .. tokenbagtag .. '.', Color.Red)
		return
	end

	for x=1, nbr, 1 do
		tokenBags[1].takeObject({position = tokenpos, smooth = false})
	end
end

function getPlayersNb()
    local nb = 0
    if not ActivePlayer then return nb end

    for _, aplayer in pairs(ActivePlayer) do
        local targetTag = "owner_" .. aplayer.color
        local objs = getObjectsWithTag(targetTag)

        local hasCharacter = false
        local board = getObjectFromGUID(aplayer.boardGUID)

        -- 보드 기준 x좌표 ±9 이내에 자기 소유권 오브젝트가 하나라도 있는지 확인
        if board and #objs > 0 then
            local bp = board.getPosition()
            for _, obj in ipairs(objs) do
                local op = obj.getPosition()
                if math.abs(op.x - bp.x) < 9 then
                    hasCharacter = true
                    break
                end
            end
        end

        -- [수정] 착석 여부(seated)는 무시하고, 오직 기물이 보드에 꺼내져 있는지(hasCharacter)만 확인
        if hasCharacter then
            nb = nb + 1
        end
    end

    return nb
end

function getWorldPosOfSnapOnObj(params)
    obj = getObjectFromGUID(params[1])

    if obj then
        for _, s in pairs(obj.getSnapPoints()) do
            for _, tag in pairs(s.tags) do
                if tag == params[2] then
                    return obj.positionToWorld(s.position)
                end
            end
        end
    end

    for _, s in pairs(Global.getSnapPoints()) do
        for _, tag in pairs(s.tags) do
            if tag == params[2] then
                return s.position
            end
        end
    end
end

function getAllSnapPos(t)
	local snaps ={}
	for _, s in pairs(Global.getSnapPoints()) do
		for _, tag in pairs(s.tags) do
            if string.lower(tag) == string.lower(t) then
                table.insert(snaps, s.position)
            end
        end
    end
	return snaps
end

function getSnapPos(t)
	for _, s in pairs(Global.getSnapPoints()) do
		for _, tag in pairs(s.tags) do
            if string.lower(tag) == string.lower(t) then
                return s.position
            end
        end
    end
end

function GetAllObjOnSnap(t)
    local olist = {}
    for _, pos in pairs(getAllSnapPos(t)) do
        table.insert(olist, {pos, GetObjOnPos({pos})})
    end
    return olist
end

function GetObjOnPos(params)
	if params then
        local objname = params[2] or "nil"
        local center = params[1]

        center.y = center.y + 10
		objs = Physics.cast({	origin = center,		direction = { x = 0, y = -1, z = 0 },		type= 1,	})

		 if objname~= "nil" then
			for _, obj in pairs(objs) do
				if obj.hit_object.getName() == objname then
                    return obj.hit_object
                end
			end
		else
			return objs
        end
	end

	return false
end


--- game load / save_state

function onLoad(script_state)
  -- [과거 세이브 버그 청소용] 굳어버린 UI 물리적 잠금을 강제로 영구 해제합니다.
  Global.UI.setAttribute("monsterUpkeepBtn", "color", "#FFFFFF")

  MusicPlayer.playlistIndex = -1
  MusicPlayer.setPlaylist({})
  megaFreeze()

  if MonsterUIOffsets then
      for guid, _ in pairs(MonsterUIOffsets) do
          local obj = getObjectFromGUID(guid)
          if obj then fixMonsterUI(obj) end
      end
  end

  if disableSave==true then script_state="" end
    if script_state ~= "" then
        local loaded_data = JSON.decode(script_state)
        ActivePlayer = loaded_data.ActivePlayer
        
        -- 세이브 파일에 옛날 GUID가 남아있을 수 있으므로 최신 GUID로 덮어씁니다.
        if not ActivePlayer then ActivePlayer = {} end
        local default_boards = {
            Blue   = {boardGUID = "8cbb53", button = "btn1"},
            Green  = {boardGUID = "3954b5", button = "btn2"},
            Yellow = {boardGUID = "c38413", button = "btn3"},
            Orange = {boardGUID = "2194d4", button = "btn4"},
            Red    = {boardGUID = "2f7792", button = "btn5"}
        }
        for color, data in pairs(default_boards) do
            if not ActivePlayer[color] then
                ActivePlayer[color] = {isActive = false, boardGUID = data.boardGUID, color = color, button = data.button, isDone = false}
            else
                ActivePlayer[color].boardGUID = data.boardGUID
                ActivePlayer[color].button = data.button
            end
        end

        CurrentMonster = loaded_data.CurrentMonster
        CurrentRound = loaded_data.CurrentRound
        FightLevel = loaded_data.FightLevel
        MonsterData = loaded_data.MonsterData
    else
        ActivePlayer= {
            Blue   = {isActive = false, boardGUID = "8cbb53", color = "Blue",   button = "btn1", isDone = false},
            Green  = {isActive = false, boardGUID = "3954b5", color = "Green",  button = "btn2", isDone = false},
            Yellow = {isActive = false, boardGUID = "c38413", color = "Yellow", button = "btn3", isDone = false},
            Orange = {isActive = false, boardGUID = "2194d4", color = "Orange", button = "btn4", isDone = false},
            Red    = {isActive = false, boardGUID = "2f7792", color = "Red",    button = "btn5", isDone = false},
        }
        CurrentMonster= "Vyraxen"
        CurrentRound = 0
        FightLevel = "0"
        MonsterData = {	}
    end

	SetBehavior()
    StartTurnUI()
end

function megaFreeze()
    local megaFreezeIT = {'dff000','095652'}

	for i=1, #megaFreezeIT, 1 do
		local obj = getObjectFromGUID(megaFreezeIT[i])
		if obj ~= nil then
			obj.interactable = false
			obj.tooltip = false
		end
	end
 end

function onSave()
    saved_data = JSON.encode({ActivePlayer = ActivePlayer, CurrentMonster = CurrentMonster,CurrentRound=CurrentRound,FightLevel=FightLevel,MonsterData=MonsterData})
    if disableSave==true then saved_data="" end
    self.script_state = saved_data
	return saved_data
end

function SetBehavior()
	for i,zGUID in pairs({"f1a17b","08c643","e76a94"}) do
		local zone = getObjectFromGUID(zGUID)
		for _, obj in pairs(zone.getObjects()) do
			if obj.hasTag("actor_behavior") then
				local img = obj.getVar("TokenImg")
				Global.UI.setAttribute("behave"..i, "image", img )
				Global.UI.setAttribute("behave"..i, "tooltip", BehaviorDescription[img])

				for _, p in pairs(ActivePlayer) do
					local board = getObjectFromGUID(p.boardGUID)
					if board then
						board.UI.setAttribute("behave"..i, "image", img )
					end
				end
			end
		end
	end
end


 ---events handling----
 function onObjectStateChange(object, old_state_guid)
    if object.hasTag("actor_stance") then
        OnStateChange(object.getStateId())
    end
end

local lastStateChangeTime = 0
local lastStateId = -1

function OnStateChange(StateId)
    local currentTime = os.clock()
    if StateId == lastStateId and currentTime - lastStateChangeTime < 0.5 then
        return
    end
    lastStateChangeTime = currentTime
    lastStateId = StateId

        local stance = MonsterData["FightLevel"][tostring(FightLevel)]["Stances"][tostring(StateId)]

        local FigPos = getWorldPosOfSnapOnObj({GetCombatBoardGUID(), "actor_mini"})

        local actor = GetObjOnPos({FigPos, CurrentMonster})

	    for _,stpair in pairs(stance.Colors) do
            actor.UI.setAttribute(stpair[1],"color",tostring(stpair[2]))
        end
        broadcastToAll("\n스탠스를 변경할 때 필요하다면 위험 카드와 목표 카드도 함께 교체하십시오.", Color.Orange)
        if stance["onSetup"]["broadcast"] ~= "" then
              local msg = stance["onSetup"]["broadcast"]
              local nb = getPlayersNb()

              msg = msg:gsub("%[%[nbr%]%]", tostring(nb))
              msg = msg:gsub("%[%[nbr%-1%]%]", tostring(math.max(0, nb - 1)))

      		broadcastToAll(msg, {r=1, g=1, b=1})
      	end

		Wait.time(function()
		for _, stanceterrain in pairs(stance["onSetup"]["Terrain"]) do
			 addTerrainInZone(stanceterrain)
		end
		end, 1)

		Wait.time(function()
		for _, stanceAction in pairs(stance["onSetup"]["Actions"]) do
			 _G[stanceAction[1]](stanceAction[2] or nil)
		end
		end, 2)
end

function onObjectEnterZone(zone, object)
	local isUnique = true

	for i, data in pairs(allZone) do
		if (data.tag == "Struggle" or data.tag == "Accel") and data.zoneGUID == zone.guid then
			local count = #zone.getObjects()
			local text = getObjectFromGUID(data.textGUID)
			text.TextTool.setValue(tostring(count))
			 break
		elseif data.tag == "Behavior" and data.zoneGUID == zone.guid then
			for _,obj in pairs(zone.getObjects()) do
				if obj.hasTag("actor_behavior") then
					if object.guid == obj.guid then
					else
						isUnique = false
					end
				end
			end

			if isUnique then
				local img = object.getVar("TokenImg")
				Global.UI.setAttribute(data.UIname, "image", img )
				Global.UI.setAttribute(data.UIname, "tooltip", BehaviorDescription[img])

				for _, p in pairs(ActivePlayer) do
					local board = getObjectFromGUID(p.boardGUID)
					if board then
						board.UI.setAttribute(data.UIname, "image", img )
					end
				end
			end
			break
		end
	end
 end

function onObjectLeaveZone(zone, leave_object)
	local isUnique = true

	for i, data in pairs(allZone) do
		if (data.tag == "Struggle" or data.tag == "Accel") and data.zoneGUID == zone.guid then
			local count = #zone.getObjects()
			local text = getObjectFromGUID(data.textGUID)
			text.TextTool.setValue(tostring(count))
			break
		elseif data.tag =="Behavior" and data.zoneGUID == zone.guid then
			for _,obj in pairs(zone.getObjects()) do
				if obj.hasTag("actor_behavior") then
					if leave_object.guid == obj.guid then
					else
						isUnique = false
					end
				end
			end

			if isUnique then
				Global.UI.setAttribute(data.UIname, "image", "Question" )
				Global.UI.setAttribute(data.UIname, "tooltip", "Draft a new Behavior card" )
				for _, p in pairs(ActivePlayer) do
					local board = getObjectFromGUID(p.boardGUID)
					if board then
						board.UI.setAttribute(data.UIname, "image", "Question" )
					end
				end
			end
			break
		end
	end
 end


 ---ui stuff---

-- 본인 보드 근처 x±9 유닛 이내에 owner 태그 오브젝트가 있을 때만 행 표시
function StartTurnUI()
    if not ActivePlayer then return end
    for i, aplayer in pairs(ActivePlayer) do
        local targetTag = "owner_" .. aplayer.color
        local objs = getObjectsWithTag(targetTag)

        local hasCharacter = false
        local board = getObjectFromGUID(aplayer.boardGUID)
        if board and #objs > 0 then
            local bp = board.getPosition()
            for _, obj in ipairs(objs) do
                local op = obj.getPosition()
                if math.abs(op.x - bp.x) < 9 then
                    hasCharacter = true
                    break
                end
            end
        end

        local isActive = hasCharacter

        if isActive then
            Global.UI.show(aplayer.button .. "_row")
        else
            Global.UI.hide(aplayer.button .. "_row")
        end
    end
end

function onPlayerChangeColor(player_color)
    Wait.time(function()
        StartTurnUI()
        local monsterBoard = getObjectFromGUID("fa932e")
        if monsterBoard then
            monsterBoard.call("updateMonsterToughnessFromActorStance")
        end
    end, 0.1)
end

function SetAggroTarget(targetColor)
    for color, aplayer in pairs(ActivePlayer) do
        local isTarget = (color == targetColor)
        local imgURL = isTarget and URL_AGGRO_ON or URL_AGGRO_OFF

        Global.UI.setAttribute("aggro_" .. color, "image", imgURL)

        local boardObj = getObjectFromGUID(aplayer.boardGUID)
        if boardObj then
            if isTarget then
                boardObj.call("enableAggro", true)
            else
                boardObj.call("disableAggro")
            end
        end
    end
end

-- UI에서 어그로 아이콘을 클릭했을 때 호출되는 함수
function ClickAggroIcon(player, value, id)
    local color = id:gsub("aggro_", "")
    SetAggroTarget(color)

    local playerName = Player[color].steam_name
    if playerName then
        broadcastToAll(playerName .. ' (' .. color .. ') has drawn aggro!', Color[color] or {1, 1, 1})
    else
        broadcastToAll(color .. ' has drawn aggro!', Color[color] or {1, 1, 1})
    end
end

function SetFirstPlayerToAggro()
    -- 현재 어그로가 활성화된 플레이어 찾기 (Global UI 이미지 기준)
    local aggroColor = nil
    for color, _ in pairs(ActivePlayer) do
        local img = Global.UI.getAttribute("aggro_" .. color, "image")
        if img == URL_AGGRO_ON then
            aggroColor = color
            break
        end
    end

    -- 어그로가 아무에게도 없으면 선플레이어 변경 안 함
    if aggroColor == nil then return end

    -- 어그로 플레이어를 선플레이어로 활성화, 나머지는 비활성화
    for color, aplayer in pairs(ActivePlayer) do
        local boardObj = getObjectFromGUID(aplayer.boardGUID)
        if boardObj then
            if color == aggroColor then
                boardObj.call("enableFirstPlayer", false)  -- hideBroadcast=true (메시지 스팸 방지)
            else
                boardObj.call("disableFirstPlayer")
            end
        end
    end

    print(aggroColor .. " 플레이어가 선플레이어로 지정되었습니다. (어그로 보유)")
end

function TurnOrderShow()
    Global.UI.setAttribute("TurnOrder", "active", TurnOrderUIisHidden)
	StartTurnUI()
    TurnOrderUIisHidden = not TurnOrderUIisHidden
end

function CampaignShow()
    Global.UI.setAttribute("CampaignPanel", "active", CampaignUIisHidden)
    CampaignUIisHidden = not CampaignUIisHidden
end

function changecolorreset(plr, toggleState, btnreset)
    Global.UI.setAttribute("btn1", "color", "white")
    Global.UI.setAttribute("btn2", "color", "white")
    Global.UI.setAttribute("btn3", "color", "white")
    Global.UI.setAttribute("btn4", "color", "white")
    Global.UI.setAttribute("btn5", "color", "white")
	NextRound()
    clearAllTurnEndDecals()
end

function changeHand(params)
    changecolor(params[1] or "", params[2], params[3])
end

function changecolor(plr, toggleState, btnId)
    local current = Global.UI.getAttribute(btnId, "color")
    local newColor
    if current == "white" then
        newColor = "#aaaaaa77"
    elseif current == "#aaaaaa77" then
        newColor = "#000000cc"
    else
        newColor = "white"
    end
    Global.UI.setAttribute(btnId, "color", newColor)

    -- ↓ 변경: 가장 어두운 단계일 때만 보드 이미지 표시
    local boardColor = BUTTON_TO_COLOR[btnId]
    if boardColor then
        local visualEnabled = (newColor == "#000000cc")   -- ← 어두움 단계만
        local boards = getObjectsWithTag('color_' .. boardColor:lower())
        for _, board in ipairs(boards) do
            board.call('setTurnEndVisualOnly', {enabled = visualEnabled})
        end
    end
end

function SetGlobalTurnEndButton(params)
    local color = params.color
    local enabled = params.enabled

    local buttonId = COLOR_TO_BUTTON[color]
    if not buttonId then return end

    -- 보드에서 켜면 가장 어두운 상태, 끄면 white
    Global.UI.setAttribute(buttonId, 'color', enabled and '#000000cc' or 'white')
end

function fixMonsterUI(targetObj)
    if not targetObj then return end

    local angle = MonsterUIOffsets[targetObj.guid]

    if not angle then
        local name = targetObj.getName():upper()
        if name == "OZEW" then
            angle = 135
        end
    end

    if angle then
        local currentXml = targetObj.UI.getXml()
        if currentXml ~= "" and not string.find(currentXml, 'id="MonsterUIRoot"') then
            local newXml = '<Panel id="MonsterUIRoot" rotation="0 0 ' .. tostring(angle) .. '">' .. currentXml .. '</Panel>'
            targetObj.UI.setXml(newXml)
        end
    end
end

function onObjectSpawn(obj)
    if MonsterUIOffsets[obj.guid] or (obj.getName():upper() == "OZEW") then
        Wait.time(function() fixMonsterUI(obj) end, 1)
    end

    Wait.time(function()
        if obj == nil then return end
        for color, _ in pairs(ActivePlayer) do
            if obj.hasTag("owner_" .. color) then
                StartTurnUI()
                local monsterBoard = getObjectFromGUID("fa932e")
                if monsterBoard then
                    monsterBoard.call("updateMonsterToughnessFromActorStance")
                end
                break
            end
        end
    end, 0.5)
end

function onObjectDrop(player_color, dropped_object)
    if dropped_object.hasTag("monster_spawn") then
        fixMonsterUI(dropped_object)
    end

    for color, _ in pairs(ActivePlayer) do
        if dropped_object.hasTag("owner_" .. color) then
            StartTurnUI()
            local monsterBoard = getObjectFromGUID("fa932e")
            if monsterBoard then
                monsterBoard.call("updateMonsterToughnessFromActorStance")
            end
            break
        end
    end

    if dropped_object.type == "Card" and (dropped_object.hasTag("Aggro") or dropped_object.hasTag("어그로")) then
        Wait.condition(
            function()
                if dropped_object == nil then return end

                -- 뒷면이면 메시지 없이 종료 (위치 무관)
                local ok_facedown, isFaceDown = pcall(function() return dropped_object.is_face_down end)
                if not ok_facedown then return end
                if isFaceDown then return end

                local ok_pos, pos = pcall(function() return dropped_object.getPosition() end)
                if not ok_pos or pos == nil then return end

                -- 본인 시퀀스 영역
                local ownZone = SequenceZones[player_color]
                if ownZone
                   and pos.x >= ownZone.min_x and pos.x <= ownZone.max_x
                   and pos.z >= ownZone.min_z and pos.z <= ownZone.max_z
                   and ActivePlayer[player_color] then
                    broadcastToAll(player_color .. " 플레이어가 어그로 카드를 시퀀스에 플레이했습니다!", player_color)
                    -- SetAggroTarget(player_color)
                    return
                end

                -- 본인 확장 시퀀스 영역 (실제 생성된 추가 슬롯 개수 기반)
                if ownZone and ActivePlayer[player_color] then
                    local boardObj = getObjectFromGUID(ActivePlayer[player_color].boardGUID)
                    if boardObj then
                        local plusCount = boardObj.call("countSequencePlusCards") or 0
                        if plusCount > 0 then
                            -- 슬롯 1개당 약 2.4의 가로 공간 차지
                            local expanded_max_x = ownZone.max_x + (2.4 * plusCount)
                            if pos.x > ownZone.max_x and pos.x <= expanded_max_x
                               and pos.z >= ownZone.min_z and pos.z <= ownZone.max_z then
                                broadcastToAll(player_color .. " 플레이어가 어그로 카드를 시퀀스에 플레이했습니다!", player_color)
                                return
                            end
                        end
                    end
                end

                -- 다른 플레이어 시퀀스 영역 (앞면일 때만 도달)
                for color, zone in pairs(SequenceZones) do
                    if color ~= player_color
                       and pos.x >= zone.min_x and pos.x <= zone.max_x
                       and pos.z >= zone.min_z and pos.z <= zone.max_z then
                        broadcastToAll("다른 플레이어보드에 어그로 카드를 플레이하였습니다. 어그로 버튼은 활성화되지 않습니다.", player_color)
                        return
                    end
                end
            end,
            function()
                if dropped_object == nil then return true end
                local ok, resting = pcall(function() return dropped_object.resting end)
                if not ok then return true end
                return resting
            end,
            2
        )
    end
end

function onObjectDestroy(destroyed_object)
    for color, _ in pairs(ActivePlayer) do
        if destroyed_object.hasTag("owner_" .. color) then
            Wait.time(function()
                StartTurnUI()
                local monsterBoard = getObjectFromGUID("fa932e")
                if monsterBoard then
                    monsterBoard.call("updateMonsterToughnessFromActorStance")
                end
            end, 0.1)
            break
        end
    end
end

function SyncAggroFromBoard(params)
    local targetID = "aggro_" .. params.color
    local imgURL = params.active and URL_AGGRO_ON or URL_AGGRO_OFF

    Global.UI.setAttribute(targetID, "image", imgURL)
end

-- 덱이나 가방에서 카드를 꺼낼 때 자동으로 손패 설정을 복구합니다.
-- (덱 생성 시 내부 카드의 use_hands=false 상태가 그대로 저장되는 TTS 특성 보완용)
function onObjectLeaveContainer(container, leave_object)
    if leave_object.type == "Card" then
        leave_object.use_hands = true
    end
end

-- ==========================================================
-- Monster Upkeep & 격앙 토큰 관리 시스템 (완전 초기화 통합본)
-- ==========================================================

-- (1) 작동 상태와 클릭된 버튼의 실제 ID를 추적하는 전역 변수
local isUpkeepRunning = false
local lastClickedUpkeepBtnId = "monsterUpkeepBtn" -- 기본값
local upkeepSafetyTimerID = nil -- [추가] 안전장치 타이머를 관리할 변수

function GetTokenCount(data)
    local textObj = getObjectFromGUID(data.textGUID)
    if textObj then
        if textObj.TextTool then return tonumber(textObj.TextTool.getValue()) or 0 end
        if textObj.Counter then return tonumber(textObj.Counter.getValue()) or 0 end
    end
    local zone = getObjectFromGUID(data.zoneGUID)
    if zone then
        local count = 0
        for _, obj in ipairs(zone.getObjects()) do
            if obj.hasTag(data.tag) or obj.getName() == data.tag then
                local q = obj.getQuantity()
                count = count + (q > 0 and q or 1)
            end
        end
        return count
    end
    return 0
end

function ClearStruggleTokens(data)
    local zone = getObjectFromGUID(data.zoneGUID)
    if zone then
        for _, obj in ipairs(zone.getObjects()) do
            if obj.hasTag(data.tag) or obj.getName() == data.tag then obj.destruct() end
        end
    end
    local textObj = getObjectFromGUID(data.textGUID)
    if textObj then
        if textObj.TextTool then textObj.TextTool.setValue("0") end
        if textObj.Counter then textObj.Counter.setValue(0) end
    end
    Global.setVar("struggleCount", 0)
end

local checkEruptionTimerID = nil
function ScheduleCheckEruption()
    if checkEruptionTimerID then Wait.stop(checkEruptionTimerID) end
    checkEruptionTimerID = Wait.time(CheckEruption, 0.5)
end

function CheckEruption()
    checkEruptionTimerID = nil

    -- [수정] 분출 한계치를 계산할 때도 기물+착석 여부를 정밀하게 체크하는 함수 사용
    local playerCount = getPlayersNb()

    local currentStruggle = GetTokenCount(allZone.StruggleData)
    local threshold = playerCount * 3

    if currentStruggle >= threshold then
        local monsterName = "몬스터"
        local spawnPos = {x = -1.52, y = 3.47, z = 10.38}
        local hits = Physics.cast({
            origin       = {spawnPos.x, spawnPos.y + 3, spawnPos.z},
            direction    = {0, -1, 0}, type = 3, size = {6, 6, 6}, max_distance = 6,
        })
        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            local foundName = obj.getName()
            if foundName and foundName ~= "" then
                monsterName = foundName
                break
            elseif obj.TextTool then
                local textValue = obj.TextTool.getValue()
                if textValue and textValue ~= "" then monsterName = textValue; break end
            end
        end

        broadcastToAll("격앙토큰이 " .. threshold .. "개 이상 쌓여 " .. monsterName .. " 이(가) 분출합니다. 피해를 입습니다.", {1, 0, 0})
        ClearStruggleTokens(allZone.StruggleData)
        Wait.frames(function() addStruggle(playerCount) end, 5)
    end
end

local function getCardOrDeckAt(pos)
    -- 감지 범위를 약간 넓히고 레이캐스트 높이를 조절하여 더 정확하게 탐지
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
            -- 잡혀있는 카드는 무시 (이동 중인 카드를 오판하는 것 방지)
            if not obj.held_by_color then
                return obj
            end
        end
    end
    return nil
end

local function getCardNumber(card)
    local level = card.getVar("Blevel")
    if level ~= nil then return tonumber(level) end
    return nil
end

local function wait(sec)
    local t = Time.time + sec
    while Time.time < t do coroutine.yield(0) end
end

function UpkeepCoroutine()
    local addedStruggle = struggleToAddDuringUpkeep or 0
    local deckPos = {x=13.90, y=1.01, z=10.41}
    local slotPos = { {x=17.40, y=1.06, z=10.48}, {x=21.06, y=1.06, z=10.48}, {x=24.61, y=1.06, z=10.48} }
    local discardPos = {x=28.09, y=0.86, z=10.33}

    if CurrentMonster == "Awakened" then
        table.insert(slotPos, {x=28.55, y=1.08, z=10.48})
        table.insert(slotPos, {x=32.17, y=1.05, z=10.48})
        table.insert(slotPos, {x=35.82, y=1.01, z=10.48})
        discardPos = {x=39.23, y=0.8, z=10.48}
    end

    local slotCards = {}
    local numbers = {}

    for i, pos in ipairs(slotPos) do
        local foundCard = getCardOrDeckAt(pos)
        if foundCard and foundCard.type == "Card" then
            local num = getCardNumber(foundCard)
            slotCards[i] = {card = foundCard, number = num, pos = pos}
            if num then
                table.insert(numbers, num)
            end
        end
    end

    -- 버릴 숫자 결정: 가장 낮은 숫자 (Awakened일 경우 두 번째로 낮은 숫자도 포함)
    local discardNumbers = {}
    local minNumber = math.huge
    for _, n in ipairs(numbers) do
        if n < minNumber then minNumber = n end
    end
    if minNumber ~= math.huge then
        discardNumbers[minNumber] = true
    end

    if CurrentMonster == "Awakened" then
        local secondMin = math.huge
        for _, n in ipairs(numbers) do
            if n > minNumber and n < secondMin then secondMin = n end
        end
        if secondMin ~= math.huge then
            discardNumbers[secondMin] = true
        end
    end

    -- 1라운드에는 카드를 버리지 않음 (격앙 토큰만 추가)
    if CurrentRound ~= 1 then
        for i, data in pairs(slotCards) do
            if data.number and discardNumbers[data.number] then
                data.card.setPositionSmooth({x=discardPos.x, y=discardPos.y + 1, z=discardPos.z}, false, true)
                data.card.setRotationSmooth({x=0, y=180, z=0}, false, true)
                slotCards[i] = nil
            end
        end
        wait(0.6) -- 카드가 슬롯에서 벗어날 시간을 충분히 줌
    end

    for i = 1, #slotPos do
        if not slotCards[i] then
            -- 덱 또는 카드를 찾기 위한 재시도 로직 추가
            local deckOrCard = nil
            for retry = 1, 3 do
                deckOrCard = getCardOrDeckAt(deckPos)
                if deckOrCard then break end
                wait(0.2)
            end

            if not deckOrCard then
                -- 덱이 없으면 버림더미에서 리필 시도
                local discardObj = getCardOrDeckAt(discardPos)
                if discardObj then
                    local struggleAmount = 1
                    if CurrentMonster == "Awakened" then
                        struggleAmount = getPlayersNb()
                    end
                    broadcastToAll("덱이 비어 있어 버림 더미를 리필합니다. (격앙 토큰 " .. struggleAmount .. "개 추가)", {r=1, g=0.5, b=0})
                    discardObj.setPositionSmooth({x=deckPos.x, y=deckPos.y + 0.5, z=deckPos.z}, false, true)
                    discardObj.setRotationSmooth({x=0, y=180, z=180}, false, true)
                    wait(1.5) -- 리필 안착 대기
                    if discardObj.type == "Deck" then discardObj.shuffle() end
                    addStruggle(struggleAmount)
                    wait(0.5)
                    deckOrCard = getCardOrDeckAt(deckPos)
                end
            end

            if deckOrCard then
                if deckOrCard.type == "Deck" then
                    deckOrCard.takeObject({ position = slotPos[i], rotation = {0, 180, 180}, smooth = true })
                else
                    deckOrCard.setPositionSmooth(slotPos[i], false, true)
                    deckOrCard.setRotationSmooth({x=0, y=180, z=180}, false, true)
                end
                wait(0.4) -- 다음 카드 보충 전 충분한 대기 시간 확보
            else
                print("[오류] 슬롯 " .. i .. "을(를) 채울 카드를 찾을 수 없습니다. (덱/버림더미 없음)")
            end
        end
    end

    -- [복구] 카드를 모두 채운 후 덱이 0장이면 즉시 버림 더미를 섞어 새 덱을 만들고 격화 발생
    local finalDeckCheck = nil
    for retry = 1, 3 do
        finalDeckCheck = getCardOrDeckAt(deckPos)
        if finalDeckCheck then break end
        wait(0.2)
    end

    if not finalDeckCheck then
        local discardObj = getCardOrDeckAt(discardPos)
        if discardObj then
            local safeMonsterName = "몬스터"
            if CurrentMonster ~= nil and type(CurrentMonster) == "string" and CurrentMonster ~= "" then
                safeMonsterName = CurrentMonster
            end

            local struggleAmount = 1
            if CurrentMonster == "Awakened" then
                struggleAmount = getPlayersNb()
            end

            broadcastToAll(safeMonsterName .. "이(가) 격화하여 격앙 토큰이 " .. struggleAmount .. "개 추가됩니다.", {r=1, g=0.5, b=0})

            discardObj.setPositionSmooth({x=deckPos.x, y=deckPos.y + 0.5, z=deckPos.z}, false, true)
            discardObj.setRotationSmooth({x=0, y=180, z=180}, false, true)
            wait(1.5) -- 안착 대기
            if discardObj.type == "Deck" then discardObj.shuffle() end

            addStruggle(struggleAmount)
            wait(0.5)
        end
    end

    -- 카드가 슬롯에 어느 정도 도착하면 바로 다음 단계 진행
    wait(0.3) -- 안착 대기 시간

    -- 카드 이동 및 격화(+1)가 모두 끝난 후
    -- 1. 인원수(+가속)만큼 토큰 추가
    addStruggle(addedStruggle)
    wait(0.2) -- 토큰이 쌓이는 연출을 위한 짧은 대기

    -- 2. 최종 분출 확인 (여기서 토큰이 줄어드는 로직이 실행됨)
    CheckEruption()
    wait(0.4) -- 분출 연출 대기

    if upkeepSafetyTimerID then
        Wait.stop(upkeepSafetyTimerID)
        upkeepSafetyTimerID = nil
    end

    isUpkeepRunning = false
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "color", "#FFFFFF")
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#FFFFFF")
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "interactable", "True")

    for _, p in pairs(ActivePlayer) do
        local board = getObjectFromGUID(p.boardGUID)
        if board then
            board.UI.setAttribute(lastClickedUpkeepBtnId, "color", "#FFFFFF")
            board.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#FFFFFF")
            board.UI.setAttribute(lastClickedUpkeepBtnId, "interactable", "True")
        end
    end

    return 1
end

-- (4) 메인 버튼 클릭 함수
function DoMonsterUpkeep(player, value, id)
    -- 엔진이 넘겨준 진짜 버튼 ID를 자동 캡처하여 저장
    if id and id ~= "" then lastClickedUpkeepBtnId = id end

    if isUpkeepRunning then
        print("[경고] 이미 Monster Upkeep이 작동 중입니다! 중복 클릭 방지됨.")
        return
    end
    isUpkeepRunning = true

    -- [추가] 전투 보드에서 현재 라운드를 가져와 화면 중앙에 브로드캐스트
    local currentRound = 1 -- 기본값 (0라운드일 경우 1라운드로 표기)
    local activeBoardGUID = GetCombatBoardGUID()
    if activeBoardGUID then
        local boardObj = getObjectFromGUID(activeBoardGUID)
        if boardObj then
            local rn = boardObj.getVar("RoundNumber")
            if rn and rn > 0 then
                currentRound = rn
            end
        end
    end
    if currentRound == 1 then
        broadcastToAll(currentRound .. "라운드 몬스터 유지 단계 실행.(1라운드는 행동재활성화 건너뜀)", {r=1, g=0.8, b=0})
    else
        broadcastToAll(currentRound .. "라운드 몬스터 유지 단계 실행.", {r=1, g=0.8, b=0})
    end

    -- UI 잠금 및 색상 변경 (모든 보드 동시 적용)
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "color", "#888888")
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#888888")

    for _, p in pairs(ActivePlayer) do
        local board = getObjectFromGUID(p.boardGUID)
        if board then
            board.UI.setAttribute(lastClickedUpkeepBtnId, "color", "#888888")
            board.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#888888")
        end
    end

    -- 6초 타임아웃 안전장치 (에러 발생 시 강제 복구)
    -- [수정] 생성된 타이머의 ID를 변수에 저장하여, 나중에 취소할 수 있게 만듭니다.
    upkeepSafetyTimerID = Wait.time(function()
        if isUpkeepRunning then
            print("[시스템] 🚨 에러 감지: 6초 타임아웃으로 버튼을 강제 복구합니다!")
            isUpkeepRunning = false
            Global.UI.setAttribute(lastClickedUpkeepBtnId, "color", "#FFFFFF")
            Global.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#FFFFFF")
            Global.UI.setAttribute(lastClickedUpkeepBtnId, "interactable", "True")
            upkeepSafetyTimerID = nil
        end
    end, 6.0)

    local playerCount = getPlayersNb()

    if playerCount == 0 then
        broadcastToAll("플레이어가 자리에 없습니다.", {r=1, g=0.2, b=0.2})
    else
        local accelerationCount = GetTokenCount(allZone.AccelData)
        local addedStruggle = playerCount + accelerationCount

        -- [수정] 즉시 추가하지 않고, 코루틴 내부에서 격화 처리 후에 추가하도록 변수만 전달
        struggleToAddDuringUpkeep = addedStruggle
        startLuaCoroutine(Global, "UpkeepCoroutine")
    end
end

-- ==========================================================
-- Zone 데이터 및 값 읽어오기 헬퍼 함수 (순서 위로 이동 및 전역화)
-- ==========================================================

function getCount(data)
    -- 1. textGUID 오브젝트에서 값 읽기 시도 (가장 정확하고 빠름)
    local textObj = getObjectFromGUID(data.textGUID)
    if textObj then
        if textObj.TextTool then
            local val = tonumber(textObj.TextTool.getValue())
            if val then return val end
        end
        if textObj.Counter then
            local val = tonumber(textObj.Counter.getValue())
            if val then return val end
        end
    end

    -- 2. 실패할 경우 Zone 내부의 오브젝트들을 직접 세기 (안전장치)
    local zone = getObjectFromGUID(data.zoneGUID)
    if zone then
        local count = 0
        for _, obj in ipairs(zone.getObjects()) do
            -- 태그(Tag)를 사용하거나 이름이 일치하는 토큰만 셈
            if obj.hasTag(data.tag) or obj.getName() == data.tag then
                local q = obj.getQuantity()
                count = count + (q > 0 and q or 1) -- 뭉쳐진 토큰 갯수 처리
            end
        end
        return count
    end

    return 0
end

-- 격앙 토큰 및 수치를 완전히 초기화하는 함수
function clearStruggle(data)
    local zone = getObjectFromGUID(data.zoneGUID)
    if zone then
        for _, obj in ipairs(zone.getObjects()) do
            -- 태그가 일치하는 토큰들을 모두 제거
            if obj.hasTag(data.tag) or obj.getName() == data.tag then
                obj.destruct()
            end
        end
    end

    -- 수치 텍스트/카운터 오브젝트를 0으로 초기화
    local textObj = getObjectFromGUID(data.textGUID)
    if textObj then
        if textObj.TextTool then textObj.TextTool.setValue("0") end
        if textObj.Counter then textObj.Counter.setValue(0) end
    end

    -- Global 스크립트 내부의 격앙 변수도 0으로 초기화 시도 (변수명이 struggleCount일 경우)
    Global.setVar("struggleCount", 0)
end

-- ==========================================================
-- 공통 분출 확인 로직 (디바운스 적용)
-- ==========================================================
local checkEruptionTimerID = nil

-- 짧은 시간 내에 여러 번 호출되어도 마지막 호출 후 0.5초 뒤에 한 번만 실행되도록 함
function ScheduleCheckEruption()
    if checkEruptionTimerID then Wait.stop(checkEruptionTimerID) end
    checkEruptionTimerID = Wait.time(CheckEruption, 0.5)
end

function CheckEruption()
    checkEruptionTimerID = nil

    local playerCount = getPlayersNb()

    -- [추가] 플레이어가 0명이면 분출 계산 자체를 하지 않고 즉시 종료
    if playerCount == 0 then return end

    local currentStruggle = GetTokenCount(allZone.StruggleData)
    local threshold = playerCount * 3

    if currentStruggle >= threshold then
        local monsterName = "몬스터"

        -- 몬스터 이름 탐색 (스폰 좌표 기반 물리 탐색)
        local spawnPos = {x = -1.52, y = 3.47, z = 10.38}

        -- 스폰 위치의 약간 위에서 아래로 Box 형태로 스캔합니다.
        local hits = Physics.cast({
            origin       = {spawnPos.x, spawnPos.y + 3, spawnPos.z},
            direction    = {0, -1, 0},
            type         = 3, -- Box 캐스트
            size         = {6, 6, 6}, -- 스케일(5.8)을 덮을 수 있는 넉넉한 크기
            max_distance = 6,
        })

        for _, hit in ipairs(hits) do
            local obj = hit.hit_object
            local foundName = obj.getName()

            -- 이름이 비어있지 않은 오브젝트를 찾습니다. (보드 등 기본 배경 구조물은 무시하도록 이름이 있는 것만 선택)
            if foundName and foundName ~= "" then
                monsterName = foundName
                break
            -- 만약 이름표가 일반 Name 속성이 아닌 3D 텍스트(TextTool) 형태라면
            elseif obj.TextTool then
                local textValue = obj.TextTool.getValue()
                if textValue and textValue ~= "" then
                    monsterName = textValue
                    break
                end
            end
        end

        broadcastToAll("격앙토큰이 " .. threshold .. "개 이상 쌓여 " .. monsterName .. " 이(가) 분출합니다. 피해를 입습니다.", {1, 0, 0})

        -- 1. 모든 격앙 토큰 지우기
        clearStruggle(allZone.StruggleData)

        -- 2. 토큰이 완전히 지워진 후 인원수만큼 다시 채우기 (프레임 단위 대기)
        Wait.frames(function() addStruggle(playerCount) end, 5)
    end
end

-- 모든 보드의 턴종료 데칼 + 글로벌 UI 버튼 초기화
function clearAllTurnEndDecals()
    -- 모든 플레이어 보드의 데칼 제거
    for _, board in ipairs(getObjectsWithTag('player_board')) do
        board.call('setTurnEndVisualOnly', {enabled = false})
    end

    -- 글로벌 UI 버튼들도 white로 리셋
    for _, btnId in pairs(COLOR_TO_BUTTON) do
        Global.UI.setAttribute(btnId, 'color', 'white')
    end
end