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

FIRST_PLAYER_URLS = {
    ['Blue']   = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535248821/110A9FFB2B665FE3139F44E22350F0CBF8A3D743/',
    ['Green']  = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535248971/E78FE186BBF1E42BD90AADF6A72B2C844BDDD8F5/',
    ['Yellow'] = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249223/DE77A57AEF52D95333974E82E1E642DA3E6D130D/',
    ['Orange'] = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249070/D878690B51AD96CBF2E542D21055F1A0EA01DB93/',
    ['Red']    = 'https://steamusercontent-a.akamaihd.net/ugc/2456230531535249147/1A2CFA56B8E90764234D91CA0B220CCB1962EA8B/',
}

function UpdateFirstPlayerUI()
    for color, _ in pairs(ActivePlayer) do
        local isActive = (color == current_first_player)
        Global.UI.setAttribute("first_player_" .. color, "active", isActive and "true" or "false")
    end
end

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
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797926049/899D5957BD9DA1D22EC1DA735B27DFDE776247B9/"] = "플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 정면 구역에서 턴을 시작할 때 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782313707938763/A35216A32C62594408CE625CF00091A6A6C333A2/"] = "플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 손패를 비운 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782948727284265/F26FC15B3213217809FA164E50B91C113511F0AA/"] = "플레이어가 위협 상태가 되었거나 플레이어가 측면 구역에서 턴을 시작할 때 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797932158/3BBF71B0FB754355A0B19FD5071CD12A4976B806/"] = "플레이어가 위협 상태가 되었거나 플레이어가 후면 구역에서 턴을 시작할 때 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2514782313707940714/FE3F3F0C8FED4C16936FBEC687331AB3155A0C1B/"] = "플레이어가 위협 상태가 되었거나 플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 플레이한 후 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039797947019/F968EA586683C55CB46A1B893F8C4E0A99DB7ED4/"] = "플레이어의 행동 단계가 끝날 때 공격(빨강) 카드가 시퀸스에 있는 경우 발동합니다.",
	["https://steamusercontent-a.akamaihd.net/ugc/2549682039798556808/DE98B5A807CDBEDE7268489F04B7688263909B39/"] = "플레이어가 시퀸스에서 공격(빨강) 카드를 두장 연속으로 플레이한 후 발동합니다.",
  ["https://steamusercontent-a.akamaihd.net/ugc/2452852111559744720/907FB13C73B2FC99684AC4CD91DF9337AFE5A288/"] = "플레이어가 위협 상태가 된 후 발동합니다.",
  ["Question"] = "행동 카드가 비어 있습니다. 행동 카드가 있는 경우 해당 행동 카드의 발동 조건이 표시됩니다.",
}

BehaviorRules = {
	-- ==============================================
	-- 카드 플레이 (단일)
	-- ==============================================
	["플레이어가 시퀸스에서 공격 (빨강) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "aa_attack" },
	["플레이어가 시퀸스에서 기동 (파랑) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "aa_maneuver" },
	["플레이어가 시퀸스에서 회피 (초록) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "aa_evade" },
	["플레이어가 시퀸스에서 방어 (노랑) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "aa_defend" },
	["플레이어가 시퀸스에서 어그로 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "Aggro" },

	-- ==============================================
	-- 카드 플레이 (복합 및 연속)
	-- ==============================================
	["플레이어가 시퀸스에서 공격형(빨강/파랑) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tags = {"aa_attack", "aa_maneuver"} },
	["플레이어가 시퀸스에서 공격형(빨강/파랑) 카드를 두장 연속으로 플레이한 후 발동합니다."] = { event = "CardPlay", tags = {"aa_attack", "aa_maneuver"}, count = 2 },
	["플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 플레이한 후 발동합니다."] = { event = "CardPlay", tags = {"aa_defend", "aa_evade"} },
	["플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 두장 연속으로 플레이한 후 발동합니다."] = { event = "CardPlay", tags = {"aa_defend", "aa_evade"}, count = 2 },
	["플레이어가 시퀸스에서 공격(빨강) 카드를 두장 연속으로 플레이한 후 발동합니다."] = { event = "CardPlay", tag = "aa_attack", count = 2 },
	["플레이어의 행동 단계가 끝날 때 공격(빨강) 카드가 시퀸스에 있는 경우 발동합니다."] = { event = "ActionEndWithAttack" },

	-- ==============================================
	-- 턴 및 라운드 처리
	-- ==============================================
	["라운드가 끝날 때 발동합니다."] = { event = "RoundEnd" },
	["플레이어가 정면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStart", zone = "Front" },
	["플레이어가 측면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStart", zone = "Flank" },
	["플레이어가 후면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStart", zone = "Rear" },
	["플레이어가 턴 시작시 측면 구역에 플레이어가 한 명이라도 있다면 발동합니다."] = { event = "TurnStart", anyZone = "Flank" },
	["플레이어가 턴 시작시 후면 구역에 플레이어가 한 명이라도 있다면 발동합니다."] = { event = "TurnStart", anyZone = "Rear" },
	["플레이어가 물 지형이 있는 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStart", terrain = "Water" },

	-- ==============================================
	-- 이동 및 지형
	-- ==============================================
	["플레이어가 이동한 후 발동합니다."] = { event = "Move" },
	["플레이어가 물 지형이 있는 구역으로 이동한 후 발동합니다."] = { event = "Move", terrain = "Water" },

	-- ==============================================
	-- 기타 상태 (손패, 위협 등)
	-- ==============================================
	["플레이어가 손패를 비운 후 발동합니다."] = { event = "EmptyHand" },
	["플레이어가 위협 상태가 된 후 발동합니다."] = { event = "Threat" },
	["마찰 단계가 끝난 후 발동합니다."] = { event = "StruggleEnd" },
	["몬스터가 다른 구역을 향해 방향을 바꾼 후 발동합니다."] = { event = "MonsterDirection" },

	-- ==============================================
	-- 복합 조건 (OR)
	-- ==============================================
	["플레이어가 손패를 비웠거나 플레이어가 시퀸스에서 회피 (초록) 카드를 플레이한 후 발동합니다."] = { event = "EmptyHandOrCardPlay", tag = "aa_evade" },
	["플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 정면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStartOrCardPlay", zone = "Front", tag = "Aggro" },
	["플레이어가 시퀸스에서 어그로 카드를 플레이했거나 플레이어가 손패를 비운 후 발동합니다."] = { event = "EmptyHandOrCardPlay", tag = "Aggro" },
	["플레이어가 위협 상태가 되었거나 플레이어가 측면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStartOrThreat", zone = "Flank" },
	["플레이어가 위협 상태가 되었거나 플레이어가 후면 구역에서 턴을 시작할 때 발동합니다."] = { event = "TurnStartOrThreat", zone = "Rear" },
	["플레이어가 위협 상태가 되었거나 플레이어가 시퀸스에서 방어형(노랑/초록) 카드를 플레이한 후 발동합니다."] = { event = "ThreatOrCardPlay", tags = {"aa_defend", "aa_evade"} },

	-- ==============================================
	-- 특수 처리
	-- ==============================================
	["이 카드가 게임에 들어온 즉시 발동합니다."] = { event = "Immediate" },
	["다른 카드가 발동할 때 같이 발동합니다."] = { event = "OtherTrigger" },

	-- ==============================================
	-- 없음
	-- ==============================================
    ["행동 카드가 비어 있습니다. 행동 카드가 있는 경우 해당 행동 카드의 발동 조건이 표시됩니다."] = { event = "None" }
}

behaviorTriggered = {
    behave1 = false,
    behave2 = false,
    behave3 = false
}
behaviorTriggerReason = {}
behaviorTriggerPlayer = {}
TRIGGER_IMAGE_URL = "https://steamusercontent-a.akamaihd.net/ugc/10640811446178692473/2D2396737FA1D893D6EA926A091059B38712EB26/"


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

is_game_started = false
is_player_turn_active = false
current_first_player = nil
saved_turn_order = {}

is_turn_system_active = false
current_turn_system_color = nil
function GetCurrentTurnColor()
    return current_turn_system_color
end
function SetTurnSystemActive(active)
    is_turn_system_active = active
    Turns.enable = false
end
function GetTurnSystemActive()
    return is_turn_system_active
end

function getTrueBoardRotation(combatBoardGUID)
    local pFront = getWorldPosOfSnapOnObj({combatBoardGUID, "terrain_2"})
    local pBack = getWorldPosOfSnapOnObj({combatBoardGUID, "terrain_8"})
    if pFront and pBack then
        local dx = pBack.x - pFront.x
        local dz = pBack.z - pFront.z
        return math.deg(math.atan2(dx, dz))
    end
    local combatBoard = getObjectFromGUID(combatBoardGUID)
    if combatBoard then return combatBoard.getRotation().y end
    return 0
end

function getTrueBoardCenter(combatBoardGUID)
    local centerPos = getWorldPosOfSnapOnObj({combatBoardGUID, "actor_mini"})
    if centerPos then return centerPos end
    
    local center = {x=0, y=0, z=0}
    local count = 0
    local terrains = Terrains
    if not terrains then return nil end
    for _, snapTags in pairs(terrains) do
        for _, snapTag in ipairs(snapTags) do
            local pos = getWorldPosOfSnapOnObj({combatBoardGUID, snapTag})
            if pos then
                center.x = center.x + pos.x
                center.y = center.y + pos.y
                center.z = center.z + pos.z
                count = count + 1
            end
        end
    end
    if count == 0 then return nil end
    center.x = center.x / count
    center.y = center.y / count
    center.z = center.z / count
    return center
end

function getPlayerQuadrantGlobal(color)
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
    
    local combatBoardGUID = GetCombatBoardGUID()
    if not combatBoardGUID then return nil end
    
    local combatBoard = getObjectFromGUID(combatBoardGUID)
    if not combatBoard then return nil end
    
    local figPos = playerFig.getPosition()
    local center = getTrueBoardCenter(combatBoardGUID)
    if not center then return nil end
    
    local dx = figPos.x - center.x
    local dz = figPos.z - center.z
    
    -- 컴뱃보드 반경 밖이면 무시 (반경 8로 설정)
    if dx*dx + dz*dz > 64 then return nil end
    
    local rad = math.rad(-getTrueBoardRotation(combatBoardGUID))
    local localX = dx * math.cos(rad) - dz * math.sin(rad)
    local localZ = dx * math.sin(rad) + dz * math.cos(rad)
    
    local absX = math.abs(localX)
    local absZ = math.abs(localZ)
    
    if localZ > absX then return "back"
    elseif localZ < -absX then return "front"
    elseif localX > absZ then return "right"
    else return "left" end
end

function getMonsterFrontZone()
    local combatBoardGUID = GetCombatBoardGUID()
    if not combatBoardGUID then return "front" end

    local monsterPos = getWorldPosOfSnapOnObj({combatBoardGUID, "actor_mini"})
    if not monsterPos then return "front" end
    
    local monster = GetObjOnPos({monsterPos, CurrentMonster})
    if not monster then return "front" end

    local currentRot = monster.getRotation().y

    local monsterCase = nil
    for caseName, monsterList in pairs(MonsterCases) do
        for _, name in ipairs(monsterList) do
            if name == CurrentMonster then monsterCase = caseName; break end
        end
        if monsterCase then break end
    end
    if not monsterCase then monsterCase = MONSTER_DEFAULT_CASE end
    
    local cfg = MonsterRotationCases[monsterCase]
    if not cfg then return "front" end
    
    local monsterFront = "front"
    local minDiff = math.huge
    for zName, rot in pairs(cfg) do
        local diff = math.abs(currentRot - rot)
        if diff > 180 then diff = math.abs(diff - 360) end
        if diff < minDiff then
            minDiff = diff
            monsterFront = zName
        end
    end
    
    return monsterFront
end

function convertToRelativeQuadrant(rawZone)
    if not rawZone then return nil end
    local monsterFront = getMonsterFrontZone()
    
    if rawZone == monsterFront then return "Front" end
    
    local opposite = { front = "back", back = "front", left = "right", right = "left" }
    if rawZone == opposite[monsterFront] then return "Rear" end
    
    return "Flank"
end

function checkTerrainInZone(zoneName, terrainType)
    local combatBoardGUID = GetCombatBoardGUID()
    if not combatBoardGUID then return false end
    
    local snapTags = Terrains[zoneName]
    if not snapTags then return false end
    
    for _, snapTag in ipairs(snapTags) do
        local snapPos = getWorldPosOfSnapOnObj({combatBoardGUID, snapTag})
        if snapPos then
            local hits = Physics.cast({
                origin = {snapPos.x, snapPos.y + 2, snapPos.z},
                direction = {0, -1, 0},
                type = 3,
                size = {2, 2, 2},
                max_distance = 4
            })
            for _, hit in ipairs(hits) do
                local obj = hit.hit_object
                local objName = string.lower(obj.getName())
                local searchType = string.lower(terrainType)
                if string.find(objName, searchType) or obj.hasTag(terrainType) or obj.hasTag(searchType) then
                    return true
                end
            end
        end
    end
    return false
end

function CheckPlayerInWater(color)
    local z = getPlayerQuadrantGlobal(color)
    if z then
        return checkTerrainInZone(z, "Water")
    end
    return false
end
function TriggerPlayerTurn(playerColor, previousColor)
    current_turn_system_color = playerColor
    for color, aplayer in pairs(ActivePlayer) do
        if aplayer.boardGUID then
            local board = getObjectFromGUID(aplayer.boardGUID)
            if board then
                board.call("onPlayerTurn", {player = playerColor, previous_player = previousColor})
            end
        end
    end
    -- personel_panel의 onPlayerTurn이 작동하지 않는 경우(옛 세이브)를 위한 직접 PhaseHUD 업데이트
    Wait.time(function()
        local phaseActive = self.UI.getAttribute("PhaseHUD", "active")
        if phaseActive ~= "true" and phaseActive ~= "True" then
            self.UI.setAttribute("PhaseHUD_Image", "image", "https://steamusercontent-a.akamaihd.net/ugc/2452852111559737310/4117293ACF34F339124FF95FC029613EEB4F8E01/")
            self.UI.setAttribute("PhaseHUD_Text", "text", "Movement Phase")
            self.UI.setAttribute("PhaseHUD", "visibility", playerColor or "")
            self.UI.setAttribute("PhaseHUD", "active", "true")
            broadcastToAll("Movement Phase", playerColor)
        end
        
        -- 턴 시작 행동 카드 체크
        UpdateAllPlayerTerrainUI()
        
        local rawZone = getPlayerQuadrantGlobal(playerColor)
        if rawZone then
            local pZone = convertToRelativeQuadrant(rawZone)
            
            TriggerBehaviorCheck({
                type = "TurnStart",
                color = playerColor,
                data = { zone = pZone }
            })
            
            local hasWater = checkTerrainInZone(rawZone, "Water")
            if hasWater then
                TriggerBehaviorCheck({
                    type = "TurnStart",
                    color = playerColor,
                    data = { terrain = "Water" }
                })
            end
        end
        
        local anyFlank = false
        local anyRear = false
        for c, _ in pairs(ActivePlayer) do
            local z = getPlayerQuadrantGlobal(c)
            local pz = convertToRelativeQuadrant(z)
            if pz == "Flank" then anyFlank = true end
            if pz == "Rear" then anyRear = true end
        end
        
        if anyFlank then
            TriggerBehaviorCheck({ type = "TurnStart", color = playerColor, data = { anyZone = "Flank" } })
        end
        if anyRear then
            TriggerBehaviorCheck({ type = "TurnStart", color = playerColor, data = { anyZone = "Rear" } })
        end
        
    end, 0.5)
end

function GetCurrentFirstPlayer()
    return current_first_player
end

function ClearFirstPlayer()
    current_first_player = nil
    UpdateFirstPlayerUI()
end

function UpdateTurnOrder(params)
    local firstColor = params.color
    current_first_player = firstColor
    UpdateFirstPlayerUI()
    local baseOrder = {"Green", "Blue", "Red", "Orange", "Yellow"}
    
    local startIndex = 1
    for i, color in ipairs(baseOrder) do
        if color == firstColor then
            startIndex = i
            break
        end
    end
    
    local newOrder = {}
    for i = 0, 4 do
        local idx = ((startIndex - 1 + i) % 5) + 1
        table.insert(newOrder, baseOrder[idx])
    end
    
    saved_turn_order = newOrder
    
    if is_player_turn_active then
        -- Turns.type = 2 -- Custom Turn Order
        -- Turns.order = newOrder
        SetTurnSystemActive(true)
        Turns.enable = false
        if current_turn_system_color ~= firstColor then
            local prev = current_turn_system_color
            TriggerPlayerTurn(firstColor, prev)
        end
    end
end

function CheckGameReady()
    if not is_player_turn_active then
        SetTurnSystemActive(false)
        -- Turns.type = 2
        -- Turns.order = {}
    else
        if _checkGameReadyTimer then
            Wait.stop(_checkGameReadyTimer)
            _checkGameReadyTimer = nil
        end
        return
    end

    if is_game_started then return end
    
    local seated = getSeatedPlayers()
    if #seated == 0 then return end
    
    local allPlaced = true
    local missingColors = {}
    local hasAnyValidPlayer = false
    for _, color in ipairs(seated) do
        local aplayer = ActivePlayer[color]
        if aplayer then
            local pBoard = getObjectFromGUID(aplayer.boardGUID)
            if pBoard then
                -- 이 플레이어가 actor_mini를 가지고 있는지 먼저 확인
                -- actor_mini가 없으면 캐릭터를 아직 선택하지 않은 것이므로 무시
                local hasMini = false
                local ownerObjs = getObjectsWithTag("owner_" .. color)
                for _, obj in ipairs(ownerObjs) do
                    if obj.hasTag("actor_mini") then
                        hasMini = true
                        break
                    end
                end
                
                if hasMini then
                    hasAnyValidPlayer = true
                    if not HasCharacterPlaced(color) then
                        allPlaced = false
                        table.insert(missingColors, color)
                    end
                end
            end
        end
    end
    
    if not hasAnyValidPlayer then return end
    if not allPlaced then return end
    if CurrentMonster == nil or CurrentMonster == "" then return end
    -- 맵 버튼 대신 화면 UI(HUD)에 버튼 생성
    local xmlTable = self.UI.getXmlTable()
    local hasStartUI = false
    local hasUpkeepUI = false
    local hasNextRoundUI = false
    local hasConsumeUI = false
    local hasQuickRefreshUI = false
    if xmlTable then
        for _, el in ipairs(xmlTable) do
            if el.attributes and el.attributes.id == "startGamePanel" then
                hasStartUI = true
            elseif el.attributes and el.attributes.id == "upkeepPhasePanel" then
                hasUpkeepUI = true
            elseif el.attributes and el.attributes.id == "nextRoundPanel" then
                hasNextRoundUI = true
            elseif el.attributes and el.attributes.id == "consumePhasePanel" then
                hasConsumeUI = true
            elseif el.attributes and el.attributes.id == "quickRefreshPanel" then
                hasQuickRefreshUI = true
            end
        end
    else
        xmlTable = {}
    end
    
    if not hasStartUI then
        table.insert(xmlTable, {
            tag = "Panel",
            attributes = {
                id = "startGamePanel",
                rectAlignment = "TopCenter",
                offsetXY = "0 450",
                width = "160",
                height = "40"
            },
            children = {
                {
                    tag = "Button",
                    attributes = {
                        id = "startGameBtnUI",
                        onClick = "ClickStartGame",
                        text = "Game Start",
                        fontSize = "26",
                        color = "#4CAF50",
                        textColor = "#FFFFFF"
                    }
                }
            }
        })
    end
    
    if not hasUpkeepUI then
        table.insert(xmlTable, {
            tag = "Panel",
            attributes = {
                id = "upkeepPhasePanel",
                rectAlignment = "TopCenter",
                offsetXY = "0 450",
                width = "200",
                height = "40",
                active = "false"
            },
            children = {
                {
                    tag = "Button",
                    attributes = {
                        id = "upkeepPhaseBtnUI",
                        onClick = "ClickUpkeepPhase",
                        text = "Upkeep Phase",
                        fontSize = "24",
                        color = "#FF9800",
                        textColor = "#FFFFFF"
                    }
                }
            }
        })
    end
    
    if not hasConsumeUI then
        table.insert(xmlTable, {
            tag = "Panel",
            attributes = {
                id = "consumePhasePanel",
                rectAlignment = "TopCenter",
                offsetXY = "0 450",
                width = "200",
                height = "40",
                active = "false"
            },
            children = {
                {
                    tag = "Button",
                    attributes = {
                        id = "consumePhaseBtnUI",
                        onClick = "ClickConsumePhase",
                        text = "Consume Phase",
                        fontSize = "24",
                        color = "#888888",
                        textColor = "#FFFFFF"
                    }
                }
            }
        })
    end
    
    if not hasNextRoundUI then
        table.insert(xmlTable, {
            tag = "Panel",
            attributes = {
                id = "nextRoundPanel",
                rectAlignment = "TopCenter",
                offsetXY = "0 450",
                width = "200",
                height = "40",
                active = "false"
            },
            children = {
                {
                    tag = "Button",
                    attributes = {
                        id = "nextRoundBtnUI",
                        onClick = "NextRound",
                        text = "Next Round",
                        fontSize = "24",
                        color = "#2196F3",
                        textColor = "#FFFFFF"
                    }
                }
            }
        })
    end
    
    if not hasQuickRefreshUI then
        table.insert(xmlTable, {
            tag = "Panel",
            attributes = {
                id = "quickRefreshPanel",
                rectAlignment = "TopCenter",
                offsetXY = "0 450",
                width = "280",
                height = "40",
                active = "false"
            },
            children = {
                {
                    tag = "HorizontalLayout",
                    attributes = {
                        spacing = "10"
                    },
                    children = {
                        {
                            tag = "Button",
                            attributes = {
                                id = "quickRefreshBtnUI",
                                onClick = "ClickQuickRefresh",
                                text = "Quick Refresh",
                                fontSize = "22",
                                color = "#4CAF50",
                                textColor = "#FFFFFF",
                                preferredWidth = "180"
                            }
                        },
                        {
                            tag = "Button",
                            attributes = {
                                id = "blindRefreshBtnUI",
                                onClick = "ClickBlindRefresh",
                                text = "Blind",
                                fontSize = "22",
                                color = "#313131ff",
                                textColor = "#FFFFFF",
                                preferredWidth = "90"
                            }
                        }
                    }
                }
            }
        })
    end
    
    if not hasStartUI or not hasUpkeepUI or not hasNextRoundUI or not hasConsumeUI or not hasQuickRefreshUI then
        self.UI.setXmlTable(xmlTable)
    end
    self.UI.setAttribute("startGamePanel", "active", "true")
    
    -- 루프 중지
    if _checkGameReadyTimer then
        Wait.stop(_checkGameReadyTimer)
        _checkGameReadyTimer = nil
    end
end

function ResetGameToInitial()
    is_game_started = false
    is_player_turn_active = false
    
    Global.UI.setAttribute("startGamePanel", "active", "false")
    Global.UI.setAttribute("consumePhasePanel", "active", "false")
    Global.UI.setAttribute("quickRefreshPanel", "active", "false")
    Global.UI.setAttribute("upkeepPhasePanel", "active", "false")
    Global.UI.setAttribute("nextRoundPanel", "active", "false")
    
    clearAllTurnEndDecals()
    
    if not _checkGameReadyTimer then
        _checkGameReadyTimer = Wait.time(CheckGameReady, 2, -1)
    end
end

function ClickStartGame()
    -- 보드 상태와 Global 상태가 일치하는지 검증 (과거의 잘못된 세이브 파일 방어)
    if current_first_player ~= nil then
        local valid = false
        for _, obj in ipairs(getObjectsWithTag("player_board")) do
            local color = obj.call('getMatColorFromTag')
            if color == current_first_player then
                if obj.getVar('is_first_player') == true then
                    valid = true
                end
                break
            end
        end
        if not valid then
            current_first_player = nil
            UpdateFirstPlayerUI()
        end
    end

    if current_first_player == nil then
        broadcastToAll("선플레이어를 먼저 정해주세요.", {1, 0, 0})
        return
    end
    
    -- 전체 필드의 피규어 개수를 카운트 (실제 게임에 참여하는지 판별)
    local totalMinis = 0
    for color, aplayer in pairs(ActivePlayer) do
        local hasMini = false
        local objs = getObjectsWithTag("owner_" .. color)
        for _, obj in ipairs(objs) do
            if obj.hasTag("actor_mini") then
                hasMini = true
                break
            end
        end
        if hasMini then
            totalMinis = totalMinis + 1
        end
    end

    -- 참여 중인 피규어가 하나도 없을 때만 시작 방지
    if totalMinis == 0 then
        broadcastToAll("캐릭터를 선택하세요. (게임에 참여할 피규어가 없습니다)", {1, 0, 0})
        return
    end
    
    is_game_started = true
    
    -- Initialize turn order visually
    ResetUIButtonsOrder()
    
    -- UI 버튼 숨기기
    self.UI.setAttribute("startGamePanel", "active", "false")
    
    -- 플레이어 피규어들을 몬스터 보드의 정면(Front)으로 이동
    local combatBoardGUID = GetCombatBoardGUID()
    if combatBoardGUID then
        for color, aplayer in pairs(ActivePlayer) do
            local objs = getObjectsWithTag("owner_" .. color)
            for _, obj in ipairs(objs) do
                if obj.hasTag("actor_mini") then
                    if not _G.validStartSnapPositions then
                        _G.validStartSnapPositions = {}
                        local allCandidates = {}
                        local combatBoard = getObjectFromGUID(combatBoardGUID)
                        
                        -- "figure_1" ~ "figure_5" 태그가 달린 스냅포인트 좌표를 명시적으로 찾음
                        local figureSnaps = {"figure_1", "figure_2", "figure_3", "figure_4", "figure_5"}
                        for i = 1, #figureSnaps do
                            local p = getWorldPosOfSnapOnObj({combatBoardGUID, figureSnaps[i]})
                            if p then table.insert(allCandidates, p) end
                        end
                        
                        -- 만약 figure 태그가 하나도 안 달려있다면 안전장치로 기존 terrain_1~3을 강제로 사용
                        if #allCandidates == 0 then
                            broadcastToAll("경고: 'figure' 계열 태그가 달린 스냅포인트를 찾을 수 없어 기본 3개(terrain_1~3)를 사용합니다.", {1, 0, 0})
                            local fallbackSnaps = {"terrain_1", "terrain_2", "terrain_3"}
                            for i = 1, #fallbackSnaps do
                                local p = getWorldPosOfSnapOnObj({combatBoardGUID, fallbackSnaps[i]})
                                if p then table.insert(allCandidates, p) end
                            end
                        end
                        
                        -- 각 후보 위치에 수풀 등 지형물이 있는지 체크하여 빈 자리만 추출
                        for _, tryPos in ipairs(allCandidates) do
                            local occupied = false
                            for _, checkObj in ipairs(getObjects()) do
                                if (checkObj.type == "Tile" or checkObj.type == "Custom_Model" or checkObj.type == "Generic") then
                                    if checkObj.guid ~= combatBoardGUID and not checkObj.hasTag("actor_mini") and not checkObj.hasTag("Monster") then
                                        local p = checkObj.getPosition()
                                        if math.abs(p.y - tryPos.y) < 5 then
                                            local dist = math.sqrt((p.x - tryPos.x)^2 + (p.z - tryPos.z)^2)
                                            if dist < 0.8 then
                                                occupied = true
                                                break
                                            end
                                        end
                                    end
                                end
                            end
                            if not occupied then table.insert(_G.validStartSnapPositions, tryPos) end
                        end
                        
                        -- 만약 빈 자리가 하나도 없다면 겹치는 것을 감수하고 모든 후보를 반환
                        if #_G.validStartSnapPositions == 0 then
                            for _, p in ipairs(allCandidates) do table.insert(_G.validStartSnapPositions, p) end
                        end
                        
                        _G.validStartSnapIdx = 1
                    end

                    local destPos = _G.validStartSnapPositions[_G.validStartSnapIdx]

                    _G.validStartSnapIdx = _G.validStartSnapIdx + 1
                    if _G.validStartSnapIdx > #_G.validStartSnapPositions then
                        _G.validStartSnapIdx = 1
                    end

                    if destPos then
                        destPos.y = destPos.y + 2 -- 살짝 위에서 떨어지도록
                        obj.setPositionSmooth(destPos, false, true)
                        
                        -- 피규어가 몬스터를 바라보도록 회전 (몬스터 보드의 회전값을 기준으로 180도)
                        local combatBoard = getObjectFromGUID(combatBoardGUID)
                        if combatBoard then
                            local boardRot = combatBoard.getRotation()
                            obj.setRotationSmooth({0, boardRot.y + 180, 0}, false, true)
                        end
                    end
                    break -- 각 색상당 하나의 피규어만
                end
            end
        end
        _G.validStartSnapIdx = nil
        _G.validStartSnapPositions = nil
    end
    
    -- 각 플레이어 보드에서 덱 셔플 및 초기 드로우(5장) 실행
    for _, board in ipairs(getObjectsWithTag('player_board')) do
        board.call('startGameDraw')
    end
    
    -- 소모단계 안내 및 소모단계 버튼 표시
    broadcastToAll("--- 소모 단계 ---", {0.5, 0.5, 0.5})
    self.UI.setAttribute("consumePhasePanel", "active", "true")
    
    -- 피규어 이동(setPositionSmooth)이 완료될 무렵(약 1.5초 후) 지형을 한 번 스캔하도록 예약
    Wait.time(UpdateAllPlayerTerrainUI, 1.5)
end

function ClickConsumePhase(player, value, id)
    if player then
        local pColor = player.color
        local firstPlayer = current_first_player
        
        if firstPlayer == nil then
            broadcastToAll("선플레이어가 지정되지 않았습니다.", pColor)
            return
        end
        
        if pColor ~= firstPlayer then
            broadcastToAll("선플레이어가 아닙니다.", pColor)
            return
        end
    end

    Wait.frames(function()
        Global.UI.setAttribute("consumePhasePanel", "active", "false")
    end, 1)
    
    -- 유지단계 안내 및 유지단계 버튼 표시
    broadcastToAll("--- 몬스터 유지 단계 ---", {1, 0.5, 0})
    self.UI.setAttribute("upkeepPhasePanel", "active", "true")
end

function ClickUpkeepPhase(player, value, id)
    if player then
        local pColor = player.color
        local firstPlayer = current_first_player
        
        if firstPlayer == nil then
            broadcastToAll("선플레이어가 지정되지 않았습니다.", pColor)
            return
        end
        
        if pColor ~= firstPlayer then
            broadcastToAll("선플레이어가 아닙니다.", pColor)
            return
        end
    end

    Wait.frames(function()
        Global.UI.setAttribute("upkeepPhasePanel", "active", "false")
    end, 1)
    
    SetFirstPlayerToAggro()
    ResetUIButtonsOrder(true)
    
    -- 실제 업킵 동작 실행
    DoMonsterUpkeep(nil, nil, "upkeepPhaseBtnUI")
    
    -- 업킵 동작이 끝날 때까지 대기 후 턴 활성화
    Wait.condition(
        function()
            is_player_turn_active = true
            
            -- 턴 시스템 활성화
            -- Turns.type = 2
            -- Turns.order = saved_turn_order
            SetTurnSystemActive(true)
            Turns.enable = false
            
            local firstColorToStart = current_first_player
            if saved_turn_order and #saved_turn_order > 0 then
                firstColorToStart = saved_turn_order[1] or current_first_player
            end
            
            if firstColorToStart then
                local isSeated = false
                for _, pColor in ipairs(getSeatedPlayers()) do
                    if pColor == firstColorToStart then
                        isSeated = true
                        break
                    end
                end
                if not isSeated then
                    local seated = getSeatedPlayers()
                    if #seated > 0 then
                        Player[seated[1]].changeColor(firstColorToStart)
                    end
                end
            end

            -- TTS 엔진 버그 우회: 턴이 기존 색상과 똑같으면 턴 시작 소리가 안 나므로 강제로 변경했다가 원상복구
            if current_turn_system_color == firstColorToStart then
                local dummyColor = "White"
                for _, c in ipairs(Player.getColors()) do
                    if c ~= firstColorToStart then
                        dummyColor = c
                        break
                    end
                end
                -- current_turn_system_color = dummyColor
            end
            local prev = current_turn_system_color
            
            broadcastToAll("플레이어의 턴이 시작되었습니다! " .. (firstColorToStart or "플레이어") .. "의 턴입니다.", {1, 1, 1})
            TriggerPlayerTurn(firstColorToStart, prev)
            
            -- Automatically move Aggro token
            if type(SetAggroTarget) == "function" then
                SetAggroTarget(firstColorToStart)
            end
        end,
        function() return not isUpkeepRunning end
    )
end



function HasCharacterPlaced(color)
    local aplayer = ActivePlayer[color]
    if not aplayer then return false end
    
    local targetTag = "owner_" .. color
    local objs = getObjectsWithTag(targetTag)
    if #objs == 0 then return false end
    
    local pBoard = getObjectFromGUID(aplayer.boardGUID)
    local pBoardPos = pBoard and pBoard.getPosition() or nil
    
    local cBoardGUID = nil
    if type(GetCombatBoardGUID) == "function" then
        cBoardGUID = GetCombatBoardGUID()
    end
    local cBoard = cBoardGUID and getObjectFromGUID(cBoardGUID) or nil
    local cBoardPos = cBoard and cBoard.getPosition() or nil
    local cBoardBounds = cBoard and cBoard.getBounds() or nil
    local cHalfX = cBoardBounds and (cBoardBounds.size.x / 2) or 0
    local cHalfZ = cBoardBounds and (cBoardBounds.size.z / 2) or 0
    
    for _, obj in ipairs(objs) do
        local op = obj.getPosition()
        
        -- 1. 개인 보드 근처(거리 9 이내)에 있는지 확인
        if pBoardPos and math.abs(op.x - pBoardPos.x) < 9 then
            return true
        end
        
        -- 2. 컴뱃 보드(전투 맵) 위에 있는지 확인
        if cBoardPos and math.abs(op.x - cBoardPos.x) <= cHalfX and math.abs(op.z - cBoardPos.z) <= cHalfZ then
            return true
        end
    end
    
    return false
end

function GetNextAlivePlayer(startColor)
    local order = saved_turn_order
    if not order or #order == 0 then return nil end
    
    local currentIndex = 0
    for i, color in ipairs(order) do
        if color == startColor then currentIndex = i end
    end
    
    local nextIndex = currentIndex
    for _ = 1, #order do
        nextIndex = nextIndex + 1
        if nextIndex > #order then nextIndex = 1 end
        
        local candidate = order[nextIndex]
        if candidate ~= startColor and HasCharacterPlaced(candidate) and not isPlayerKOGlobal(candidate) then
            return candidate
        end
    end
    return nil
end

function CheckDefeatCondition()
    local participatingColors = {}
    if ActivePlayer then
        for color, _ in pairs(ActivePlayer) do
            -- actor_mini가 있는 플레이어만 참전 중으로 판단
            local hasMini = false
            local ownerObjs = getObjectsWithTag("owner_" .. color)
            for _, obj in ipairs(ownerObjs) do
                if obj.hasTag("actor_mini") then
                    hasMini = true
                    break
                end
            end
            if hasMini then
                table.insert(participatingColors, color)
            end
        end
    end
    
    if #participatingColors == 0 then return false end
    
    local allDefeated = true
    for _, color in ipairs(participatingColors) do
        local pBoard = nil
        for _, board in ipairs(getObjectsWithTag('player_board')) do
            if board.call('getMatColorFromTag') == color then
                pBoard = board
                break
            end
        end
        
        if pBoard then
            local isKO = pBoard.call('isPlayerKO')
            if not isKO then
                allDefeated = false
                break
            end
        else
            allDefeated = false
        end
    end
    
    if allDefeated then
        broadcastToAll("패배 하였습니다.", {1, 0, 0})
        return true
    end
    return false
end

local quick_refresh_pending = false

function PassTurn()
    if CurrentMonster == "Nagarjas" and not quick_refresh_pending then
        Global.UI.setAttribute("quickRefreshPanel", "active", "true")
        broadcastToAll("--- 행동 재활성화 (Quick Refresh) 대기 중 ---", {0.2, 0.8, 1.0})
        quick_refresh_pending = true
        return
    end
    
    quick_refresh_pending = false
    DoPassTurn()
end

function DoPassTurn()
    if not is_game_started then return end
    
    if GetTurnSystemActive() then
        local current = current_turn_system_color
        local order = saved_turn_order
        
        if current and order and #order > 0 then
            -- 턴이 종료된 현재 플레이어 보드에 Turn End 데칼 켜기
            for _, obj in ipairs(getObjectsWithTag("player_board")) do
                local color = obj.call('getMatColorFromTag')
                if color == current then
                    obj.call('setTurnEndVisualOnly', {enabled = true})
                    break
                end
            end

            local currentIndex = 0
            for i, color in ipairs(order) do
                if color == current then currentIndex = i end
            end
            
            local nextColor = nil
            local nextIndex = currentIndex
            
            -- 순서대로 다음 플레이어를 찾음 (기물이 배치된 자리만 유효)
            for _ = 1, #order do
                nextIndex = nextIndex + 1
                if nextIndex > #order then
                    -- 순서가 끝까지 도달했으므로 라운드 종료
                    break
                end
                
                local candidate = order[nextIndex]
                if HasCharacterPlaced(candidate) then
                    nextColor = candidate
                    break
                end
            end
            
            if nextColor == nil then
                SetTurnSystemActive(false)
                broadcastToAll("모든 플레이어의 턴이 종료되었습니다. 다음 라운드로 진행해주세요.", {1,1,1})
                self.UI.setAttribute("nextRoundPanel", "active", "true")
                TriggerBehaviorCheck({ type = "RoundEnd" })
            else
                -- 자동 착석 로직 (빈 자리에 기물이 있으면 현재 플레이어가 이동)
                -- 턴을 넘기기 '전에' 자리를 먼저 옮겨야 TTS가 빈 자리라고 스킵하지 않음
                local isSeated = false
                for _, pColor in ipairs(getSeatedPlayers()) do
                    if pColor == nextColor then
                        isSeated = true
                        break
                    end
                end
                
                if not isSeated then
                    local currentPlayerObj = Player[current]
                    if currentPlayerObj and currentPlayerObj.seated then
                        currentPlayerObj.changeColor(nextColor)
                    end
                end
                
                local prev = current_turn_system_color
                TriggerPlayerTurn(nextColor, prev)
            end
        end
    end
end


--- monster setups related functions

function CleanMonster()
	MonsterData = {}
	CurrentMonster= ""
	FightLevel = "0"
	CurrentRound = 0
	ResetGameToInitial()

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
    
    -- 몬스터 보드 위의 플레이어 피규어들을 각자의 보드로 귀환 (게임이 진행 중일 때 클린업 한 경우에만)
    if is_game_started then
        for color, aplayer in pairs(ActivePlayer) do
            local pBoard = getObjectFromGUID(aplayer.boardGUID)
            if pBoard then
                local pBoardPos = pBoard.getPosition()
                local figs = getObjectsWithTag("owner_" .. color)
                for _, fig in ipairs(figs) do
                    if fig.hasTag("actor_mini") then
                        local dest = {x = pBoardPos.x + 2, y = pBoardPos.y + 2, z = pBoardPos.z}
                        fig.setPositionSmooth(dest, false, true)
                    end
                end
            end
        end
    end
    
    -- 클린업 이후 게임 상태 UI 초기화 (진행 여부 관계없이 무조건 실행하여 Start Game 버튼 등을 숨김)
    ResetGameToInitial()
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
                        callback_function = function(storebag)
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
	local attpos = getWorldPosOfSnapOnObj({"fa932e"})
	local actorData = {
    position = attpos,
    rotation = featureData.rotation,
    actor_tag = "actor_attrition",
  }

  spawnActorFromBag(actorData, bag, function(actor)
      Wait.time(function()
          if actor and not actor.isDestroyed() and actor.type == "Deck" then
              actor.shuffle()
              printToAll("마찰덱을 섞었습니다.", {0.5, 0.5, 1})
          end
      end, 1.0)
  end)
end

function HasAttritionDeck()
    local monsterBoard = getObjectFromGUID("fa932e")
    if not monsterBoard then return false end
    
    local deckLocal = {x = 1.2368, y = 0.2106, z = 0.8573}
    
    for _, obj in ipairs(getAllObjects()) do
        if obj.type == "Deck" or obj.type == "Card" then
            local pos = obj.getPosition()
            local localPos = monsterBoard.positionToLocal(pos)
            local dx = localPos.x - deckLocal.x
            local dz = localPos.z - deckLocal.z
            local dist = math.sqrt(dx*dx + dz*dz)
            if dist < 0.5 then
                return true
            end
        end
    end
    return false
end

function MonsterUsesAttrition()
    if MonsterData and MonsterData["attrition"] and MonsterData["attrition"] ~= "" then
        return true
    end
    return false
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

function NextRound(player, value, id)
    if id == "btnNext" then return end
    if not is_game_started then return end
    
    if player then
        local pColor = player.color
        local lastPlayer = current_turn_system_color
        
        if lastPlayer and pColor ~= lastPlayer then
            broadcastToAll("마지막 플레이어만 다음라운드로 진행 가능합니다.", pColor)
            return
        end
    end

    if os.clock() - lastClickTime < 0.2 then return end
    lastClickTime = os.clock()
    
    Wait.frames(function()
        Global.UI.setAttribute("nextRoundPanel", "active", "false")
        Global.UI.setAttribute("quickRefreshPanel", "active", "false")
    end, 1)
    
    is_player_turn_active = false
    SetTurnSystemActive(false)
    -- Turns.type = 2
    -- Turns.order = {}
    
    SetFirstPlayerToAggro()
    ResetUIButtonsOrder(true)

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
    ProcessFireTokens()
    ProcessDustTokens()
    ProcessMonsterStatusTokens()
    clearAllTurnEndDecals()
    
    if not _checkGameReadyTimer then
        _checkGameReadyTimer = Wait.time(CheckGameReady, 2, -1)
    end
    
    -- 다음 라운드 진입 시 소모단계 안내 및 소모단계 버튼 표시
    broadcastToAll("--- 소모 단계 ---", {0.5, 0.5, 0.5})
    self.UI.setAttribute("consumePhasePanel", "active", "true")
end

function AdvanceRoundToken()
    local currentPos = 1
    local activeBoardGUID = GetCombatBoardGUID()
    if activeBoardGUID then
        local boardObj = getObjectFromGUID(activeBoardGUID)
        if boardObj then
            local rn = boardObj.getVar("RoundNumber")
            if rn and rn > 0 then
                currentPos = rn
            else
                currentPos = CurrentRound
            end
        end
    end
    
    local nextRound = currentPos + 1
    if nextRound > 10 then nextRound = 1 end
    CurrentRound = nextRound
    
    for _, guid in ipairs(CombatBoardGUIDs) do
        local board = getObjectFromGUID(guid)
        if board then
            board.call("SetRound", nextRound)
        end
    end
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
        local rot = token.getRotation()
        -- 모든 플레이어의 토큰을 항상 앞면(ON 상태, z=0)으로 초기화
        if rot.z > 45 and rot.z < 315 then
            token.setRotationSmooth({rot.x, rot.y, 0}, false, true)
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

function RotateMonsterToAggro(forcedColor)
    local aggroColor = forcedColor
    if not aggroColor then
        for color, _ in pairs(ActivePlayer) do
            local img = Global.UI.getAttribute("aggro_" .. color, "image")
            if img == URL_AGGRO_ON then aggroColor = color; break end
        end
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
    
    local diff = math.abs(currentRot.y - targetRotY)
    if diff > 180 then diff = math.abs(diff - 360) end
    local directionChanged = (diff > 5)
    
    monster.setRotationSmooth({currentRot.x, targetRotY, currentRot.z}, false, false)

    if directionChanged then
        broadcastToAll(
            string.format("몬스터가 (%s)(%s) 을 향해 회전하였습니다.", aggroColor, playerFig.getName()),
            Color[aggroColor]
        )
        TriggerBehaviorCheck({ type = "MonsterDirection" })
    else
        broadcastToAll(
            string.format("몬스터가 회전하지 않고 (%s)(%s) 어그로 플레이어를 주시합니다.", aggroColor, playerFig.getName()),
            Color[aggroColor]
        )
    end
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
            if obj:hasTag("Struggle") then count = count + 1 end
        end
    end
    return count
end

function getAccelCount()
    local zone = getObjectFromGUID(allZone.AccelData.zoneGUID)
    local count = 0
    if zone then
        for _, obj in ipairs(zone.getObjects()) do
            if obj:hasTag("Accel") then count = count + 1 end
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

function FixPanelDrag()
    Wait.frames(function()
        local xmlTable = Global.UI.getXmlTable()
        if not xmlTable then return end
        
        local changed = false
        
        local function searchXML(node)
            if node.attributes and node.attributes.allowDragging then
                if node.attributes.allowDragging == "true" or node.attributes.allowDragging == "True" then
                    node.attributes.allowDragging = "false"
                    changed = true
                end
            end
            if node.children then
                for _, child in ipairs(node.children) do
                    searchXML(child)
                end
            end
        end
        
        searchXML({children = xmlTable})
        
        if changed then
            Global.UI.setXmlTable(xmlTable)
        end
    end, 2)
end

local player_hand_counts = {}

function checkEmptyHandTrigger(color)
    if not is_game_started then return end
    
    local p = Player[color]
    if p and p.seated and ActivePlayer[color] then
        -- 기물(actor_mini)가 보드에 있는지 확인
        local quadrant = getPlayerQuadrantGlobal(color)
        if quadrant then
            local ok, handObjs = pcall(function() return p.getHandObjects() end)
            if ok and handObjs then
                local current_size = #handObjs
                local prev_size = player_hand_counts[color] or 0
                
                if prev_size > 0 and current_size == 0 then
                    -- 핸드가 1 이상에서 0으로 떨어졌을 때만 트리거
                    TriggerBehaviorCheck({ type = "EmptyHand", color = color })
                end
                player_hand_counts[color] = current_size
            end
        else
            player_hand_counts[color] = nil
        end
    else
        player_hand_counts[color] = nil
    end
end

function onLoad(script_state)

    Wait.time(checkBehaviorFlips, 1, -1)
    Turns.enable = false
    Turns.enable = false
    FixPanelDrag()
    
    -- 몬스터 보드 데칼 이미지 프리로드 (흰색 네모 깜빡임 방지)
    -- 보이지 않는 테이블 저 아래에 토큰을 미리 생성해두어 텍스쳐를 캐싱합니다.
    local preloadToken = spawnObject({
        type = "Custom_Token",
        position = {0, -100, 0},
        scale = {0.01, 0.01, 0.01},
        sound = false,
    })
    preloadToken.setCustomObject({
        image = TRIGGER_IMAGE_URL,
        thickness = 0.1,
    })
    preloadToken.locked = true
    preloadToken.interactable = false
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
        is_turn_system_active = loaded_data.is_turn_system_active or false
        current_turn_system_color = loaded_data.current_turn_system_color
        saved_turn_order = loaded_data.saved_turn_order or {}
        current_first_player = loaded_data.current_first_player
        is_game_started = loaded_data.is_game_started or ((loaded_data.CurrentRound or 0) > 0)
        is_player_turn_active = loaded_data.is_player_turn_active or false
        
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
        CurrentRound= 1
        FightLevel= 1
        MonsterData= {}
    end

	SetBehavior()
    StartTurnUI()
    
    if not is_game_started then
        SetTurnSystemActive(false)
        _checkGameReadyTimer = Wait.time(CheckGameReady, 2, -1)
    else
        -- 게임이 이미 시작된 상태로 로드된 경우, 턴 시스템 복원
        -- 옛날 세이브에는 is_player_turn_active가 없으므로 is_game_started로 추론
        is_player_turn_active = true
        
        -- 활성 턴 색상 결정: 저장된 값 > 선공 플레이어 > 턴 순서 첫 번째
        local turnColor = current_turn_system_color
        if not turnColor then
            turnColor = current_first_player
        end
        if not turnColor and saved_turn_order and #saved_turn_order > 0 then
            turnColor = saved_turn_order[1]
        end
        
        if turnColor then
            SetTurnSystemActive(true)
            Wait.time(function()
                TriggerPlayerTurn(turnColor, nil)
                broadcastToAll(turnColor .. "의 턴입니다.", {1, 1, 1})
            end, 1)
        end
    end
    
    -- 플레이어 턴 버튼 조작 안내 툴팁 추가
    for _, btnId in pairs(COLOR_TO_BUTTON) do
        Global.UI.setAttribute(btnId, "tooltip", "좌클릭: 턴 순서 위로\n우클릭: 턴 순서 아래로")
    end
    Wait.time(function() UpdateAllPlayerTerrainUI() end, 3)
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
    saved_data = JSON.encode({ActivePlayer = ActivePlayer, CurrentMonster = CurrentMonster,CurrentRound=CurrentRound,FightLevel=FightLevel,MonsterData=MonsterData, is_turn_system_active=is_turn_system_active, current_turn_system_color=current_turn_system_color, saved_turn_order=saved_turn_order, current_first_player=current_first_player, is_game_started=is_game_started, is_player_turn_active=is_player_turn_active})
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
			local actionName = stanceAction[1]
			if actionName == "NextRound" then
				actionName = "AdvanceRoundToken"
			end
			_G[actionName](stanceAction[2] or nil)
		end
		end, 2)
end

function onObjectEnterZone(zone, object)
	if zone.type == "Hand" then
		local color = zone.getValue()
		if color then
			Wait.time(function() checkEmptyHandTrigger(color) end, 0.1)
		end
	end

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

				local desc = BehaviorDescription[img]
				if desc then
					local rule = BehaviorRules[desc]
					if rule and rule.event == "Immediate" then
						Wait.time(function()
							TriggerBehaviorCheck({ type = "Immediate" })
						end, 0.5)
					end
				end
			end
			break
		end
	end
 end

function onObjectLeaveZone(zone, leave_object)
	if zone.type == "Hand" then
		local color = zone.getValue()
		if color then
			Wait.time(function() checkEmptyHandTrigger(color) end, 0.1)
		end
	end

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

function EvaluateXitherosAggro()
    if CurrentMonster ~= "Xitheros" and CurrentMonster ~= "자이테로스" then return end
    
    local highestDamage = -1
    local highestColors = {}
    
    for color, aplayer in pairs(ActivePlayer) do
        local boardObj = getObjectFromGUID(aplayer.boardGUID)
        if boardObj then
            local dmg = boardObj.getVar("damage_counter") or 0
            if dmg > highestDamage then
                highestDamage = dmg
                highestColors = {color}
            elseif dmg == highestDamage then
                table.insert(highestColors, color)
            end
        end
    end
    
    if #highestColors == 0 then return end
    
    -- 동점자 처리: 현재 어그로를 가진 플레이어가 최고 피해자 그룹에 있다면 그대로 유지
    local currentAggroColor = nil
    for _, color in ipairs(highestColors) do
        local img = Global.UI.getAttribute("aggro_" .. color, "image")
        if img == URL_AGGRO_ON then
            currentAggroColor = color
            break
        end
    end
    
    if currentAggroColor then
        return
    else
        local targetColor = highestColors[1]
        SetAggroTarget(targetColor)
        printToAll("Xitheros 규칙: 가장 피해가 높은 " .. targetColor .. " 플레이어에게 어그로가 집중됩니다.", Color[targetColor] or {1,1,1})
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
                boardObj.call("enableAggro", {hideBroadcast=true})
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
                boardObj.call("enableFirstPlayer", true)  -- hideBroadcast=true (메시지 스팸 방지)
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

function changeHand(player, value, id)
    broadcastToAll("changeHand called! player: " .. tostring(player) .. ", value: " .. tostring(value) .. ", id: " .. tostring(id))
    if type(player) == "table" and value == nil and id == nil then
        changecolor(player[1] or "", player[2], player[3])
    else
        changecolor(player, value, id)
    end
end

function ResetUIButtonsOrder(skipTurnJump)
    local xmlTable = Global.UI.getXmlTable()
    
    local btnList = {}
    local function gatherBtns(node)
        if node.children then
            for i, child in ipairs(node.children) do
                if child.tag == "Row" then
                    local extractBtnId = nil
                    local function findBtn(innerNode)
                        if innerNode.attributes and innerNode.attributes.id and BUTTON_TO_COLOR[innerNode.attributes.id] then
                            extractBtnId = innerNode.attributes.id
                        end
                        if innerNode.children then
                            for _, c in ipairs(innerNode.children) do findBtn(c) end
                        end
                    end
                    findBtn(child)
                    
                    if extractBtnId then
                        if child.attributes and child.attributes.active ~= "false" and child.attributes.active ~= "False" then
                            table.insert(btnList, {parent = node.children, idx = i, node = child, id = extractBtnId})
                        end
                    end
                end
                gatherBtns(child)
            end
        end
    end
    gatherBtns({children = xmlTable})
    
    if #btnList > 0 then
        local sortedItems = {}
        for _, item in ipairs(btnList) do
            table.insert(sortedItems, item)
        end
        
        local baseOrder = {"Green", "Blue", "Red", "Orange", "Yellow"}
        local orderMap = {}
        local startIndex = 1
        
        if current_first_player then
            for i, c in ipairs(baseOrder) do
                if c == current_first_player then
                    startIndex = i
                    break
                end
            end
        end
        
        for i = 1, #baseOrder do
            local color = baseOrder[startIndex]
            local btnId = COLOR_TO_BUTTON[color]
            if btnId then
                orderMap[btnId] = i
            end
            startIndex = startIndex + 1
            if startIndex > #baseOrder then startIndex = 1 end
        end

        table.sort(sortedItems, function(a, b)
            local rankA = orderMap[a.id] or 99
            local rankB = orderMap[b.id] or 99
            return rankA < rankB
        end)
        
        for i, item in ipairs(btnList) do
            item.parent[item.idx] = sortedItems[i].node
            
            -- Bypass TTS caching
            local newBase = "r_" .. tostring(math.random(100000, 999999))
            sortedItems[i].node.attributes.id = newBase .. "_row"
            
            local color = BUTTON_TO_COLOR[sortedItems[i].id]
            if ActivePlayer and ActivePlayer[color] then
                ActivePlayer[color].button = newBase
            end
            
            if color and sortedItems[i].node.children then
                local hasFP = false
                
                local function findAndSetFP(node)
                    if node.attributes and node.attributes.id == "first_player_" .. color then
                        node.attributes.active = (color == current_first_player) and "true" or "false"
                        hasFP = true
                    end
                    if node.children then
                        for _, c in ipairs(node.children) do
                            findAndSetFP(c)
                        end
                    end
                end
                
                for _, child in ipairs(sortedItems[i].node.children) do
                    findAndSetFP(child)
                end
                
                if not hasFP then
                    table.insert(sortedItems[i].node.children, {
                        tag = "Cell",
                        children = {
                            {
                                tag = "Panel",
                                attributes = {
                                    preferredWidth = "35",
                                    preferredHeight = "35"
                                },
                                children = {
                                    {
                                        tag = "Image",
                                        attributes = {
                                            id = "first_player_" .. color,
                                            image = FIRST_PLAYER_URLS[color] or "",
                                            width = "25",
                                            height = "25",
                                            rotation = "0 0 -45",
                                            rectAlignment = "MiddleCenter",
                                            offsetXY = "-25 0",
                                            active = (color == current_first_player) and "true" or "false"
                                        }
                                    }
                                }
                            }
                        }
                    })
                end
            end
        end
        
        Global.UI.setXmlTable(xmlTable)
        
        -- REBUILD Turns.order from the exact visual list!
        local newOrder = {}
        for _, item in ipairs(sortedItems) do
            local c = BUTTON_TO_COLOR[item.id]
            if c then
                table.insert(newOrder, c)
            end
        end
        
        if saved_turn_order and #saved_turn_order > 0 then
            -- Turns.order = newOrder
            if GetTurnSystemActive() and #newOrder > 0 and not skipTurnJump then
                -- The player at the very top of the UI gets the turn immediately!
                local nextColor = newOrder[1]
                
                local isSeated = false
                for _, pColor in ipairs(getSeatedPlayers()) do
                    if pColor == nextColor then
                        isSeated = true
                        break
                    end
                end
                
                if not isSeated then
                    local current = current_turn_system_color
                    local currentPlayerObj = Player[current]
                    if currentPlayerObj and currentPlayerObj.seated then
                        currentPlayerObj.changeColor(nextColor)
                    else
                        local seated = getSeatedPlayers()
                        if #seated > 0 then
                            Player[seated[1]].changeColor(nextColor)
                        end
                    end
                end
                
                local prev = current_turn_system_color
                
                broadcastToAll("플레이어의 턴이 시작되었습니다! " .. nextColor .. "의 턴입니다.", {1, 1, 1})
                TriggerPlayerTurn(nextColor, prev)
                
                -- Update the Aggro target automatically
                if type(SetAggroTarget) == "function" then
                    SetAggroTarget(nextColor)
                end
            end
        end
        saved_turn_order = newOrder
    end
end

function MoveUIButtonAndTurn(btnId, direction)
    local xmlTable = Global.UI.getXmlTable()
    
    local btnList = {}
    local function gatherBtns(node)
        if node.children then
            for i, child in ipairs(node.children) do
                if child.tag == "Row" then
                    local extractBtnId = nil
                    local function findBtn(innerNode)
                        if innerNode.attributes and innerNode.attributes.id and BUTTON_TO_COLOR[innerNode.attributes.id] then
                            extractBtnId = innerNode.attributes.id
                        end
                        if innerNode.children then
                            for _, c in ipairs(innerNode.children) do findBtn(c) end
                        end
                    end
                    findBtn(child)
                    
                    if extractBtnId then
                        if child.attributes and child.attributes.active ~= "false" and child.attributes.active ~= "False" then
                            table.insert(btnList, {parent = node.children, idx = i, node = child, id = extractBtnId})
                        end
                    end
                end
                gatherBtns(child)
            end
        end
    end
    gatherBtns({children = xmlTable})
    
    if #btnList > 0 then
        local pos = -1
        for i, item in ipairs(btnList) do
            if item.id == btnId then
                pos = i
                break
            end
        end
        
        if pos > 0 then
            local clickedColorAttr = Global.UI.getAttribute(btnId, "color") or "white"
            if clickedColorAttr == "#000000cc" or clickedColorAttr == "#000000CC" then
                return -- Ignore clicks on players whose turn is done
            end
            
            local targetPos = pos
            local found = false
            while true do
                targetPos = targetPos + direction
                if targetPos < 1 or targetPos > #btnList then
                    break
                end
                
                local targetColorAttr = Global.UI.getAttribute(btnList[targetPos].id, "color") or "white"
                if targetColorAttr ~= "#000000cc" and targetColorAttr ~= "#000000CC" then
                    found = true
                    break
                end
            end
            
            if not found then return end
            
            local item1 = btnList[pos]
            local item2 = btnList[targetPos]
            
            item1.parent[item1.idx] = item2.node
            item2.parent[item2.idx] = item1.node
            
            -- Update btnList to reflect the new swap so we can extract the correct visual order
            btnList[pos] = item2
            btnList[targetPos] = item1
            
            local color1 = BUTTON_TO_COLOR[item1.id]
            local color2 = BUTTON_TO_COLOR[item2.id]
            
            -- Apply dynamic IDs to force complete UI rerender
            local newId1 = "r_" .. tostring(math.random(100000, 999999))
            local newId2 = "r_" .. tostring(math.random(100000, 999999))
            item1.node.attributes.id = newId1 .. "_row"
            item2.node.attributes.id = newId2 .. "_row"
            
            if ActivePlayer and ActivePlayer[color1] then ActivePlayer[color1].button = newId1 end
            if ActivePlayer and ActivePlayer[color2] then ActivePlayer[color2].button = newId2 end
            
            Global.UI.setXmlTable(xmlTable)
            
            -- REBUILD Turns.order from the exact visual list!
            local newOrder = {}
            for _, item in ipairs(btnList) do
                local c = BUTTON_TO_COLOR[item.id]
                if c then
                    table.insert(newOrder, c)
                end
            end
            
            if saved_turn_order and #saved_turn_order > 0 then
                -- Turns.order = newOrder
                if GetTurnSystemActive() and #newOrder > 0 then
                    -- The player at the very top of the UI gets the turn immediately!
                    local nextColor = newOrder[1]
                    
                    local isSeated = false
                    for _, pColor in ipairs(getSeatedPlayers()) do
                        if pColor == nextColor then
                            isSeated = true
                            break
                        end
                    end
                    
                    if not isSeated then
                        local current = current_turn_system_color
                        local currentPlayerObj = current and Player[current]
                        if currentPlayerObj and currentPlayerObj.seated then
                            currentPlayerObj.changeColor(nextColor)
                        else
                            local seated = getSeatedPlayers()
                            if #seated > 0 then
                                Player[seated[1]].changeColor(nextColor)
                            end
                        end
                    end
                    
                    local prev = current_turn_system_color
                    
                    broadcastToAll("플레이어의 턴이 시작되었습니다! " .. nextColor .. "의 턴입니다.", {1, 1, 1})
                    TriggerPlayerTurn(nextColor, prev)
                    
                    -- Update the Aggro target automatically
                    if type(SetAggroTarget) == "function" then
                        SetAggroTarget(nextColor)
                    end
                end
            end
            saved_turn_order = newOrder
        end
    end
end

function changecolor(plr, toggleState, btnId)
    broadcastToAll("changecolor -> plr: " .. tostring(plr) .. ", state: " .. tostring(toggleState) .. ", id: " .. tostring(btnId))
    if toggleState == "-1" then
        -- 좌클릭: 이전 순서 (위로)
        MoveUIButtonAndTurn(btnId, -1)
    elseif toggleState == "-2" then
        -- 우클릭: 다음 순서 (아래로)
        MoveUIButtonAndTurn(btnId, 1)
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
    
    Wait.time(function() handleTerrainAdded(obj) end, 0.5)

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
    
    Wait.time(function() handleTerrainAdded(dropped_object) end, 0.5)

    for color, _ in pairs(ActivePlayer) do
        if dropped_object.hasTag("owner_" .. color) then
            StartTurnUI()
            local monsterBoard = getObjectFromGUID("fa932e")
            if monsterBoard then
                monsterBoard.call("updateMonsterToughnessFromActorStance")
            end
            
            if dropped_object.hasTag("actor_mini") then
                Wait.time(function()
                    if dropped_object == nil or dropped_object.isDestroyed() then return end
                    local newZone = getPlayerQuadrantGlobal(color)
                    UpdateAllPlayerTerrainUI()
                    local oldZone = actor_pickup_zone and actor_pickup_zone[dropped_object.getGUID()]
                    
                    if oldZone and newZone and oldZone ~= newZone then
                        TriggerBehaviorCheck({ type = "Move", color = color })
                        
                        local hasWater = checkTerrainInZone(newZone, "Water")
                        if hasWater then
                            TriggerBehaviorCheck({ type = "Move", color = color, data = { terrain = "Water" } })
                        end
                        
                        local aplayer = ActivePlayer[color]
                        if aplayer and aplayer.boardGUID then
                            local board = getObjectFromGUID(aplayer.boardGUID)
                            if board then
                                board.call("updateSequenceSlotDecals")
                            end
                        end
                    end
                    if actor_pickup_zone then actor_pickup_zone[dropped_object.getGUID()] = nil end
                end, 0.5)
            end
            break
        end
    end
    
    if CurrentMonster and dropped_object.getName() == CurrentMonster and dropped_object.hasTag("actor_mini") then
        Wait.time(function()
            if dropped_object == nil or dropped_object.isDestroyed() then return end
            local newRotY = dropped_object.getRotation().y
            if actor_pickup_rot_y then
                local diff = math.abs(newRotY - actor_pickup_rot_y)
                if diff > 180 then diff = math.abs(diff - 360) end
                if diff > 5 then
                    TriggerBehaviorCheck({ type = "MonsterDirection" })
                end
            end
            actor_pickup_rot_y = nil
        end, 0.5)
    end

    if dropped_object.type == "Card" then
        if dropped_object.hasTag("Aggro") or dropped_object.hasTag("어그로") then
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
end

function onObjectDestroy(destroyed_object)
    handleTerrainRemoved(destroyed_object)
    
    if destroyed_object.type == "Card" then
        Wait.time(ReevaluateCardPlayBehaviors, 0.5)
    end
    
    if destroyed_object.hasTag("monster_spawn") then
        Wait.time(function()
            local monsters = getObjectsWithTag("monster_spawn")
            local hasMonsterFigure = false
            for _, obj in ipairs(monsters) do
                if obj.type == "Figurine" or obj.type == "Custom_Model" or obj.type == "Custom_Assetbundle" then
                    hasMonsterFigure = true
                    break
                end
            end
            
            if not hasMonsterFigure then
                if type(SetTurnSystemActive) == "function" then
                    SetTurnSystemActive(false)
                end
                global_current_phase = 0
                if type(setGlobalPhaseHUD) == "function" then
                    setGlobalPhaseHUD(0)
                end
            end
        end, 0.5)
    end

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

aggro_history = {}

function ClearAggroHistory()
    aggro_history = {}
end

function SavePreviousAggro()
    for color, _ in pairs(ActivePlayer) do
        local img = Global.UI.getAttribute("aggro_" .. color, "image")
        if img == URL_AGGRO_ON then
            table.insert(aggro_history, color)
            break
        end
    end
end

function RevertAggro()
    if #aggro_history > 0 then
        local prev_color = table.remove(aggro_history)
        for _, board in ipairs(getObjectsWithTag('player_board')) do
            if board.hasTag('color_' .. string.lower(prev_color)) then
                board.call("enableAggro")
            else
                board.call("disableAggro")
            end
        end
    end
end

function SyncAggroFromBoard(params)
    local targetID = "aggro_" .. params.color
    local imgURL = params.active and URL_AGGRO_ON or URL_AGGRO_OFF

    Global.UI.setAttribute(targetID, "image", imgURL)
end

local last_attrition_draw_time = 0

local function checkAttritionDraw(objPos)
    local currentTime = Time.time
    if currentTime - last_attrition_draw_time < 0.5 then
        return
    end

    local monsterBoard = getObjectFromGUID("fa932e")
    if not monsterBoard then
        return
    end
    local localPos = monsterBoard.positionToLocal(objPos)
    local deckLocal = {x = 1.2368, y = 0.2106, z = 0.8573}
    
    local dx = localPos.x - deckLocal.x
    local dz = localPos.z - deckLocal.z
    local dist = math.sqrt(dx*dx + dz*dz)
    
    if dist < 0.1 then
        local targetColor = current_turn_system_color
        local valid = false
        
        if not targetColor then
            for color, aplayer in pairs(ActivePlayer) do
                if aplayer.boardGUID then targetColor = color; break end
            end
        end
        
        if targetColor then
            local aplayer = ActivePlayer[targetColor]
            if aplayer and aplayer.boardGUID then
                local board = getObjectFromGUID(aplayer.boardGUID)
                if board then
                    local phase = board.getVar("current_phase")
                    if phase == 3 then
                        valid = true
                        last_attrition_draw_time = currentTime
                        board.setVar("has_drawn_attrition", true)
                        local count = board.getVar("drawn_attrition_count") or 0
                        board.setVar("drawn_attrition_count", count + 1)
                    end
                end
            end
        end
        
        if valid and targetColor then
            TriggerBehaviorCheck({type = "StruggleEnd", color = targetColor})
        end
    end
end

-- 덱이나 가방에서 카드를 꺼낼 때 자동으로 손패 설정을 복구합니다.
-- (덱 생성 시 내부 카드의 use_hands=false 상태가 그대로 저장되는 TTS 특성 보완용)
function onObjectLeaveContainer(container, leave_object)

    if leave_object.type == "Card" then
        leave_object.use_hands = true
        
        -- 마찰 덱에서 카드가 뽑혔는지 위치 기반 검사
        checkAttritionDraw(container.getPosition())
    end
end

function onPlayerAction(player, action, targets)
    if action == Player.Action.RotateIncrementalLeft or action == Player.Action.RotateIncrementalRight or action == Player.Action.RotateOver then
        for _, obj in ipairs(targets) do
            if CurrentMonster and obj.getName() == CurrentMonster and obj.hasTag("actor_mini") then
                -- Q/E키 입력으로 회전된 경우 (즉시가 아닌 약간 딜레이 후 발동)
                Wait.time(function()
                    if obj and not obj.isDestroyed() then
                        TriggerBehaviorCheck({ type = "MonsterDirection" })
                    end
                end, 0.2)
                break
            end
        end
    end
    return true
end

actor_pickup_zone = {}
actor_pickup_rot_y = nil

function onObjectPickUp(player_color, picked_up_object)
    if picked_up_object.type == "Card" then
        Wait.time(ReevaluateCardPlayBehaviors, 0.5)
        
        -- 바닥에 마지막 1장 남은 마찰 카드가 뽑혔는지 위치 기반 검사
        checkAttritionDraw(picked_up_object.getPosition())
    end
    for color, _ in pairs(ActivePlayer) do
        if picked_up_object.hasTag("owner_" .. color) and picked_up_object.hasTag("actor_mini") then
            actor_pickup_zone[picked_up_object.getGUID()] = getPlayerQuadrantGlobal(color)
            break
        end
    end
    
    if CurrentMonster and picked_up_object.getName() == CurrentMonster and picked_up_object.hasTag("actor_mini") then
        actor_pickup_rot_y = picked_up_object.getRotation().y
    end
    
    if isObjectTerrainType(picked_up_object) then
        UpdateAllPlayerTerrainUI()
    end
end

-- ==========================================================
-- Monster Upkeep & 격앙 토큰 관리 시스템 (완전 초기화 통합본)
-- ==========================================================

-- (1) 작동 상태와 클릭된 버튼의 실제 ID를 추적하는 전역 변수
isUpkeepRunning = false
lastClickedUpkeepBtnId = "monsterUpkeepBtn" -- 기본값
upkeepSafetyTimerID = nil -- [추가] 안전장치 타이머를 관리할 변수

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

    -- 1라운드 또는 Nagarjas인 경우 카드를 버리지 않음 (격앙 토큰만 추가)
    if CurrentRound ~= 1 and CurrentMonster ~= "Nagarjas" then
        for i, data in pairs(slotCards) do
            if data.number and discardNumbers[data.number] then
                data.card.setPositionSmooth({x=discardPos.x, y=discardPos.y + 1, z=discardPos.z}, false, true)
                data.card.setRotationSmooth({x=0, y=180, z=0}, false, true)
                slotCards[i] = nil
            end
        end
        wait(0.6) -- 카드가 슬롯에서 벗어날 시간을 충분히 줌
    end
    
    local newlyDealtCards = {}

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
                    local spawnedCard = deckOrCard.takeObject({ position = slotPos[i], rotation = {0, 180, 180}, smooth = true })
                    if spawnedCard then table.insert(newlyDealtCards, spawnedCard) end
                else
                    deckOrCard.setPositionSmooth(slotPos[i], false, true)
                    deckOrCard.setRotationSmooth({x=0, y=180, z=180}, false, true)
                    table.insert(newlyDealtCards, deckOrCard)
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
    -- 고정 시간 대기 대신, 새로 배치된 카드가 모두 물리적으로 안착(resting)할 때까지 대기 (최대 3초 안전장치)
    local timeout = Time.time + 3.0
    while Time.time < timeout do
        local allResting = true
        for _, card in ipairs(newlyDealtCards) do
            if card and not card.isDestroyed() then
                if card.isSmoothMoving() or not card.resting then
                    allResting = false
                    break
                end
            end
        end
        if allResting then break end
        coroutine.yield(0)
    end

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
    
    local restoredColor = "#FFFFFF"
    if lastClickedUpkeepBtnId == "upkeepPhaseBtnUI" then
        restoredColor = "#FF9800"
    end
    
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "color", restoredColor)
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#FFFFFF")
    Global.UI.setAttribute(lastClickedUpkeepBtnId, "interactable", "True")

    for _, p in pairs(ActivePlayer) do
        local board = getObjectFromGUID(p.boardGUID)
        if board then
            board.UI.setAttribute(lastClickedUpkeepBtnId, "color", restoredColor)
            board.UI.setAttribute(lastClickedUpkeepBtnId, "textColor", "#FFFFFF")
            board.UI.setAttribute(lastClickedUpkeepBtnId, "interactable", "True")
        end
    end

    return 1
end

function ClickQuickRefresh(player, value, id)
    if CurrentMonster ~= "Nagarjas" then return end
    
    if player then
        local pColor = player.color
        local activePlayer = current_turn_system_color
        
        if activePlayer == nil then
            broadcastToAll("현재 진행중인 턴이 없습니다.", pColor)
            return
        end
        
        if pColor ~= activePlayer then
            broadcastToAll("현재 턴 플레이어가 아닙니다.", pColor)
            return
        end
    end

    Wait.frames(function()
        Global.UI.setAttribute("quickRefreshPanel", "active", "false")
    end, 1)

    broadcastToAll("--- 행동 재활성화 (Quick Refresh) ---", {0.2, 0.8, 1.0})
    startLuaCoroutine(Global, "QuickRefreshCoroutine")
end

function ClickBlindRefresh(player, value, id)
    if CurrentMonster ~= "Nagarjas" then return end
    
    if player then
        local pColor = player.color
        local activePlayer = current_turn_system_color
        
        if activePlayer == nil then
            broadcastToAll("현재 진행중인 턴이 없습니다.", pColor)
            return
        end
        
        if pColor ~= activePlayer then
            broadcastToAll("현재 턴 플레이어가 아닙니다.", pColor)
            return
        end
    end

    Wait.frames(function()
        Global.UI.setAttribute("quickRefreshPanel", "active", "false")
    end, 1)

    broadcastToAll("--- 행동 재활성화 건너뜀 (Blind) ---", {0.8, 0.2, 0.2})
    quick_refresh_pending = false
    DoPassTurn()
end

function QuickRefreshCoroutine()
    local deckPos = {x=13.90, y=1.01, z=10.41}
    local slotPos = { {x=17.40, y=1.06, z=10.48}, {x=21.06, y=1.06, z=10.48}, {x=24.61, y=1.06, z=10.48} }
    local discardPos = {x=28.09, y=0.86, z=10.33}

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

    local discardNumbers = {}
    local minNumber = math.huge
    for _, n in ipairs(numbers) do
        if n < minNumber then minNumber = n end
    end
    if minNumber ~= math.huge then
        discardNumbers[minNumber] = true
    end

    for i, data in pairs(slotCards) do
        if data.number and discardNumbers[data.number] then
            data.card.setPositionSmooth({x=discardPos.x, y=discardPos.y + 1, z=discardPos.z}, false, true)
            data.card.setRotationSmooth({x=0, y=180, z=0}, false, true)
            slotCards[i] = nil
        end
    end
    wait(0.6)

    for i = 1, #slotPos do
        if not slotCards[i] then
            local deckOrCard = nil
            for retry = 1, 3 do
                deckOrCard = getCardOrDeckAt(deckPos)
                if deckOrCard then break end
                wait(0.3)
            end

            if not deckOrCard then
                -- 덱이 없으면 버림더미에서 리필 시도 (격화)
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
                local spawnPos = {x=slotPos[i].x, y=slotPos[i].y + 1, z=slotPos[i].z}
                if deckOrCard.type == "Deck" then
                    deckOrCard.takeObject({
                        position = spawnPos,
                        rotation = {0, 180, 180},
                        smooth = true
                    })
                elseif deckOrCard.type == "Card" then
                    deckOrCard.setPositionSmooth(spawnPos, false, true)
                    deckOrCard.setRotationSmooth({0, 180, 180}, false, true)
                end
                wait(0.4)
            end
        end
    end
    
    -- 행동 재활성화 종료 후 턴 종료 처리 (회전은 이미 완료됨)
    PassTurn()
    
    return 1
end

-- (4) 메인 버튼 클릭 함수
function DoMonsterUpkeep(player, value, id)
    if player then
        local pColor = player.color
        local firstPlayer = current_first_player
        
        if firstPlayer == nil then
            broadcastToAll("선플레이어가 지정되지 않았습니다.", pColor)
            return
        end
        
        if pColor ~= firstPlayer then
            broadcastToAll("선플레이어가 아닙니다.", pColor)
            return
        end
    end

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
    
    if CurrentMonster == "Nagarjas" then
        broadcastToAll("나가르자스는 빠른 재활성화 능력으로 행동유지단계시 재활성화를 건너 뜁니다", {r=0.2, g=0.8, b=1.0})
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
-- 글로벌 페이즈 추적 (보드 스크립트가 구버전인 경우를 위한 폴백)
global_current_phase = 0

function onPhaseHUDClick(player, value, id)
    local turnColor = current_turn_system_color
    if not turnColor then return end

    -- ActivePlayer boardGUID로 직접 보드를 찾기
    local aplayer = ActivePlayer[turnColor]
    if aplayer and aplayer.boardGUID then
        local board = getObjectFromGUID(aplayer.boardGUID)
        if board then
            -- 보드에 toggleTurnEndFromGlobal 함수가 있는지 시도
            local hasFunc = board.getVar("toggleTurnEndFromGlobal")
            if hasFunc ~= nil then
                board.call("toggleTurnEndFromGlobal", player)
                return
            end
        end
    end

    -- 폴백: 보드 스크립트가 구버전이면 글로벌에서 직접 페이즈 전환
    advancePhaseFromGlobal(turnColor)
end

-- 페이즈 URL 상수 (글로벌용)
GLOBAL_MOVEMENT_PHASE_URL = "https://steamusercontent-a.akamaihd.net/ugc/2452852111559737310/4117293ACF34F339124FF95FC029613EEB4F8E01/"
GLOBAL_ACTION_PHASE_URL = "https://steamusercontent-a.akamaihd.net/ugc/2452852111559733007/C9578229C5D3B0C7EB431B40DD4D9302EF0CCB50/"
GLOBAL_ATTRITION_PHASE_URL = "https://steamusercontent-a.akamaihd.net/ugc/2452852111559729521/EBF77250CBC0937ACE62E5CA5EE40B6894B108AE/"
GLOBAL_TURN_END_URL = "https://steamusercontent-a.akamaihd.net/ugc/16465744318144975434/E48AF0CDCADD68E22EFD78EE062E8CBE0D2D5C00/"

function advancePhaseFromGlobal(turnColor)
    if global_current_phase == 0 or global_current_phase == nil then
        global_current_phase = 1
        setGlobalPhaseHUD(1)
        broadcastToAll("Movement Phase", turnColor)
    elseif global_current_phase == 1 then
        global_current_phase = 2
        setGlobalPhaseHUD(2)
        broadcastToAll("Action Phase", turnColor)
    elseif global_current_phase == 2 then
        global_current_phase = 3
        setGlobalPhaseHUD(3)
        broadcastToAll("Attrition Phase", turnColor)
    elseif global_current_phase == 3 then
        global_current_phase = 0
        self.UI.setAttribute("PhaseHUD", "active", "false")
        broadcastToAll("End Turn", turnColor)
        
        -- 공통: 몬스터를 먼저 어그로 대상에게 회전시킨다.
        RotateMonsterToAggro()
        PassTurn()
    end
end

function setGlobalPhaseHUD(phase_num)
    local url = ""
    local text = ""
    if phase_num == 1 then 
        url = GLOBAL_MOVEMENT_PHASE_URL
        text = "Movement Phase"
    elseif phase_num == 2 then 
        url = GLOBAL_ACTION_PHASE_URL
        text = "Action Phase"
    elseif phase_num == 3 then 
        url = GLOBAL_ATTRITION_PHASE_URL
        text = "Attrition Phase"
    end
    
    -- TurnIndicatorHUD는 항상 턴 색상에 맞춰 켜져야 합니다 (페이즈가 없더라도)
    if current_turn_system_color and current_turn_system_color ~= "" and Color[current_turn_system_color] then
        local all_colors = {"White", "Brown", "Red", "Orange", "Yellow", "Green", "Teal", "Blue", "Purple", "Pink", "Grey", "Black"}
        local others = {}
        for _, c in ipairs(all_colors) do 
            if c ~= current_turn_system_color then table.insert(others, c) end 
        end
        local visString = table.concat(others, "|")
        
        self.UI.setAttribute("TurnIndicatorHUD", "visibility", visString)
        self.UI.setAttribute("TurnIndicatorHUD", "outline", "#" .. Color[current_turn_system_color]:toHex(false))
        self.UI.setAttribute("TurnIndicatorHUD_Text", "text", current_turn_system_color .. " turn")
        self.UI.setAttribute("TurnIndicatorHUD", "active", "true")
    else
        self.UI.setAttribute("TurnIndicatorHUD", "active", "false")
    end

    if url ~= "" then
        self.UI.setAttribute("PhaseHUD_Image", "image", url)
        self.UI.setAttribute("PhaseHUD_Text", "text", text)
        self.UI.setAttribute("PhaseHUD", "visibility", current_turn_system_color or "")
        
        if current_turn_system_color and Color[current_turn_system_color] then
            self.UI.setAttribute("PhaseHUD", "outline", "#" .. Color[current_turn_system_color]:toHex(false))
        else
            self.UI.setAttribute("PhaseHUD", "outline", "none")
        end
        
        self.UI.setAttribute("PhaseHUD", "active", "true")
    else
        self.UI.setAttribute("PhaseHUD", "active", "false")
    end
end

function onChat(msg, player)
    if msg == "!resetgame" then
        if player.admin then
            ResetGameToInitial()
            broadcastToAll("게임 상태가 강제 초기화되었습니다. (Game Start 버튼 확인 요망)", {0, 1, 0})
        else
            broadcastToAll("방장만 초기화 명령어를 사용할 수 있습니다.", {1, 0, 0})
        end
        return false
    end
end

-- =========================================================
-- Behavior Auto-Trigger System
-- =========================================================

function checkBehaviorFlips()
    local maxSlots = 3
    if CurrentMonster == "Awakened" or CurrentMonster == "어웨이큰" then
        maxSlots = 6
    end

    for uiNum = 1, maxSlots do
        local uiName = "behave" .. uiNum
        local pos = getBehaviorSlotPos(uiNum)
        if pos then
            local obj = getCardOrDeckAt(pos)
            local hasFaceDownBehavior = false
            
            if obj and obj.type == "Card" and obj.is_face_down then
                hasFaceDownBehavior = true
            end
            
            if not hasFaceDownBehavior and behaviorTriggered[uiName] then
                setBehaviorTriggered(uiName, false)
            end
        end
    end
end

function ClearBehaviorTriggers()
    local maxSlots = 3
    if CurrentMonster == "Awakened" or CurrentMonster == "어웨이큰" then
        maxSlots = 6
    end
    for uiNum = 1, maxSlots do
        local uiName = "behave" .. uiNum
        if behaviorTriggered[uiName] then
            setBehaviorTriggered(uiName, false)
        end
    end
    
end

local triggerTokens = {}
local playerTriggerTokens = {}

function getBehaviorSlotPos(uiNum)
    local slotPos = { {x=17.40, y=1.06, z=10.48}, {x=21.06, y=1.06, z=10.48}, {x=24.61, y=1.06, z=10.48} }
    if CurrentMonster == "Awakened" or CurrentMonster == "어웨이큰" then
        table.insert(slotPos, {x=28.55, y=1.08, z=10.48})
        table.insert(slotPos, {x=32.17, y=1.05, z=10.48})
        table.insert(slotPos, {x=35.82, y=1.01, z=10.48})
    end
    return slotPos[uiNum]
end

function setBehaviorTriggered(uiName, is_triggered, player_color, img_url)
    local uiNum = tonumber(string.sub(uiName, -1))
    local pos = getBehaviorSlotPos(uiNum)
    if not pos then return end

    -- 상태 변화가 있을 때만 한 번 일어나야 하는 동작 (토큰 스폰/삭제, 글로벌 UI, 브로드캐스트)
    local stateChanged = (behaviorTriggered[uiName] ~= is_triggered)
    if stateChanged then
        behaviorTriggered[uiName] = is_triggered

        if is_triggered then
            broadcastToAll("행동 카드가 발동되었습니다! (" .. uiName .. ")", "Orange")

            -- 글로벌 UI의 슬롯 이미지 업데이트
            if img_url then
                UI.setAttribute(uiName, "image", img_url)
            end

            -- 몬스터 보드의 해당 슬롯 위치(Zone 위치)에 트리거 이미지 토큰 생성
            local cardFound = false
            local obj = getCardOrDeckAt(pos)
            if obj and obj.type == "Card" then
                pos.y = obj.getPosition().y + 0.02
                cardFound = true
            end
            if not cardFound then
                pos.y = 1.05
            end

            local token = spawnObject({
                type = "Custom_Token",
                position = pos,
                rotation = {0, 180, 0},
                scale = {0.85, 0.1, 0.85},
                sound = false,
            })
            token.setCustomObject({
                image = TRIGGER_IMAGE_URL,
                thickness = 0.1,
                merge_distance = 15,
            })
            token.setName("Trigger Indicator")
            token.locked = true
            token.interactable = false
            triggerTokens[uiNum] = token
        else
            -- 글로벌 UI 이미지 원상 복구
            UI.setAttribute(uiName, "image", "Question")

            -- 트리거 이미지 토큰 삭제
            local token = triggerTokens[uiNum]
            if token and not token.isDestroyed() then
                token.destruct()
            end
            triggerTokens[uiNum] = nil
            behaviorTriggerReason[uiName] = nil
            behaviorTriggerPlayer[uiName] = nil
        end
    end

    -- 플레이어 보드 UI 갱신은 '항상' 실행한다.
    -- (예전 호출 시점에 일부 보드가 누락됐을 수 있고, 글로벌 상태가 이미 true여도
    --  나중에 추가/복원된 보드는 링이 꺼진 상태일 수 있기 때문)
    local _boards = getObjectsWithTag('player_board')
    for _, board in ipairs(_boards) do
        board.call("setBehaviorRing", {uiName = uiName, active = is_triggered})
    end
    if #_boards == 0 then
        print("[BehaviorRing] 'player_board' 태그가 붙은 보드를 찾지 못했습니다. 각 보드에 태그가 있는지 확인하세요.")
    end
end

local function isBehaviorCardStunned(pos)
    for _, stunToken in ipairs(getObjectsWithTag("Stunned")) do
        local tPos = stunToken.getPosition()
        if math.abs(tPos.x - pos.x) < 2 and math.abs(tPos.z - pos.z) < 2 then
            return true
        end
    end
    for _, stunToken in ipairs(getObjectsWithTag("bag_stunned")) do
        local tPos = stunToken.getPosition()
        if math.abs(tPos.x - pos.x) < 2 and math.abs(tPos.z - pos.z) < 2 then
            return true
        end
    end
    return false
end
function isPlayerKOGlobal(playerColor)
    if not playerColor then return false end
    if not ActivePlayer or not ActivePlayer[playerColor] then return false end
    local boardGUID = ActivePlayer[playerColor].boardGUID
    local board = getObjectFromGUID(boardGUID)
    if board then
        return board.call("isPlayerKO")
    end
    return false
end

function TriggerBehaviorCheck(params)
    if not is_game_started then return false end

    local event_type = params.type
    local event_data = params.data or {}
    local player_color = params.color or current_turn_system_color

    if isPlayerKOGlobal(player_color) then
        return false
    end
    local maxSlots = 3
    if CurrentMonster == "Awakened" or CurrentMonster == "어웨이큰" then
        maxSlots = 6
    end

    local newly_triggered = false
    local any_checked = false
    for uiNum = 1, maxSlots do
        local uiName = "behave" .. uiNum
        local pos = getBehaviorSlotPos(uiNum)
        if pos then
            local obj = getCardOrDeckAt(pos)

            if obj and obj.type == "Card" and obj.hasTag("actor_behavior") and obj.is_face_down then
                if not isBehaviorCardStunned(pos) then
                    local url = obj.getVar("TokenImg")
                    if not url then
                        local customObj = obj.getCustomObject()
                        if customObj and customObj.image then
                            url = customObj.image
                        end
                    end

                    if url then
                        local desc = BehaviorDescription[url]
                        if desc then
                            local rule = BehaviorRules[desc]
                            if rule then
                                any_checked = true
                                local matched = checkRuleMatch(rule, event_type, event_data, player_color)

                                if matched then
                                    local was_triggered = behaviorTriggered[uiName]
                                    setBehaviorTriggered(uiName, true, player_color, url)
                                    if not was_triggered then
                                        behaviorTriggerReason[uiName] = event_type
                                        behaviorTriggerPlayer[uiName] = player_color
                                        newly_triggered = true
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    
    -- 다른 카드가 발동할 때 같이 발동하는 특수 처리 (OtherTrigger)
    if newly_triggered then
        for uiNum = 1, maxSlots do
            local uiName = "behave" .. uiNum
            local pos = getBehaviorSlotPos(uiNum)
            if pos then
                local obj = getCardOrDeckAt(pos)
                if obj and obj.type == "Card" and obj.hasTag("actor_behavior") and obj.is_face_down then
                    if not isBehaviorCardStunned(pos) then
                        local url = obj.getVar("TokenImg")
                        if url then
                            local desc = BehaviorDescription[url]
                            local rule = BehaviorRules[desc]
                            if rule and rule.event == "OtherTrigger" then
                                local was_triggered = behaviorTriggered[uiName]
                                setBehaviorTriggered(uiName, true, player_color, url)
                                if not was_triggered then
                                    behaviorTriggerReason[uiName] = "OtherTrigger"
                                    behaviorTriggerPlayer[uiName] = player_color
                                end
                            end
                        end
                    end
                end
            end
        end
    end
    
    if event_type == "CardPlay" and not any_checked then
        
    end
end


function takeTerrainCard(terrainNames, targetPos, targetRot)
    targetPos = targetPos or {-19.21, 5, 21.72}
    targetRot = targetRot or {0, 180, 180}
    
    local hits = Physics.cast({
        origin = {-19.21, 10, 21.72},
        direction = {0, -1, 0},
        type = 3,
        size = {3, 3, 3},
        max_distance = 20
    })
    
    local function matchesName(objData)
        local rawname = tostring(objData.name or (type(objData.getName)=="function" and objData.getName()) or "no name")
        local desc = ""
        local cname = ""
        if type(objData.getDescription) == "function" then
            desc = objData.getDescription() or ""
            cname = objData.getName() or ""
        else
            desc = objData.description or ""
            cname = objData.name or ""
        end
        local function trim(s) return (s:gsub("^%s*(.-)%s*$", "%1")) end
        desc = trim(string.lower(desc))
        cname = trim(string.lower(cname))
        
        local allSearchNames = {}
        for _, tName in ipairs(terrainNames) do
            local ln = trim(string.lower(tName))
            table.insert(allSearchNames, ln)
            if TerrainNameMap and TerrainNameMap[ln] then table.insert(allSearchNames, trim(string.lower(TerrainNameMap[ln]))) end
            if ReverseTerrainMap and ReverseTerrainMap[ln] then table.insert(allSearchNames, trim(string.lower(ReverseTerrainMap[ln]))) end
        end

        for _, tName in ipairs(allSearchNames) do
            -- 정확히 이름이 일치하는 경우만! (부분 일치는 '정글덤불'에 '덤불'이 매칭되는 문제 발생)
            if cname == tName then
                return true
            end
        end
        return false
    end

    for _, hit in ipairs(hits) do
        local obj = hit.hit_object
        if obj.type == "Card" then
            if matchesName(obj) then
                obj.setPositionSmooth(targetPos, false, true)
                obj.setRotationSmooth(targetRot, false, true)
                return obj
            end
        elseif obj.type == "Deck" then
            for _, cardData in ipairs(obj.getObjects()) do
                if matchesName(cardData) then
                    local pulledCard = obj.takeObject({
                        guid = cardData.guid,
                        position = targetPos,
                        rotation = targetRot,
                        smooth = true
                    })
                    return pulledCard
                end
            end
        end
    end
    return false
end

function checkRuleMatch(rule, event_type, event_data, player_color)
    if rule.event == "TurnStartOrCardPlay" then
        if event_type == "TurnStart" and rule.zone and event_data.zone and string.lower(rule.zone) == string.lower(event_data.zone) then return true end
        if event_type == "CardPlay" and checkTagMatch(rule.tag, event_data.tag) then return true end
        return false
    end
    if rule.event == "EmptyHandOrCardPlay" then
        if event_type == "EmptyHand" then return true end
        if event_type == "CardPlay" and checkTagMatch(rule.tag, event_data.tag) then return true end
        return false
    end
    if rule.event == "TurnStartOrThreat" then
        if event_type == "TurnStart" and rule.zone and event_data.zone and string.lower(rule.zone) == string.lower(event_data.zone) then return true end
        if event_type == "Threat" then return true end
        return false
    end
    if rule.event == "ThreatOrCardPlay" then
        if event_type == "Threat" then return true end
        if event_type == "CardPlay" and checkTagMatch(rule.tags, event_data.tag) then return true end
        return false
    end

    if rule.event ~= event_type then return false end

    if rule.event == "CardPlay" then
        if rule.count then
            if not player_color then return false end
            local boardGUID = ActivePlayer[player_color].boardGUID
            local board = getObjectFromGUID(boardGUID)
            if not board then return false end
            local seqTags = board.call("getSequenceTagsSorted") or {}
            
            local max_consecutive = 0
            local current_consecutive = 0
            for _, cardTags in ipairs(seqTags) do
                local match = false
                if rule.tag then
                    match = checkTagMatch(cardTags.tags, rule.tag)
                elseif rule.tags then
                    for _, rt in ipairs(rule.tags) do
                        if checkTagMatch(cardTags.tags, rt) then
                            match = true
                            break
                        end
                    end
                end
                
                if match then
                    current_consecutive = current_consecutive + 1
                    if current_consecutive > max_consecutive then
                        max_consecutive = current_consecutive
                    end
                else
                    current_consecutive = 0
                end
            end
            if max_consecutive < rule.count then return false end
        else
            if rule.tag and not checkTagMatch(rule.tag, event_data.tag) then return false end
            if rule.tags and not checkTagMatch(rule.tags, event_data.tag) then return false end
        end
    end
    if rule.event == "TurnStart" then
        if rule.zone and (not event_data.zone or string.lower(rule.zone) ~= string.lower(event_data.zone)) then return false end
        if rule.anyZone and (not event_data.anyZone or string.lower(rule.anyZone) ~= string.lower(event_data.anyZone)) then return false end
        if rule.terrain and (not event_data.terrain or string.lower(rule.terrain) ~= string.lower(event_data.terrain)) then return false end
    end
    if rule.event == "Move" then
        if rule.terrain and rule.terrain ~= event_data.terrain then return false end
    end
    return true
end

function checkTagMatch(ruleTags, targetTag)
    if not ruleTags or not targetTag then return false end
    local lowerTarget = string.lower(targetTag)
    if type(ruleTags) == "string" then
        return string.lower(ruleTags) == lowerTarget
    elseif type(ruleTags) == "table" then
        for _, t in ipairs(ruleTags) do
            if string.lower(t) == lowerTarget then return true end
        end
    end
    return false
end

function ReevaluateCardPlayBehaviors()
    for uiName, isTriggered in pairs(behaviorTriggered) do
        if isTriggered and behaviorTriggerReason[uiName] == "CardPlay" then
            local uiNum = tonumber(string.sub(uiName, -1))
            local pos = getBehaviorSlotPos(uiNum)
            
            if pos then
                local obj = getCardOrDeckAt(pos)
                if obj and obj.type == "Card" and obj.hasTag("actor_behavior") and obj.is_face_down then
                    local url = obj.getVar("TokenImg")
                            if url then
                                local desc = BehaviorDescription[url]
                                local rule = BehaviorRules[desc]
                                if rule then
                                    local pColor = behaviorTriggerPlayer[uiName]
                                    if pColor then
                                        local stillMatches = false
                                        local boardGUID = ActivePlayer[pColor].boardGUID
                                        local board = getObjectFromGUID(boardGUID)
                                        if board then
                                            local seqTags = board.call("getSequenceTagsSorted") or {}
                                            if rule.count then
                                                local max_consecutive = 0
                                                local current_consecutive = 0
                                                for _, cardData in ipairs(seqTags) do
                                                    local match = false
                                                    if rule.tag then
                                                        match = checkTagMatch(cardData.tags, rule.tag)
                                                    elseif rule.tags then
                                                        for _, rt in ipairs(rule.tags) do
                                                            if checkTagMatch(cardData.tags, rt) then
                                                                match = true
                                                                break
                                                            end
                                                        end
                                                    end
                                                    if match then
                                                        current_consecutive = current_consecutive + 1
                                                        if not cardData.is_stealthed and current_consecutive >= rule.count then
                                                            stillMatches = true
                                                            break
                                                        end
                                                    else
                                                        current_consecutive = 0
                                                    end
                                                end
                                            else
                                                for _, cardData in ipairs(seqTags) do
                                                    if not cardData.is_stealthed then
                                                        if rule.tag and checkTagMatch(cardData.tags, rule.tag) then
                                                            stillMatches = true
                                                            break
                                                        elseif rule.tags then
                                                            for _, rt in ipairs(rule.tags) do
                                                                if checkTagMatch(cardData.tags, rt) then
                                                                    stillMatches = true
                                                                    break
                                                                end
                                                            end
                                                            if stillMatches then break end
                                                        end
                                                    end
                                                end
                                            end
                                        end
                                        
                                        if not stillMatches then
                                            setBehaviorTriggered(uiName, false)
                                            broadcastToAll("조건이 더 이상 만족되지 않아 행동 카드("..uiName..")의 발동이 취소되었습니다.", "Orange")
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
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
    local combatBoardGUID = GetCombatBoardGUID()
    if not combatBoardGUID then return nil end
    local combatBoard = getObjectFromGUID(combatBoardGUID)
    if not combatBoard then return nil end
    
    local pos = terrainObj.getPosition()
    local center = getTrueBoardCenter(combatBoardGUID)
    if not center then return nil end
    
    local dx = pos.x - center.x
    local dz = pos.z - center.z
    
    -- 컴뱃보드 반경 밖이면 무시 (반경 8로 설정)
    if dx*dx + dz*dz > 64 then return nil end
    
    local rad = math.rad(-getTrueBoardRotation(combatBoardGUID))
    local localX = dx * math.cos(rad) - dz * math.sin(rad)
    local localZ = dx * math.sin(rad) + dz * math.cos(rad)
    
    local absX = math.abs(localX)
    local absZ = math.abs(localZ)
    
    if localZ > absX then return "back"
    elseif localZ < -absX then return "front"
    elseif localX > absZ then return "right"
    else return "left" end
end

function UpdateAllPlayerTerrainUI()
    -- print("[TerrainUI] UpdateAllPlayerTerrainUI called.")
    local terrainObjects = {}
    local combatBoardGUID = GetCombatBoardGUID()
    if combatBoardGUID then
        local combatBoard = getObjectFromGUID(combatBoardGUID)
        if combatBoard then
            local center = getTrueBoardCenter(combatBoardGUID)
            local cbPos = combatBoard.getPosition() -- 높이 기준점으로만 사용
            if center then
                local hits = Physics.cast({
                    origin       = {center.x, cbPos.y + 5, center.z},
                    direction    = {0, -1, 0},
                    type         = 3, -- Box cast
                    size         = {18, 20, 18}, -- 컴뱃보드 반경(8)을 살짝 넘게 덮을 크기
                    max_distance = 15
                })
                
                for _, hit in ipairs(hits) do
                local obj = hit.hit_object
                if obj and not obj.isDestroyed() then
                    local rawName = obj.getName()
                    if rawName and rawName ~= "" then
                        local name = stripHex(rawName)
                        local lowerName = string.lower(name)
                        if TerrainNameMap[lowerName] or ReverseTerrainMap[lowerName] then
                            -- print("[TerrainUI] Found terrain token: " .. tostring(name))
                            table.insert(terrainObjects, obj)
                        end
                    end
                end
                end -- end for hits loop
            end -- end if center
        else
            print("[TerrainUI] combatBoard not found for GUID: " .. tostring(combatBoardGUID))
        end
    else
        print("[TerrainUI] combatBoardGUID is nil")
    end

    local playerBoards = getObjectsWithTag("player_board")
    -- print("[TerrainUI] Found " .. #playerBoards .. " player boards.")
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
        -- print("[TerrainUI] Player " .. tostring(pColor) .. " is in quadrant: " .. tostring(quadrant))
        
        local urls = {}
        local seen = {}
        if quadrant then
            for _, t in ipairs(terrainObjects) do
                local tQuad = getTerrainQuadrant(t)
                -- print("[TerrainUI]   Checking terrain '" .. tostring(t.getName()) .. "' in quadrant: " .. tostring(tQuad))
                if tQuad == quadrant then
                    local rawName = t.getName()
                    local name = stripHex(rawName)
                    local mapped = TerrainNameMap[string.lower(name)] or name
                    
                    if not seen[mapped] then
                        seen[mapped] = true
                        local url = TerrainImageUrls[mapped]

                        if mapped == "불" then
                            if t.is_face_down then url = TerrainImageUrls["불2"]
                            else url = TerrainImageUrls["불1"] end
                        end

                        if url then
                            -- print("[TerrainUI]   -> Adding URL for " .. mapped)
                            table.insert(urls, {url = url, name = mapped})
                        end
                    end
                end
            end
        end
        local finalUrls = {}
        for i=1, 3 do
            if urls[i] then table.insert(finalUrls, urls[i]) end
        end
        -- print("[TerrainUI] Calling UpdateQuadrantTerrains for " .. pColor .. " with " .. #finalUrls .. " urls")
        board.call("UpdateQuadrantTerrains", finalUrls)
    end
end

function handleTerrainAdded(terrainObj)
    if not terrainObj or terrainObj.isDestroyed() then
        return
    end
    if terrainObj.hasTag("terrain_card_handled") then
        local found = false
        for _, data in ipairs(active_terrain_cards) do
            for _, t in ipairs(data.terrains) do
                if t == terrainObj then
                    found = true
                    break
                end
            end
            if found then break end
        end
        if found then
            Wait.frames(function() UpdateAllPlayerTerrainUI() end, 1)
            return
        else
            terrainObj.removeTag("terrain_card_handled")
        end
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
                terrainObj.removeTag("terrain_card_handled")
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
    
    -- active_terrain_cards에 없는데 태그만 남아있을 수 있으므로 안전장치로 한 번 더 지움
    terrainObj.removeTag("terrain_card_handled")
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
