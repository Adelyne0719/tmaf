function gO(GUID) --lol
	return getObjectFromGUID(GUID)
end

function onSave()
	newSeed()
    saved_data = JSON.encode({
        save_setupComplete = setupComplete,
		save_automaticSeat = automaticSeat,
		save_manualSeat1 = playerInfoTable['Brown'].manualSeat,
		save_manualSeat2 = playerInfoTable['Pink'].manualSeat,
		save_manualSeat3 = playerInfoTable['Blue'].manualSeat,
		save_manualSeat4 = playerInfoTable['Green'].manualSeat,
		save_manualSeat5 = playerInfoTable['Purple'].manualSeat,
		save_manualSeat6 = playerInfoTable['Orange'].manualSeat,
		save_manualSeat7 = playerInfoTable['Red'].manualSeat,
		save_manualSeat8 = playerInfoTable['White'].manualSeat,
		save_manualSeat9 = playerInfoTable['Yellow'].manualSeat,
		save_manualSeat10 = playerInfoTable['Teal'].manualSeat,
		
		save_insiderEnable = insiderEnable,
		save_insiderStoryGUID = insiderStoryGUID,
		
		save_deadlyMode = deadlyMode,
		save_useXyrian = useXyrian,
		save_useContractors = useContractors,
		save_useLanderVoices = useLanderVoices,
		save_lifeforms = lifeforms,
		
		save_figureGUID1 = playerInfoTable['Brown'].figureGUID,
		save_figureGUID2 = playerInfoTable['Pink'].figureGUID,
		save_figureGUID3 = playerInfoTable['Blue'].figureGUID,
		save_figureGUID4 = playerInfoTable['Green'].figureGUID,
		save_figureGUID5 = playerInfoTable['Purple'].figureGUID,
		save_figureGUID6 = playerInfoTable['Orange'].figureGUID,
		save_figureGUID7 = playerInfoTable['Red'].figureGUID,
		save_figureGUID8 = playerInfoTable['White'].figureGUID,
		save_figureGUID9 = playerInfoTable['Yellow'].figureGUID,
		save_figureGUID10 = playerInfoTable['Teal'].figureGUID,
		
		save_scriptEnabled = scriptEnabled,
		
		save_queenFigGUID = queenFigGUID,
		save_prevXyrianCardGUID = prevXyrianCardGUID
		
    })
    --saved_data = ""
    return saved_data
end


function onLoad(saved_data)
	
	prevXyrianCardGUID = ''
	
	seedYearOffset = 8
	
	newSeed()
	for i = 1, 3 do
		math.random()
	end
	
	seedYearOffset = math.random(0,8)
	
	newSeed()
	for i = 1, 3 do --I red a lua tip saying it helps, I dunno but ok.
		math.random()
	end
	
	scriptEnabled = true
	centerCube = gO('c80f0b')
	
	hiddenRoom = gO('3d73e4')
	hiddenCorridorsGUID = {'89a391', '536804', 'a7ddb5', 'a457a5'}
	
	RoomsMap = {		--this is not a local variable, we will build it as the game progress through exploration, events, xyrian activation, and queen activations.
	[hiddenRoom.getGUID()] = {'room', {}}
	}
	
	for _, corridorGUID in pairs(hiddenCorridorsGUID) do
		RoomsMap[corridorGUID] = {'corridor', {hiddenRoom.getGUID()}}
		table.insert(RoomsMap[hiddenRoom.getGUID()][2], corridorGUID)
		--gO(corridorGUID).setPosition(gO(corridorGUID).getPosition() + Vector(0,0.25,0)) --1.48?
	end
	
	
	hiddenRoomDesiredSize = Vector(3.137135, 0.158555, 1.99036)
	intruderSizeOrder = {
		['Primebloods'] = {
			['queen'] = 10,
			['breeder'] = 9,
			['adult'] = 5,
			['larvae'] = 2
		},
		['Neoflesh'] = {
			['queen'] = 10,
			['breeder'] = 9,
			['slasher'] = 8,
			['crawlmine'] = 7,
			['ironclad'] = 6,
			['firespitter'] = 5,
			['larvae'] = 2,
		},
		['Sangrevores'] = {
			['queen'] = 10,
			['breeder'] = 9,
			['adult'] = 5,
			['noise'] = 1,
		},
		['Carnomorph'] = {
			['queen'] = 10,
			['breeder'] = 9,
			['adult'] = 5,
			['creeper'] = 3,
		},
	}
	-- print('hiddenroom pos Y= ' .. hiddenRoom.getPosition().y)
	--hiddenRoom.setPosition(hiddenRoom.getPosition() + Vector(0,6,0))
	--hiddenRoom.setPosition({hiddenRoom.getPosition().x, 1.28, hiddenRoom.getPosition().z})
	
	

	--Uncomment to get some debug measurements
	-- for _, GUID in pairs(hiddenCorridorsGUID) do
		-- local locCor = gO(GUID)
		-- local locRotY = locCor.getRotation().y
		-- locCor.setRotation({0, locRotY, 0})
		-- locCor.setPosition(locCor.getPosition()+Vector(0,6,0))
	-- end
	--hiddenRoom.setPosition(hiddenRoom.getPosition() + Vector(0,6,0)) --(a way to recover that hidden room tile under hibernatorium)
	
	--Uncomment to redo all snap Points on Corridor currently on the table.
	-- for _, obj in pairs(getAllObjects()) do
		-- if obj.hasTag('Corridors') then
			-- local locSnaps =
			-- {
				-- {
					-- position = {-1.4,0,0},
					-- rotation = {0,90,0},
					-- rotation_snap = true
				-- },
				
				-- {
					-- position = {1.4,0,0},
					-- rotation = {0,90,0},
					-- rotation_snap = true
				-- },
			-- }
			
			-- if obj.hasTag('snapDoor') then
				-- table.insert(locSnaps,
				-- {
					-- position = {-1.4,0,0},
					-- rotation = {0,90,0},
					-- tags = {'doorSlot'}
				-- })
			-- end
			-- obj.setSnapPoints(locSnaps)
		-- end
	-- end
	
	deadlyMode = false
	
	tileImportedSize = Vector(2.757976, 0.100351, 3.184573) * Vector(1.038463,1,0.781075) 
	--So that the size is related to the base of the tips, not the tip of the tips.
	corridorImportedSize = Vector(2.731651, 0.099999, 2.571995) * Vector(1.08, 1, 0.813538)
	--To ignore vertical tips and include horizontal tips.
	standeeSize = 0.48
	
	soundboard1 = gO('8307a4')
	soundboard2 = gO('f6d4ac')
	soundboard3 = gO('4a252d')
	soundboard4 = gO('75bc75')
	soundboard5 = gO('0393d0')
	soundboard6 = gO('97d5ca')
	sound1Used = false
	sound2Used = false
	sound3Used = false
	sound4Used = false
	sound5Used = false
	sound6Used = false
	soundDuration = {6.745,
	3.042,
	2.043,
	2.067,
	4.156,
	2.784,
	0.785,
	0.536,
	0.485,
	0.479,
	0.626,
	3.960,
	0.817,
	0.156,
	0.162,
	0.129,
	0.655,
	0.124,
	0.877,
	2.040,
	2.113,
	1.821,
	1.073,
	1.030,
	1.366,
	0.443,
	0.451,
	1.607,
	0.674,
	4.224, 
	3.093, 
	16.848,
	6.607, 
	5.592,
	2.879, 
	1.033, 
	2.032, 
	2.09, 
	2.113,
	1.788, 
	0.698,
	0.231,
	0.214, 
	0.289, 
	0.177, 
	4.944,
	1.181,
	9.888,
	0.372,
	0.293,
	0.370,
	0.256,
	0.402,
	5.581,
	0.516,
	1.857,
	1.445,
	1.847,
	1.652,
	0.957,
	2.2,
	1.973,
	2.396,
	3.622,
	2.597,
	2.073,
	2.125,
	2.431,
	2.833,
	2.709,
	3.068,
	2.697,
	2.905,
	3.123,
	6.205,
	2.745,
	2.064,
	2.529,
	2.719,
	0.798,
	0.720,
	0.879,
	0.710,
	0.492,
	0.574,
	0.514,
	0.969,
	0.392,
	0.538,
	0.451,
	2.508,
	1.650,
	0.447,
	2.365,
	0.99,
	2.247,
	0.555,
	2.536,
	6.385,
	2.571,
	1.459,
	0.945,
	15.961,
	0.573,
	0.625,
	0.196,
	11.578,
	6.821,
	0.367,
	0.576,
	0.492,
	0.605,
	0.776,
	0.630,
	0.676,
	0.605,
	0.836,
	0.183,
	0.892,
	1.137,
	0.559,
	0.222,
	0.22,
	0.201,
	0.212,
	0.329,
	0.371,
	0.438,
	0.415,
	0.446,
	0.286,
	4.323,
	4.139,
	1.88,
	1.013,
	1.232,
	1.383,
	4.242,
	3.043,
	3.232,
	0.256,
	0.277,
	0.306,
	0.245,
	0.298,
	0.320,
	0.272,
	0.284,
	1.395,
	1.446,
	1.353,
	1.334,
	1.082,
	5.821,
	0.772,
	0.869,
	0.882,
	1.054,
	0.978,
	0.901,
	2.208,
	7.072,
	0.844,
	2.495,
	1.234,
	0.669,
	1.714,
	3.077,
	2.878,
	2.812,
	2.798,
	3.375,
	2.787,
	3.246,
	2.889,
	3.173,
	3.275,
	2.496,
	2.930,
	3.488,
	30.552,
	12.447,
	0.138,
	
	2.568, --i
	4.488,
	3.216,
	2.664,
	5.352,
	2.232,
	3.072,
	7.176,
	5.472,
	8.856,
	5.59,
	6.191,
	4.206,
	5.329,
	5.224,
	6.217,
	5.277,
	7.2,
	7.608,
	7.752,
	7.368,
	7.8,
	5.952,
	10.464,
	1.416,
	3.03,
	1.44,
	1.248,
	2.116,
	1.885,
	0.993,
	1.68,
	1.464,
	1.128,
	1.152,
	0.936,
	0.888,
	0.862,
	0.967,
	1.464,
	1.704,
	1.872,
	2.208,
	1.512,
	2.448,
	2.712,
	2.472,
	1.584,
	1.08,
	1.152,
	1.08,
	1.776,
	1.515,
	1.541,
	1.411,
	1.384,
	1.254,
	3.84,
	
	0.758,
	0.784,
	0.47,
	0.47,
	1.228,
	1.306,
	0.94,
	0.914,
	
	0.235,
	0.183,
	0.261,
	0.705,
	0.549,
	0.522,
	0.34,
	0.313,
	1.881,
	1.855,
	2.064,
	1.855,
	1.045,
	0.914,
	
	1.872,
	1.704,
	1.704,
	
	}
	
	-- RoomIDs
	-- 1) Fire Control Room
	-- 2) Shelter
	-- 3) Emergency Room
	-- 4) Supply Room
	-- 5) Armory
	-- 6) Door Control Room
	-- 7) Security Robot Room
	-- 8) Gunnery Room
	-- 9) Pressure Control (old Sprinkles Control)
	-- 10) Alarm Room
	-- 11) Experimental Military Lab
	-- 12) Technical Corridor Entrance
	-- 13) Decontamination Room
	-- 14) Landing Zone
	-- 15) LifeSupport A
	-- 16) Surgery Room
	-- 17) Drilling Station
	-- 18) Hibernatorium
	-- 19) LifeSupportB
	-- 20) Server Room
	-- 21) Cooling System
	-- 22) LifeSupportC
	-- 23) Reactor
	-- 24) Escape Shuttle
	-- 25) Nest
	
	soundEnable = true
	useLanderVoices = false
	landerVoicesTbl = {	--We do it differently because... I might not do them all in one go, that makes it easier to come back to aswell, and it'll avoid sound cut I guess...?
		['Goody'] = {
			['Landing'] = {
				{ID = 0, Duration = 23.898},
				{ID = 1, Duration = 19.993},
				{ID = 2, Duration = 13.114},
				{ID = 3, Duration = 19.225},
				{ID = 4, Duration = 14.142},
			},
			['Crashing'] = {
				{ID = 5, Duration = 7.098},
				{ID = 6, Duration = 9.227},
				{ID = 7, Duration = 7.73},
				{ID = 8, Duration = 10.135},
				{ID = 9, Duration = 10.181},
				{ID = 10, Duration = 15.941},
				{ID = 11, Duration = 7.025},
			}
		},
		
		['Rage'] = {
			['Landing'] = {
				{ID = 12, Duration = 36.209},
				{ID = 13, Duration = 32.823},
				{ID = 14, Duration = 30.873},
				{ID = 15, Duration = 29.573},
			},
			['Crashing'] = {
				{ID = 16, Duration = 27.897},
				{ID = 17, Duration = 24.208},
				{ID = 18, Duration = 29.155},
				{ID = 19, Duration = 33.566},
				{ID = 20, Duration = 13.027},
			}
		},
		
		['Nasty'] = {
			['Landing'] = {
				{ID = 21, Duration = 7.947},
				{ID = 22, Duration = 9.831},
				{ID = 23, Duration = 7.718},
				{ID = 24, Duration = 12.495},
				{ID = 25, Duration = 8.59},
			
			},
			['Crashing'] = {
				{ID = 26, Duration = 5.926},
				{ID = 27, Duration = 6.661},
				{ID = 28, Duration = 8.085},
				{ID = 29, Duration = 7.488},
				{ID = 30, Duration = 7.442},
				{ID = 31, Duration = 7.58},
				{ID = 32, Duration = 7.58},
				{ID = 33, Duration = 8.085},
				{ID = 34, Duration = 7.672},
				{ID = 35, Duration = 6.845},
				{ID = 36, Duration = 4.686},
			
			}
		},
		
				
		['Smooth'] = {
			['Landing'] = {
				{ID = 37, Duration = 17.456},
				{ID = 38, Duration = 19.34},
				{ID = 39, Duration = 18.329},
				{ID = 40, Duration = 24.255},
				{ID = 41, Duration = 10.566},
			
			},
			['Crashing'] = {
				{ID = 42, Duration = 18.831},
				{ID = 43, Duration = 12.495},
				{ID = 44, Duration = 14.333},
				{ID = 45, Duration = 14.057},
				{ID = 46, Duration = 8.085},
				{ID = 47, Duration = 11.209},
				{ID = 48, Duration = 10.014},
			}
		},

		['Stoic'] = {
			['Landing'] = {
				{ID = 49, Duration = 5.329},
				{ID = 50, Duration = 5.788},
				{ID = 51, Duration = 5.237},
				{ID = 52, Duration = 5.007},
				{ID = 53, Duration = 6.156},
				
			
			},
			['Crashing'] = {
				{ID = 54, Duration = 2.986},
				{ID = 55, Duration = 3.905},
				{ID = 56, Duration = 3.537},
				{ID = 57, Duration = 3.262},
				{ID = 58, Duration = 4.548},
				{ID = 59, Duration = 4.364},
				{ID = 60, Duration = 3.078},
				{ID = 61, Duration = 5.604},
			}
		},
		
		['Mocking'] = {
			['Landing'] = {
				{ID = 62, Duration = 12.128},
				{ID = 63, Duration = 11.806},
				{ID = 64, Duration = 12.495},
				{ID = 65, Duration = 13.598},
				{ID = 66, Duration = 14.838},

			
			},
			['Crashing'] = {
				{ID = 67, Duration = 14.057},
				{ID = 68, Duration = 15.527},
				{ID = 69, Duration = 12.128},
				{ID = 70, Duration = 13.873},
				{ID = 71, Duration = 13.414},
				{ID = 72, Duration = 13.092},

			}
		},
		
		['CoolMom'] = {
			['Landing'] = {
				{ID = 73, Duration = 12.036},
				{ID = 74, Duration = 13.046},
				{ID = 75, Duration = 10.152},
				{ID = 76, Duration = 11.163},
			
			},
			['Crashing'] = {
				{ID = 77, Duration = 14.195},
				{ID = 78, Duration = 8.958},
				{ID = 79, Duration = 9.555},
				{ID = 80, Duration = 9.096},
				{ID = 81, Duration = 10.703},
				{ID = 82, Duration = 10.06},
			}
		},
	}
	
	boardTable = {'801411', 'a19c68', 'a44130', '848e7d', '0ed963', '84f381', '', boardindex = 7}
	
	lifeforms = 'Primebloods'
	weaponAttackType = 1
	
	autoDestructionToken = gO('d24061')
	shuttleFigure = gO('2d0e04')
	lightColorStart = Lighting.getLightColor()  --default was {1, 0.984, 0.894}
	lightAnimPlaying = false
	powerTokens = {'b1695b', 'dfa218', '08fbb3', '4eb61b', 2}
	
	
    gameBox = gO('a64f43')
    hibUnexplored = gO('3817bc')
    boarderTile = gO('006497')
    local cObj = boarderTile.getCustomObject()
    if cObj.image ~= "https://steamusercontent-a.akamaihd.net/ugc/15823456762423426549/315B498D7A106704BBCB8A0A2EA81FE2BE93E4DA/" then
        cObj.image = "https://steamusercontent-a.akamaihd.net/ugc/15823456762423426549/315B498D7A106704BBCB8A0A2EA81FE2BE93E4DA/"
        boarderTile.setCustomObject(cObj)
        boarderTile = boarderTile.reload()
    end
	
	turnMarker = gO('513438')
	turnOffset = Vector(0,0,0.92428572142857142857142857142857 / 8.67936611175537 *boarderTile.getScale().z) --in case someone change the board scale.
	
    scanner = gO('5b3265')
	if scanner != nil then
		scanner.registerCollisions(false)
	end
	
	robot = gO('cbf1f3')
	robotDeck = gO('5e2330')
	robotDeckPos = {-11.38,2.5, 20.77}
	robotToken = gO('828c1d')
	
    contaminationDeck = gO('7e89ea')
    queenHealthDeck = gO('7ca8cc')
    objectiveMissonDeck = gO('9a6c65')
    objectivePersonalDeck = gO('4987ec')
	objectiveCoopDeck = gO('5deb2f')
	objectiveCoopCustomDeck = gO('831e19')
    missionTaskDeck = gO('dccf14')
    characterDraftDeck = gO('2abdf6')
    startItemDeck = gO('3391a2')
	
	attacksDeck = gO('34c73e')
	greenItemsDeck = gO('32d1dc')
	redItemsDeck = gO('fd7af8')
	yellowItemsDeck = gO('dd3ee6')
	eventDeck = gO('0cea62')
	seriouswoundDeck = gO('f0e8e7')

	roomIABag = gO('4f7672')
	roomIBBag = gO('127c36')
	roomICBag = gO('2002b1')
	roomIIBag = gO('f81ba6')
	corridorBag = gO('527c41')
	noiseBag = gO('c59c6b')
	landingZone = gO('195123')
	playerHelpBag = gO('d8a0fb')
	trashBag = gO('718459')
	carcassBag = gO('25585f')
	trapBag = gO('0987e4')
	airlockToken = gO('73cc48')
	
	larvaeBag = gO('26b980')
	creeperBag = gO('26b980')
    adultBag = gO('1a0e0c')
	breederBag = gO('ff790c')
	queenBag = gO('52ae01')
	queenFigGUID = '4b9edc'
	
	larvaeFBag = gO('978afc')
	creeperFBag = gO('978afc')
	adultFBag = gO('d85f3b')
	breederFBag = gO('31f65c')
	queenFBag = gO('bf3dc5')
	
	--queenFBag.removeAttachments() --removeAttachment should be used to Detach figurine and its figurine bag.
	--breederFBag.removeAttachments()
	
	intruderHelp = gO('1e58e7')
	
	nestBag = gO('da6c44')
	eggBag = gO('05fd7c')
	
    intruderBag = gO('1283e4')
    healthBag = gO('50e559')
    grenadeBag = gO('0a9a06')
    ammoBag = gO('ed4a41')
    oxygenBag = gO('d2f7a3')
    medpackBag = gO('c218a3')
	doorBag = gO('435a9a')
	fireBag = gO('602a2e')
	malfunctionBag = gO('05e833')
	secureBag = gO('162108')
	dataTokenBag = gO('dbc018')

    firstPlayerToken = gO('002ba0')
	zoneHide = gO('041d27') --playerboard size is {15.5, 1, 12.68} for now

    antiAircraftGUIDTable = {'6c75b4','0b3190'}
	OnScriptButtonSet = 0

    red = {0.856, 0.1, 0.094,0.95}
    blue = {0.118, 0.53, 1, 0.95}
	secureWarning = '보안 토큰이 없으면, 침입자 공격이 발생합니다!'
	secureRemove = '보안 토큰이 제거되었습니다.'
	fireWarning = '더 이상 배치할 화재 마커가 없습니다. 모든 것이 파괴되었습니다!'
	malfunctionWarning = '더 이상 배치할 오작동 마커가 없습니다. 대신 화재 마커를 배치합니다'
	robotWarning = '로봇이 폭발했습니다! 근처 캐릭터들이 부상을 입었습니다.'
	robotSkipMsg = '이벤트 주요 효과를 건너뜁니다, 로봇이 아직 활성화되지 않았습니다.'
	autoDestructionWarning = '자폭 절차가 시작되었습니다.'
	removeWarning = '탐험 카드를 게임에서 제거해야 합니다.'
	alarmRoomMsg = '좌클릭으로 위험을 유발합니다.\n 우클릭으로 소음 마커를 제거합니다.'
	motionTrackerMsg = '소음 마커를 제거합니다. \n 소음 주사위를 굴리세요.'
	xenoChoiceMsg = '조직 1개를 소비하여\n다른 침입자 토큰을 뽑겠습니까?'
	insiderWarningMsg = '현재 인사이더 스토리 카드가 이 행동을 막고 있습니다.'
	setupEndMsg = '플레이어들은 순서에 관계없이, 아이템 덱 근처의 전술 장비 토큰으로 전술 벨트를 채울 수 있습니다. 완료되면 게임을 시작할 수 있습니다.'

    standeePosTable = {
		{-13.83, 2, 4.77},
        {-12.69, 2, 5.50},
        {-12.84, 2, 6.53},
        {-13.83, 2, 7.25},
        {-14.85, 2, 6.56},
        {-15.16, 2, 5.64},
		{-16, 2, 3.98},
		{-14.87, 2, 3.98},
		{-16, 2, 2.95},
		{-14.87, 2, 2.95},
    }

    beltSlotPosX = -4.09
    beltSlotPosZTable = {3.18, 2.30, 1.43, 0.56}
	
    playerInfoTable = {
		['Brown']={tint={0.443, 0.231, 0.090}, boardGUID = '79e72b', manualSeat = false, healthGUID = 'f05941', figureGUID = '',},
		['Pink']={tint={0.961, 0.439, 0.808}, boardGUID = '657f92', manualSeat = false, healthGUID = 'ae6191', figureGUID = '',},
		['Blue']={tint={0.122, 0.529, 1}, boardGUID = '22147f', manualSeat = false, healthGUID = '863a00', figureGUID = '',},
        ['Green']={tint={0.192, 0.702, 0.169}, boardGUID = '54f2f8', manualSeat = false, healthGUID = '733f1e', figureGUID = '',},
        ['Purple']={tint={0.627, 0.125, 0.941}, boardGUID = '0a9555', manualSeat = false, healthGUID = 'ce0e9f', figureGUID = '',},
        ['Orange']={tint={0.957, 0.392, 0.114}, boardGUID = 'c31c41', manualSeat = false, healthGUID = '1d51f6', figureGUID = '',},
        ['Red']={tint={0.855, 0.098, 0.094}, boardGUID = 'c8758b', manualSeat = false, healthGUID = 'd13ff6', figureGUID = '',},
        ['White']={tint={1, 1, 1}, boardGUID = '7563b9', manualSeat = false, healthGUID = '0cdfcc', figureGUID = '',},
		['Yellow']={tint={0.906, 0.898, 0.173}, boardGUID = '491d11', manualSeat = false, healthGUID = 'd78290', figureGUID = '',},
		['Teal']={tint={0.129, 0.694, 0.608}, boardGUID = '76301e', manualSeat = false, healthGUID = '390db1', figureGUID = '',},
    }
	
	playerHealthLocalPosX = {-3.13, -2.25, -1.75, -1.25, -0.21, 0.27, 0.79, 1.79, 2.29, 2.8}

	hotseat = false
	local laststeamid = 0
	
	for color, entry in pairs(playerInfoTable) do
		if Player[color].steam_id != nil then
			if laststeamid == Player[color].steam_id then
				hotseat = true
				print('여러분, 핫시트 모드가 켜졌습니다.')
				break
			end
			if laststeamid == 0 then
				laststeamid = Player[color].steam_id
			end
		end
	end
	
	supportItemDraftCount = 0
	
	
	automaticSeat = true
	actCol = false
	actColTile = gO('5fbf1a')
	weaponCol = true
	weaponColTile = gO('f5da36')
	
	
	soundTile = gO('162b51')
	roundTile = gO('dfc0e5')
	turnTiles = {'dc15cb', 'b97889'}
	drawTile = gO('7e707f')

	burstTile = gO('50894f')
	bagDevTile = gO('aa4ead')
	
	autoEventEnable = true
	autoEventTile = gO('74d8cc')
	
	use3DFig = true
	
	numpadSetTile = gO('3aa3ea')
	exploreNoiseEnable = true
	exploreNoiseTile = gO('04ec83')
	rollAnimationTile = gO('2e26e6')
	rollModeTile = gO('f24c3c')
	queenActivateTile = gO('55cd1a')
	
	shootRollDice = gO('d8282d')
	burstRollDice = gO('9cd65f')
	noiseRollDice = gO('effa9f')
	rollBowl = gO('c54938')
	
	-- shootRollDice.setRotationValues({
		-- {value = 1, rotation = {326,357,270}},
		-- {value = 2, rotation = {326,357,180}},
		-- {value = 3, rotation = {34,177,270}},
		-- {value = 4, rotation = {34,177,0}},
		-- {value = 5, rotation = {326,357,90}},
		-- {value = 6, rotation = {326,357,0}},
		-- {value = 7, rotation = {34,177,180}},
		-- {value = 8, rotation = {34,177,90}}
	-- })
	
	-- burstRollDice.setRotationValues({
		-- {value = 1, rotation = {0,0,0}},
		-- {value = 2, rotation = {270,180,0}},
		-- {value = 3, rotation = {0,0,270}},
		-- {value = 4, rotation = {0,0,90}},
		-- {value = 5, rotation = {0,0,180}},
		-- {value = 6, rotation = {90,180,0}}
	-- })
	
		-- noiseRollDice.setRotationValues({
			-- {value = 1, rotation = {38,180,343}},
			-- {value = 2, rotation = {321,0,235}},
			-- {value = 3, rotation = {38,180,271}},
			-- {value = 4, rotation = {321,0,19}},
			-- {value = 5, rotation = {321,6,163}},
			
			-- {value = 6, rotation = {38,184,126}},
			-- {value = 7, rotation = {321,3,92}},
			-- {value = 8, rotation = {39,183,55}},
			-- {value = 9, rotation = {38,184,199}},
			-- {value = 10, rotation = {321,3,307}}
		-- })

	
	landerPilotSoundBoard = gO('801a46')
	
	local locObjectsToHide = {actColTile, soundTile, weaponColTile, soundboard1, soundboard2, soundboard3, soundboard4, soundboard5, soundboard6, landerPilotSoundBoard, rollModeTile}
	
	for _, hibernatoriumCorGUID in pairs (hiddenCorridorsGUID) do
		table.insert(locObjectsToHide, gO(hibernatoriumCorGUID))
	end
	
	local locHideTbl = {}
	for color, entry in pairs (playerInfoTable) do
		table.insert(locHideTbl, color)
	end
	
	for _, hideEntry in pairs(locObjectsToHide) do
		if hideEntry != nil then
			hideEntry.setInvisibleTo(locHideTbl)
		end
	end
	
	if actColTile != nil then
		actColTile.createButton({
			click_function = 'actColToggle',
			function_owner = Global,
			label          = '액션 카드를 플레이어에게',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 1200,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(actColTile, 0)
	end
	
	if weaponColTile != nil then
		weaponColTile.createButton({
			click_function = 'weaponColToggle',
			function_owner = Global,
			label          = '무기 버튼을 턴 색상으로',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 1400,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(weaponColTile, 0)
	end
	
	if soundTile != nil then
		soundTile.createButton({
			click_function = 'soundToggle',
			function_owner = Global,
			label          = '사운드보드 활성화',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 1200,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(soundTile, 0)
	end
	
	if roundTile != nil then
		roundTile.createButton({
			click_function = 'nextRound',
			function_owner = Global,
			label          = '↓ 라운드 ↓',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 500,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(roundTile, 0)
	end
	
	for _, entry in pairs (turnTiles) do
		local locObj = gO(entry)
		if locObj != nil then
			locObj.createButton({
				click_function = 'endTurn',
				function_owner = Global,
				label          = '턴 종료',
				position       = {0, 0.15, 0},
				scale          = {2,2,2},
				width          = 500,
				height         = 200,
				font_size      = 100,
				color          = {0,0,0,0.8},
				font_color     = {0.8,0.8,0.8,0.95},
				tooltip        = '',
			})
			setFontSizeToButton(locObj, 0)
		end
	end
	
	if burstTile != nil then
		burstTile.createButton({
			click_function = 'autoBurstToggle',
			function_owner = Global,
			label          = '자동 집중사격',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 600,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(burstTile, 0)
	end
	
	if drawTile != nil then
		drawTile.createButton({
			click_function = 'drawButton',
			function_owner = Global,
			label          = '액션 카드 뽑기',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 620,
			height         = 200,
			font_size      = 100,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		setFontSizeToButton(drawTile, 0)
	end
	
	if bagDevTile != nil then
		bagDevTile.createButton({
			click_function = 'bagDevelopment',
			function_owner = Global,
			label          = '주머니\n 성장',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 700,
			height         = 200,
			font_size      = 75,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
	end
	
	if numpadSetTile != nil then
		numpadSetTile.createButton({
			click_function = 'none',
			function_owner = Global,
			label          = '숫자 설정 0',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 500,
			height         = 112,
			font_size      = 56,
			color          = {0.6,0,0,1},
			font_color     = {1,1,1,1},
			tooltip        = '',
		})
		setFontSizeToButton(numpadSetTile, 0)
	end
		
	explorationDeck = gO('b30d75')
	useXyrian = false
	useContractors = false
	useCustomContractors = false
	pickContractorsDeck = gO('24a5c3')
	pickCustomContractorsDeck = gO('7ace5d')
	
	xyrianExplorationDeck = gO('63292b')
	xyrianEventDeck = gO('419348')
	xyrianPhase = gO('4c54e2')
	xyrianFBag = gO('0aeeb4')
	xyrianInjuryBag = gO('2ed00a')
	xyrianTracerBag = gO('89c362')
	xyrianStatusBag = gO('261bba')
	xyrianActivationDeck = gO('f0e3ae')
	xyrianTokenGUID = '4bae0b'
	xyrianEventGUIDs = {'19c034', '635a85', 'dde726'}
	xyrianAllegiance = gO('9d31c8')
	xyrianAllegianceToken = gO('e6dc9b')
	
	insiderEnable = false
	insiderStoryGUID = ''
	insiderDeck = gO('1c3be3')
	insiderFig = gO('b8323a')
	insiderCard = gO('04e7a0')
	insiderHealth = gO('03446d')
	insiderRunaway = gO('1b11a3')

	
	xyrianColor = {0.392, 0.875, 1, 1}
	shootColor = {0.992,0.184, 0.149}
	burstColor = {0.667, 0.18, 0.61}
	
	insiderColor = {0.655,0.37,1}
	
	useCharacterDraft = true
	
	
	local locCols = {
			{0.288,0.485,0.8625},
			{0.332,0.699,0.3615},
			{0.392,0.239,0.678},
			{0.9375,0.519,0.198},
			{0.83,0.235,0.218},
			{0.6,0.6,0.6}
		}
	crewLabelTable = {
					{'Officer',1},{'Sharpshooter',2},{'Bioenhancment Expert',2},{'Recon',3},{'Combat Engineer',4},{'UAV Operator',4},
					{'Medical Support',4},{'Heavy Gun Operator',5},{'Contractor',6},
					{'Captain',6},{'Pilot',6},{'Scout',6},{'Mechanic',6},{'Soldier',6},{'Scientist',6},
					{'Sentry',6},{'Hacker',6},{'Lab Rat',6},{'Janitor',6},{'Survivor',6},{'Xenobiologist',6},
					{'CEO', 6}, {'Android', 6}, {'Bounty Hunter', 6}, {'Medic', 6}, {'Convict', 6}, {'Psychologist', 6},
					{'Hunter', 6}
					}
	
	for i=1, #crewLabelTable do
		crewLabelTable[i][3] = locCols[crewLabelTable[i][2]]
	end
	
	


    --Uncomment to clear any saved data
	--saved_data = ""
    if saved_data != '' then
        local loaded_data = JSON.decode(saved_data)
        setupComplete = loaded_data.save_setupComplete
		automaticSeat = loaded_data.save_automaticSeat
		useXyrian = loaded_data.save_useXyrian
		useContractors = loaded_data.save_useContractors
		useLanderVoices = loaded_data.save_useLanderVoices
		lifeforms = loaded_data.save_lifeforms
		
		if not automaticSeat then
			playerInfoTable['Brown'].manualSeat = loaded_data.save_manualSeat1
			playerInfoTable['Pink'].manualSeat = loaded_data.save_manualSeat2
			playerInfoTable['Blue'].manualSeat = loaded_data.save_manualSeat3
			playerInfoTable['Green'].manualSeat = loaded_data.save_manualSeat4
			playerInfoTable['Purple'].manualSeat = loaded_data.save_manualSeat5
			playerInfoTable['Orange'].manualSeat = loaded_data.save_manualSeat6
			playerInfoTable['Red'].manualSeat = loaded_data.save_manualSeat7
			playerInfoTable['White'].manualSeat = loaded_data.save_manualSeat8
			playerInfoTable['Yellow'].manualSeat = loaded_data.save_manualSeat9
			playerInfoTable['Teal'].manualSeat = loaded_data.save_manualSeat10
		end
		deadlyMode = loaded_data.save_deadlyMode
		
		playerInfoTable['Brown'].figureGUID = loaded_data.save_figureGUID1
		playerInfoTable['Pink'].figureGUID = loaded_data.save_figureGUID2
		playerInfoTable['Blue'].figureGUID = loaded_data.save_figureGUID3
		playerInfoTable['Green'].figureGUID = loaded_data.save_figureGUID4
		playerInfoTable['Purple'].figureGUID = loaded_data.save_figureGUID5
		playerInfoTable['Orange'].figureGUID = loaded_data.save_figureGUID6
		playerInfoTable['Red'].figureGUID = loaded_data.save_figureGUID7
		playerInfoTable['White'].figureGUID = loaded_data.save_figureGUID8
		playerInfoTable['Yellow'].figureGUID = loaded_data.save_figureGUID9
		playerInfoTable['Teal'].figureGUID = loaded_data.save_figureGUID10
		
		insiderEnable = loaded_data.save_insiderEnable
		insiderStoryGUID = loaded_data.save_insiderStoryGUID
		
		scriptEnabled = loaded_data.save_scriptEnabled
		
		queenFigGUID = loaded_data.save_queenFigGUID
		
		prevXyrianCardGUID = loaded_data.save_prevXyrianCardGUID
		previousXyrianCard = gO(prevXyrianCardGUID)
		
    else
        setupComplete = false
    end
	
    if not setupComplete then
		
		local locW = 650
		local locH = 200
		local locOffX = 0.35
		
		boarderTile.createButton({
			click_function = 'automaticSeatToggle',
			function_owner = Global,
			label = '자동\n자리배치',
			position       = {locOffX,0.2,0},
			scale = {0.8,0.8,0.8},
			width = locW,
			height         = locH,
			font_size      = 80,
			color = {0.65,0,0},
			font_color     = {1,1,1},
		})
		--setFontSizeToButton(boarderTile, 0)
		
		boarderTile.createButton({
			click_function = 'deadlyModeToggle',
			function_owner = Global,
			label = '데들리 모드\n비활성화',
			position       = {locOffX,0.2,-0.4},
			scale = {0.8,0.8,0.8},
			width = locW,
			height         = locH,
			font_size      = 80,
			color = {0,0,0,0.8},
			font_color     = {1,1,1},
		})
		--setFontSizeToButton(boarderTile, 1)
		
        boarderTile.createButton({
            click_function = 'lifeformCheck',
            function_owner = Global,
            label          = '셋팅하기',
            position       = {locOffX, 0.15, 0.4},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 120,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
            tooltip        = '설정을 실행하기 전에 모든 인원이 자리에 착석했는지 확인하세요.',
        })
		--setFontSizeToButton(boarderTile, 2)
		
		
        boarderTile.createButton({
            click_function = 'useXyrianToggle',
            function_owner = Global,
            label          = '자이리안\n비활성화',
            position       = {1.1 + locOffX, 0.15, -0.4},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 3)

        boarderTile.createButton({
            click_function = 'useContractorsToggle',
            function_owner = Global,
            label          = '계약자\n비활성화',
            position       = {1.1 + locOffX, 0.15, 0},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 4)
		
        boarderTile.createButton({
            click_function = 'useLanderVoicesToggle',
            function_owner = Global,
            label          = '착륙선 목소리\n비활성화',
            position       = {1.1 + locOffX, 0.15, 0.4},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 70,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 5)
		
        boarderTile.createButton({
            click_function = 'characterDraftToggle',
            function_owner = Global,
            label          = '캐릭터 드래프트\n활성화',
            position       = {-1.1 + locOffX, 0.15, -0.4},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 70,
            color          = {0.05,0.1,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 6)
		
        boarderTile.createButton({
            click_function = 'lifeformToggle',
            function_owner = Global,
            label          = 'VS\n프라임블러드',
            position       = {-1.1 + locOffX, 0.15, 0},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0.156, 0.6855, 0.47025},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 7)
		
        boarderTile.createButton({
            click_function = 'coopToggle',
            function_owner = Global,
            label          = '세미 협동\n모드',
            position       = {-1.1 + locOffX, 0.15, 0.8},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0.75,0.075,0.05},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 8)
		
        boarderTile.createButton({
            click_function = 'coopCustomToggle',
            function_owner = Global,
            label          = '커스텀 협동\n비활성화',
            position       = {-1.1 + locOffX, 0.15, 1.2},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 9)
		
        boarderTile.createButton({
            click_function = 'insiderToggle',
            function_owner = Global,
            label          = '인사이더\n비활성화',
            position       = {1.1 + locOffX, 0.15, 0.8},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 10)
		
        boarderTile.createButton({
            click_function = 'skipScript',
            function_owner = Global,
            label          = '스크립트\n비활성화',
            position       = {locOffX, 0.15, 0.8},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 11)
		
        boarderTile.createButton({
            click_function = 'figToggle',
            function_owner = Global,
            label          = '3D 피규어\n선호',
            position       = {-1.1 + locOffX, 0.15, 0.4},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 12)
		
		        boarderTile.createButton({
            click_function = 'customContractorToggle',
            function_owner = Global,
            label          = '커스텀 계약자\n비활성화',
            position       = {2.2 + locOffX, 0.15, 0},
            scale          = {0.8,0.8,0.8},
            width          = locW,
            height         = locH,
            font_size      = 80,
            color          = {0,0,0,0.8},
            font_color     = {1,1,1},
        })
		--setFontSizeToButton(boarderTile, 13)
		
		soundToggle()
		
	else
		if scriptEnabled then
			for color, entry in pairs(playerInfoTable) do
				if not (Player[color].seated or (not automaticSeat and entry.manualSeat)) then
					local locBoard = gO(entry.boardGUID)
					local locPos = locBoard.getPosition()
					
					locBoard.setInvisibleTo(locHideTbl) --Better than destroying and checking if board is valid later I think...?
				end
			end
			
			local locRooms = {}
			local locCorridors = {}
			
			for _, castObj in pairs(getAllObjects()) do
				for _, tag in pairs(castObj.getTags()) do
					if tag == 'room' then
						table.insert(locRooms, castObj)
						break
					elseif tag == 'Corridors' then
						table.insert(locCorridors, castObj)
						break
					end
				end
			end
			
			registerToRoomsMap(locRooms, locCorridors)
		end
    end






	if hibUnexplored != nil then
		hibUnexplored.createButton({
			click_function = 'hibExplore',
			function_owner = Global,
			label          = '동면실 발견',
			position       = {0, 0.15, -1.0},
			scale          = {0.5,0.5,0.5},
			width          = 1300,
			height         = 400,
			font_size      = 360,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '클릭하여 동면실을 발견합니다.',
		})
	end


	
	Wait.frames(|| buildButtons(), 30)
	--prevents error from multiple scans
	Wait.frames(function() scanNotActive = true end, 60)
	
	broadcastToAll('행운을 빌어요. 즐거운 게임 되세요! :D', {0.5,1,1})
	broadcastToAll('안녕하세요.', {0.5,1,0.5})
	Turns.enable = true
	countPlayers(true)

	if scriptEnabled then
		if setupComplete and lifeforms != 'Primebloods' then
			if lifeforms == 'Neoflesh' then
				recallNeoflesh()
			elseif lifeforms == 'Sangrevores' then
				recallSangrevores()
			elseif lifeforms == 'Carnomorph' then
				recallCarnomorph()
			end
		else
			lifeformColor = Color(0.208,0.914,0.627, 1)
			lightColorStart = maxColor(lifeformColor)
			lightColorStart = setSaturation(lightColorStart, 0.25)
			Lighting.setLightColor(lightColorStart)
			Lighting.apply()
		end


		autoBurstToggle(burstTile, 'Red', false)
		
		tileImportedSize = tileImportedSize*landingZone.getScale()
		corridorImportedSize = corridorImportedSize*landingZone.getScale()
		
		autoEventTile.createButton({
			click_function = 'autoEventToggle',
			function_owner = Global,
			label          = '자동 이벤트',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 500,
			height         = 112,
			font_size      = 56,
			color          = {lifeformColor[1]*0.75, lifeformColor[2]*0.75, lifeformColor[3]*0.75},
			font_color     = {1,1,1,1},
			tooltip        = '',
		})
		setFontSizeToButton(autoEventTile, 0)
		
		exploreNoiseTile.createButton({
			click_function = 'exploreNoiseToggle',
			function_owner = Global,
			label          = '자동 탐험' .. '\n' .. '소음 ON',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 500,
			height         = 112,
			font_size      = 56,
			color          = {0.984,0.776,0.204,1},
			font_color     = {0,0,0,1},
			tooltip        = '',
		})
			
		rollAnimationEnable = false
		rollAnimationTile.createButton({
			click_function = 'rollAnimationToggle',
			function_owner = Global,
			label          = '주사위 애니' .. '\n' .. '미예상',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 400,
			height         = 100,
			font_size      = 60,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})
		
		rollMode = true
		rollModeTile.createButton({
			click_function = 'rollModeToggle',
			function_owner = Global,
			label          = '수동 주사위',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 700,
			height         = 100,
			font_size      = 100,
			color          = {0,0,0.6,1},
			font_color     = {1,1,1,1},
			tooltip        = '',
		})
		
		queenActivateTile.createButton({
			click_function = 'queenCall',
			function_owner = Global,
			label          = '여왕 활성화',
			position       = {0, 0.15, 0},
			scale          = {2,2,2},
			width          = 500,
			height         = 100,
			font_size      = 60,
			color          = {0,0,0,0.8},
			font_color     = {0.8,0.8,0.8,0.95},
			tooltip        = '',
		})

	end
	
	trapCheck = false
	trapsList = {}
	
	for color, entry in pairs (playerInfoTable) do
		if entry.figureGUID != '' then
			local locFig = gO(entry.figureGUID)
			if locFig != nil then
				if string.find(locFig.getName(), 'Hunter') != nil then
					trapCheck = true
					for _, obj in pairs (getAllObjects()) do
						if obj.getGMNotes() == 'trap' then
							table.insert(trapsList,obj)
						end
					end
					break
				end
			end
		end
	end
	
end

delayedSkipScript = false
function skipScript()
	
	choiceToPlayer({1.5,2.68,-10.57}, 'Yes = Put objects in Box\n No = Disable script at Setup.', 50)
	
	
	Wait.condition(function()
		
		if choiceState == 1 then
			for _, obj in pairs (gameBox.getObjects()) do
				if obj.name == 'Primebloods' then
					gameBox.takeObject({
						position = gameBox.getPosition() + Vector(0,10,0),
						smooth = false,
						callback_function = function(o)
							o.setLock(true)
							
							for _, bag in pairs ({larvaeBag, larvaeFBag, adultBag, adultFBag, breederBag, breederFBag, queenBag, queenFBag,
							explorationDeck, eventDeck, attacksDeck, queenHealthDeck, intruderHelp}) do
								bag.setLock(false)
								o.putObject(bag)
							end

							intruderBag.takeObject({
								position = intruderBag.getPosition() + Vector(0,10,0),
								callback_function = function (o2)
									o.putObject(o2)
									o.setLock(false)
									gameBox.putObject(o)
								end,
							})

						end,
						guid = obj.guid,
					})
				
				elseif obj.name == 'Xyrians' then
					gameBox.takeObject({
						position = gameBox.getPosition() + Vector(5,10,0),
						smooth = false,
						callback_function = function(o)
							o.setLock(true)
							
							for _, xyr in pairs 
							({xyrianFBag, xyrianInjuryBag, xyrianTracerBag, xyrianAllegianceToken, gO(xyrianTokenGUID), gO('347097'), xyrianAllegiance, xyrianExplorationDeck, xyrianEventDeck, gO('85c7f7'), xyrianPhase, xyrianActivationDeck, gO('9fad4f'), xyrianStatusBag}) do
								xyr.setLock(false)
								o.putObject(xyr)
							end
							o.setLock(false)
							gameBox.putObject(o)
						end,
						guid = obj.guid,
					})
				end
			end
			
			for _, obj in pairs({gO('a29f4d'), gO('34e73c'), gO('57f148'), gO('4df8ef'), gO('eef7fc'), rollAnimationTile,  rollModeTile, exploreNoiseTile, roundTile, drawTile, gO('dc15cb'), gO('b97889'), numpadSetTile, gO('0e8d84'), trashBag, autoEventTile, bagDevTile, burstTile}) do
				obj.destruct()
			end
			
			for _, obj in pairs ({firstPlayerToken, playerHelpBag}) do
				obj.setLock(false)
				toBox(obj)
			end
		
			boarderTile.clearButtons()
			scriptEnabled = false
			setupComplete = true
		else
			delayedSkipScript = true
		end
		
		choiceState = 2

	end, function() return choiceState < 2 end, 999999, function() end)
	
		
end

function recallNeoflesh()
	if not scriptEnabled then
		return true
	end
	
	lifeformColor = Color(1,0.488,0.226, 1)
	lightColorStart = maxColor(lifeformColor)
	lightColorStart = setSaturation(lightColorStart, 0.25)
	Lighting.setLightColor(lightColorStart)
	Lighting.apply()
	
	explorationDeck = gO('a24dc8')
	attacksDeck = gO('61a87c')
	eventDeck = gO('abbdd0')
	queenHealthDeck = gO('99e2ce')
 

	larvaeBag = gO('595bcc')
	adultBag = gO('ecc8e6')
	queenBag = gO('f31180')

	larvaeFBag = gO('a00d06')
	adultFBag = gO('c36ee8')
	ironcladFBag = gO('fd7091')
	firespitterFBag = gO('e0feed')
	crawlmineFBag = gO('1ca1ec')
	breederFBag = gO('84381e')
	queenFBag = gO('f6fec4')	
	
	cultistDeadBag = gO('63aef2')



end



function recallSangrevores()
	if not scriptEnabled then
		return true
	end
	
	lifeformColor = Color(1,0.192,0.282)
	lightColorStart = maxColor(lifeformColor)
	lightColorStart = setSaturation(lightColorStart, 0.25)
	Lighting.setLightColor(lightColorStart)
	Lighting.apply()
	
	explorationDeck = gO('dd1eda')
	attacksDeck = gO('3a25fc')
	eventDeck = gO('58aa1c')
	queenHealthDeck = gO('3b65b3')


	adultBag = gO('d181aa')
	breederBag = gO('405099')
	queenBag = gO('37f835')

	adultFBag = gO('f7fd5f')
	breederFBag = gO('a0f2a3')
	queenFBag = gO('4abca0')
	
	shadowBag = gO('aff77d')
	taintedDeck = gO('7347e2')
	contaminationDeck = gO('ebef8b')
	noiseBag = gO('7cb24e')
	
	gO('56ae35').createButton({
		click_function = 'none',
		position = {0,0.2,0},
		label = '감염\n카드\n버리기',
		width = 0,
		height = 0,
		color = {0,0,0,1},
		font_color = lifeformColor,
		font_size = 150,
	})
end

function recallCarnomorph()

	if not scriptEnabled then
		return true
	end
	
	lifeformColor = Color(1,0.192,0.192)
	lightColorStart = maxColor(lifeformColor)
	lightColorStart = setSaturation(lightColorStart, 0.25)
	Lighting.setLightColor(lightColorStart)
	Lighting.apply()
	
	explorationDeck = gO('2e8e9d')
	attacksDeck = gO('9aefbc')
	eventDeck = gO('0da709')
	queenHealthDeck = gO('6963a5')
	
	
	larvaeBag = gO('c2c9ea')
	creeperBag = gO('c2c9ea')
	adultBag = gO('81dd12')
	breederBag = gO('4b660f')
	queenBag = gO('c13884')
	
	larvaeFBag = gO('231d79')
	creeperFBag = gO('231d79')
	adultFBag = gO('47fde0')
	breederFBag = gO('3be840')
	queenFBag = gO('db891d')
	
	mutationDeck = gO('c74454')
	mutationMarker = gO('a1a031')

end



function getMaxValueColor(col)
	if not scriptEnabled then
		return true
	end
	
	return math.max(math.max(col[1], col[2]), col[3])
end

function maxColor(col)
	if not scriptEnabled then
		return true
	end
	
	local S = 1 / getMaxValueColor(col)
	local locCol = Color(col[1]*S,col[2]*S,col[3]*S)
	
	if col[4] != nil then
		table.insert(locCol, col[4])
	end
	
	return locCol
end

function getSaturation(col)
	if not scriptEnabled then
		return true
	end
	
	return ( 1 - (math.min(math.min(col[1], col[2]), col[3]) ) / getMaxValueColor(col))
end

function setSaturation(col, saturation)
	if not scriptEnabled then
		return true
	end
	
	local S = getSaturation(col)
	local S2 = getMaxValueColor(col)
	
	local locColLerp0 = Color(col[1]*S, col[2]*S, col[3]*S)
	local locColLerp1  = Color(col[1]/S2, col[2]/S2, col[3]/S2)

	local locR = (locColLerp0:lerp(col, locColLerp1[1]))[1]
	local locG = (locColLerp0:lerp(col, locColLerp1[2]))[2]
	local locB = (locColLerp0:lerp(col, locColLerp1[3]))[3]
	
	
	local colS = Color(S2,S2,S2):lerp(Color(locR,locG,locB), saturation)
	
	if col[4] != nil then
		colS[4] = col[4]
	end
	
	return colS

end

function numpadToggle()
	if not scriptEnabled then
		return true
	end
	
	local locCol = {0,0,0,1}
	if OnScriptButtonSet == 0 then
		locCol = {0.6,0,0,1}
	elseif OnScriptButtonSet == 1 then
		locCol = {0,0.6,0,1}
	elseif OnScriptButtonSet == 2 then
		locCol = {0,0,0.6,1}
	end
	
	numpadSetTile.editButton({ index = 0, label = '숫자 설정 ' .. OnScriptButtonSet, color = locCol})
end

function figToggle()
	if not scriptEnabled then
		return true
	end
	
	if use3DFig then
		use3DFig = false
		boarderTile.editButton({index = 12, label = '2D 피규어\n선호'})
	else
		use3DFig = true
		boarderTile.editButton({index = 12, label = '3D 피규어\n선호'})
	end
end

function exploreNoiseToggle()
	if not scriptEnabled then
		return true
	end
	
	if exploreNoiseEnable then
		exploreNoiseEnable = false
		exploreNoiseTile.editButton({ index = 0, label = '자동 탐험' .. '\n' .. '소음 OFF', color = {0,0,0,0.8}, font_color = {1,1,1,1}})
	else
		exploreNoiseEnable = true
		exploreNoiseTile.editButton({ index = 0, label = '자동 탐험' .. '\n' .. '소음 ON', color = {0.984,0.776,0.204,1}, font_color = {0,0,0,1}})
	end
	
end

function autoEventToggle()
	if not scriptEnabled then
		return true
	end
	
	if autoEventEnable then
		autoEventTile.editButton({index = 0, color = {0,0,0,0.8}})
		autoEventEnable = false
	else
		autoEventTile.editButton({index = 0, color = {lifeformColor[1]*0.75, lifeformColor[2]*0.75, lifeformColor[3]*0.75}})
		autoEventEnable = true
	end
end

markedWeapon = nil
shootingState = 0
mayRerollNextShoot = false
mayRerollNextBurst = false

function markWeaponToggle(obj, enemy, isInRoom)
	if not scriptEnabled then
		return true
	end
	
	local locRoom = true
	
	if isInRoom != nil then
		locRoom = isInRoom
	end
	
	shootingState = 0
	if markedWeapon != nil then
		markedWeapon.editButton({index = #markedWeapon.getButtons() - 1, label = '--', color = {0,0,0,0.8}})
		if enemy != nil then
			local locLastIndex = #enemy.getButtons() -1
			for i = 1, locLastIndex do
				if i != locLastIndex then
					enemy.editButton({index = i, color = {0,0,0,1}})
				end
			end
		end
	end
	
	if obj != nil then
		local locState = 0
		local locPos = obj.getPosition()
		local locSize = obj.getBounds().size
		local locPCol = getNearestPColor(locPos.x)

		
		if not obj.hasTag('weapon') or obj.getGMNotes() == 'grenade' then
		elseif getTaggedObjAtPos('malfunction', locPos, 3, locSize) != nil then
			locState = 1
		elseif obj.hasTag('TacticalSlots') then
			if getTaggedObjAtPos('ammo', locPos, 3, locSize) == nil then
				local locPlayerEntry = playerInfoTable[locPCol]
				local locBoard = gO(locPlayerEntry.boardGUID)
				local locArmor = getTaggedObjAtPos('StartItem2', locBoard.getPosition(), 0, locBoard.getBounds().size)
				if locArmor != nil then
					if locArmor.getGMNotes() == 'AA' and getTaggedObjAtPos('ammo', locArmor.getPosition(), 3, locArmor.getBounds().size) != nil then
							locState = 0
					else
						locState = 2
					end
				else
					locState = 2
				end
			end
			
			if obj.hasTag('ammoCharges') then --that's because of the CEO Robot having it all man, it's fun but it's such a messy exception for the script.
				if obj.getVar("count") == 0 then
					locState = 2
				else
					if locRoom then 
						locState = 0
					end
				end
			end
			
		elseif obj.hasTag('ammoCharges') then
			if obj.getVar("count") == 0 then
				locState = 2
			end
		end
		
		if enemy != nil then
			if enemy.getGMNotes() == 'xyrian' then
				if playerHasTag('xyrianAllegiance', 3, nil, locPCol) then
					locState = 3
				end
			end
		end
		
		if obj != markedWeapon and locState == 0 then

			obj.editButton({index = #obj.getButtons() - 1, label = '표시됨', color = {0.2,0,0,1}})
			if enemy != nil then
				if enemy.getButtons() != nil then
					local j = 0
					--local locDesc = obj.getDescription()
					
					-- if locDesc == 'MELEE' then
						-- for _, button in pairs (enemy.getButtons()) do
							-- if button.label == 'MELEE' or button.label == 'ROOM/ROBOT' then
								-- locDesc = button.label
								-- break
							-- end
						-- end
					-- end

					
					local locGUID = obj.getGUID()
					for _, button in pairs (enemy.getButtons()) do
						if button.tooltip == locGUID then
							enemy.editButton({index = j, color = shootColor})
							if lifeforms == 'Sangrevores' then
								if playerHasTag('HEADACHES', 1, nil, locPCol) then
									broadcastToAll('플레이어 ' .. locPCol .. '의 두통으로 인해 사격/집중사격에 액션 카드가 1장 더 필요합니다.', lifeformColor)
								end
							end
							break
						end
						j = j + 1
					end
				end
			end		
			markedWeapon = obj
		else
			markedWeapon = nil
			if locState > 0 then
				local locMsg = '이 무기를 사용할 수 없습니다: '
				local locFontColor = lifeformColor
				if locState == 1 then
					locMsg = locMsg .. '수리가 필요합니다.'
				elseif locState == 2 then
					locMsg = locMsg .. '탄약이 필요합니다.'
				elseif locState == 3 then
					locMsg = '플레이어 ' .. locPCol .. '는 충성을 맹세한 자이리안을 공격할 수 없습니다.'
					locFontColor = xyrianColor
				end
				broadcastToAll(locMsg,locFontColor)
			end
		end
	else
		markedWeapon = nil
	end
end

function markButton(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	markWeaponToggle(obj, nil)
end


function meleeMark(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	if shootingState == 0 then
		local locBoard = gO(playerInfoTable[pColor].boardGUID)
		
		if locBoard != nil then
			markWeaponToggle(locBoard, obj)
		end
	end
end

function queenCall()

	if not scriptEnabled then
		return true
	end
	
	if isQueenAlive() then
		if queenFBag.getQuantity() == 0 then
			activateQueen()
		end
	end

end

function loseAmmo(weapon, skipCharge)
	if not scriptEnabled then
		return true
	end
	
	local locSkip = false
	
	if skipCharge != nil then
		locSkip = skipCharge
	end
	
	if weapon.hasTag('TacticalSlots') then
		local locPos = weapon.getPosition()
		local locObj = getTaggedObjAtPos('ammo', locPos, 3, weapon.getBounds().size)
		
		if locObj == nil then
			local locPlayerEntry = playerInfoTable[getNearestPColor(locPos.x)]
			local locBoard = gO(locPlayerEntry.boardGUID)
			local locArmor = getTaggedObjAtPos('StartItem2', locBoard.getPosition(), 0, locBoard.getBounds().size)
			if locArmor != nil then
				if locArmor.getGMNotes() == 'AA'then
					locObj = getTaggedObjAtPos('ammo', locArmor.getPosition(), 3, locArmor.getBounds().size)
				end
			end
		end
		
		if locObj != nil then
			if locObj.getStateId() == 1 then
				locObj.setState(2)
			elseif locObj.getStateId() == 2 then
				onObjectNumberTyped(locObj,'Red',0)
			end
			broadcastToAll('플레이어 ' .. getNearestPColor(weapon.getPosition().x) .. '가 탄약을 사용했습니다.', {1,1,1})
		end
	end
	
	if not locSkip then
		loseCharge (weapon)
	end
end

function loseCharge (weapon)
	if not scriptEnabled then
		return true
	end
	
	if weapon.hasTag('ammoCharges') then
		weapon.setVar("count", weapon.getVar("count") - 1)
		weapon.call("updateDisplay")
	end
end

function isInOxygenSection(obj)
	if not scriptEnabled then
		return true
	end
	
	if obj != nil then
		local locSection = getSectionFromXPos(obj.getPosition().x)
		local locOx = false
		local locOff = {0,0,0}


		
		if locSection == 'A' then
			locOff = {6.6,0.0,-14.02}
		elseif locSection == 'B' then
			locOff = {-3.88,0.0,-12.97}
		elseif locSection == 'C' then
			locOff = {-15.22,0.0,-14.02}
		end
		
		locOff = Vector(locOff[1]/8.7, locOff[2], locOff[3] / 8.68)
		
		local locPos = boarderTile.getPosition() + rotateVectorAboutY(locOff * boarderTile.getScale(), boarderTile.getRotation().y) 
		
		return (getTaggedObjAtPos('LifeSupport', locPos, 0) != nil)
	else
		return false
	end
end

function hibExplore(obj)
	if scriptEnabled then
		if robotToken != nil then
			robotToken.setState(1)
		end
		
		local locRobotName= ''
		local locRobotMsg = ''
		if robot.getGMNotes() == '' then
			for _, entry in pairs(getAllObjects()) do
                if entry.hasTag('RobotCard') then
                    entry.flip()
                    locRobotName = entry.getName()
                    break
                end
            end
			
			robot.setGMNotes('active')
			locRobotMsg = locRobotName .. '이 활성화되어 공개되었습니다.'
		end
		
		
		broadcastToAll('동면실이 발견되었습니다. ' .. locRobotMsg, lifeformColor)
		local locGateSoundID = 45
		
		if math.random() > 0.5 then
			locGateSoundID = 184
		end
		
		playsounds(locGateSoundID)
		Wait.time(function() playsounds(185) end, soundDuration[locGateSoundID+1] * 0.4)
	end
	
	toBox(obj)
end

function characterDraftToggle()
	if not scriptEnabled then
		return true
	end
	
	if useCharacterDraft then
		useCharacterDraft = false
		boarderTile.editButton({index = 6, label = '캐릭터 드래프트\n비활성화', color = {0,0,0,0.8}})
		
	else
		useCharacterDraft = true
		boarderTile.editButton({index = 6, label = '캐릭터 드래프트\n활성화', color = {0.05,0.1,0.8,1}})
	end

end

function lifeformToggle()
	if not scriptEnabled then
		return true
	end
	
	if lifeforms == 'Primebloods' then
		lifeforms = 'Neoflesh'
		lifeformColor = Color(1,0.488,0.226, 1)
		local c = lifeformColor
		boarderTile.editButton({index = 7, label = 'VS\n네오플레시', color = {c[1]*0.75,c[2]*0.75,c[3]*0.75}})

	elseif lifeforms == 'Neoflesh' then
		lifeforms = 'Sangrevores'
		lifeformColor = Color(1,0.192,0.282)
		local c = lifeformColor
		boarderTile.editButton({index = 7, label = 'VS\n상그레보어', color = {c[1]*0.75,c[2]*0.75,c[3]*0.75}})
	elseif lifeforms == 'Sangrevores' then
		lifeforms = 'Carnomorph'
		lifeformColor = Color(1,0.192,0.192)
		boarderTile.editButton({index = 7, label = 'VS\n카르노모프', color = {0.75,0,0}})
	elseif lifeforms == 'Carnomorph' then
		lifeforms = 'Random'
		lifeformColor = Color(1,1,1)
		boarderTile.editButton({index = 7, label = 'VS\n랜덤', color = {1,0,0}})
		shiningRandomButton()
	elseif lifeforms == 'Random' then
		lifeforms = 'Primebloods'
		lifeformColor = Color(0.208,0.914,0.627, 1)
		local c = lifeformColor
		boarderTile.editButton({index = 7, label = 'VS\n프라임블러드', color = {c[1]*0.75,c[2]*0.75,c[3]*0.75}})
	end
	
	lightColorStart = maxColor(lifeformColor)
	lightColorStart = setSaturation(lightColorStart, 0.25)
	Lighting.setLightColor(lightColorStart)
	Lighting.apply()
	
	if autoEventEnable then
		autoEventTile.editButton({index = 0, color = lifeformColor})
	end
	
end

function shiningRandomButton()
	
	if lifeforms == 'Random' then
		
		local locColor = {math.abs(math.cos(Time.time)), math.abs(math.cos(Time.time + 3.14/4)), math.abs(math.cos(Time.time + 1.75 *3.14/4))}
		boarderTile.editButton({index = 7, color = locColor})
		Wait.frames(function () shiningRandomButton() end, 2)
	end
end

coopMode = false
function coopToggle()
	if not scriptEnabled then
		return true
	end
	
	if coopMode then
		if coopCustom then
			coopCustomToggle()
		end
		coopMode = false
		boarderTile.editButton({index = 8, label = '세미 협동\n모드', color = {0.75,0.075,0.05}})
	else
		coopMode = true
		boarderTile.editButton({index = 8, label = '솔로/협동\n모드', color = {0.075,0.38,0.75}})
	end
end


coopCustom = false
function coopCustomToggle()
	if not scriptEnabled then
		return true
	end
	
	if coopMode then
		if coopCustom then
			coopCustom = false
			boarderTile.editButton({index = 9, label = '커스텀 협동\n비활성화', color = {0,0,0,0.8}})
		else
			coopCustom = true
			boarderTile.editButton({index = 9, label = '커스텀 협동\n활성화', color = {0.075,0.38,0.75}})
		end
	end
end

function insiderToggle()
	if not scriptEnabled then
		return true
	end
	
	if insiderEnable then
		insiderEnable = false
		boarderTile.editButton({index = 10, label = '인사이더\n비활성화', color = {0,0,0,0.8}})
	else
		insiderEnable = true
		boarderTile.editButton({index = 10, label = '인사이더\n활성화', color = insiderColor})
	end
end

selectingCrew = false
function createSelectCrew(pBoardColor)
	if not scriptEnabled then
		return true
	end
	
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and entry.manualSeat) then
			pBoard = gO(entry.boardGUID)

			if pBoardColor == nil or pBoardColor == color then
				for i, label in pairs(crewLabelTable) do
					

					local locW = 1125
					local locH = 300
					local fsize = math.min(2*locW/string.len(label[1]) ,locH/2)
					local bcolor = label[3]
					local fcolor = {0.75+(label[3][1]*0.25), 0.75+(label[3][2]*0.25), 0.75+(label[3][3]*0.25)}
					
					local xpos = (-1.12+((i-0.5)%6)*0.37)
					local zpos = (-0.8)+(math.floor((i-0.5)/6)*0.1)
					
					pBoard.createButton({
						click_function = 'selectCrew' .. i,
						function_owner = Global,
						label = label[1],
						position       = {xpos,2,zpos},
						scale = {0.15,0.15,0.15},
						width = locW,
						height         = locH,
						font_size      = fsize,
						color		   = bcolor,
						font_color     = fcolor,
					})
					
					if not useContractors and label[1] == 'Contractor' then
						break
					elseif not useCustomContractors and label[1] == 'Xenobiologist' then
						break
					end
				end
			end
		end
	end
	
	for i=1, #crewLabelTable do
		--build functions
		local func = function(obj, pColor, alt_click)
			
			
			if not selectingCrew and obj.getGUID() == playerInfoTable[pColor].boardGUID then
				selectingCrew = true
				
				-- for color, entry in pairs(playerInfoTable) do
					-- if Player[color].seated or (not automaticSeat and entry.manualSeat) then
						-- local locPBoard = gO(playerInfoTable[color].boardGUID)
						-- if locPBoard.getButtons() != nil then
							-- for _, obj in pairs(locPBoard.getButtons()) do
						
								-- if crewLabelTable[i][1] == obj.label then
									-- locPBoard.removeButton(obj.index)
								-- end
							-- end
						-- end
					-- end
				-- end
				
				for _, entry in pairs(characterDraftDeck.getObjects()) do
					if entry.name == crewLabelTable[i][1] then
						characterDraftDeck.takeObject({
							position = characterDraftDeck.getPosition() + Vector(0,5,0),
							guid = entry.guid,
							callback_function = function (o)
								copyCharacterBag(o, pColor)
								characterDraftDeck.putObject(o)
							end,
						})
					end
				end
			else
				broadcastToAll('누군가 자신의 플레이어 보드 버튼을 클릭하지 않고 있는 것 같습니다.', {1,0.25,0.25})
			end
		end
		_G['selectCrew' .. i] = func		
	end
end

function copyCharacterBag(selectedCard, pColor)
	if not scriptEnabled then
		return true
	end
	
	local name = selectedCard.getName()
	local locCardGUID = selectedCard.getGUID()
	
	local locBoard = gO(playerInfoTable[pColor].boardGUID)
    local locBPos = locBoard.getPosition()
	
	local locItemCount = 0
	
	local locCharBag = nil
	local locPos
	local locPos2
	local locRot
	local locRot2
	local locOff
	local locLHandTaken = false

	for _, obj in pairs(gameBox.getObjects()) do
		if obj.name == name then
			gameBox.takeObject({
				position = gameBox.getPosition() + Vector(0,9,0),
				smooth = false,
				callback_function = function (o)
					o.setLock(true)
					gameBox.putObject(o.clone()) 
					locCharBag = o
					for _, obj in pairs(locCharBag.getObjects()) do
						
						local locTagFound = false
						local tagTbl = obj.tags
						for _, tag in pairs(tagTbl) do
							if tag == 'CharacterTile' then
								locOff = {x=-0.02, y=1.68, z=1.53}
								locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
								locRot = {0,180,0}
								locTagFound = true
							elseif tag == 'ActionDeck' then
								locOff = {x=-6.34, y=2, z=1.48}
								locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
								locRot = {0,180,180}
								locTagFound = true
							elseif tag == 'Item' then
								locOff = {x=-3.97 + 1.78*locItemCount, y=2, z=-4.93}
								locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
								locRot = {0,180,0}
								locItemCount = locItemCount + 1
								locTagFound = true
								
							elseif tag == 'StartItem' then
							
								locOff = {x=-3.14, y=1.6, z=-1.95}
								
								if locLHandTaken then
									locOff.x = 3.14
								end
								
								locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
								locRot = {0,90,0}
								locLHandTaken = true
								locTagFound = true
							elseif tag == 'StartItem2' then

								if name == 'CEO' then
									locOff = {x=-3.97 + 1.78*locItemCount, y=2, z=-4.93}
									locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
									locItemCount = locItemCount + 1
								else
									locOff = {x=-1.76, y=2, z=4.82}
									locPos = {locBPos.x+locOff.x, locOff.y, locBPos.z+locOff.z}
								end
								
								locRot = {0,180,0}
								locTagFound = true								
								
							elseif tag == 'Standee' then
								locPos = locBPos + Vector(0,2,0)
								locRot = {0,180,0}
								locTagFound = true
							elseif tag == 'UAV' then
								locPos = locBPos + Vector(1,2,0) --{-13.89, 2, 5.98}
								locRot = {0,180,0}
								locTagFound = true
							end
						end
						
						if locTagFound then
							locCharBag.takeObject({
								position          = locPos,
								rotation = locRot,
								callback_function = function(o)
														afterSpawn(o,pColor)
													end,
								guid              = obj.guid,
								smooth = false,
							})
						end
					end
					Wait.time(function() locCharBag.destruct() end, 1)
					
				end,
				guid = obj.guid,
				smooth = false,
			})
			break
		end
	end
	
	locBoard.clearButtons()
	
	locBoard.createButton({
		click_function = 'acceptChar',
		function_owner = Global,
		label = '확인',
		position       = {-0.3,2,0.75},
		scale = {0.45,0.45,0.45},
		width = 600,
		height	= 300,
		font_size	= 150,
		color	= {1,1,1,1},
		font_color	= {0,0,0},
		tooltip = name,
	})
	
	locBoard.createButton({
		click_function = 'cancelChar',
		function_owner = Global,
		label = '취소',
		position       = {0.3,2,0.75},
		scale = {0.45,0.45,0.45},
		width = 600,
		height	= 300,
		font_size	= 150,
		color	= {1,1,1,1},
		font_color	= {0,0,0},
		tooltip = locCardGUID,
	})
	
	selectingCrew = false
	
end

function acceptChar(pBoard, pColor)
	if not scriptEnabled then
		return true
	end
	
	local boardColor = ''
	
	for color, entry in pairs(playerInfoTable) do
		if entry.boardGUID == pBoard.getGUID() then
			boardColor = color
			break
		end
	end
	
	
	for _, obj in pairs (shapeCast(pBoard.getPosition(), pBoard.getBounds().size)) do
		if obj != pBoard and obj.getPosition().y > -8 and not obj.hasTag('playerHelp') and obj != firstPlayerToken then
			afterSpawn(obj,boardColor, 1)
		end
	end
	
	pickCard(pBoard.getButtons()[1].tooltip, boardColor, pBoard.getButtons()[2].tooltip)
	pBoard.clearButtons()
	labelWeapon(pBoard)
	
end

function cancelChar(pBoard, pColor)
	if not scriptEnabled then
		return true
	end
	
	pBoard.clearButtons()
	labelWeapon(pBoard)
	
	local boardColor = ''
	
	for color, entry in pairs(playerInfoTable) do
		if entry.boardGUID == pBoard.getGUID() then
			boardColor = color
			break
		end
	end
	
	for _, obj in pairs (shapeCast(pBoard.getPosition(), pBoard.getBounds().size)) do
		if obj != pBoard and obj.getPosition().y > -8 and not obj.hasTag('playerHelp') and obj != firstPlayerToken then
			local locDestroy = true
			if obj.getButtons() != nil then
				locDestroy = obj.getButtons()[1].label != '선택'
			end
			
			if locDestroy then
				obj.destruct()
			end
		end
	end
	
	if not useCharacterDraft then
		createSelectCrew(boardColor)
	end
end



function useLanderVoicesToggle()
	if not scriptEnabled then
		return true
	end
	
	if useLanderVoices then
		useLanderVoices = false
		boarderTile.editButton({index = 5, label = '착륙선 목소리\n비활성화', color = {0,0,0,0.8}})
		
	else
		useLanderVoices = true
		boarderTile.editButton({index = 5, label = '착륙선 목소리\n활성화', color = {0.15,0.7,0.05}})
		broadcastToAll('주의: 착륙선 파일럿 음성은 다양한 등급이 있으며, 일부는 성인에게 적합합니다.', {0.5,1,0.5})
	end

end

landerCheckWaitTime = 0
function landerCheck()
	if not scriptEnabled then
		return true
	end
	
	proceedToNextPhase = false
	
	shuttleFigure.setLock(true)
	
	
	local locAAOffsetLocalSpace = rotateVectorAboutY(Vector(-3.44 / 8.7, 0, 13.37 / 8.68), 180) --reset from the time this was measured
	locAAOffsetLocalSpace = rotateVectorAboutY(locAAOffsetLocalSpace, boarderTile.getRotation().y) * boarderTile.getScale() --apply current Transforms.
	local locRayPos = boarderTile.getPosition() + locAAOffsetLocalSpace
	
	local locHighestAA = nil
	for _, locObj in pairs(shapeCast(locRayPos)) do
		if locObj != boarderTile then
			if locHighestAA == nil then
				locHighestAA = locObj
			elseif locObj.getPosition().y > locHighestAA.getPosition().y then
				locHighestAA = locObj
			end
			
		end
	end
	
	landerCheckWaitTime = 6
	local locAA = false
	if locHighestAA != nil then
		if locHighestAA.getGMNotes() == 'active' then
			locAA = true
		end	
	end
	
	local locPilotName = nil
	local locSoundElemTbl = nil
	local locSoundID = nil
	
	if useLanderVoices then
		
		local locBreak = 0
		for _, dummy in pairs(landerVoicesTbl) do
			locBreak = locBreak +1
		end
		locBreak = math.random(1,locBreak)
		local locIndx = 1
		for pilotN, entry in pairs(landerVoicesTbl) do
			if locIndx == locBreak then
				locPilotName = pilotN
				break
			end
			locIndx = locIndx+1
		end
		
	end
	
	if locAA then
		if useLanderVoices then
			locSoundElemTbl = math.random(1,#(landerVoicesTbl[locPilotName]['Crashing']))
			locSoundID = landerVoicesTbl[locPilotName]['Crashing'][locSoundElemTbl].ID
			landerCheckWaitTime = landerVoicesTbl[locPilotName]['Crashing'][locSoundElemTbl].Duration - 0.3
			landerPilotSoundBoard.AssetBundle.playTriggerEffect(locSoundID)
			
			Wait.time(function ()
				playsounds(-1)
				playsounds(math.random(190,192))
				broadcastToAll('착륙선이 대공 시스템에 의해 파괴되었습니다!!', lifeformColor)
				shuttleFigure.destruct()
				lightAlert()
				Wait.time(function()
					proceedToNextPhase = true
				end,1)
			end, landerCheckWaitTime)
		else
			AAShoot()
		end

	else
		if useLanderVoices then
			locSoundElemTbl = math.random(1,#(landerVoicesTbl[locPilotName]['Landing']))
			locSoundID = landerVoicesTbl[locPilotName]['Landing'][locSoundElemTbl].ID
			landerCheckWaitTime = landerVoicesTbl[locPilotName]['Landing'][locSoundElemTbl].Duration
			landerPilotSoundBoard.AssetBundle.playTriggerEffect(locSoundID)
			
		else
			playsounds(180)
		end
		Wait.time(function ()
			shuttleFigure.setPosition(landingZone.getPosition() + Vector(-1.1,0.16,-2.95))
			shuttleFigure.setScale({1.1,1,1.1})
			playsounds(-1)
			onObjectDrop('Red', shuttleFigure)
			broadcastToAll('착륙선이 안전하게 착륙했습니다.', lifeformColor)
			Wait.time(function()
				proceedToNextPhase = true
			end,1)
		end, landerCheckWaitTime)
	end
end

function nextRound()
	if not scriptEnabled then
		return true
	end
	
	reinforceTurn = true
	xyrianActivationRound = false
	
	local locPos = turnMarker.getPosition()  - turnOffset
	turnMarker.setLock(true)
	turnMarker.setPosition(locPos)
	
	if insiderEnable and insiderStoryGUID != '' then
		insiderRecall()
		local locInsiderStory = gO(insiderStoryGUID)
		
		if locInsiderStory != nil then
			for _, tag in pairs (locInsiderStory.getTags()) do
				if string.find(tag, 'insiderEffectRound') != nil then
					autoInsider(2, tag)
				end
			end
			
			
			
			local locInsiderStoryDesc = locInsiderStory.getDescription()
			local locChapter = string.find(locInsiderStoryDesc, 'r')  --r for round
			
			if locChapter != nil then
				local locSequelPass = true
				local locRoom = nil
				for _, tag in pairs (locInsiderStory.getTags()) do
					if tag == 'insiderSequelRoundInsider' then
						if insiderFig != nil then
							locSequelPass = distanceMath(insiderFig.getPosition(), locPos) < turnOffset.z*0.5
						end
						break
						
					elseif 	tag == 'insiderSequelRoundInsiderDead' then
					
						if insiderFig != nil then
							locSequelPass = false
						end
						
						
					elseif tag == 'insiderSequelRoundEgg' then
						locSequelPass = false
						for _, eggObj in pairs (getAllObjects()) do
							if eggObj.getName() == 'Egg' then
								if distanceMath(eggObj.getPosition(), locPos) < turnOffset.z*0.5 then
									locSequelPass = true
									break
								end
							end
						end
						break
					
					elseif tag == 'insiderSequelRoundRunaway' then
						if insiderRunaway != nil then
							insiderRunaway.setPositionSmooth({-16.54, 1.9, 19.89}, false, true)
							insiderRunaway.setRotation({0,0,0})
							broadcastToAll('도망자가 탈출 셔틀로 이륙하는 데 성공했습니까?!', insiderColor)
							playsounds(math.random(257,260))
							
							for _, roomTile in pairs (getAllObjects()) do
								if roomTile.getName() == 'ESCAPE SHUTTLE' then
									locRoom = roomTile
									break
								end
							end
						end
						break
					elseif tag == 'insiderSequelRoundInsiderWithNoChar' then
					
						if insiderFig != nil then
							local locInsiderPos = insiderFig.getPosition()
							local locPlayerRooms = getPlayerRoomsInFirstTurnOrder()
							
							for _, roomTile in pairs (getAllObjects()) do
								if roomTile.hasTag('room') then
									if distanceMath(roomTile.getPosition(), locInsiderPos) < returnRoomDiameter(roomTile) then
										local locRoomTileGUID = roomTile.getGUID()
										
										for color, playerRoomGUID in pairs (locPlayerRooms) do
											if playerRoomGUID == locRoomTileGUID then
												locSequelPass = false
												break
											end
										end
										break
									end
								end
							end
						else
							locSequelPass = false
						end
					end
				end
				
				if locSequelPass then
					if string.len(locChapter) > 1 then
						locChapter = tonumber(string.sub(locChapter,1,1))
					end
					
					locChapter = string.sub(locInsiderStoryDesc, locChapter+1, locChapter+2)
					
					for _, storyCard in pairs (insiderDeck.getObjects()) do
						if storyCard.gm_notes == locChapter then
							insiderDeck.takeObject({
								position = insiderDeck.getPosition() + Vector(0,4,4),
								guid = storyCard.guid,
								callback_function = function(o2)
										local locNewDesc = string.gsub(locInsiderStoryDesc, 'r'.. locChapter,'')
										locInsiderStory.setDescription(string.sub(locNewDesc,1,string.len(locNewDesc)))
										insiderSequel(o2, locRoom)
									end,
								
							})
							break
						end
					end
				end
			end
		end
	end
	
	local locCurrentRound = 2 + math.floor ( ((14.58 - turnMarker.getPosition().z) / turnOffset.z) )
	local locMsg = '라운드 마커가 ' .. locCurrentRound .. ' 라운드로 이동했습니다.'
	
	local locShuttleRound = (getTaggedObjAtPos('lander',locPos, 0) != nil)
	
	if lifeforms == 'Neoflesh' then
		local locBodyToken = getTaggedObjAtPos('bodyToken', locPos, 1)
		
		if locBodyToken != nil then
			absorbBody(locBodyToken)
		end
	end
	
	if locCurrentRound > 14 then
		locMsg = '남은 라운드가 없습니다. 게임이 종료되었습니다.'
	elseif locShuttleRound then
		landerCheck()
	else
		playbombticks(math.random(2,7))
	end
	broadcastToAll(locMsg, {1,1,1})
	
	drawFullHands()
	allPassed = false
	
	xyrianEventEffect = true
	
	if trapCheck then
		for _, obj in pairs (getAllObjects()) do
			if obj.hasTag('trapped') then
				obj.removeTag('trapped')
			end
		end
		
		for _, trap in pairs (trapsList) do
			if trap != nil then
				if trap.getRotation().z > 160 and trap.getRotation().z < 200 then
					trap.destruct()
				end
			end
		end
	end
end

function drawButton(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	if playerInfoTable[pColor].figureGUID != '' then
		playerDrawActions(pColor, 1)
	end
end

function playerDrawActions(pColor, number)
	if not scriptEnabled then
		return true
	end
	
	if number > 0 then
		local locBoard = gO(playerInfoTable[pColor].boardGUID)
		
		local locDraw = number
		local boardObj = nil
		for _, entry2 in pairs(shapeCast( locBoard.getPosition(), locBoard.getBounds().size)) do
			boardObj = entry2
			if (boardObj.getGMNotes() == 'action' or boardObj.getGMNotes() == 'actionDiscard') then
				if (locBoard.getPosition().x - boardObj.getPosition().x) > 0 then
					
					local locDraw2 = 1
					if boardObj.getGMNotes() == 'actionDiscard' then
						locDraw2 = boardObj.getQuantity()
					end
					locDraw2 = math.max(locDraw-locDraw2, 0)
					boardObj.deal(locDraw, pColor)
					locDraw = locDraw2
					break
					
				end
			end
		end
			
		if locDraw > 0 then
			for _, entry2 in pairs(shapeCast( locBoard.getPosition(), locBoard.getBounds().size)) do
				boardObj = entry2
				if boardObj.getGMNotes() == 'actionDiscard' then
					if (boardObj.getPosition().x - locBoard.getPosition().x) > 0 then
						
						boardObj.shuffle()
						boardObj.deal(locDraw, pColor)
						onObjectNumberTyped(boardObj, pColor, 0)
						break
					end
				end
			end
		end
	end
end

function drawFullHands()
	if not scriptEnabled then
		return true
	end
	
	for color, entry in pairs(playerInfoTable) do
		if isPlayerAlive(color) then
			local locBoard = gO(entry.boardGUID)
			local locActionCount = 0
			for _, card in pairs(Player[color].getHandObjects()) do
				if card.getGMNotes() == 'action' then
					locActionCount = locActionCount + 1
				end
			end
			
			local locDraw = 5
			local locFig = gO(entry.figureGUID)
			
			if insiderEnable then
				insiderRecall()
				
				if insiderFig != nil and insiderCard != nil then
					if insiderFig.hasTag('characterFig') and insiderCard.getGMNotes() == 'active' and (insiderCard.getRotation().z < 10 or insiderCard.getRotation().z > 350) then
						if distanceMath(locFig.getPosition(), insiderFig.getPosition()) < tileImportedSize.x then
							locDraw = locDraw+1
						end
					end
				end
			end
			
			local locBody = true
			
			for _, boardObj in pairs(shapeCast(locBoard.getPosition(), locBoard.getBounds().size)) do
				
				if boardObj.getName() == 'body' then
					if locBody and not (boardObj.getRotation().z < 185 and boardObj.getRotation().z > 175) then
						locDraw = locDraw - 1
						locBody = false
					end
				elseif boardObj.hasTag('playerHelp') then
					boardObj.setRotation({0,180,0})
					boardObj.setLock(false)
				elseif boardObj.getDescription() == 'Adrenaline Chip' then
					if boardObj.getButtons()[1].label == 'ACTIVE' then
						locDraw = locDraw + 1
					end
				elseif boardObj.getGMNotes() == 'tainted' and boardObj.getRotation().z > 175 and boardObj.getRotation().z < 185 then
					boardObj.flip()
				elseif boardObj.hasTag('roundBark') then
					playsounds(math.random(148,152))
					broadcastToAll('플레이어 ' .. color .. '는 현상금 사냥꾼이 전투 중이 아닐 경우 라이카를 한 번 무료로 사용할 수 있습니다.', {1,1,1})
				end
			end
			
			
			locDraw = math.max(locDraw - locActionCount, 0)
			playerDrawActions(color, locDraw)
		end
	end
	
	local loc1stPColor = getFirstPlayerColor()
	local locBPos = {0,0,0}
	
	if loc1stPColor != nil then
		local locColorFound = false
		for color, entry in pairs(playerInfoTable) do
			if Player[color].seated or (not automaticSeat and entry.manualSeat) then
				if not locColorFound and color == loc1stPColor then
					locColorFound = true
				elseif locColorFound and isPlayerAlive(color) then
					locColorFound = false
					loc1stPColor = color
					break
				end
			end
		end
		
		countPlayers(true)
		
		if locColorFound and seatedPlayers > 1 then
			for color, entry in pairs(playerInfoTable) do
				if (Player[color].seated or (not automaticSeat and entry.manualSeat)) and isPlayerAlive(color) then
					loc1stPColor = color
					break
				end
			end
		end
		
		locBPos = gO(playerInfoTable[loc1stPColor].boardGUID).getPosition()
		firstPlayerToken.setPosition({locBPos.x + 6.60, 2, locBPos.z + 5.15})
		if Player[loc1stPColor].seated then
			Turns.turn_color = loc1stPColor
		else
			createPlayerColorSwitch(loc1stPColor)
		end
	end
end

function returnPlayerHealth(pColor)
	if not scriptEnabled then
		return true
	end
	
	local locBoard = gO(playerInfoTable[pColor].boardGUID)
	local locHealth = gO(playerInfoTable[pColor].healthGUID)
	local localHealthPos = locHealth.getPosition().x - locBoard.getPosition().x
	
	local locCurrentHealth = 1
	
	for _, entry in pairs (playerHealthLocalPosX) do
		if math.abs(localHealthPos - entry) <= 0.2 then
			return locCurrentHealth
		else
			locCurrentHealth = locCurrentHealth + 1
		end
	end
	
	return 1
end

function isPlayerAlive(pColor)
	if not scriptEnabled then
		return true
	end
	
	local locBoard = gO(playerInfoTable[pColor].boardGUID)
	
	local locPlayerAlive = false
	
	if locBoard != nil then
		local locBPos = locBoard.getPosition()
		
		if gO(playerInfoTable[pColor].healthGUID) != nil then
			local locPos = gO(playerInfoTable[pColor].healthGUID).getPosition()
			
			if locPos.z > (locBPos.z + 3.6) and  locPos.z < (locBPos.z + 4.5) and locPos.x > (locBPos.x -3.6) and locPos.x < (locBPos.x +3.2) then
				locPlayerAlive = true
			end
		else
			locPlayerAlive = true
		end
	end
	
	return locPlayerAlive
end

function AAShoot()
	if not scriptEnabled then
		return true
	end
	
	local locShoots = math.random (3,7)
	local locTime = 2
	local locSounds = {}
	playsounds(180)
	for i = 1, locShoots do
		table.insert(locSounds, math.random(90,91))
		
		Wait.time(function() playsounds(locSounds[i]) end,locTime)
		locTime = locTime + (soundDuration[locSounds[i]+1]*0.2)
	end
	landerCheckWaitTime = locTime +3
	
	Wait.time(function() playsounds(181) end, locTime)
	Wait.time(function()
		playsounds(-1)
		playsounds(math.random(190,192))
		shuttleFigure.destruct()
		broadcastToAll('착륙선이 대공 시스템에 의해 파괴되었습니다!!', lifeformColor)
		lightAlert()
		Wait.time(function()
			proceedToNextPhase = true
		end,1)
	end, landerCheckWaitTime)
end

function useXyrianToggle()
	if not scriptEnabled then
		return true
	end
	
	if useXyrian then
		useXyrian = false
		boarderTile.editButton({index = 3, label = '자이리안\n비활성화', color = {0,0,0,0.8}})
		xyrianPhase.setPosition({33,1.5,-1})
		xyrianPhase.setRotation({0,180,180})
		
	else
		useXyrian = true
		boarderTile.editButton({index = 3, label = '자이리안\n활성화', color = xyrianColor})
		xyrianPhase.setPosition({35,1.5,10.87})
		xyrianPhase.setRotation({0,180,0})
	end
	

end

function useContractorsToggle()
	if not scriptEnabled then
		return true
	end
	
	if useContractors then
		useContractors = false
		boarderTile.editButton({index = 4, label = '계약자\n비활성화', color = {0,0,0,0.8}})
		
		useCustomContractors = false
		boarderTile.editButton({index = 13, label = '커스텀 계약자\n비활성화', color = {0,0,0,0.8}})
		
	else
		useContractors = true
		boarderTile.editButton({index = 4, label = '계약자\n활성화', color = {0.5,0.5,0.5,1}})
	end
end

function customContractorToggle()
	if not scriptEnabled then
		return true
	end
	
	if useCustomContractors then
		useCustomContractors = false
		boarderTile.editButton({index = 13, label = '커스텀 계약자\n비활성화', color = {0,0,0,0.8}})
		
	elseif useContractors then
		useCustomContractors = true
		boarderTile.editButton({index = 13, label = '커스텀 계약자\n활성화', color = {0.5,0.5,0.5,1}})
	end
end


function soundToggle()
	if not scriptEnabled then
		return true
	end
	
	if soundEnable then
		soundEnable = false
		soundTile.editButton({index = 0, label = '사운드보드 비활성화'})
	else
		soundEnable = true
		soundTile.editButton({index = 0, label = '사운드보드 활성화'})
	end

end

function blinkingDeadlyButton()
	if not scriptEnabled then
		return true
	end
	
	if not setupComplete and deadlyMode then
		local locTime = Time.time / 6
		local S = locTime - math.floor(locTime) --frac(0-1)
		S = math.abs( (S * 2) - 1)
		
		boarderTile.editButton({index = 1, color = {1*S,0.1*S,0} })
		
		Wait.frames(function () blinkingDeadlyButton() end, 2)
	end

end

function setFontSizeToButton(buttonOwner, buttonID)
	if not scriptEnabled then
		return true
	end
	
	local locButton = buttonOwner.getButtons()[buttonID+1]
	
	local locW = locButton.width
	local locH = locButton.height
	local locLabel = locButton.label
	
	local locS =  math.min(2*locW/string.len(locLabel) , locH/1.5) * 0.8
	buttonOwner.editButton({index = buttonID, font_size = locS})
end

function countPlayers(countAllSeats)
	if not scriptEnabled then
		return true
	end
	
	seatedPlayers = 0
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and entry.manualSeat and countAllSeats) then
			seatedPlayers = seatedPlayers + 1
		end
	end
end	

function deadlyModeToggle()
	if not scriptEnabled then
		return true
	end
	
	if not deadlyMode then
		deadlyMode = true 
		boarderTile.editButton({index = 1, label = '데들리 모드\n활성화'})	
		soundEnable = true
		blinkingDeadlyButton()
		playsounds(139)
		sound2Used = false
		
		soundEnable = false
		
	else
		deadlyMode = false
		boarderTile.editButton({index = 1, color = {0,0,0,0.8}, label = '데들리 모드\n비활성화'})
	end
	--setFontSizeToButton(boarderTile, 1)
end

function automaticSeatToggle()
	if not scriptEnabled then
		return true
	end
	
	if automaticSeat then
		automaticSeat = false
		boarderTile.editButton({index = 0, color = {0,0.35,0.95}, label = '수동\n자리배치'})
		broadcastToAll('착석으로 처리할 플레이어 보드를 클릭하세요', {0.05,0.5,1})
		for color, entry in pairs (playerInfoTable) do
		
			pBoard = gO(entry.boardGUID)
			local bcolor = {0.75,0,0}
			local locLabel = '미착석'
			
			if Player[color].seated or entry.manualSeat then
				bcolor = {0.1,0.25,0.75}
				locLabel = '착석'
				entry.manualSeat = true
			end
			
			pBoard.createButton({
				click_function = 'locmanualSeatToggle',
				function_owner = Global,
				label = locLabel,
				position       = {0,2,0},
				scale = {0.15,0.15,0.15},
				width = 4500,
				height         = 1200,
				font_size      = 600,
				color		   = bcolor,
				font_color     = {1,1,1},
			})
			
			--build functions
			local func2 = function(obj, pColor, alt_click)
				--local pIndex = pIndex -- store a local ref to the i inside of this function declaration, otherwise all your redirect functions would have i == #heroSelectDataTable
				
				manualSeatToggle(obj,pColor)
			end
			_G['locmanualSeatToggle'] = func2	
		end
		
	else
		automaticSeat = true
		boarderTile.editButton({index = 0, color = {0.65,0,0}, label = '자동\n자리배치'})
		broadcastToAll('수동으로 배정된 자리가 무시됩니다', {1,0.25,0.05})
		
		for color, entry in pairs (playerInfoTable) do
			pBoard = gO(entry.boardGUID)
			pBoard.removeButton(1)
		end
		
	end
	setFontSizeToButton(boarderTile, 1)
end

function manualSeatToggle(playerBoard, pColor)
	if not scriptEnabled then
		return true
	end
	
	for color, entry in pairs (playerInfoTable) do
		if	playerBoard.getGUID() == entry.boardGUID then
			
			if entry.manualSeat and not Player[color].seated then
				entry.manualSeat = false
				playerBoard.editButton({index = 1, color = {0.75,0,0}, label = '미착석'})
			else
				entry.manualSeat = true
				playerBoard.editButton({index = 1, color = {0.1,0.25,0.75}, label = '착석'})
			end
			break
		end
	end
end

function actColToggle()
	if not scriptEnabled then
		return true
	end
	
	if not actCol then
		actCol = true
		actColTile.editButton({index = 0, label = '액션 카드를 가장 가까운 색상으로'})
	else
		actCol = false
		actColTile.editButton({index = 0, label = '액션 카드를 플레이어에게'})
	end
end

function weaponColToggle()
	if not scriptEnabled then
		return true
	end
	
	if not weaponCol then
		weaponCol = true
		weaponColTile.editButton({index = 0, label = '무기 버튼을 턴 색상으로'})
	else
		weaponCol = false
		weaponColTile.editButton({index = 0, label = '무기 버튼을 플레이어에게'})
	end
end

function rollAnimationToggle()
	if not scriptEnabled then
		return true
	end
	
	if not rollAnimationEnable then
		rollAnimationEnable = true
		rollAnimationTile.editButton({index = 0, label = '주사위 애니' .. '\n' .. '예상됨', color={0,0.5,0.5,1}, font_color = {1,1,1,1}})
		rollModeTile.setInvisibleTo({})
	else
		rollAnimationEnable = false
		rollAnimationTile.editButton({index = 0, label = '주사위 애니' .. '\n' .. '미예상', color={0,0,0,.8}, font_color = {0.8,0.8,0.8,0.95}})
		local locHideTbl = {}
		for color, entry in pairs (playerInfoTable) do
			table.insert(locHideTbl, color)
		end
		rollModeTile.setInvisibleTo(locHideTbl)
	end
end

function rollModeToggle()
	if not scriptEnabled then
		return true
	end
	
	if not rollMode then
		rollMode = true
		rollModeTile.editButton({index = 0, label = '수동 주사위', color = {0,0,0.6,1}, font_color = {1,1,1}})
	else
		rollMode = false
		rollModeTile.editButton({index = 0, label = '자동 주사위', color = {0,0.6,0.6,1}, font_color = {1,1,1}})
	end
end

function balanceBagClone(bag, loop)
	if not scriptEnabled then
		return true
	end
	
	local locpos = bag.getPosition() + Vector(0,2,0)
	
		
	bag.takeObject({
		position = locpos,
		smooth = false,
		callback_function = function(obj) 
			for i = 1, loop do
				obj2 = obj.clone({position = locpos + Vector(0,i*0.5,0)})
				obj2 = bag.putObject(obj2)
			end
			bag.putObject(obj)
		end,
	})
	
end

function lifeformCheck()
	if not scriptEnabled then
		return true
	end

	if lifeforms == 'Random' then
		local locRand = math.random(1,4)
		if locRand == 1 then
			lifeforms = 'Primebloods'
			lifeformColor = Color(0.208,0.914,0.627, 1)
		elseif locRand == 2 then
			lifeforms = 'Neoflesh'
			lifeformColor = Color(1,0.488,0.226, 1)
		elseif locRand == 3 then
			lifeforms = 'Sangrevores'
			lifeformColor = Color(1,0.192,0.282)
		elseif locRand == 4 then
			lifeforms = 'Carnomorph'
			lifeformColor = Color(1,0.192,0.192)
		end
		
		lightColorStart = maxColor(lifeformColor)
		lightColorStart = setSaturation(lightColorStart, 0.25)
		Lighting.setLightColor(lightColorStart)
		Lighting.apply()
		
		if autoEventEnable then
			autoEventTile.editButton({index = 0, color = lifeformColor})
		end
	end





	if lifeforms == 'Primebloods' then
		setupPhase01()
	elseif lifeforms == 'Neoflesh' then
		deployNeoflesh()
	elseif lifeforms == 'Sangrevores' then
		deploySangrevores()
	elseif lifeforms == 'Carnomorph' then
		deployCarnomorph()
	end
	
	if insiderEnable then
		for _, obj in pairs(gameBox.getObjects()) do
			if obj.name == 'InsiderExpansion' then
				gameBox.takeObject({
					position = gameBox.getPosition() + Vector(0,9,5),
					callback_function = function (o)
						o.setLock(true)
						for _, obj2 in pairs(o.getObjects()) do
							if obj2.name == 'insiderStoryDeck' then
								
								o.takeObject({
									position = {-24,1.77,8},
									rotation = {0,180,0},
									guid = obj2.guid,
									smooth = false,
								})

								
							elseif obj2.name == 'insiderRulebook' then
								o.takeObject({
									position = {-80,1.48,0},
									rotation = {0,180,0},
									guid = obj2.guid,
									smooth = false,
									callback_function = function (o2) o2.setLock(true) end,
								})
								
							elseif obj2.name == 'insiderCard' then
								o.takeObject({
									position = {-29,1.5,12},
									rotation = {0,180,0},
									guid = obj2.guid,
									smooth = false,
								})
								
								
							elseif obj2.name == 'insiderFig' then
								o.takeObject({
									position = {-29,1.7,12},
									rotation = {0,0,0},
									guid = obj2.guid,
									smooth = false,
								})
								
							elseif obj2.name == 'runawayFig' then
								o.takeObject({
									position = {-29,1.7,14.5},
									rotation = {0,0,0},
									guid = obj2.guid,
									smooth = false,
								})
								
							end
							
						end	
						o.setLock(false)
					end,
					guid = obj.guid,
					smooth = false,
				})
			end
		end
	end
	
end

function deployNeoflesh()
	if not scriptEnabled then
		return true
	end
	
	queenFigGUID = '3393ba'
	
	for _, obj in pairs(gameBox.getObjects()) do
		if obj.name == 'NeofleshExpansion' then
			gameBox.takeObject({
				position = gameBox.getPosition() + Vector(0,9,0),
				callback_function = function (o)
					o.setLock(true)
					for _, obj2 in pairs(o.getObjects()) do
						if obj2.name == 'blank' then
						
							intruderBag.takeObject({
								position = trashBag.getPosition() + Vector(0,5,0),
							})
							
							o.takeObject({
								position = intruderBag.getPosition() + Vector(0,9,0),
								guid = obj2.guid,
								smooth = false,
							})

							
						elseif obj2.name == 'rulebook' then
							o.takeObject({
								position = {-68,1.48,0},
								rotation = {0,180,0},
								callback_function = function (o2) o2.setLock(true) end,
								guid = obj2.guid,
								smooth = false,
							})
						
						elseif obj2.name == 'queenHealth' then
							o.takeObject({
								position = queenHealthDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(queenHealthDeck) queenHealthDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'exploration' then
							o.takeObject({
								position = explorationDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(explorationDeck) explorationDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'attack' then
							o.takeObject({
								position = attacksDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(attacksDeck) attacksDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'eventDeck' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(eventDeck) eventDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'queenTokenBag' then
							o.takeObject({
								position = queenBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(queenBag) trashBag.putObject(breederBag) queenBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'twitchlingTokenBag' then
							o.takeObject({
								position = larvaeBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(larvaeBag) larvaeBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'adultTokenBag' then
							o.takeObject({
								position = adultBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(adultBag) adultBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'motherbrainBag' then
							o.takeObject({
								position = queenFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(queenFBag) queenFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'cultistBag' then
							o.takeObject({
								position = breederFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(breederFBag) breederFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'cultistDeadBag' then --deadbag
							o.takeObject({
								position = adultFBag.getPosition() + Vector(12,9,3),
								rotation = {0,0,0},
								callback_function = function (o2) cultistDeadBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
						
						elseif obj2.name == 'slasherBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(adultFBag) adultFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'crawlmineBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(6,9,3),
								rotation = {0,0,0},
								callback_function = function (o2) crawlmineFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'ironcladBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(2,9,3),
								rotation = {0,0,0},
								callback_function = function (o2) ironcladFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'firespitterBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(-2,9,3),
								rotation = {0,0,0},
								callback_function = function (o2) firespitterFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							

							
							
							
						elseif obj2.name == 'twitchlingBag' then
							o.takeObject({
								position = larvaeFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(larvaeFBag) larvaeFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'bodyToken' then
							
							o.takeObject({
								position = o.getPosition() + Vector(0,5,0),
								rotation = {0,180,0},
								callback_function = function (o2)
									o2.setPosition(turnMarker.getPosition() - turnOffset*7)
									local locOffZ = turnOffset.z
									local locPos = turnMarker.getPosition()
									o2.clone({position = locPos - turnOffset*10}) o2.clone({position = locPos - turnOffset*13}) end,
								guid = obj2.guid,
								smooth = false,
							})
							
							
						elseif obj2.name == 'intruderHelp' then
							
							o.takeObject({
								position = intruderHelp.getPosition() + Vector(0,3,0),
								rotation = {0,180,0},
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'buffs' then
							
							local locZ = 10.2
							
							if useXyrian then
								locZ = 12.4
							end
							
							o.takeObject({
								position = {20,1.5,locZ},
								rotation = {0,180,0},
								callback_function = function (o2)
									for i = 1, 5 do
										o2.takeObject({
											position = o2.getPosition() + Vector(0,0,i*2.2),
											rotation = {0,180,0},
											smooth = false,
										})
									end
								end,
								guid = obj2.guid,
								smooth = false,
							})
						end
						
					end	
					o.setLock(false)
				end,
				guid = obj.guid,
				smooth = false,
			})
		end
	end
	
	trashBag.putObject(intruderHelp)
	Wait.time(function() setupPhase01() end, 3)
end

function deploySangrevores()
	if not scriptEnabled then
		return true
	end
	
	queenFigGUID = '50cde1'
	
	for _, obj in pairs(gameBox.getObjects()) do
		if obj.name == 'SangrevoresExpansion' then
			gameBox.takeObject({
				position = gameBox.getPosition() + Vector(0,9,0),
				callback_function = function (o)
					o.setLock(true)
					for _, obj2 in pairs(o.getObjects()) do
						if obj2.name == 'blank' then
						
							intruderBag.takeObject({
								position = trashBag.getPosition() + Vector(0,5,0),
							})
							
							o.takeObject({
								position = intruderBag.getPosition() + Vector(0,9,0),
								guid = obj2.guid,
								smooth = false,
							})

							
						elseif obj2.name == 'rulebook' then
							o.takeObject({
								position = {-68,1.48,0},
								rotation = {0,180,0},
								callback_function = function (o2) o2.setLock(true) end,
								guid = obj2.guid,
								smooth = false,
							})
						
						elseif obj2.name == 'kingHealth' then
							o.takeObject({
								position = queenHealthDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(queenHealthDeck) queenHealthDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'exploration' then
							o.takeObject({
								position = explorationDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(explorationDeck) explorationDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'attack' then
							o.takeObject({
								position = attacksDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(attacksDeck) attacksDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'eventDeck' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(eventDeck) eventDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'kingTokenBag' then
							o.takeObject({
								position = queenBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2)
									for _, bag in pairs ({queenBag, larvaeBag, larvaeFBag}) do
										trashBag.putObject(bag)
									end
									queenBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						
						elseif obj2.name == 'specterTokenBag' then
							o.takeObject({
								position = breederBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(breederBag) breederBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'ghoulTokenBag' then
							o.takeObject({
								position = adultBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(adultBag) adultBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'kingBag' then
							o.takeObject({
								position = queenFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(queenFBag) queenFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'specterBag' then
							o.takeObject({
								position = breederFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(breederFBag) breederFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						
						elseif obj2.name == 'ghoulBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(adultFBag) adultFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'shadowBag' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(0,0,8),
								rotation = {0,180,0},
								callback_function = function(o2) shadowBag = o2 shadowBag.shuffle() end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'tainted' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(3,0,8),
								rotation = {0,180,180},
								callback_function = function(o2) taintedDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'infection' then
							o.takeObject({
								position = contaminationDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function(o2) trashBag.putObject(contaminationDeck) contaminationDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'noiseBag' then
							o.takeObject({
								position = noiseBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function(o2) trashBag.putObject(noiseBag) noiseBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'infectionDiscardSign' then
							o.takeObject({
								position = {26,1.7,7},
								rotation = {0,180,0},
								callback_function = function (o2) o2.setLock(true) Wait.time(function() recallSangrevores() end, 2) end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'intruderHelp' then
							
							o.takeObject({
								position = intruderHelp.getPosition() + Vector(0,3,0),
								rotation = {0,180,0},
								guid = obj2.guid,
								smooth = false,
							})
							
						end
						
					end	
					o.setLock(false)
				end,
				guid = obj.guid,
				smooth = false,
			})
		end
	end
	
	for _, trashObj in pairs ({intruderHelp, scanner}) do
		trashBag.putObject(trashObj)
	end

	Wait.time(function() setupPhase01() end, 3)
end

function deployCarnomorph()
	if not scriptEnabled then
		return true
	end
	
	queenFigGUID = 'aa78e0'
	
	for _, obj in pairs(gameBox.getObjects()) do
		if obj.name == 'Carnomorph' then
			gameBox.takeObject({
				position = gameBox.getPosition() + Vector(0,9,0),
				callback_function = function (o)
					o.setLock(true)
					for _, obj2 in pairs(o.getObjects()) do
						if obj2.name == 'blank' then
						
							intruderBag.takeObject({
								position = trashBag.getPosition() + Vector(0,5,0),
							})
							
							o.takeObject({
								position = intruderBag.getPosition() + Vector(0,9,0),
								guid = obj2.guid,
								smooth = false,
							})

							
						elseif obj2.name == 'rulebook' then
							o.takeObject({
								position = {-68,1.48,0},
								rotation = {0,180,0},
								callback_function = function (o2) o2.setLock(true) end,
								guid = obj2.guid,
							})
						
						elseif obj2.name == 'queenHealth' then
							o.takeObject({
								position = queenHealthDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(queenHealthDeck) queenHealthDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'exploration' then
							o.takeObject({
								position = explorationDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(explorationDeck) explorationDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'attack' then
							o.takeObject({
								position = attacksDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(attacksDeck) attacksDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'eventDeck' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(0,9,0),
								rotation = {0,180,180},
								callback_function = function (o2) trashBag.putObject(eventDeck) eventDeck = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'butcherBag' then
							o.takeObject({
								position = queenBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(queenBag) queenBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'metagorgerBag' then
							o.takeObject({
								position = larvaeBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(larvaeBag) larvaeBag = o2 creeperBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'shamblerBag' then
							o.takeObject({
								position = adultBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(adultBag) adultBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'fleshbeastBag' then
							o.takeObject({
								position = breederBag.getPosition() + Vector(0,9,0),
								rotation = {0,180,0},
								callback_function = function (o2) trashBag.putObject(breederBag) breederBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
							
						elseif obj2.name == 'butcherFBag' then
							o.takeObject({
								position = queenFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(queenFBag) queenFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'fleshbeastFBag' then
							o.takeObject({
								position = breederFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(breederFBag) breederFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})

						
						elseif obj2.name == 'shamblerFBag' then
							o.takeObject({
								position = adultFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(adultFBag) adultFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							

							
						elseif obj2.name == 'metagorgerFBag' then
							o.takeObject({
								position = larvaeFBag.getPosition() + Vector(0,9,0),
								rotation = {0,0,0},
								callback_function = function (o2) trashBag.putObject(larvaeFBag) larvaeFBag = o2 creeperFBag = o2 end,
								guid = obj2.guid,
								smooth = false,
							})
							
						elseif obj2.name == 'mutationMarker' then
							
							o.takeObject({
								position = {56,-9,0},
								rotation = {0,180,0},
								guid = obj2.guid,
								callback_function = function (o2) o2.setLock(true) mutationMarker = o2 end,
								smooth = false,
							})
							
						elseif obj2.name == 'mutation' then
							o.takeObject({
								position = eventDeck.getPosition() + Vector(3,0,8),
								rotation = {0,180,180},
								guid = obj2.guid,
								smooth = false,
								callback_function = function (o2) mutationDeck = o2 end,
							})
							
							
						elseif obj2.name == 'intruderHelp' then
							
							o.takeObject({
								position = intruderHelp.getPosition() + Vector(0,3,0),
								rotation = {0,180,0},
								guid = obj2.guid,
								smooth = false,
							})
						
						end
						
					end	
					o.setLock(false)
				end,
				guid = obj.guid,
				smooth = false,
			})
		end
	end
	
	nestBag.takeObject({
		position = nestBag.getPosition() + Vector(0,3,0),
		callback_function = function(o)
			for i = 1, 3 do
				o.clone({position = o.getPosition() + Vector(0,i*2,0)})
			end
		end,
	})
	
	carcassBag.setPosition({-28,1.47,-5})
	
	trashBag.putObject(intruderHelp)
	Wait.time(function() setupPhase01() end, 3)
end

function setupPhase01()
	if not scriptEnabled then
		return true
	end
	
    boarderTile.clearButtons()
    setupComplete = true
	
	
	local locHideTbl = {}

	seatedPlayers = 0
	local locMinP = 0
	local locMaxP = 0
	local i = 1
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and entry.manualSeat) then
			seatedPlayers = seatedPlayers + 1
			
			if locMinP == 0 then
				locMinP = i
				locMaxP = i
			else
				locMaxP = i
			end
			table.insert(locHideTbl, color)
		end
		i = i+1
		
	end
	
	if seatedPlayers < 10 then
		local locTableControl = gO('bd69bd')
		local locScaleValue = '6.3'
		
		if locMaxP == 10 then
		elseif locMaxP == 9 then
			locScaleValue = '4.89'
		elseif locMinP == 2 or locMaxP == 8 then
			locScaleValue = '3.8'
		elseif locMinP > 2 and locMaxP < 8 then
			locScaleValue = '2.8'
		end
		
		if locScaleValue != '6.3' then
			for color, entry in pairs(playerInfoTable) do
				if not (Player[color].seated or (not automaticSeat and entry.manualSeat)) then
					local locBoard = gO(entry.boardGUID)
					local locPos = locBoard.getPosition()
					
					locBoard.setInvisibleTo(locHideTbl) --Better than destroying and checking if board is valid later I think...?
				end
			end
			
			locTableControl.call("click_toggleControl")
			locTableControl.editInput({index = 2, value = locScaleValue}) --min = 2.8 max = 6.3 ?
			locTableControl.call("click_applyScale")
			locTableControl.call("click_toggleControl")
		end
		

	end
	
	if seatedPlayers > 9 then
		useContractors = true
	end
	
	if useCustomContractors then
		for i = 1, pickCustomContractorsDeck.getQuantity() do
					pickCustomContractorsDeck.takeObject({
						position = pickContractorsDeck.getPosition() + Vector(0,i+1,0),
						rotation = {0,180,180},
						callback_function = function(o) pickContractorsDeck.putObject(o) end,
					})
		end
		
	else
		trashBag.putObject(pickCustomContractorsDeck)
	end
	
	
	local locAddedPlayers = math.max(0,seatedPlayers-5)
	
	if lifeforms == 'Primebloods' then
		if use3DFig then
			for _, bag in pairs ({larvaeFBag, adultFBag, breederFBag, queenFBag}) do
				for _, obj in pairs (bag.getObjects()) do
					if not containTag('figure3D', obj.tags) then
						bag.takeObject({
							position = bag.getPosition() + Vector(0,5,0),
							guid = obj.guid,
							callback_function = function(o) trashBag.putObject(o) end,
						})
					end
				end
			end
			
			balanceBagClone(larvaeFBag, 7 + locAddedPlayers)
			for i = 1, 6 do
				balanceBagClone(adultFBag, 5 + locAddedPlayers)
			end
			
			for i = 1, 4 do
				balanceBagClone(breederFBag, 1 + locAddedPlayers)
			end
		else
			for _, bag in pairs ({larvaeFBag, adultFBag, breederFBag, queenFBag}) do
				for _, obj in pairs (bag.getObjects()) do
					if containTag('figure3D', obj.tags) then
						bag.takeObject({
							position = bag.getPosition() + Vector(0,5,0),
							guid = obj.guid,
							callback_function = function(o) trashBag.putObject(o) end,
						})
					end
				end
			end
			balanceBagClone(larvaeFBag, 7 + locAddedPlayers)
			
			for i = 1, 2 do
				balanceBagClone(adultFBag, 17 + locAddedPlayers)
			end
			
			balanceBagClone(breederFBag, 7 + locAddedPlayers)
			
			queenFigGUID = '68d9e4'
		end
	
	elseif lifeforms == 'Neoflesh' then
		balanceBagClone(larvaeFBag, 9 + locAddedPlayers)
		for _, fBag in pairs ({adultFBag, ironcladFBag, firespitterFBag, crawlmineFBag}) do
			balanceBagClone(fBag, 8 + locAddedPlayers)
		end
		balanceBagClone(breederFBag, 4)
		
	elseif lifeforms == 'Sangrevores' then
		for i = 1, 2 do
			balanceBagClone(adultFBag, 17 + locAddedPlayers)
		end
		balanceBagClone(breederFBag, 7 + locAddedPlayers)
	
	elseif lifeforms == 'Carnomorph' then
		balanceBagClone(larvaeFBag, 35 + locAddedPlayers)
		balanceBagClone(adultFBag, 35 + locAddedPlayers)
		balanceBagClone(breederFBag, 7 + locAddedPlayers)
	end
	
	characterDraftTable = {}
	if useContractors then
		Wait.time(function()
			pickContractorsDeck.shuffle()
			pickContractorsDeck.setRotation({0,180,180})
			if useCharacterDraft then
				Wait.time(function() trashBag.putObject(pickContractorsDeck) end, 0.5)
				
				for i = 1, 2 do
					pickContractorsDeck.takeObject({
						position = {-6 + i*4,1.7,-6},
						rotation = {0,90,0},
						callback_function = function(o) Wait.time(function() setupDraftCard(o) end,3) end,
					})
				end
				broadcastToAll('계약자 드래프트 카드가 한 플레이어의 옵션으로 테이블에 준비되었습니다.', {0.2,1,1})
				
			else
			
				for i = 1, pickContractorsDeck.getQuantity() do
					pickContractorsDeck.takeObject({
						position = characterDraftDeck.getPosition() + Vector(0,i+1,0),
						rotation = {0,180,180},
						callback_function = function(o) characterDraftDeck.putObject(o) end,
					})
				end
			end
		end, 2)
	else
		trashBag.putObject(pickContractorsDeck)
	end
	
	
	if seatedPlayers > 5 then
		local locBags = {ammoBag, grenadeBag, oxygenBag, medpackBag}
		
		for i = 1, seatedPlayers - 5 do
			queenHealthDeck.shuffle()
			
			for _, obj in pairs (queenHealthDeck.getObjects()) do
				if obj.gm_notes != '3' then
					queenHealthDeck.takeObject({
						position = queenHealthDeck.getPosition() + Vector(0,2+i,0),
						callback_function = function(o)
							o.clone({position=o.getPosition() + Vector(0,5,0)})
						end,
						guid = obj.guid,
					})
					break
				end
			end
			
			for _, bag in pairs (locBags) do
				for j = 1, 2 do
					bag.takeObject({
						position = bag.getPosition() + Vector(0,1+j,0),
						callback_function = function(o2)
							bag.putObject(o2.clone())
							bag.putObject(o2)
						end,
					})
				end
			end
		end
	end
	
	if not automaticSeat then
		for color, entry in pairs(playerInfoTable) do
			gO(entry.boardGUID).clearButtons()
		end
	end
	
    for _, obj in pairs(getAllObjects()) do
        if obj.type == 'Deck' and not obj.hasTag('NoShuffle') then
            obj.shuffle()
        end
    end


	if useXyrian then
	
		explorationDeck.putObject(xyrianExplorationDeck)
		xyrianEventDeck.shuffle()
		xyrianEventDeck.takeObject({
			position = eventDeck.getPosition() + Vector(0,3,0),
			callback_function = function(o) eventDeck.putObject(o) end,
			smooth = false,
		})
		trashBag.putObject(xyrianEventDeck)
		
		Wait.time(function()
			
			for i = 1, 100 do
				explorationDeck.shuffle()
				if explorationDeck.getObjects()[1].gm_notes != 'xyrianExplore' then
					break
				end
			end
			
			for i = 1, 100 do
				eventDeck.shuffle()
				if eventDeck.getObjects()[1].gm_notes != 'xyrianEvent' then
					break
				end
			end
		end, 2)
	end
	



    local locPos = nil
	
	
    robotDeck.takeObject({
        position          = robotDeck.getPosition() + Vector(0,2,0),
		callback_function = function(obj)
			if obj.getName() == 'Exploration Robot' then
				robot.addTag('characterFig')
				robot.addTag('noEntrance')
			end
		end,
    })
    
	robotDeck.setPosition({-54,2,29}) --not throwing it because of one insider story



    for i, guid in pairs(shuffleTable(antiAircraftGUIDTable)) do
        token = gO(guid)
        locPos = token.getPosition()
        token.setPosition({locPos.x, 1.48+((i-1)*0.1), locPos.z})
    end


    -- pos = queenHealthDeck.getPosition()
    -- for i=1, 3 do
        -- queenHealthDeck.takeObject({
            -- position          = {pos.x, 2 + (i*0.3), pos.z},
            -- callback_function = function(obj) gameBox.putObject(obj) end,
        -- })
    -- end



    corridorStartData = {
        {locPos= {-12.12, 1.48, 9.00}, rot={0, -60, 0}},
        {locPos= {-10.39, 1.48, 6.00}, rot={0, 0, 0}},
        {locPos= {-12.11, 1.48, 3.00}, rot={0, 60, 0}},
    }
	
	local locLZGuid = landingZone.getGUID()
	RoomsMap[locLZGuid] = {'room', {}}
	
    for _, entry in pairs(corridorStartData) do
        corridorBag.takeObject({
            position          = entry.locPos,
            rotation          = entry.rot,
            callback_function = function(obj)
				obj.setLock(true)
				local locCorGUID = obj.getGUID()
				RoomsMap[locCorGUID] = {'corridor', {locLZGuid}}
				table.insert(RoomsMap[locLZGuid][2],locCorGUID)
			end,
        })
    end

	countPlayers(true)
    locPos = adultBag.getPosition()
	
	if lifeforms == 'Carnomorph' then
		locPos = larvaeBag.getPosition()
		for i=1, 3+seatedPlayers do
			larvaeBag.takeObject({
				position          = {locPos.x, 5 + (i*0.3), locPos.z},
				callback_function = function(obj) intruderBag.putObject(obj) end,
			})
		end	
	else
		for i=1, 3+seatedPlayers do
			adultBag.takeObject({
				position          = {locPos.x, 5 + (i*0.3), locPos.z},
				callback_function = function(obj) intruderBag.putObject(obj) end,
			})
		end
	end
	
	if lifeforms == 'Sangrevores' then
		locPos = breederBag.getPosition()
		for i=1, 2 do
			breederBag.takeObject({
				position          = {locPos.x, 5 + (i*0.3), locPos.z},
				callback_function = function(obj) intruderBag.putObject(obj) end,
			})
		end
	else
		locPos = larvaeBag.getPosition()
		for i=1, 2 do
			larvaeBag.takeObject({
				position          = {locPos.x, 5 + (i*0.3), locPos.z},
				callback_function = function(obj) intruderBag.putObject(obj) end,
			})
		end	
	end


    pCount = 0
	
	
    seatedPlayersTable = {}
    for color, entry in pairs(playerInfoTable) do

        if Player[color].seated or (not automaticSeat and entry.manualSeat) then
            pCount = pCount + 1
            table.insert(seatedPlayersTable, color)

        end
    end

    broadcastToAll(pCount .. '인 게임 설정.', Table)

    seatedPlayersTable = shuffleTable(seatedPlayersTable)


    Wait.time(|| setupPhase02(), 1)
end

function setupPhase02()
	if not scriptEnabled then
		return true
	end
	
	if missionTaskDeck == nil then missionTaskDeck = gO('eabc1d') end
	if objectiveMissonDeck == nil then objectiveMissonDeck = gO('fae6cf') end
	if objectivePersonalDeck == nil then objectivePersonalDeck = gO('263314') end
	
	local locMissionTaskPos = missionTaskDeck.getPosition()
	local locMissionPos = objectiveMissonDeck.getPosition()
	
	if seatedPlayers == 1 then
		coopMode = true
	end
	
	if not coopMode then
		

		decksToFix = {objectivePersonalDeck, missionTaskDeck, objectiveMissonDeck}
		--remove invalid player count cards from the deck
		for _, deck in pairs(decksToFix) do
			local locPos = deck.getPosition()
			locPos.y = 2
			for _, card in pairs(deck.getObjects()) do
				if tonumber(card.gm_notes) > pCount then
					locPos.y = locPos.y + 0.3
					deck.takeObject({
						position          = locPos,
						callback_function = function(obj) trashBag.putObject(obj) end,
						guid              = card.guid,
					})
				end
			end
		end


		missionTaskDeck.takeObject({
			position          = locMissionTaskPos + Vector(0,2,0),
			rotation          = {0, 180.00, 0},
		})
	end
	
    trashBag.putObject(missionTaskDeck)

    for i, color in pairs(seatedPlayersTable) do
		local locBPos = gO(playerInfoTable[color].boardGUID).getPosition()
		
		if not coopMode then
			objectivePersonalDeck.deal(1, color)
			if objectiveMissonDeck != nil then
				objectiveMissonDeck.deal(1, color)
			else
				local locObj = getTaggedObjAtPos('objective', locMissionPos, 0)
				if locObj != nil then
					trashBag.putObject(locObj)
				end
			end
		else
			local locCoopDeck = objectiveCoopDeck
			if coopCustom and i >= 2 then
				if math.random() > 0.25 then
					locCoopDeck = objectiveCoopCustomDeck
					newSeed(i)
				end
			end
			
			--locCoopDeck.shuffle()
			
			locCoopDeck.takeObject({
				position = locMissionTaskPos + Vector(0,2,0),
				rotation = {0,180,0},
			})
			
			
			
		end

        
		
		playerHelpBag.takeObject({
            position          = {locBPos.x - 6.73, 2, locBPos.z + 4.89},
            rotation          = {0, 180, 0},
        })

        if i == 1 then
            firstPlayerToken.setPosition({locBPos.x + 6.60, 2, locBPos.z + 5.15})
        end
    end
	
	toBox(playerHelpBag)

    Wait.time(function()
		for _, deck in pairs ({objectivePersonalDeck, objectiveCoopDeck, objectiveCoopCustomDeck}) do
			trashBag.putObject(deck)
		end

		if objectiveMissonDeck != nil then
			trashBag.putObject(objectiveMissonDeck)
		else
			local locObj = getTaggedObjAtPos('objective', locMissionPos, 0)
			if locObj != nil then
				trashBag.putObject(locObj)
			end
		end
		
	end, 2)

	currentRound = 1
    color = seatedPlayersTable[currentRound]
	
	if useCharacterDraft then
		Wait.time(|| startCharacterDraft(1), 3)
	else
		Wait.time(function()
			createSelectCrew()
			broadcastToAll('플레이어들은 자신의 규칙에 따라 원하는 캐릭터를 선택할 수 있습니다.', {0.2,1,1})
		end, 2.25)
	end


end

function startCharacterDraft(round)
	if not scriptEnabled then
		return true
	end

	currentRound = round
    local color = seatedPlayersTable[currentRound]
	
    broadcastToAll('플레이어 ' .. color .. '는 사용 가능한 캐릭터 중 하나를 선택해야 합니다.', {0.4,1,1})

    local locBPos = gO(playerInfoTable[color].boardGUID).getPosition()

	
    for i=1, 2 do
		if characterDraftDeck.getQuantity() > 0 then
			characterDraftDeck.takeObject({
				position          = {locBPos.x -2 + ((i-1)*4), 2, locBPos.z + 2 },
				rotation          = {0,90,180},
				callback_function = function(obj)
										setupDraftCard(obj, color)
									end,
			})
		end
    end
end




function setupDraftCard(card, color)
	if not scriptEnabled then
		return true
	end
	
	table.insert(characterDraftTable, card)
	
    hideFrom = {}
	if color != nil then
		for _, pColor in pairs(seatedPlayersTable) do
			if pColor ~= color then
				table.insert(hideFrom, pColor)
			end
		end
	end

    card.setInvisibleTo(hideFrom)
    card.setRotationSmooth({0, 90, 0})

    card.createButton({
        click_function = 'copyCharacterBag',
        function_owner = Global,
        label          = '선택',
        position       = {-1.5,0.2,0},
        rotation       = {0,90,0},
        --scale          = {0.8,0.8,0.8},
        width          = 1200,
        height         = 400,
        font_size      = 360,
        color          = {0,0,0,0.8},
        font_color     = {0.8,0.8,0.8,0.99},
        --tooltip        = -- string,
    })



end

function setupEquipment(card)
	if not scriptEnabled then
		return true
	end
	
	local locRotY = 90
	local locPos = {-1.5,0.2,0}
	
	if card.hasTag('rot180') then
		locRotY = 0
		locPos = {0,0.2,2}
	end
	
    card.createButton({
        click_function = 'pickEquipment',
        function_owner = Global,
        label          = '선택',
        position       = locPos,
        rotation       = {0,locRotY,0},
        --scale          = {0.8,0.8,0.8},
        width          = 1200,
        height         = 400,
        font_size      = 360,
        color          = {0,0,0,0.8},
        font_color     = {0.8,0.8,0.8,0.99},
        --tooltip        = -- string,
    })
	
end

function equipItem(card, pColor)
	
	if not scriptEnabled then
		return true
	end
	
	local locBoard = gO(playerInfoTable[pColor].boardGUID) 
	local locBPos = locBoard.getPosition()
	locBPos = Vector(locBPos.x, 0, locBPos.z)
	
	local locSpaceAvailable = true
	local locItemType = '중장비'
	if card.hasTag('StartItem') then
	
		local locArmWound = getTaggedObjAtPos('ARM', locBPos, 1, locBoard.getBounds().size)
		
		locSpaceAvailable = not (locArmWound != nil and playerHasTag('StartItem', 0, nil, pColor))
		
		local locItemRightHand = getTaggedObjAtPos('StartItem', locBPos+Vector(3.14, 1.6, -1.95), 0)
		local locItemLeftHand = getTaggedObjAtPos('StartItem', locBPos+Vector(-3.14, 1.6, -1.95), 0)
		
		if locSpaceAvailable then
			offset = Vector(3.14, 1.6, -1.95)
			
			
			if locItemRightHand != nil then
				offset = Vector(-3.14, 1.6, -1.95)
				locSpaceAvailable = locItemLeftHand == nil
			end
		end

		if card.getName() == 'bayonet' then
			if locItemLeftHand != nil then
				if locItemLeftHand.hasTag('weapon') and not (locItemLeftHand.hasTag('melee') or locItemLeftHand.hasTag('meleeRange')) then
					offset = Vector(-3.14, 1.6, -4.48)
				end
			elseif locItemRightHand != nil then
				if locItemRightHand.hasTag('weapon') and not (locItemRightHand.hasTag('melee') or locItemRightHand.hasTag('meleeRange')) then
					offset = Vector(3.14, 1.6, -4.48)
				end
			end
		end
		
		rot = {0,90,0}
	elseif card.hasTag('StartItem2') then
	   offset = Vector(-1.76, 2, 4.82)
		rot = {0,180,0}
		
		locSpaceAvailable = getTaggedObjAtPos('StartItem2', locBPos+offset, 0) == nil
		locItemType = '방어구'
	end
	
	local locPos = locBPos + offset --pos
	
	if locSpaceAvailable then
		card.setPosition(locPos)
		card.setRotation(rot)
		
		if card.hasTag('TacticalSlots') then
			refillEquipment(card, 0.08)
		end

		playsounds(math.random(186,188))
		
		local locButtonTbl = card.getButtons() --I panicked.
		local i = 0 
		for _, entry in pairs (locButtonTbl) do
			if entry.label  == '선택' then
				card.removeButton(i)
				break
			end
			i = i + 1
		end
		
		if card.hasTag('CEOArmor') then
			local locRobots = getTaggedObjAtPos('CEOArmor', locBPos, 0, locBoard.getBounds().size, {0,0,0}, true)
			for _, robot in pairs (locRobots) do
				if robot != card then
					robot.destruct()
				end
			end
		end
	else
		broadcastToAll('플레이어 ' .. pColor .. '는 새로운 ' .. locItemType .. '을(를) 선택하기 전에 먼저 하나를 버려야 합니다.', pColor)
	end
end

function pickEquipment(card, pColor)
	if not scriptEnabled then
		return true
	end
	
	if supportItemDraftCount > 0 then
		if isPlayingContractor(pColor) then
			broadcastToAll('플레이어 ' .. pColor .. '는 계약자 캐릭터로 인해 시작 아이템을 선택할 수 없습니다', {1,0.4,0.4})
		else
			
			equipItem(card, pColor)

			supportItemDraftCount = supportItemDraftCount - 1
			
			if supportItemDraftCount == 0 then
				Wait.time(function()
					for _, obj in pairs(draftSupportItemTable) do
						local buttonsTbl = obj.getButtons()
						if buttonsTbl != nil then
							for _, entry in pairs(buttonsTbl) do
								if entry.label  == '선택' then
									obj.destruct()
								end
							end
						end
					end
					
					Wait.time(function()
						broadcastToAll(setupEndMsg, {1,1,1})
						playsounds(185)
						
						local locPCol = getFirstPlayerColor()
						if Player[locPCol].seated then
							Turns.turn_color = locPCol
						else
							createPlayerColorSwitch(locPCol)
						end
						
						
						if delayedSkipScript then
							scriptEnabled = false
						end
					end, 1)
				end,0.5)
			end
		end
	else
		equipItem(card, pColor)
	end
end


function pickCard(selectedCardName, pColor, selectedCardGUID)
	if not scriptEnabled then
		return true
	end
	
	local name = selectedCardName
   -- print('Selected ' .. name)
	local locIsContractor = false
	
	local selectedCard = gO(selectedCardGUID)
	local locWait = 0
	
	if selectedCard == nil then
		locWait = 1
		for _, entry in pairs(characterDraftDeck.getObjects()) do
			if entry.name == name then
				characterDraftDeck.takeObject({
					position = characterDraftDeck.getPosition() + Vector(0,5,0),
					guid = entry.guid,
					callback_function = function (o)
						o.setLock(true)
						selectedCard = o
					end,
				})
			end
		end
	end
	
	Wait.time(function()
		if selectedCard.hasTag('Contractor') then
			locIsContractor = true
		else
			supportItemDraftCount = supportItemDraftCount + 1
		end

		
		local locPos = gameBox.getPosition()
		selectedCard.clearButtons()
		selectedCard.setLock(true)



		if useCharacterDraft then
			--Return other card
			
			
			for _, obj in pairs(characterDraftTable) do
				if obj != nil then
					local buttonsTbl = obj.getButtons()
					if buttonsTbl ~= nil then
						if buttonsTbl[1].label == '선택' then
							if locIsContractor and obj.hasTag('Contractor') and (seatedPlayers < 10 or selectedCard.getPosition().z > -12) then
								trashBag.putObject(obj)
							elseif obj.getPosition().z < -12 then
								characterDraftDeck.putObject(obj)
							end
						end
					end
				end
			end
			
			if locIsContractor and useContractors then
				for _, entry in pairs(characterDraftDeck.getObjects()) do
					if containTag('Contractor', entry.tags) then
						characterDraftDeck.takeObject({
							position = characterDraftDeck.getPosition() + Vector(0,5,0),
							guid = entry.guid,
							callback_function = function (o)
								trashBag.putObject(o)
							end,
						})
						break
					end
				end
			end
		end
		selectedCard.setPosition({5,-9,5})
		--setup selected character
		
		local locBoard = gO(playerInfoTable[pColor].boardGUID)
		local locBPos = locBoard.getPosition()
		
		local locItemCount = 0
		
		local locCharBag = nil
		local locPos
		local locPos2
		local locRot
		local locRot2
		local locOff
		local locLHandTaken = false
		

		
		if locIsContractor then
			
			local locContractorDeck = nil
			for _, obj2 in pairs(gameBox.getObjects()) do
				if obj2.name == 'Shared Contractor' then
					locOff = {x=-6.34, y=2, z=1.48}
					locPos2 = {locBPos.x+locOff.x, locOff.y + 1, locBPos.z+locOff.z}
					locRot = {0,180,180}
					
					gameBox.takeObject({
						position	= gameBox.getPosition() + Vector(0,10,0),
						rotation	= locRot,
						callback_function = function(o2) 
												locContractorDeck = o2.clone({position = locPos2})
												
												Wait.time(function()
													gameBox.putObject(o2)
												end, 0.5)
												
											end,
						guid              = obj2.guid,
						smooth            = false,
					})	
					break 
				end
			end
			
			Wait.time(function()
				if locContractorDeck != nil then
				
					locContractorDeck.setLock(true)
					
					if selectedCardName == 'Android' then
						for _, card in pairs (locContractorDeck.getObjects()) do
							
							if card.name == 'Rest' then
								locContractorDeck.takeObject({
									position = locContractorDeck.getPosition() + Vector(0,5,0),
									callback_function = function(o) o.destruct() end,
									guid = card.guid,
								})
								break
							end
						end
						
						for _, hitDeck in pairs (shapeCast(locBPos, locBoard.getBounds().size)) do
							if hitDeck.hasTag('ActionDeck') and hitDeck.getName() != 'Shared Contractor' then
								hitDeck.deal(12,pColor)
								broadcastToAll('플레이어 ' .. pColor .. '는 안드로이드 액션 카드 6장으로 덱을 만들어 액션 덱에 넣고 나머지는 예비 덱으로 플레이어 보드 옆에 배치해야 합니다.', playerInfoTable[pColor].tint)
								break
							end
						end
						
					elseif selectedCardName == 'CEO' then
						local i = 0
						for _, card in pairs (locContractorDeck.getObjects()) do
							
							if card.name == 'Repairs' or card.name == 'Demolition' then
								locContractorDeck.takeObject({
									position = locContractorDeck.getPosition() + Vector(0,5+i,0),
									callback_function = function(o) o.destruct() end,
									guid = card.guid,
								})
								i = i+1
							end
						end
					elseif selectedCardName == 'Hunter' then
						trapCheck = true
						trapBag.setPosition({45,1.48,-5})
						for t = 1, 3 do
							trapBag.takeObject({
								position = locBPos + Vector(-6 + t*2,1,-5),
							})
						end
					end

					locContractorDeck.setLock(false)
				end
			end, 0.5)
		end

		--{2.80, 1.90, 3.91}
		-- healthBag.takeObject({
			-- position          = {locBPos.x+ 2.80, 3, locBPos.z + 3.91},
			-- smooth            = false,
		-- })
		
		local healthObj = gO(playerInfoTable[pColor].healthGUID)
		healthObj.setPosition({locBPos.x+ 2.80, 3, locBPos.z + 3.91})
		healthObj.setLock(false)
		
		if lifeforms == 'Carnomorph' then
			local locMutaClone = mutationMarker.clone()
			
			locMutaClone.setLock(true)
			locMutaClone.setPositionSmooth({locBPos.x+1.11, 1.78, locBPos.z + 1}, false, true)
			
		end
		
		currentRound = currentRound + 1
							
		if currentRound <= #seatedPlayersTable then
			if useCharacterDraft then
				Wait.frames(|| characterDraftDeck.shuffle(), 60)
				Wait.frames(|| startCharacterDraft(currentRound), 120)
			end
		else
			--next phase

			for _, obj in pairs(characterDraftTable) do
				if obj != nil then
					local buttonsTbl = obj.getButtons()
					if buttonsTbl ~= nil then
						if buttonsTbl[1].label == '선택' then
							trashBag.putObject(obj)
						end
					end
				end
			end
			Wait.frames(function() trashBag.putObject(characterDraftDeck) toBox(trashBag) end, 120)
			Wait.frames(|| setupPhase03(), 120)

		end
		
		if useCharacterDraft then
			selectedCard.destruct()
		else
			characterDraftDeck.putObject(selectedCard)
		end
		
	end, locWait)

end

function isPlayingContractor(playerColor)
	if not scriptEnabled then
		return true
	end
	
	local locRayPos = gO(playerInfoTable[playerColor].boardGUID).getPosition()	
	return (getTaggedObjAtPos('Contractor', locRayPos, 0, {0.5,9,0.5}) != nil)

end

function afterSpawn(obj,playerColor, accept)
	if not scriptEnabled then
		return true
	end
	
	for _, tag in pairs (obj.getTags()) do
		if tag == 'CharacterTile' then
			obj.setLock(true)
		elseif tag == 'ActionDeck' then
			obj.shuffle()
			obj.setName('')
			obj.tooltip = true
		end
	end
	
	if accept != nil then
		for _, tag in pairs (obj.getTags()) do
			if tag == 'StartItem' then
				refillEquipment(obj, 0)
			elseif tag == 'Standee' then
				if not obj.hasTag('noRecolor') then
					obj.setColorTint(playerInfoTable[playerColor].tint)
				end
				obj.setName(obj.getName() .. ' of player ' .. playerColor)
				playerInfoTable[playerColor].figureGUID = obj.getGUID()
				obj.setPosition(standeePosTable[currentRound])
				obj.setRotation({0,180,0})
			elseif tag == 'UAV' then
				if not obj.hasTag('noRecolor') then
					obj.setColorTint(playerInfoTable[playerColor].tint)
				end
				obj.setName('UAV Drone' .. ' of player ' .. playerColor)
				obj.setPosition(landingZone.getPosition() + Vector(0,1.5,0))
				obj.setRotation({0,180,0})
			elseif tag == 'forceSelect' then
				setupEquipment(obj)
			end
		end
		
		if obj.getName() == 'connection' then
			countPlayers(true)
			for i = 1, math.max(0,seatedPlayers-2) do
				obj.clone({position = obj.getPosition() + Vector(i*0.8,0.5,0)})
			end
		elseif obj.getGMNotes() == 'dog' then
			obj.setColorTint(playerInfoTable[playerColor].tint)
		end
		
	end
end

function refillEquipment(obj, offsetZ)
	if not scriptEnabled then
		return true
	end
	
	local locTokenAmount = string.len(obj.getGMNotes())
	local locOffs = {}
	if locTokenAmount == 1 then
		locOffs = {0}
	elseif locTokenAmount == 2 then
		locOffs = {-0.40, 0.40}
	elseif locTokenAmount == 3 then
		locOffs = { -0.8, 0, 0.8}
	end
	
	local locOffZ = -0.99 + offsetZ
	
	if obj.hasTag('StartItem2') then
		locOffZ = -1.38
	end
	
	center = obj.getPosition()
	local j = 1
	local locGMNotes = obj.getGMNotes()
	
	for _, entry in pairs(locOffs) do
		local locTacticalBag = nil
		local locS = string.sub(locGMNotes,j,j)
		if locS == 'A' then
			locTacticalBag = ammoBag
		elseif locS == 'G' then
			locTacticalBag = grenadeBag
		elseif locS == 'O' then
			locTacticalBag = oxygenBag
		elseif locS == 'M' then
			locTacticalBag = medpackBag
		end
		
		if locTacticalBag != nil then
			if locTacticalBag.getQuantity() > 0 then
				locTacticalBag.takeObject({
					position          = {center.x + entry, 3, center.z + locOffZ},
					rotation = {0,90,0},
					smooth = false,
				})
			end
		end
		
		j = j+1
	end
end

function setupPhase03()
	if not scriptEnabled then
		return true
	end
	
	soundToggle()
	
	for _, bag in pairs ({larvaeFBag, creeperFBag, adultFBag, breederFBag, queenFBag, firespitterFBag, ironcladFBag, crawlmineFBag, larvaeBag, creeperBag, adultBag, breederBag, queenBag}) do
		if bag != nil then
			bag.setLock(true)
		end
	end
	
	if supportItemDraftCount > 0 then
		draftSupportItemTable = {}
		
		for i=1, math.max(7,supportItemDraftCount) do
			startItemDeck.takeObject({
				position          = {20 + ((i-1)*3), 2, -8},
				rotation          = {0,90,0},
				callback_function = function(obj)
										rotCheck(obj) 
										table.insert(draftSupportItemTable, obj)
									end,
			})
		end
		broadcastToAll('가장 높은 플레이어 번호부터 순서대로 한 명씩 지원 장비를 선택하세요.', {0.6,1,1})
	else
		broadcastToAll('계약자 캐릭터만 게임 중이므로 지원 아이템 드래프트를 건너뜁니다.', {0.8,1,1})
		broadcastToAll(setupEndMsg, {1,1,1})
		playsounds(185)
		
		local locPCol = getFirstPlayerColor()
		if Player[locPCol].seated then
			Turns.turn_color = locPCol
		else
			createPlayerColorSwitch(locPCol)
		end
		
		if delayedSkipScript then
			scriptEnabled = false
		end
	end
	
	if seatedPlayers > 5 then
		contaminationDeck.clone({position = contaminationDeck.getPosition() + Vector(0,3,0)})
		
		Wait.time(function()
			contaminationDeck.shuffle()
		end, 3)
	end
end


function rotCheck(card)
	if not scriptEnabled then
		return true
	end
	
    if card.hasTag('rot180') then
        card.setRotation({0,180,0})
    end
end

function buildButtons()
	
    for _, obj in pairs(getAllObjects()) do
		for _, tag in pairs (obj.getTags()) do
			if tag == 'Corridors' then
				labelCorridor(obj)
				break
			elseif tag == 'room' then
				labelRoom(obj)
				break
			elseif tag == 'Toggle' then
				labelToggle(obj)
				break
			elseif tag == 'Ammo' then
				labelAmmo(obj)
				break
			elseif tag == 'weapon' or tag == 'melee' then
				labelWeapon(obj)
				break
			elseif tag == 'insiderStory' then
				labelStory(obj)
				break
			end
		end
		if obj.getGMNotes() == 'grenade' then
			labelWeapon(obj)
		end
		
		if obj == xyrianAllegiance then
			obj.createButton({
				click_function = 'allegianceXyrianActivation',
				function_owner = Global,
				label          = '자이리안 활성화 실행',
				position       = {1.25, 0.5, 0},
				rotation = {0,90,0},
				scale          = {1.5,1,1},
				width          = 1000,
				height         = 200,
				font_size      = 90,
				color          = {0.086,0.44,0.603},
				font_color     = {0.769,0.957,0.906},
				tooltip        = '',
			})
		end
    end	
end

function allegianceXyrianActivation(allege)
	if not scriptEnabled then
		return true
	end
	
	local locAllegiance = true
	
	if allege != nil then
		locAllegiance = allege
	end
	
	xyrianActivationDeck.takeObject({
		position = xyrianActivationDeck.getPosition() + Vector(0,5,0),
		callback_function = function(o) xyrianActivationSeq(o, locAllegiance) end,
	})
end

function labelStory(object)
	if not scriptEnabled then
		return true
	end
	
	local locDesc = object.getDescription()
	local locACount = 0
	local locDescTmp = locDesc
	
	for i = 1, 4 do
		local locAIndex = string.find(locDescTmp, 'a')
		
		if locAIndex != nil then
		
			if string.len(locAIndex) > 1 then
				locAIndex = tonumber(string.sub(locAIndex,1,1))
			end					


			locAIndex = string.sub(locDescTmp,locAIndex+1,locAIndex+2)
			object.createButton({
				click_function = 'clickStory'.. uniqueID,
				function_owner = Global,
				label          = '이동 #' .. locAIndex,
				position       = {-1.4, -0.5, 0.9+(i-1)*0.4},
				rotation = {0,0,180},
				scale          = {2,2,1.3},
				width          = 300,
				height         = 80,
				font_size      = 50,
				color          = {0,0,0,0.8},
				font_color     = {1,1,1,1},
				tooltip        = '',
			})
			
			local func4 = function(obj, pColor, alt_click)
				local locChapter = locAIndex
				if insiderStoryGUID != '' then
					local locInsiderStoryDesc = obj.getDescription()
					local locSequelPass = true
					
					if locChapter != nil then
					
						if obj.hasTag('insiderSequelActionEgg') then
							if not playerHasTag('Egg', 1, nil, pColor) then
								locSequelPass = false
								broadcastToAll('플레이어 ' .. pColor .. '는 알이 없습니다.', insiderColor)
							end
							
						elseif obj.hasTag('insiderSequelActionData') then
							if insiderFig != nil and shuttleFigure != nil then
								insiderFig.setLock(true)
								shuttleFigure.setLock(true)
								
								insiderFig.setPositionSmooth(shuttleFigure.getPosition() + Vector(0,0.07,0), false, true)
								insiderFig.setRotation({0,0,0})
								
								Wait.time(function() shuttleFigure.addAttachment(insiderFig) end, 1)
									
								
								dataTokenBag.takeObject({
									position = gO(playerInfoTable[pColor].boardGUID).getPosition()+Vector(0,2,0),
								})
								broadcastToAll('인사이더가 플레이어 ' .. pColor .. '에게 데이터 토큰을 주었습니다.', insiderColor)
								
							else
								locSequelPass = false
							end
						end
						
						if locSequelPass then
							
							for _, storyCard in pairs (insiderDeck.getObjects()) do
								if storyCard.gm_notes == locChapter then
									--obj.clearButtons()
									insiderDeck.takeObject({
										position = insiderDeck.getPosition() + Vector(0,4,4),
										guid = storyCard.guid,
										callback_function = function(o2)
												local locNewDesc = string.gsub(locInsiderStoryDesc, 'a'.. locChapter,'')  --a for action
												obj.setDescription(string.sub(locNewDesc,1,string.len(locNewDesc)))
												insiderSequel(o2, nil, pColor)
											end,
										
									})
									break
								end
							end
						end
					end
				end
			end
			
			_G['clickStory' .. uniqueID] = func4
			uniqueID = uniqueID + 1

			
			locDescTmp = string.gsub(locDescTmp, 'a'..locAIndex, '')
			locDescTmp = string.sub(locDescTmp, 1, string.len(locDescTmp))
			
		else
			break
		end
	end
end

function onObjectSpawn(object)
	for _, tag in pairs(object.getTags()) do
		if tag == 'Corridors' then
			labelCorridor(object)
			break
		elseif tag == 'Toggle' then
			labelToggle(object)
			break
		elseif tag == 'Ammo' then
			labelAmmo(object)
			break
		elseif tag == 'weapon' or tag == 'melee' then
			labelWeapon(object)
			break
		elseif tag == 'room' then
			labelRoom(object)
			break
		elseif tag == 'insiderStory' then
			labelStory(object)
			break
		end
	end
	
	if object.getGMNotes() == 'grenade' then
		labelWeapon(object)
	elseif object.getDescription() == 'door' then
		object.registerCollisions(false)
	end
end

function labelRoom(room)
	local locPos = {0,0.12,-1}
	if room == hiddenRoom then
		locPos = {0,0.26,-0.75}
	end
	
	room.createButton({
		click_function = 'none',
		function_owner = Global,
		label          = room.getGMNotes(),
		position       = locPos,
		rotation       = {0,0,0},
		scale          = {0.4,0.4,0.4},
		width          = 400,
		height         = 400,
		color = {0,0,0,0.8},
		font_size      = 360,
		font_color     = {1,1,1,1},
	})
end

function labelWeapon(weapon)

	if not scriptEnabled then
		return true
	end

	local locPos = {1.55,0.15,0}
	local locRot = {0,90,0}
	local locS = {0.5,0.5,0.5}
	
	if weapon.getGMNotes() == 'grenade' then
		locPos = {-2.2,0.1,0}
		locRot = {0,-90,0}
		locS = {1,1,1}
		weapon.setDescription('GRENADE')
	elseif weapon.hasTag('melee') and not weapon.hasTag('weapon') then
		locPos = {0,0.15,0.3}
		locRot = {0,0,0}
		locS = {0.125, 0.125,0.125}
	elseif weapon.hasTag('StartItem2') then
		locPos = {0,0.15,-1.85}
		locRot = {0,0,0}
	end
	
	weapon.createButton({
	click_function = 'markButton',
	function_owner = Global,
	label          = '--',
	position       = locPos,
	rotation		= locRot,
	scale          = locS,
	width          = 1500,
	height         = 800,
	font_size      = 300,
	color          = {0,0,0,0.8},
	font_color     = {0.8,0.8,0.8,0.95},
	tooltip        = '클릭하여 다음 사격(Shoot)이나 집중사격(Burst)에 이 무기를 지정합니다.',
	})
end

function labelCorridor(corridor)
    local lbl = corridor.getGMNotes()

    local datatbl = {
        {pos= {-0.8,0.11,0.95}, rot={0,0,0}, arrow = '←'},
        {pos= {0.8,0.11,-0.95}, rot={0,180,0}, arrow = '→'},
        {pos= {0.8,-0.01,0.95}, rot={0,0,180}, arrow = '←'},
        {pos= {-0.8,-0.01,-0.95}, rot={0,180,180}, arrow = '→'},
    }
	
    for _, entry in pairs(datatbl) do
		
        corridor.createButton({
            click_function = 'none',
            function_owner = Global,
            label          = entry.arrow .. lbl .. entry.arrow,
            position       = entry.pos,
            rotation       = entry.rot,
            scale          = {0.19,0.19,0.19},
            width          = 0,
            height         = 0,
            font_size      = 360,
            font_color     = {0.5,0.5,0.5, 0.6},
        })
    end

end

function labelToggle(token)
    token.createButton({
        click_function = 'toggleState',
        function_owner = Global,
        label          = '',
        position       = {0,0.1,0},
        width          = 1200,
        height         = 1200,
        color          = {1,1,1,0},
        tooltip        = '클릭하여 켜짐/꺼짐 상태를 전환합니다.',
    })
end

function labelAmmo(token)
    token.createButton({
        click_function = 'toggleState',
        function_owner = Global,
        label          = '\u{00AB}',
        position       = {-2,0.1,0},
        scale          = {2.5,1,2.5},
        width          = 400,
        height         = 400,
        font_size      = 360,
        font_color     = {0.5,0.5,0.5, 0.6},
        color          = {0,0,0,0.8},
        tooltip        = '전체/절반 상태를 전환합니다.',
    })
end




--------------------------------------------------------------------------------
---------------------------------------GAME PLAY SCRIPT-------------------------
--------------------------------------------------------------------------------






function toggleState(obj)
    if obj.getStateId() == 1 then
        obj.setState(2)
    else
        obj.setState(1)
    end
end

function toBox(obj)
    gameBox.putObject(obj)
end


function onObjectCollisionEnter(registered_object, info)
	--print(tostring(info.collision_object) .. " collided with " .. tostring(registered_object))
	local locRObj = registered_object
	local obj = info.collision_object
	if locRObj == scanner then
		if scanNotActive then

			local objGUID = obj.getGUID()


			if obj.getGMNotes('action') then
				--prevents error from multiple scans
				scanNotActive = false

				--obj.setLock(true)
				obj.setRotation({0,180,0})

				obj.createButton({
					click_function = 'none',
					function_owner = Global,
					label          = '스캔 중',
					position       = {0, 0.2, 0.7},
					scale          = {0.5,0.5,0.5},
					width          = 1600,
					height         = 1200,
					font_size      = 250,
					color          = {0,0,0,0.8},
					font_color     = {0.8,0.8,0.8,100},
					tooltip        = '잠시만 기다려주세요.',
				})

				Wait.time(function() obj.editButton({label='.스캔 중.',}) end, 0.5)
				Wait.time(function() obj.editButton({label='..스캔 중..',}) end, 1)
				Wait.time(function() obj.editButton({label='...스캔 중...',}) end, 1.5)

				local msg = ''
				local locColor = {1,0,0}
				
				if obj.hasTag('Infection') then
					msg = 'Infection\nDetected'
					locColor = {1,0,0}
				else
					msg = 'No Infection\nDetected'
					locColor = {0,0,1}
				end

				Wait.time(function() obj.editButton({label=msg, color=locColor }) end, 2)
				Wait.time(function() broadcastToAll(msg, locColor) end, 2)
				Wait.time(function() scanNotActive = true end, 2)
				Wait.time(function() obj.clearButtons() end, 3)

			end
		end
	elseif locRObj.getDescription() == 'door' then
		if doorDropping and (obj.hasTag('room') or obj.hasTag('Corridors') or obj == boarderTile) then
			locRObj.setLock(true)
		end
		doorDropping = false
	end
end

--Round number (num) to the second decimal
function round(num,dec)
	if not scriptEnabled then
		return true
	end
	
  local mult = 10^(dec or 0)
  return math.floor(num * mult + 0.5) / mult
end

function lightlerp (seconds, lerpA, lerpB)
	if not scriptEnabled then
		return true
	end
	
	local steps = seconds*60
	for i=1, steps do
			Wait.time(function() Lighting.setLightColor(lerpA:lerp(lerpB, (i/steps))) 
			Lighting.apply()
			end, (i/steps)*seconds)
	end
end

victoryloop = 10
function rainbowlerp(timeloop)
	if not scriptEnabled then
		return true
	end
	
	local Colorlist = {Color(1,0,0), Color(1,1,0), Color(0,1,0), Color(0,1,1), Color(0,0,1), Color(1,0,1)
	}
	if victoryloop == 10 and lightAnimPlaying then
		local light
		light = Lighting.getLightColor()
		
		Wait.time(function() lightlerp(timeloop,Lighting.getLightColor(), light) 
					lightAnimPlaying = false
				end, timeloop)
	elseif not lightAnimPlaying then
		lightAnimPlaying = true
		lightlerp(timeloop, Lighting.getLightColor(), Colorlist[victoryloop])
		Wait.time(function() rainbowlerp(timeloop) end, timeloop)
		victoryloop = 1+(victoryloop+1)%6
	end

end

function lightAlert()
	if not scriptEnabled then
		return true
	end
	
	if not lightAnimPlaying then
		lightAnimPlaying = true
		local light
		if powerTokens[5] != 0 then
			light = lightColorStart
		else
			light = Lighting.getLightColor()
		end
		Wait.time(function() lightlerp (0.2, light, Color(0.6,0,0)) end, 0.053)
		Wait.time(function() lightlerp (0.664, Color(0.6,0,0), Color(0.2,0,0)) end, 0.74)
		Wait.time(function() lightlerp (0.2, Color(0.2,0,0), Color(0.6,0,0)) end, 1.41)
		Wait.time(function() lightlerp (0.664, Color(0.6,0,0), Color(0.2,0.2,0.2)) end, 2.183)
		Wait.time(function() lightlerp (3, Color(0.2,0.2,0.2), light) end, 2.88)
		Wait.time(function() lightAnimPlaying = false end, 5.88)
	end
end

function lightFlicker()
	if not scriptEnabled then
		return true
	end
	

	local light
	if powerTokens[5] != 0 then
		light = lightColorStart
	else
		light = Lighting.getLightColor()
	end
	if not lightAnimPlaying then
		lightAnimPlaying = true
		lightlerp(0.25, Color(light.r*0.6, light.g*0.6, light.b*0.6), light)
		Wait.time(function() lightlerp(0.1, light, Color(light.r*0.8, light.g*0.8, light.b*0.8)) end, 0.25)
		Wait.time(function() lightlerp(0.1, Color(light.r*0.8, light.g*0.8, light.b*0.8), light) end, 0.35)
		Wait.time(function() lightlerp(0.1, light, Color(light.r*0.8, light.g*0.8, light.b*0.8)) end, 0.45)
		Wait.time(function() lightlerp(0.1, Color(light.r*0.8, light.g*0.8, light.b*0.8), light) end, 0.55)
		Wait.time(function() lightAnimPlaying = false end, 0.65)
	end
end

function lightFire()
	if not scriptEnabled then
		return true
	end
	
	if not lightAnimPlaying then
		lightAnimPlaying = true
		local light
		if powerTokens[5] != 0 then
				light = lightColorStart
			else
				light = Lighting.getLightColor()
		end
		lightlerp(0.5, light, Color(light.r*0.25, light.g*0.25, light.b*0.25))
		Wait.time(function() lightlerp(4, Color(light.r*0.25, light.g*0.25, light.b*0.25 ),light) lightAnimPlaying = false end, 4)
		Wait.time(function() lightAnimPlaying = false end, 8)
	end
end

function rolldice(dice, roll)
	if not scriptEnabled then
		return true
	end
	
	if dice =='red' then
		redOneroll = roll
		if boardTable.boardindex < 7 then
			
			if roll == 1 then
				redOne = " 빗나감 "
			elseif roll == 2 then
				redOne = " 크리퍼 또는 유충 명중"
			elseif roll == 3 then
				redOne = " 크리퍼 또는 유충 명중"
			elseif roll == 4 then
				redOne = " 성체, 크리퍼, 또는 유충 명중"
			elseif roll == 5 then
				redOne = " 명중 "
			elseif roll == 6 then
				redOne = " !! 치명타 !!"
			elseif roll == 7 then
				redOne = " ?! 치명적 빗나감 ?!"
			end
			
		else
			--1 2 3 3 4 4 Ammo Critical
			if roll < 7 then

				if roll > 2 and roll < 5 then
					redOneroll = 3
				elseif roll > 4 and roll < 7 then
					redOneroll = 4
				end
				redOneroll = redOneroll + 1
				redOne = '' .. redOneroll
				
			elseif roll == 7 then
				redOne = "명중 및 탄약 손실. "
			elseif roll == 8 then
				redOne = " 치명타 ! "
			end
		end

	elseif dice == 'blue' then
		blueOneroll = roll
		if roll == 1 or roll == 2 then
			blueOne = " 빗나감"
		elseif roll == 3 or roll == 4 then
			blueOne = " 크리퍼 또는 유충 명중"
		elseif roll == 5 or roll == 6  then
			blueOne = " 성체, 크리퍼, 또는 유충 명중"
		elseif roll == 7 or roll == 8 then
			blueOne = " 버리고 +부상"
		elseif roll == 9 or roll == 10 then
			blueOne = " 명중 + (버리고 +부상)"
		elseif roll == 11 or roll == 12 then
			blueOne = " !! 치명타 !!"
		elseif roll == 13 then
			blueOne = " ?! 치명적 빗나감 ?!"
		end

	elseif dice == 'black' then
		blackOneroll = roll
		if roll == 1 or roll == 2 then
			blackOne = "통로 1 에 소음"
		elseif roll == 3 or roll == 4 then
			blackOne = "통로 2 에 소음"
		elseif roll == 5 or roll == 6 then
			blackOne = "통로 3 에 소음"
		elseif roll == 7 or roll == 8 then
			blackOne = "통로 4 에 소음"	
		elseif roll == 9 then
			blackOne = "점액질 묻지 않은 경우 정적"
		elseif roll == 10 then
			blackOne = "!!! 위험 !!!"
		end
	
	elseif dice == 'orange' then
		orangeOneroll = roll
		if roll == 1 or roll == 2 then
			orangeOne = "통로 1 에 소음"
		elseif roll == 3 or roll == 4 then
			orangeOne = "통로 2 에 소음"
		elseif roll == 5 or roll == 6 then
			orangeOne = "통로 3 에 소음"
		elseif roll == 7 or roll == 8 then
			orangeOne = "통로 4 에 소음"	
		elseif roll == 9 then
			orangeOne = "점액질 묻지 않은 경우 정적"
		elseif roll == 10 then
			orangeOne = "!!! 위험 !!!"
		elseif roll == 11 or roll == 12 then	
			orangeOne = "화성 표면"
		end
		
	elseif dice == 'fail' then
		failOneroll = roll
		if roll == 1 then
			if weaponAttackType == 0 or weaponAttackType == 4 then
				failOne = "중상 입음"
			else
				failOne = "경상 입음"
			end
		elseif roll == 2 then
			failOne = "방 안의 다른 플레이어를 공격"
		elseif roll == 3 then
			failOne = "방 파괴"
		end
		
	elseif dice == 'purple' then --1 1 1 2 3 4
		if roll < 4 then
			purpleOneroll = 1
		elseif roll == 4 then
			purpleOneroll = 2
		elseif roll == 5 then
			purpleOneroll = 3
		elseif roll == 6 then
			purpleOneroll = 4
		end
		
	elseif dice == 'yellow' then
		yellowOneroll = roll
		--1 2 2 3 3 4 4 4 Enc Enc
		if roll == 1 then
			yellowOne = "통로 1 에 소음"
		
		elseif roll == 2 or roll == 3 then
			yellowOne = "통로 2 에 소음"

		elseif roll == 4 or roll == 5 then
			yellowOne = "통로 3 에 소음"
			
		elseif roll > 5 and roll < 9 then
			yellowOne = "통로 4 에 소음"
			
		elseif roll > 8 then
			yellowOne = "조우 !!"
		end
	end	
end

numberAttacks = 1
timeAttacks = 0
VoteFailCount = 0

function endTurn(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	mayRerollNextShoot = false
	mayRerollNextBurst = false
	
	playerMoveStartRoomGUID = nil
	
	local locPCol = pColor
	local locFig = gO(playerInfoTable[locPCol].figureGUID)
	if locFig != nil then
		if isPlayerAlive(locPCol) then
			if not isInOxygenSection(locFig) then
				local locBoard = gO(playerInfoTable[locPCol].boardGUID)
				local locObj = getTaggedObjAtPos('CharacterTile', locBoard.getPosition(), 0, locBoard.getBounds().size)
				
				if locObj != nil then
					if locObj.getName() != 'Android' then
						locObj.setVar("count", math.max(-2,locObj.getVar("count") - 1))
						locObj.call("updateDisplay")
						
						if locObj.getVar("count") == -1 then
							broadcastToAll('플레이어 ' .. locPCol .. '가 질식하고 있습니다!', {1,1,1})
						elseif locObj.getVar("count") == -2 then
							broadcastToAll('플레이어 ' .. locPCol .. '가 산소 부족으로 사망했습니다.', {1,1,1})
						end
					end
				end
			end

			local locRoom = getRoomAtPlayer(locPCol)
			
			if locRoom != nil and not playerHasTag('TurnNoBurn', 0, nil, locPCol) then
				if getTaggedObjAtPos('fire', locRoom.getPosition(), 3, tileImportedSize) != nil then
					broadcastToAll('플레이어 ' .. locPCol .. '가 불타고 있습니다!', {1,1,1})
					loseHealth(locPCol)
				end
			end
			
			
			if insiderEnable and insiderStoryGUID != '' then
				local locInsiderStory = gO(insiderStoryGUID)
				if locInsiderStory != nil then
					for _, tag in pairs (locInsiderStory.getTags()) do
						if string.find(tag, 'insiderEffectEndTurn') != nil then
							autoInsider(2, tag, locRoom, locPCol)
						end
					end
				end
			end
			
		end
		
		local locColorFound = false
		local locHelpFound = false
		local locNoMsg = '모든 플레이어가 턴을 종료했습니다. 침입자 단계로 넘어갑니다.'
		
		for color, entry in pairs(playerInfoTable) do
			if color == locPCol then
				locColorFound = true
			elseif locColorFound then
				if Player[color].seated or (not automaticSeat and playerInfoTable[color].manualSeat) then
					if isPlayerAlive(color) then
						local locBoard2 = gO(entry.boardGUID)
						local locObj = getTaggedObjAtPos('playerHelp', locBoard2.getPosition(), 0, locBoard2.getBounds().size)
						
						if locObj != nil then
							if locObj.getRotation().z > 350 or locObj.getRotation().z < 10 then
								if Player[color].seated then
									Turns.turn_color = color
								else
									createPlayerColorSwitch(color)
								end
								locHelpFound = true
								break
							end
						end
					end
				end
			end
		end
		
		if locColorFound and not locHelpFound then
			for color, entry in pairs(playerInfoTable) do
				if Player[color].seated or (not automaticSeat and playerInfoTable[color].manualSeat) then
					if isPlayerAlive(color) then
						local locBoard2 = gO(playerInfoTable[color].boardGUID)
						local locObj = getTaggedObjAtPos('playerHelp', locBoard2.getPosition(), 0, locBoard2.getBounds().size)
						
						if locObj != nil then
							if locObj.getRotation().z > 350 or locObj.getRotation().z < 10 then
								if Player[color].seated then
									Turns.turn_color = color
								else
									createPlayerColorSwitch(color)
								end
								locHelpFound = true
								break
							end
						end
					end
				end
			end
		end
		
		if not locHelpFound then
			broadcastToAll(locNoMsg, {1,1,1})
			allPassed = true
			
			if airlockToken.getGMNotes() == 'active' then
				airlockToken.setGMNotes('')
				local locRooms = {}
				local locTokens = {}
				local locIntruders = {}
				local locMeats = {}
				local locFires = {}
				local locPlayerTiles = getPlayerRoomsInFirstTurnOrder()
				
				playsounds(185)
				broadcastToAll('에어락 절차가 끝났습니다.')
				
				
				for _, obj in pairs (getAllObjects()) do
					if obj.getName() == 'airlockToken' and obj != airlockToken then
						table.insert(locTokens, obj)
					elseif obj.hasTag('room') then
						table.insert(locRooms, obj)
					elseif obj.hasTag('intruder') then
						table.insert(locIntruders, obj)
					elseif obj.getGMNotes() == 'carcass' then
						table.insert(locMeats, obj)
					elseif obj.getGMNotes() == 'fire' then
						table.insert(locFires, obj)
					end
				end
				
				for _, roomTile in pairs (locRooms) do
					local locPos = roomTile.getPosition()
					local locGUID = roomTile.getGUID()
					
					for _, token in pairs (locTokens) do
						if token != nil then
							if distanceMath(locPos, token.getPosition()) < tileImportedSize.x then
								token.setPosition({45,-9,0})
								token.destruct()
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(locPos, intruder.getPosition()) < tileImportedSize.x*0.5 then
											intruder.setPosition({45,-9,0})
											enemyFigReturn(intruder)
										end
									end
								end
								
								for color, playerRoomGUID in pairs (locPlayerTiles) do
									if playerRoomGUID == locGUID then
										local locFig2 = gO(playerInfoTable[color].figureGUID)
										
										if locFig2 != nil then
											locFig2.destruct()
											local locHealth = gO(playerInfoTable[color].healthGUID)
											locHealth.setLock(true)
											locHealth.setPosition({115,-9,0})
											
											broadcastToAll('플레이어 ' .. color .. '가 에어락 절차로 사망했습니다.', lifeformColor)
										end
									end
								end
								
								for _, carcass in pairs (locMeats) do
									if carcass != nil then
										if distanceMath(locPos, carcass.getPosition()) < tileImportedSize.x then
											carcass.setPosition({45,-9,0})
											carcass.destruct()
										end
									end
								end
								
								for _, fire in pairs (locFires) do
									if fire != nil then
										if distanceMath(locPos, fire.getPosition()) < tileImportedSize.x then
											fire.setPosition({45,-9,0})
											fire.destruct()
										end
									end
								end
								
								break
							end
						end
					end
				end
			end
			
			Wait.time(function()
				if insiderEnable and insiderStoryGUID != '' then
					local locInsiderStory = gO(insiderStoryGUID)
					
					if locInsiderStory != nil then
						for _, tag in pairs (locInsiderStory.getTags()) do
							if string.find(tag, 'insiderEffectPlayerPhase') != nil then
								autoInsider(2, tag)
							end
						end
					end
				end
				

				intruderBurn()
			end, 1)
		end
	end
end

nextColor = nil
function createPlayerColorSwitch(color)
	if not scriptEnabled then
		return true
	end
	
	nextColor = color
	local locLab = 'Switch to Player ' .. color
	local locW = 650
	local locH = 200
	local fsize = math.min(2*locW/string.len(locLab) ,locH/2)
	broadcastToAll('플레이어 색상 전환 버튼이 응답을 기다리고 있습니다', {1,1,1})
	
	boarderTile.createButton({
			click_function = 'playerColorSwitch',
			function_owner = Global,
			label = locLab,
			position       = {1.6,0.5,2},
			scale = {0.8,0.8,0.8},
			width = locW,
			height         = locH,
			font_size      = fsize,
			color = playerInfoTable[color].tint,
			font_color     = {1,1,1},
		})
end

function playerColorSwitch(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	
	Player[pColor].changeColor(nextColor)
	Turns.turn_color = nextColor
	obj.clearButtons()
	
end

function intruderMock()
	if not scriptEnabled then
		return true
	end
	
	for i = 1, 3 do
		Wait.time(function()
			playsounds(52)
		end, (math.max(i-1,0)*0.47 + math.max(i-2,0))* soundDuration[52+1])
	end
end

function ironcladBuffCheck()
	if not scriptEnabled then
		return true
	end
	
	if lifeforms == 'Neoflesh' then
		local locIroncladBuff = getTaggedObjAtPos('ironcladBuff', {20,1.7,15.71}, 3, {0.5,9, 18})
		
		if locIroncladBuff != nil then
			local locRotZ = locIroncladBuff.getRotation().z
			locIroncladBuff = not (locRotZ > 170 and locRotZ < 190)
		else
			locIroncladBuff = false
		end
		
		return locIroncladBuff
	else
		return false
	end
end

function ironcladCheck(obj)
	if not scriptEnabled then
		return true
	end
	
	local locShoot = not ironcladBuffCheck()
	
	if not locShoot then
		local locRoom = getTaggedObjAtPos('room', obj.getPosition(), 0)
		
		if locRoom == nil then
			locRoom = getTaggedObjAtPos('Corridors', obj.getPosition(), 0)
		end
		
		if locRoom != nil then
			local locRoomPos = locRoom.getPosition()
			local locRoomSize = locRoom.getBounds().size
			local locIronclads = getTaggedObjAtPos('ironclad', locRoomPos, 3, locRoomSize, locRoom.getRotation(), true)
			local locIronclad = nil
			
			for _, iron in pairs (locIronclads) do
				if	distanceMath(iron.getPosition(), locRoomPos) < locRoomSize.x*0.5 then
					locIronclad = iron
					break
				end
			end
			
			if ((locIronclad != nil and obj.getGMNotes() == 'ironclad') or locIronclad == nil) then
				locShoot = true
			else
				broadcastToAll('방 안의 아이언클래드를 먼저 공격해야 합니다.', lifeformColor)
			end
		else 
			return true
		end
	end
	
	return locShoot
end


lastPickedDice = nil
lastDicePosition = Vector(0,0,0)
lastDiceValue = 0
lastDiceTarget = nil
lastDiceParams = nil
lastDiceParamsType = nil

function resetDiceParams()
	if not scriptEnabled then
		return true
	end
	
	lastDiceValue = 0
	lastDiceTarget = nil
	lastDiceParams = nil
	lastDiceParamsType = nil
	lastPickedDice = nil
end

function returnDiceValue(dice, params, paramsType)
	if not scriptEnabled then
		return true
	end
	
	local locPos = dice.getPosition()
	if distanceMath(locPos, lastDicePosition) < 0.001 then
		lastDiceValue = dice.getRotationValue()
		rollBowl.setPosition({2,-7,2})
		
		
		if dice == noiseRollDice then
			if paramsType == 'noise' then
				motionTrackerAction(params)
			elseif paramsType == 'GUID' then
				autoNoise(nil, params, false, noiseRollDice)
			end
			dice.setPositionSmooth({-20,1.95,-7.86}, false, true)
			
			
		elseif dice == shootRollDice then
			lastDiceTarget = params[1]
			rollShoot(params[1], params[2], params[3], true)
			dice.setPositionSmooth({-22, 1.95, -7.86}, false, true)
			
			
		elseif dice == burstRollDice then
			lastDiceTarget = params[1]
			rollBurst(params[1], params[2], params[3], true)
			dice.setPositionSmooth({-24, 1.94, -7.86}, false, true)
		end
	else
		lastDicePosition = locPos
		Wait.time(function() returnDiceValue(dice, params, paramsType) end, 0.1)
	end
end

function rollShoot(obj, pColor, alt_click, skipMay)
	if not scriptEnabled then
		return true
	end
	
	if shootingState == 0 and markedWeapon != nil then
		local locSkipMay = false
		
		if skipMay != nil then
			locSkipMay = skipMay
		end
		
		
		local locPass2 = true
		if not locSkipMay then
			if markedWeapon.hasTag('mayShootSpendAmmoAdd2Hits') then
				choiceToPlayer(obj.getPosition() + Vector(5,1,-2), '탄약 소모해서\n명중 2 추가?', 90)
				locPass2 = false
				
				Wait.condition(function()
					previousHCountObj = obj
					
					if choiceState == 1 then
						loseAmmo(markedWeapon)
						obj.setVar("count", obj.getVar("count") + 2)
						obj.call("updateDisplay")
					end
					locPass2 = true
					
					choiceState = 2
				end, function() return choiceState < 2 end, 999999, function() end)
				
			elseif markedWeapon.hasTag('mayShootSpendAmmoAoE1Hit') then
				choiceToPlayer(obj.getPosition() + Vector(5,1,-2), '탄약 소모해서\n침입자에게 1명중?', 90)
				locPass2 = false
				
				Wait.condition(function()
					
					
					if choiceState == 1 then

						
						local locRoom = getTaggedObjAtPos('room', obj.getPosition(), 0)
						
						if locRoom != nil then
							loseAmmo(markedWeapon)
							obj.setVar("count", obj.getVar("count") + 1)
							obj.call("updateDisplay")
							
							local locRoomPos = locRoom.getPosition()
							
							Wait.time(function()
								for _, intruder in pairs (getAllObjects()) do
									if intruder.hasTag('healthCount') and intruder != obj then
										if distanceMath(locRoomPos, intruder.getPosition()) < returnRoomDiameter(locRoom)*0.506 then
											intruder.call("onClick")
										end
									end
								end
							end, 1)
						end
					end
					
					choiceState = 2
					
					previousHCountObj = obj
					locPass2 = true
					
					
					
				end, function() return choiceState < 2 end, 999999, function() end)
			elseif markedWeapon.hasTag('mayMelee') then
			
				if getTaggedObjAtPos('ammo', markedWeapon.getPosition(), 3, markedWeapon.getBounds().size) != nil then
					choiceToPlayer(obj.getPosition() + Vector(5,1,-2), 'Melee Attack\nwith Weapon ?', 90)
					locPass2 = false
					
					Wait.condition(function()
						previousHCountObj = obj
						
						if choiceState == 1 then
							markedWeapon.addTag('melee')
						end

						locPass2 = true
						choiceState = 2
						
					end, function() return choiceState < 2 end, 999999, function() end)
				else
					markedWeapon.addTag('melee')
				end
			end
		end
		
		Wait.condition(function()
			local locPass = not rollAnimationEnable or (rollAnimationEnable and lastDiceValue != 0)
			if locPass then
				if lifeforms == 'Neoflesh' then
					
					if ironcladCheck(obj) then
						OnScriptButtonSet = 0
						onScriptingButtonDown(1, pColor)
						numpadToggle()
					end
					
				else
					OnScriptButtonSet = 0
					onScriptingButtonDown(1, pColor)
					numpadToggle()
				end
			else
				lastPickedDice = shootRollDice
				lastDicePosition = Vector(0,-5,0)
				lastDiceParams = {obj, pColor, alt_click}
				lastDiceParamsType = 'table'
				shootRollDice.setPosition(obj.getPosition() + Vector(4,5,0))
				rollBowl.setPosition(obj.getPosition() + Vector(4,4,0))
				
				if rollMode then
					broadcastToAll('플레이어 ' .. pColor .. '는 이제 사격 주사위를 굴려야 합니다.', shootColor)
				else

					for i = 1, math.random(2,3) do
						shootRollDice.roll()
					end
					Wait.time(function() returnDiceValue(shootRollDice, lastDiceParams) end, 0.25)
				end
				
			end
		end, function() return locPass2 end, 999999, function() end)
	end
end

function rollBurst(obj, pColor, alt_click, skipMay)
	if not scriptEnabled then
		return true
	end
	
	if shootingState == 0 and markedWeapon != nil then
	
		local locSkipMay = false
		
		if skipMay != nil then
			locSkipMay = skipMay
		end
	
		local locPass2 = true
		
		if not locSkipMay then
			if markedWeapon.hasTag('mayBurst1HitNoAmmo') then
				choiceToPlayer(obj.getPosition() + Vector(5,1,-2), 'Deal 1 Hit \n without spending Ammo ?', 50)
				
				locPass2 = false
				Wait.condition(function()
					previousHCountObj = obj
					
					if choiceState == 1 then
						lastDiceValue = 1
						markedWeapon.removeTag('TacticalSlots')
						
						if lifeforms == 'Neoflesh' then
							
							if ironcladCheck(obj) then
								OnScriptButtonSet = 0
								onScriptingButtonDown(2, pColor)
								numpadToggle()
							end
							
						else
							
							OnScriptButtonSet = 0
							onScriptingButtonDown(2,pColor)
							numpadToggle()
							
						end
						
						local locMarkedWeap = markedWeapon
						Wait.time(function()
							Wait.stop(burstWaitID)
							Wait.condition(function()
								locMarkedWeap.addTag('TacticalSlots')
								previousHCountObj = nil
								choiceState = 2
							end, function() return shootingState == 0 end, 999999, function() end)
						end, 1)
					else
						locPass2 = true
					end
					choiceState = 2
				end, function() return choiceState < 2 end, 999999, function() end)
			end
		end
		
		burstWaitID = Wait.condition(function()
			local locPass = not rollAnimationEnable or (rollAnimationEnable and lastDiceValue != 0)
			if locPass then
				if lifeforms == 'Neoflesh' then
					
					if ironcladCheck(obj) then
						OnScriptButtonSet = 0
						onScriptingButtonDown(2, pColor)
						numpadToggle()
					end
					
				else
					OnScriptButtonSet = 0
					onScriptingButtonDown(2,pColor)
					numpadToggle()
				end
			else
				lastPickedDice = burstRollDice
				lastDicePosition = Vector(0,-5,0)
				lastDiceParams = {obj, pColor, alt_click}
				lastDiceParamsType = 'table'
				burstRollDice.setPosition(obj.getPosition() + Vector(4,5,0))
				rollBowl.setPosition(obj.getPosition() + Vector(4,4,0))
				
				if rollMode then
					broadcastToAll('플레이어 ' .. pColor .. '는 이제 집중사격 주사위를 굴려야 합니다.', burstColor)
				else

					for i = 1, math.random(2,3) do
						burstRollDice.roll()
					end
					Wait.time(function() returnDiceValue(lastPickedDice, lastDiceParams) end, 0.25)
				end
			end
		end, function() return locPass2 end, 999999, function() end)
	end
end

choiceState = 2
function choiceToPlayer(pos, msg, fSize)
	if not scriptEnabled then
		return true
	end
	
	if choiceState == 2 then
		
		choiceState = 3 --to prevent multiple calls. Temporarily I suppose.
		local locPos = Vector(0,4,1)
		local locScale = Vector(1,1,1)
		local locFSize = 100
		
		if pos != nil then
			local S = boarderTile.getScale()
			S = Vector(S[1],S[2],S[3])
						
			locPos = Vector(pos[1]/S[1], pos[2]/S[2], (-1)*pos[3]/S[3])
			
			locScale = Vector(0.5,0.5,0.5)
		end
		
		if fSize != nil then
			locFSize = fSize
		end
		
		boarderTile.createButton({
			click_function = 'none',
			function_owner = Global,
			label          = msg,
			position       = locPos,
			scale          = locScale,
			width          = 700,
			height         = 200,
			font_size      = locFSize,
			color          = lifeformColor,
			font_color     = {1,1,1,1},
			tooltip        = '',
		})
		
		
		for i = 1, 2 do
			local locFunc = 'clickYes'
			local locLab = '예'
			if i == 2 then
				locFunc = 'clickNo'
				locLab = '아니오'
			end
			boarderTile.createButton({
				click_function = locFunc,
				function_owner = Global,
				label          = locLab,
				position       = locPos+Vector((-1.5+i)*locScale[1],0, 0.36*locScale[3]),
				scale          = locScale,
				width          = 250,
				height         = 200,
				font_size      = 100,
				color          = lifeformColor,
				font_color     = {1,1,1,1},
				tooltip        = '',
			})
		end
	end
end

function clickYes()
	if not scriptEnabled then
		return true
	end
	
	choiceState = 1
	
	local start = #boarderTile.getButtons()

	
	for i = 1, 3 do
		boarderTile.removeButton(start-i)
	end
end

function clickNo()
	if not scriptEnabled then
		return true
	end
	
	choiceState = 0
	local start = #boarderTile.getButtons()
	
	for i = 1, 3 do
		boarderTile.removeButton(start-i)
	end
end

autoBurst = false
autoBurstBig = false
function autoBurstToggle(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	if shootingState == 0 then
		if autoBurst then
			obj.removeButton(1)
			obj.editButton({index = 0, color =  {0,0,0,0.8}})
			autoBurst = false
		else
			local locLabel = ''
			if autoBurstBig then
				locLabel = '큰 것 먼저'
			else
				locLabel = '작은 것 먼저'
			end
			
			obj.createButton({
					click_function = 'autoBurstPriorityToggle',
					function_owner = Global,
					label          = locLabel,
					position       = {0, 0.15, 0.7},
					scale          = {2,2,2},
					width          = 600,
					height         = 200,
					font_size      = 100,
					color          = burstColor,
					font_color     = {0.8,0.8,0.8,0.95},
					tooltip        = '',
				})
			obj.editButton({index = 0, color = burstColor})
			autoBurst = true
		end
	end
end

function autoBurstPriorityToggle(obj, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	if shootingState == 0 then
		if autoBurstBig then
			obj.editButton({index = 1, label = '작은 것 먼저'})
			autoBurstBig = false
		else
			obj.editButton({index = 1, label = '큰 것 먼저'})
			autoBurstBig = true
		end
	end
end

lastHitEnemies = {}
lastAttackColor = nil
function hitCounterCheck(params)
	if not scriptEnabled then
		return true
	end
	
	local locObj = params.obj
	local locGM = locObj.getGMNotes()
	local locCount = params.count
	local locCor = false
	if autoBurst then
		locCor = shootingState == 2
	else
		locCor = getTaggedObjAtPos('Corridors', locObj.getPosition(), 0) != nil
	end
	
	if locGM != 'xyrian' then
		if lifeforms != 'Neoflesh' then

			
			if locGM != 'queen' and locCor then 
				local locBurstHits = 1
				
				if locGM == 'breeder' then
					locBurstHits = 2
				end
				
				if locCount == locBurstHits then
					if lifeforms == 'Carnomorph' and locGM == 'breeder' then
						local locCorObj = getTaggedObjAtPos('Corridors', locObj.getPosition(), 0)
						if adultFBag.getQuantity() > 0 then
							adultFBag.takeObject({
								position = adultFBag.getPosition() + Vector(0,6,0),
								callback_function = function (o)
									o.setLock(true)
									o.setRotation({0,math.random(0,360),0})
									o.setPositionSmooth(findSpaceOnTile(locCorObj,nil, true, o), false, true)
								end,
							})
						end
					end
					enemyFigReturn(locObj)
				end
				
			elseif locGM == 'queen' then
				if locCount == 5 then
					local locQueenName = '여왕'
					
					if lifeforms == 'Sangrevores' then
						locQueenName = '킹'
					elseif lifeforms == 'Carnomorph' then
						locQueenName = '슬래셔'
					end
					
					broadcastToAll(locQueenName .. ' 이 5 피해를 입었습니다, ' .. locQueenName .. ' 체력카드를 한장뽑고 추가로 버려진 카드를 공개하지 않고 해결합니다.', lifeformColor)
				end
			end
		elseif lifeforms == 'Neoflesh' then --Now that the Motherbrain hits are done properly I should move all that above
		
			
				
			if locGM != 'queen' and locCor then 
				local locBurstHits = 1
				
				if locGM == 'ironclad' and ironcladBuffCheck() then
					locBurstHits = 2
				end
				
				if locCount == locBurstHits then
					enemyFigReturn(locObj)
				end
				
				if locGM == 'breeder' then --not possible anymore but at some point an event card was suggesting it could be :o
					local locCultistBuff = getTaggedObjAtPos('cultistBuff', {20,1.7,15.71}, 3, {0.5,9,18})

					if locCultistBuff != nil then
						local locRotZ = locCultistBuff.getRotation().z
						locCultistBuff = not (locRotZ > 170 and locRotZ < 190)
					else
						locCultistBuff = false
					end
					
					if locCultistBuff then
						lastHitEnemies[locObj] = 0
						autoNoise(locObj.getPosition(), gO(playerInfoTable[lastAttackColor].figureGUID), false)
						broadcastToAll('광신도가 무리를 유인하기 위해 외쳤습니다.', lifeformColor)
					end
				end
				
			elseif locGM == 'queen' then
				local locReqHits = 5
				if locCount == locReqHits then
					
					broadcastToAll('마더브레인이 '..locReqHits..'회 피격되었습니다. 여왕 체력 카드를 뽑아 해결하되 추가로 버려진 카드는 공개하지 마세요.', lifeformColor)
				end
				
			elseif locGM == 'breeder' then
			
				if shootingState > 0 then
					if lastHitEnemies[locObj] != nil then
						return true
					end
					
					local locCultistBuff = getTaggedObjAtPos('cultistBuff', {20,1.7,15.71}, 3, {0.5,9,18})

					if locCultistBuff != nil then
						local locRotZ = locCultistBuff.getRotation().z
						locCultistBuff = not (locRotZ > 170 and locRotZ < 190)
					else
						locCultistBuff = false
					end
					
					if locCultistBuff then
						lastHitEnemies[locObj] = 0
						autoNoise(locObj.getPosition(), gO(playerInfoTable[lastAttackColor].figureGUID), false)
						broadcastToAll('광신도가 무리를 유인하기 위해 외쳤습니다.', lifeformColor)
					end
				end
				
			end
		end
	else
		if shootingState == 1 then
			if lastHitEnemies[locObj] != nil then
				return true
			end
			lastHitEnemies[locObj] = 0
			
			autoNoise(locObj.getPosition(), gO(playerInfoTable[lastAttackColor].figureGUID), false)
			broadcastToAll('자이리안이 무리를 유인하기 위해 외쳤습니다.', xyrianColor)
		end
	end
end

function critOnXyrian(xyrian)
	if not scriptEnabled then
		return true
	end
	
	playsounds(math.random(20,22))
	if xyrian.getName() == '' then
	
		xyrian.setName('injured')
		xyrian.setVar("count", 0)
		xyrian.call("updateDisplay")
		local locEnPos = xyrian.getPosition()
		xyrian.setPosition(locEnPos + Vector(0,0.16,0))
		
		xyrianInjuryBag.takeObject({
			position = {locEnPos.x,1.8,locEnPos.z-0.2},
			rotation = {0,180,180},
			callback_function = function(o)
									o.setLock(true)
									o.setPositionSmooth({locEnPos.x,1.8,locEnPos.z-0.2}, false,true)
									o.setRotation({0,180,180})
								end,
			smooth = false,
		})
		
		broadcastToAll('자이리안이 부상을 입었습니다.', xyrianColor)
	else
		--Wait.time(function()
			local locRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
			
			local locInj = getTaggedObjAtPos('xyrianInjury', locRoom.getPosition(), 3, locRoom.getBounds().size)
			if locInj != nil then
				locInj.setLock(false)
				locInj.flip()
				locInj.setGMNotes('')
			end
			
			xyrian.destruct()
			broadcastToAll('자이리안이 죽었습니다!', xyrianColor)
		--end, 1)
	end
end


function gainFromBagToPBoard(bag, color, tag, stringType, limit, clearGM)	

	if bag != nil then
		if bag.getQuantity() > 0 then
			local locBoard = gO(playerInfoTable[color].boardGUID)
			local locPos = locBoard.getPosition() + Vector(3.12, 2.5, -1.92)
			
			local locTag = nil
			local locClearGM = false
			
			if tag != nil then
				locTag = tag
			end
			
			if clearGM != nil then
				locClearGM = clearGM
			end
			
			bag.takeObject({
				position = bag.getPosition() + Vector(0,5,0),
				callback_function = function(o)
					o.setLock(true)
					local locPass = true
					
					if locTag != nil then
						local locList = getTaggedObjAtPos(locTag, locPos, stringType, locBoard.getBounds().size, {0,0,0}, true)
						
						if locList != nil then
							if #locList >= limit then
								locPass = false
							end
						end
					end
					
					o.setLock(false)
					
					if locPass then
						o.setPositionSmooth(locPos, false, true)
						
						if locClearGM then
							o.setGMNotes('')
						end
					else
						bag.putObject(o)
					end
				end,
			})
		end
	end
end

onScriptButtonFailSafe = false
rerolled = false
function onScriptingButtonDown(index, playerColor)
	
	if scriptEnabled then
		local Keypresser
		local R = boardTable.boardindex > 6
		
		if not hotseat and Player[playerColor].getPointerPosition() != nil then
			Keypresser = playerColor
		else
			Keypresser = Turns.turn_color
		end
		
		local pointer = Player[Keypresser].getPointerPosition() + Vector(0,3,0)
		
		if index==1 then
			if OnScriptButtonSet == 0 and shootingState == 0 and encounterTime == 0 
			and (Player[Keypresser].getHoverObject() != nil or lastDiceTarget != nil or previousHCountObj != nil)
			then
				lastHitEnemies = {}
				local locCanShoot = (markedWeapon != nil)
				local locPCol = nil
				local locPBoard = nil
				local locRoom = nil
				local locInsiderStory = nil
				local locFig = nil
				local locKillGain = nil
				local locKillGainLimit = nil
				local locReroll = mayRerollNextShoot
				
				
				
				if insiderEnable and insiderStoryGUID != '' then
					locInsiderStory = gO(insiderStoryGUID)
				end
				
				if locCanShoot then
					locPCol = getNearestPColor(markedWeapon.getPosition().x)
					lastAttackColor = locPCol
					locPBoard = gO(playerInfoTable[locPCol].boardGUID)
					locRoom = getRoomAtPlayer(locPCol)
					locFig = gO(playerInfoTable[locPCol].figureGUID)
					if markedWeapon.getGMNotes() == 'grenade' then
						locCanShoot = false
					end
					
					if locPBoard != nil then
						if playerHasTag('killGain', 0, nil, locPCol)  != nil then
							if playerHasTag('killGainCarcass', 0, nil, locPCol) then
								locKillGain = 'carcass'
								
								if playerHasTag('BAG OF CARCASSES', 2, nil, locPCol) then
									locKillGainLimit = 3
								else
									locKillGainLimit = 1
								end
							end
						end
					end
				else
					broadcastToAll('스크립트는 사격 전에 플레이어가 무기를 표시해야 합니다.', {1,1,1})
				end
				
				if locCanShoot then
					shootingState = 1
					
					local locScreamDelay = 0
					local enemyF = nil
					if lastDiceTarget != nil then
						enemyF = lastDiceTarget
					elseif previousHCountObj != nil then
						enemyF = previousHCountObj
						if not isHovered(previousHCountObj) then
							previousHCountObj = nil
						end
					else
						enemyF = Player[Keypresser].getHoverObject()
					end
					
					local locEnGM = enemyF.getGMNotes()
					local locShootOverride = false
					
					
					if markedWeapon.hasTag('mayShootRerollUAV') and not locReroll then
						if locFig != nil and locRoom != nil then
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('UAV') then
									if distanceMath(locRoom.getPosition(), obj.getPosition()) < tileImportedSize.x then
										locReroll = true
									end
									break
								end
							end
						end
					end
					

					
					if enemyF.hasTag('healthCount') then
					
						local hiss = math.random(1,3)
						
						
						if enemyF.getName() == 'insiderFig' or enemyF.getName() == 'runawayFig' then
							hiss = math.random(257,260)
							
						elseif lifeforms == 'Neoflesh' and locEnGM != 'xyrian' then
						
							if locEnGM == 'queen' then
								hiss = math.random(193,199)
							elseif locEnGM == 'crawlmine' then
								hiss = math.random(207,208)
							elseif locEnGM == 'ironclad' then
								hiss = math.random(211,212)
							elseif locEnGM == 'larvae' then
								hiss = math.random(214,215)
							elseif locEnGM == 'slasher' then
								hiss = math.random(234, 235)
							else
								hiss = math.random(219,221)
							end
						elseif locEnGM == 'xyrian' then
							hiss = math.random(167,178)
						end
						
						
						
						local cock = 0
						local shoot = 0
						
						
						if R then
							
							local locDurHiss = soundDuration[hiss+1]
							
							local screamSound = math.random(35,40)
							
							if enemyF.getName() == 'insiderFig' or enemyF.getName() == 'runawayFig' then
								screamSound = math.random(249,256)
								locScreamDelay = 0.2
								
							elseif lifeforms == 'Neoflesh' and locEnGM != 'xyrian' and locEnGM != 'breeder' then
								local locSoundTable = {}
								if locEnGM == 'queen' then
									for i = 1, 7 do
										table.insert(locSoundTable, 199 + i)
									end
								
								elseif locEnGM == 'slasher' then
									for i = 1, 2 do
										table.insert(locSoundTable, 235 + i)
									end
										
								elseif locEnGM == 'larvae' then
									for i = 1, 3 do
										table.insert(locSoundTable, 215 + i)
									end
										
								elseif math.random() > 0.4 then
									newSeed()
									for i = 1, 5 do
										table.insert(locSoundTable, 221 + i)
									end
									
								else
									if locEnGM == 'crawlmine' then
										for i = 1, 2 do
											table.insert(locSoundTable, 208 + i)
										end
										
									elseif locEnGM == 'ironclad' then
										table.insert(locSoundTable, 213)
									else
										for i = 1, 5 do
											table.insert(locSoundTable, 221 + i)
										end
									end
								end
								
								screamSound = locSoundTable[math.random(1, #locSoundTable)]
							end
							
							local killtext = ''
							
							if rollAnimationEnable then
								rolldice('red', lastDiceValue)
								resetDiceParams()
							else
								rolldice('red', math.random(1,8))
							end
							--rolldice('red', 7)
							
							local locFirstRedRoll = redOneroll
							local locRollNumber = redOneroll <= 5
							
							
							local locCount = enemyF.getVar("count") + 1

							local locCortisol = getTaggedObjAtPos('Cortisol Chip', locPBoard.getPosition(), 2, locPBoard.getBounds().size)
							
							
							if locCortisol != nil then
								if locCortisol.getButtons()[1].label == 'ACTIVE' then
									locCount = locCount + 1
								end
							end
							
							if locEnGM == 'creeper' then --for classic Nemesis addons
								locCount = locCount + 1
							end
							
							local locSkipCharge = false
							local locAmmoLoss = ''
							
							local meleeWeapon = markedWeapon.hasTag('melee') or markedWeapon.hasTag('meleeRange')
							
							if not (meleeWeapon and markedWeapon.hasTag('meleeNoShootTrait')) then
								for _, tag in pairs (markedWeapon.getTags()) do
									
									if redOneroll == 7 then
										
										

										
										if tag == 'shootAmmoCrit' then
											rolldice('red', 8)
											locRollNumber = false
											locAmmoLoss = ' Losing Ammo.'
											
										elseif tag == 'shootAmmoCritOnly' then
											rolldice('red', 8)
											locFirstRedRoll = 8
											locRollNumber = false
											
										-- elseif tag == 'shootAmmoFireRoom' then
										-- elseif tag == 'shootAmmoHealth2x' then
										-- elseif tag == 'shootAmmoMalf' then
										-- elseif tag == 'shootAmmoMalfRoom' then
										end
										
									elseif redOneroll == 8 then
										
										
										if tag == 'shootCritAmmoOnly' then
											rolldice('red', 7)
											locFirstRedRoll = 7
											locRollNumber = false
										-- elseif tag == 'shootCritAmmo' then
										elseif tag == 'shootCritRepel' then
											locShootOverride = true
										end
									
									elseif locRollNumber then
										if tag == 'shootSub1' then
											redOneroll = redOneroll - 1
											redOne = redOne .. '-1'
											
										elseif tag == 'shootSub2' then
											redOneroll = redOneroll - 2
											redOne = redOne .. '-2'
										end
										

									end

									
									if tag == 'shootCrit' then
										rolldice('red', 8)
										locRollNumber = false
									-- elseif tag == 'shootAoE' then
									-- elseif tag == 'shootMalf' then
									elseif tag == 'shootHitAdd1' then
										locCount = locCount + 1 
									-- elseif tag == 'shootHitAfterAdd1' then
									-- elseif tag == 'shootKillAdd1A' then
									-- elseif tag == 'shootLifeSupport' then
									
									elseif tag == 'shootOverride' then
										locShootOverride = true
									end
									
								end
							end
							
							if locInsiderStory != nil and locRollNumber then
								if locInsiderStory.hasTag('insiderEffectShootSub1') then
									redOneroll = redOneroll - 1
									redOne = redOne .. '-1'
								end
							end
							
							
							local locEyes = getTaggedObjAtPos('Eyes', locPBoard.getPosition(), 1, locPBoard.getBounds().size) 
							
							
							
							if locEyes != nil then
								if (locEyes.getRotation().z > 350 or locEyes.getRotation().z < 10) and locRollNumber then
									redOneroll = redOneroll + 1
									redOne = redOne .. '+1'
									broadcastToAll('플레이어 ' .. locPCol .. '의 눈 부상으로 사격이 어렵습니다!', lifeformColor)
								end
							end
							
							if locRollNumber then
								redOne = '(' .. redOne .. '). '
							end
							
							if rollShootWaitID != nil then
								Wait.stop(rollShootWaitID)
							end
							
							local locPass = not locReroll or rerolled
							
							if locReroll and not rerolled then
							
								locPass = false
								choiceToPlayer(enemyF.getPosition() + Vector(5,1,-2),'Reroll Shoot?', 90)
								local locWeapTmp = markedWeapon
								broadcastToAll('현재 사격 주사위 결과: ' .. redOne .. locAmmoLoss, shootColor)
								
								Wait.condition(function()
									mayRerollNextShoot = false
									
									if choiceState == 1 then
										previousHCountObj = enemyF
										if rollShootWaitID != nil then
											Wait.stop(rollShootWaitID)
										end
										
										rerolled = true
										shootingState = 0
										rollShoot(enemyF, locPCol)
										
									elseif choiceState == 0 then
										locPass = true
									end
									
									choiceState = 2

								end, function() return choiceState < 2 end, 999999, function() end)
							end
							
							if rerolled then
								rerolled = false
							end
							

							
							rollShootWaitID = Wait.condition(function()
								playsounds(hiss)
							
							
							
								local locTwitchlingBuff = false
								local locCrawlmineBuff = false
								if lifeforms == 'Neoflesh' then
									locTwitchlingBuff = getTaggedObjAtPos('twitchlingBuff', {20,1.7,15.71}, 3, {0.5,9,18})
									
									if locTwitchlingBuff != nil then
										local locRotZ = locTwitchlingBuff.getRotation().z
										locTwitchlingBuff = not (locRotZ > 170 and locRotZ < 190)
									else
										locTwitchlingBuff = false
									end
									
									locCrawlmineBuff = getTaggedObjAtPos('crawlmineBuff', {20,1.7,15.71}, 3, {0.5,9,18})
									
									if locCrawlmineBuff != nil then
										local locRotZ = locCrawlmineBuff.getRotation().z
										locCrawlmineBuff = not (locRotZ > 170 and locRotZ < 190)
									else
										locCrawlmineBuff = false
									end
								end
								
								if ((locCount >= redOneroll or (locEnGM == 'larvae' and not locTwitchlingBuff) or (locEnGM == 'creeper' and lifeforms == 'Carnomorph') ) and redOneroll != 7 )
								or redOneroll == 8 then
								-- if ((enemyF.getVar("count") > redOneroll and locEnGM != 'queen' or locEnGM == 'larvae') and redOneroll != 7 )
								-- or redOneroll == 8 then
									
									
									

									
									if enemyF.getName() != 'insiderFig' and enemyF.getName() != 'runawayFig' then
										if lifeforms == 'Neoflesh' and locEnGM != 'xyrian' then
										
											if locEnGM == 'queen' then
											
											elseif locEnGM == 'slasher' then
												screamSound = math.random(238,239)
											else
												screamSound = math.random(227,233)
											end
										else
											screamSound = math.random(20,22)
										end
									end
									
									
									killtext = "목표물을 처치했습니다."
									if locEnGM == 'queen' then
										killtext = '여왕 체력 카드를 뽑고, 추가로 버려진 카드를 공개하지 않고 해결합니다.'
									
									elseif locEnGM == 'xyrian'	and enemyF.getName() == '' then
										killtext = '자이리안이 전투에서 패배했습니다.'
									end
								end
								
								if markedWeapon.hasTag('shootHitAfterAdd1') then
									locCount = locCount + 1
								end
								
								
								
								
								if meleeWeapon and not markedWeapon.hasTag('StartItem') and not markedWeapon.hasTag('StartItem2') then
									if math.random() > 0.5 then
										shoot = 48
									else
										shoot = 50
									end
									if math.random() > 0.5 then
										cock = 51
									else
										shoot = 49
									end
									if lifeforms != 'Sangrevores' then
										addContamination(locPCol)
									end
									
								elseif markedWeapon.hasTag('soundFlamethrower') then
									
									if killtext == '' then
										shoot = math.random(131,133)	
									else
										shoot = 132
									end
									cock = 134
									
								elseif meleeWeapon then
								
									if killtext == '' then
										if math.random() > 0.5 then
											shoot = 164
										else
											shoot = 166
										end
									else
										shoot = 165
									end
									if math.random() > 0.5 then
										cock = 51
									else
										shoot = 49
									end
									
									if lifeforms != 'Sangrevores' and not markedWeapon.hasTag('meleeNoContamination') then
										addContamination(locPCol)
									end
									
									if markedWeapon.hasTag('meleeTissueAdd') then
										local locBoard = gO(playerInfoTable[locPCol].boardGUID)
										local locTile = getTaggedObjAtPos('CharacterTile', locBoard.getPosition(), 0, locBoard.getBounds().size)
										
										if locTile.getVar("countTissue") != nil then
											--locTile.setVar("countTissue", locTile.getVar("countTissue") + 1)
											locTile.call("updateTissue")
											broadcastToAll('플레이어 ' .. locPCol .. '가 조직 1개를 얻었습니다.', playerInfoTable[locPCol].tint)
										end
									end
									
								else
									if killtext == '' then
										shoot = math.random(80,83)
										cock = math.random(84,89)
									else
										shoot = math.random(90,91)
										cock = math.random(84,85)
									end	
								end
								

								
								local locDurCock = 0
								
								if cock != 0 then
									locDurCock = soundDuration[cock+1]
									Wait.time(function()
										sound1Used = false
										playsounds(cock)
									end, locDurHiss)
								end
								

								
								Wait.time(function()

									sound1Used = false --failsafe for critOnXyrian function which also plays a sound, oops
									sound2Used = false
									
									
									if locShootOverride then
										broadcastToAll('플레이어 ' .. locPCol .. '가 선택된 무기의 사격 효과를 사용합니다.', shootColor)
									else
										for i = 1, locCount - enemyF.getVar("count") do
											enemyF.call("onClick")
										end
									
										if killtext != '' then
											if locEnGM == 'xyrian' then
												critOnXyrian(enemyF)
											elseif locEnGM == 'queen' then
												local locReset = 0
												
												if lifeforms == 'Neoflesh' then
													locReset = 0-2*(3-queenBag.getQuantity())
												end
												
												enemyF.setVar("count", locReset)
												enemyF.call("updateDisplay")
												
											elseif locCrawlmineBuff and locEnGM == 'crawlmine' then
													
													enemyFigReturn(enemyF)
													broadcastToAll('크롤마인이 죽으면서 폭발합니다. 공격 카드 3장과 폭발 카드 1장을 해결하세요. 이후 뽑은 카드를 덱에 섞어 넣으세요.', lifeformColor)
													
											elseif ironcladBuffCheck() and locEnGM == 'ironclad' then
												
													killtext = '그리고 아이언클래드를 격퇴했습니다.'
													enemyF.setVar("count", 0)
													enemyF.call("updateDisplay")
													broadcastToAll('아이언클래드는 전투에서 죽지 않으므로 대신 격퇴하세요.', lifeformColor)
												
											else
												local locReturnEn = true
												if insiderEnable and locInsiderStory != nil then
													if locInsiderStory.hasTag('insiderSequelKillRunaway') then
														if insiderRunaway != nil then
															if enemyF == insiderRunaway then
																locReturnEn = false
																insiderRunaway.destruct()
																for _, storyCard in pairs (insiderDeck.getObjects()) do
																	if storyCard.gm_notes == '22' then
																		insiderDeck.takeObject({
																			position = insiderDeck.getPosition() + Vector(0,4,4),
																			guid = storyCard.guid,
																			callback_function = function(o)
																					insiderSequel(o, locRoom, locPCol)
																				end,
																		})
																		break
																	end
																end
															end
														end
													elseif locInsiderStory.hasTag('insiderEffectKilledInsiderRemove') then
														if insiderFig != nil then
															if insiderFig == enemyF then
																insiderCard.setGMNotes('')
																
																if insiderFig != nil then
																	toBox(insiderFig)
																end
																
																if insiderDeck != nil then
																	toBox(insiderDeck)
																end
																
																insiderStoryGUID = ''
																
																insiderEnable = false
															end
														end
													elseif enemyF.getName() == 'insiderFig' then
														locReturnEn = false
														enemyF.destruct()
													end
												end
												
												if locReturnEn then
													if lifeforms == 'Carnomorph' then
														carcassBag.takeObject({
															position = enemyF.getPosition(),
														})
														
														if locEnGM == 'breeder' then
															local locCarnoRoom = getTaggedObjAtPos('room', enemyF.getPosition(), 0)
															if adultFBag.getQuantity() > 0 then
																adultFBag.takeObject({
																	position = adultFBag.getPosition(),
																	callback_function = function(o)
																		o.setLock(true)
																		o.setRotation({0,180,0})
																		o.setPositionSmooth(findSpaceOnTile(locCarnoRoom, nil, true, o), false, true)
																	end,
																})
															end
														end
													end
													
													enemyFigReturn(enemyF)
													
													if locKillGain != nil then
														if locKillGain == 'carcass' then
															gainFromBagToPBoard(carcassBag, locPCol, 'Carcass', 1, locKillGainLimit, true)
														end
													end
												end
											end
										else
											if meleeWeapon and not enemyF.hasTag('noCounter') then
												if markedWeapon.hasTag('meleeLose1Health') then
													loseHealth(lastAttackColor)
												end
												
												if not markedWeapon.hasTag('meleeNoCounter') then
													intruderAttack(locRoom, enemyF, lastAttackColor)
													broadcastToAll('침입자가 죽지 않고 반격합니다!', lifeformColor)
												end
											end
										end
										
										broadcastToAll( '플레이어 ' .. locPCol .. ' 주사위 결과: ' .. redOne .. killtext,shootColor)
									end
									
									sound1Used = false
									playsounds(shoot)
									if locScreamDelay != 0 then
										Wait.time(function()
											playsounds(screamSound)
										end, locScreamDelay)
									else
										if not sound2Used then
											playsounds(screamSound)
										end
									end

								end , locDurCock + locDurHiss)
								
								Wait.time(function()
								
									if markedWeapon != nil then
										sound1Used = false
										
										if locFirstRedRoll == 7 and not meleeWeapon then
											loseAmmo(markedWeapon, locSkipCharge)
											locSkipCharge = true
										end
										
										for _, tag in pairs (markedWeapon.getTags()) do
											
											if locFirstRedRoll == 7 then
												

												
												-- if tag == 'shootAmmoCrit' then
												-- elseif tag == 'shootAmmoCritOnly' then
												if tag == 'shootAmmoFireRoom' then
													if getTaggedObjAtPos('fire', locRoom.getPosition(), 3, tileImportedSize) == nil then
														placeFire(findSpaceOnTile(locRoom), false)
														broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
														Wait.time(function() intruderMock() end, 2)
													end
													
												elseif tag == 'shootAmmoHealth2x' then
													if markedWeapon.getVar("count") > 0 then
														for i = 1, markedWeapon.getVar("count") do
															loseHealth(locPCol)
															loseHealth(locPCol)
														end
														broadcastToAll('플레이어 ' .. locPCol .. '가 결함 있는 플라즈마 건으로 체력 2를 잃었습니다!', {1,1,1})
													end
													markedWeapon.call("onClick")
													
													
												elseif tag == 'shootAmmoMalf' then
													if getTaggedObjAtPos('malfunction', markedWeapon.getPosition(), 3, markedWeapon.getBounds().size) == nil then
														if malfunctionBag.getQuantity() > 0 then
															placeMalfunction(markedWeapon.getPosition() + Vector(0,2,0))
															broadcastToAll('플레이어 ' .. locPCol .. '의 무기가 손상되었습니다!', {1,1,1})
															Wait.time(function() intruderMock() end, 2)
														else
															placeFire(findSpaceOnTile(locRoom))
															broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
														end
														
														
													end
													
												elseif tag == 'shootAmmoMalfRoom' then
													if locRoom.getName() != 'NEST' then
														if getTaggedObjAtPos('malfunction', locRoom.getPosition(), 3, tileImportedSize) == nil then
															placeMalfunction(findSpaceOnTile(locRoom))
															broadcastToAll('플레이어 ' .. locPCol .. '가 방을 손상시켰습니다!', {1,1,1})
															Wait.time(function() intruderMock() end, 2)
														end
													end
												end
												
											elseif locFirstRedRoll == 8 then
												
												
												if tag == 'shootCritAmmo' then
													loseAmmo(markedWeapon, locSkipCharge)
													locSkipCharge = true
												end
												
											end

											
											if tag == 'shootAoE' then
												for _, locEn in pairs (shapeCast(locRoom.getPosition(), tileImportedSize)) do
													if locEn.hasTag('healthCount') and distanceMath(locRoom.getPosition(), locEn.getPosition()) < returnRoomDiameter(locRoom)*0.506 then
														locEn.call("onClick")
													end
												end
												
											elseif tag == 'shootCharge' and not locSkipCharge then
												loseCharge(markedWeapon)
												locSkipCharge = true
												
											-- elseif tag == 'shootCrit' then
												
											elseif tag == 'shootMalf' then
												if getTaggedObjAtPos('malfunction', markedWeapon.getPosition(), 3, markedWeapon.getBounds().size) == nil then
													if malfunctionBag.getQuantity() > 0 then
														placeMalfunction(markedWeapon.getPosition() + Vector(0,2,0))
														broadcastToAll('플레이어 ' .. locPCol .. '의 무기가 손상되었습니다!', {1,1,1})
														Wait.time(function() intruderMock() end, 1)
													else
														placeFire(findSpaceOnTile(locRoom), true)
														broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
													end
													
													
												end
												
											-- elseif tag == 'shootHitAdd1' then
											
											-- elseif tag == 'shootHitAfterAdd1' then

												
											elseif tag == 'shootKillAdd1A' then
												if killtext == '목표물을 처치했습니다.' then
													broadcastToAll('플레이어 ' .. locPCol .. '가 치명타를 날리고 액션 카드를 뽑습니다!', {1,1,1})
													playerDrawActions(locPCol, 1)
												end
											elseif tag == 'shootLifeSupport' then
												if not isInOxygenSection(gO(playerInfoTable[locPCol].figureGUID)) then
													local locBoard = gO(playerInfoTable[locPCol].boardGUID)
													local locTile = getTaggedObjAtPos('CharacterTile', locBoard.getPosition(), 0, locBoard.getBounds().size)
													
													if locTile.getName() != 'Android' then
														locTile.setVar("count", math.max(-2,locTile.getVar("count") - 1))
														locTile.call("updateDisplay")
														
														broadcastToAll('플레이어 ' .. locPCol .. '가 산소를 일부 소모했습니다.', {1,1,1})
													end
												end
											
											elseif tag == 'shootSpendAmmo' then
												loseAmmo(markedWeapon, locSkipCharge)
												locSkipCharge = true
											
											-- elseif tag == 'shootSub1' then
											-- elseif tag == 'shootSub2' then
											
											end
											
											
										end

										
										if (killtext == '' or (killtext != '' and (locEnGM == 'xyrian' or locEnGM == 'queen'))) then
											if markedWeapon.hasTag('mayShootSpendAmmoShootAgain') then
												
												if enemyF != nil then
													if enemyF.hasTag('noShoot') then
														enemyF.removeTag('noShoot')
													else
													
														choiceToPlayer(enemyF.getPosition() + Vector(5,1,-2),'탄약 소모해서\n다시 사격?', 90)
														local locWeapTmp = markedWeapon
														Wait.condition(function()
															if choiceState == 1 then
																markWeaponToggle(locWeapTmp)
																loseAmmo(locWeapTmp)
																previousHCountObj = enemyF
																enemyF.addTag('noShoot')
																rollShoot(enemyF, locPCol)
															end
															choiceState = 2

														end, function() return choiceState < 2 end, 999999, function() end)
													end
												end
											end
										end
										
										if markedWeapon.hasTag('mayMelee') then
											if markedWeapon.hasTag('melee') then
												markedWeapon.removeTag('melee')
											end
										end
										
										markWeaponToggle(markedWeapon, enemyF)
									end
								end, locDurCock +locDurHiss + soundDuration[shoot+1])
							end, function() return locPass end, 999999, function() end)
						end
					end
				end
			
			elseif OnScriptButtonSet == 1 then
				if larvaeFBag.getQuantity() > 0 then
					larvaeFBag.takeObject({position = pointer, rotation = {0,0,0}})
					
					if pointer.z < (-13) then
						local locNear = getNearestPColor(pointer.x)
						if locNear != '' then
						
							broadcastToAll('플레이어 ' .. locNear .. '가 유충에 감염되었습니다.', lifeformColor)
							addContamination(locNear)
							
						end
					end
				else
					broadcastToAll('보드에 추가할 유충 피규어가 더 없습니다. 유충에 대한 상황이 최악입니다.', lifeformColor)
					intruderMock()
				end
			elseif OnScriptButtonSet == 2 then
				weaponAttackType = (weaponAttackType+1)%5 --melee, energy, classic, flamethrower, sword
				local weaponname
				if weaponAttackType == 1 then
					weaponname = '에너지 건'
				elseif weaponAttackType == 2 then
					weaponname = '클래식 건'
				elseif weaponAttackType == 3 then
					weaponname = '화염방사기'
				elseif weaponAttackType == 4 then
					weaponname = '검'
				else
					weaponname = '근접 무기'
				end
				broadcastToColor('weaponAttackType set to '.. weaponname, Keypresser, {0.50, 0.50, 0.50})
			end

		elseif index==2 then
			if OnScriptButtonSet == 0 and shootingState == 0  and encounterTime == 0
			and (Player[Keypresser].getHoverObject() != nil or lastDiceTarget != nil or previousHCountObj != nil)
			then
				lastHitEnemies = {}
				local locCanShoot = (markedWeapon != nil)
				local locPCol = nil
				local locRoom = nil
				local locInsiderStory = nil
				local locBoard = nil
				local locFig = nil
				local locKillGain = nil
				local locKillGainLimit = nil
				local locReroll = mayRerollNextBurst
				
				if insiderEnable and insiderStoryGUID != '' then
					locInsiderStory = gO(insiderStoryGUID)
				end
				
				if locCanShoot then
					locPCol = getNearestPColor(markedWeapon.getPosition().x)
					lastAttackColor = locPCol
					locRoom = getRoomAtPlayer(locPCol)
					shootingState = 2
					locBoard = gO(playerInfoTable[locPCol].boardGUID)
					locFig = gO(playerInfoTable[locPCol].figureGUID)
					
					if locBoard != nil then
						if playerHasTag('killGain', 0, nil, locPCol)  != nil then
							if playerHasTag('killGainCarcass', 0, nil, locPCol) then
								locKillGain = 'carcass'
								
								if playerHasTag('BAG OF CARCASSES', 2, nil, locPCol) then
									locKillGainLimit = 3
								else
									locKillGainLimit = 1
								end
							end
						end
					end
					
					local enemyF = nil
					if lastDiceTarget != nil then
						enemyF = lastDiceTarget
					elseif previousHCountObj != nil then
						enemyF = previousHCountObj
						if not isHovered(previousHCountObj) then
							previousHCountObj = nil
						end
					else
						enemyF = Player[Keypresser].getHoverObject()
					end
					
					local locRepel = false
					local locRepelRoom = nil
					
					if enemyF.hasTag('healthCount') then
						local locEnPos = enemyF.getPosition()
						local locLastEnGM = enemyF.getGMNotes()
						local hiss = math.random(1,3)
						
						if lifeforms == 'Neoflesh' and locLastEnGM != 'xyrian' then
						
							if locLastEnGM == 'queen' then
								hiss = math.random(193,199)

							elseif locLastEnGM == 'crawlmine' then
								hiss = math.random(207,208)
							elseif locLastEnGM == 'ironclad' then
								hiss = math.random(211,212)
							elseif locLastEnGM == 'larvae' then
								hiss = math.random(214,215)
							elseif locLastEnGM == 'slasher' then
								hiss = math.random(234, 235)
							else
								hiss = math.random(219,221)
							end
						end
						
						
						local locDurHiss = soundDuration[hiss+1]
						
						local cock = 0
						local ishoot = {}
						local itimeAttacks = {}
						timeAttacks = 0
						
						local locDurCock = 0
						
						if markedWeapon.hasTag('soundFlamethrower') then
							cock = 134
							
						elseif markedWeapon.hasTag('meleeRange') then
							if math.random() > 0.5 then
								cock = 51
							end
							
						elseif markedWeapon.getGMNotes() != 'grenade' then
							cock = math.random(84,85)
						end
						

						

						
						if lastDiceValue != 0 then
							rolldice('purple', lastDiceValue)
							resetDiceParams()
						else
							rolldice('purple', math.random(1,6))
						end
						
						numberAttacks = purpleOneroll
						
						local locCor = nil
						locCor = getTaggedObjAtPos('Corridors', enemyF.getPosition(), 0)
						
						if markedWeapon != nil then
							
							
							for _, tag in pairs (markedWeapon.getTags()) do
								if tag == 'burstAdd1' then
									numberAttacks = numberAttacks+1
								-- elseif tag == 'burstLifeSupport' then
								-- elseif tag == 'burstMalf' then
								elseif tag == 'burstMaxHit2' then
									numberAttacks = math.min(numberAttacks,2)
								elseif tag == 'burstMaxHit1' then
									numberAttacks = math.min(numberAttacks,1)
								elseif tag == 'burstMinHit2' then
									numberAttacks = math.max(numberAttacks,2)
								elseif tag == 'burstSub1' then
									numberAttacks = math.max(numberAttacks-1,0)
								elseif tag == 'burstRepel' then
									locRepel = true
									for _, roomGUID in pairs(RoomsMap[locCor.getGUID()][2]) do
										if roomGUID != locRoom.getGUID() then
											locRepelRoom = gO(roomGUID)
											break
										end
									end
								elseif tag == 'burstAddLaika' then
									local locLaika = gO('b6b3dd')
									
									if locLaika != nil then
										local locLaikaRoom = getTaggedObjAtPos('room', locLaika.getPosition(), 0)
										
										if locLaikaRoom != nil then
											for _, roomGUID in pairs(RoomsMap[locCor.getGUID()][2]) do
												if roomGUID == locLaikaRoom.getGUID() and roomGUID != locRoom.getGUID() then
													numberAttacks = numberAttacks+2
													break
												end
											end
										end
									end
								end
								
								if purpleOneroll == 4 then

									-- if tag == 'burstSPFireRoom' then
									--elseif tag == 'burstSPHealth2x' then
									if tag == 'burstSPHit1' then
										numberAttacks = 1
									-- elseif tag == 'burstSPMalf' then
									-- elseif tag == 'burstSPMalfRoom' then
									-- elseif tag == 'burstSPSub1A' then
									end
								end
							end
							
							if locInsiderStory != nil then
								if locInsiderStory.hasTag('insiderEffectBurstAdd1') then
									numberAttacks = numberAttacks+1
								end
							end

							if markedWeapon.getGMNotes() == 'grenade' then
								numberAttacks = numberAttacks + 2
							end
						end
						
						if rollBurstWaitID != nil then
							Wait.stop(rollBurstWaitID)
						end
						
						local locPass = not locReroll or rerolled
						
						if locReroll and not rerolled then
						
							locPass = false
							choiceToPlayer(enemyF.getPosition() + Vector(5,1,-2),'Reroll Burst?', 90)
							local locWeapTmp = markedWeapon
							broadcastToAll('현재 집중사격 주사위 결과: ' .. purpleOneroll, burstColor)
							
							Wait.condition(function()
								
								mayRerollNextBurst = false
								
								if choiceState == 1 then
									previousHCountObj = enemyF
									if rollBurstWaitID != nil then
										Wait.stop(rollBurstWaitID)
									end
									
									shootingState = 0
									rerolled = true
									rollBurst(enemyF, locPCol)
									
								elseif choiceState == 0 then
									locPass = true
								end
								
								choiceState = 2
								
							end, function() return choiceState < 2 end, 999999, function() end)
						end
						
						if rerolled then
							rerolled = false
						end
						
						rollBurstWaitID = Wait.condition(function()
							
							playsounds(hiss)
							if cock != 0 then
								locDurCock = soundDuration[cock+1]
									Wait.time(function()
										sound1Used = false
										playsounds(cock)
									end, locDurHiss)
							end
							
							
							local locEnTargets = {}
							table.insert(locEnTargets, enemyF)
							
							if enemyF.getGMNotes() != 'queen' then
								enemyF.setVar("count", 0)
								enemyF.call("updateDisplay")
							end
							

							local locBurstHits = 0
							
							
							if locCor != nil then
								
								local locQueens = {}
								local locBreeders = {}
								local locAdults = {}
								local locIronclads = {}
								local locFirespitters = {}
								local locSlashers = {}
								local locCrawlmines = {}
								local locLarvaes = {}
								local locCreepers = {}
								local locNoises = {}
								local locAllTables = {}
								
								local locFirespitterBuff = false
								local locIroncladBuff = false
								if lifeforms == 'Neoflesh' then
									locFirespitterBuff = getTaggedObjAtPos('firespitterBuff', {20,1.7,15.71}, 3, {0.5,9,18})
				
									if locFirespitterBuff != nil then
										local locRotZ = locFirespitterBuff.getRotation().z
										locFirespitterBuff = not (locRotZ > 170 and locRotZ < 190)
									else
										locFirespitterBuff = false
									end
									
									locIroncladBuff = ironcladBuffCheck()
								end
								
								
								for _, locIntruder in pairs (shapeCast(locCor.getPosition(), corridorImportedSize, locCor.getRotation())) do
									if distanceMath(locIntruder.getPosition(), locCor.getPosition()) < corridorImportedSize.x*0.5 then
										local locIGM = locIntruder.getGMNotes()
										local locT = nil
										if locIGM == 'queen' then
											locT = locQueens
										elseif locIGM == 'breeder' then
											locT = locBreeders
										elseif locIGM == 'adult' then
											locT = locAdults
										elseif locIGM == 'ironclad' then
											locT = locIronclads
											
										elseif locIGM == 'firespitter' then
											locT = locFirespitters
											if locFirespitterBuff and (markedWeapon.hasTag('weapon') and markedWeapon.getDescription() != 'GRENADE') then
												loseHealth(locPCol)
												broadcastToAll('플레이어 ' .. locPCol ..'가 파이어스피터에게 사격을 받고 있습니다!', lifeformColor)
												-- if locFirespitters[1] == nil then 			--not good enough.
													-- playsounds(160)
													-- Wait.time(function()
														-- playsounds(math.random(80,83))
														-- playsounds(math.random(12,18))
													-- end, soundDuration[160+1])
												-- end
											end
											
										elseif locIGM == 'slasher' then
											locT = locSlashers
										elseif locIGM == 'crawlmine' then
											locT = locCrawlmines
										elseif locIGM == 'larvae' then
											locT = locLarvaes
										elseif locIGM == 'creeper' then
											locT = locCreepers
										elseif locIGM == 'noise' then
											locT = locNoises
										end
										
										if locT != nil and locIntruder != enemyF then
											table.insert(locT, locIntruder)
											if locIGM != 'queen' then
												locIntruder.setVar("count", 0)
												locIntruder.call("updateDisplay")
											end
										end
									end
								end
							
								if autoBurst then
									if autoBurstBig then
										locAllTables[1] = locQueens
										locAllTables[2] = locBreeders
										locAllTables[3] = locAdults
										locAllTables[4] = locSlashers
										locAllTables[5] = locCrawlmines
										locAllTables[6] = locIronclads
										locAllTables[7] = locFirespitters
										locAllTables[8] = locLarvaes
										locAllTables[9] = locCreepers
										locAllTables[10] = locNoises
										
									else
										locAllTables[1] = locNoises
										locAllTables[2] = locLarvaes
										locAllTables[3] = locCreepers
										locAllTables[4] = locFirespitters
										locAllTables[5] = locIronclads
										locAllTables[6] = locCrawlmines
										locAllTables[7] = locSlashers
										locAllTables[8] = locAdults
										locAllTables[9] = locBreeders
										locAllTables[10] = locQueens
									end
									
									if lifeforms == 'Neoflesh' and locIroncladBuff then
										if autoBurstBig then
											table.remove(locAllTables,6)
										else
											table.remove(locAllTables,5)
										end
										table.insert(locAllTables,1, locIronclads)
									end
									
									for i = 1, #locAllTables do
										for _, intruder in pairs(locAllTables[i]) do
											table.insert(locEnTargets, intruder)
										end
									end
								end
							end
							
							local locIroncladBuff = false
							local locQueenMaxHits = 4
							local locQueenReset = 0
							
							if lifeforms == 'Neoflesh' then
								locIroncladBuff = ironcladBuffCheck()
								locQueenReset = 0-2*(3-queenBag.getQuantity())
							end
							
							for i = 1, numberAttacks do
								
													


								if markedWeapon.hasTag('soundFlamethrower') then
									ishoot[i] = 132
								elseif markedWeapon.getGMNotes() == 'grenade' then
									ishoot[i] = math.random(263,265)
								elseif markedWeapon.hasTag('meleeRange') then
									if math.random() > 0.5 then
										ishoot[i] = 165
									else
										ishoot[i] = 49
									end
									
								else
									ishoot[i] = math.random(90,91)
								end
								
								if i != 1 then
									timeAttacks = timeAttacks + soundDuration[ishoot[i]+1]*(1-(math.min(numberAttacks-0.5,i)/numberAttacks))
								end
								
								itimeAttacks[i] = timeAttacks
								
								
								Wait.time(function()
									if ishoot[i] < 100 then
										sound1Used = false
									elseif ishoot[i] > 260 then
										sound5Used = false
									end
									
									playsounds(ishoot[i])
									
									local locHurstSound = math.random(20,22)
									
									if lifeforms == 'Neoflesh' and locLastEnGM != 'xyrian' then
									
										if locLastEnGM == 'queen' then
											locHurstSound = math.random(200,206)
										elseif locLastEnGM == 'slasher' then
											locHurstSound = math.random(238,239)
										else
											locHurstSound = math.random(227,233)
										end
									end
									
									
									playsounds(locHurstSound)
									local locKill = false
									
									if locEnTargets[1] != nil then
										local locTar = locEnTargets[1]
										local locGM = locTar.getGMNotes()
										locLastEnGM = locGM
										
										
										if not locRepel or locGM == 'noise' then
											if locGM == 'noise' or locGM == 'larvae' or locGM == 'creeper' or locGM == 'adult' or locGM == 'firespitter' or locGM == 'crawlmine' or locGM == 'slasher' or (locGM == 'breeder' and lifeforms == 'Neoflesh') then
												table.remove(locEnTargets, 1)
												locKill = true
												
											elseif locGM == 'breeder' and locTar.getVar("count") == 1 then
												table.remove(locEnTargets, 1)
												locKill = true
												
											elseif locGM == 'ironclad' then
												if locIroncladBuff and locTar.getVar("count") == 1 then
													table.remove(locEnTargets, 1)
													locKill = true
													
												elseif not locIroncladBuff then
													table.remove(locEnTargets, 1)
													locKill = true
												end
												
											elseif locGM == 'queen' and locTar.getVar("count") == locQueenMaxHits then
												table.remove(locEnTargets, 1)
												local locQueen = locTar
												
												
												Wait.time(function()
													locQueen.setVar("count", locQueenReset)
													locQueen.call("updateDisplay")
												end, 3)
											end
												locTar.call("onClick")
												locBurstHits = numberAttacks - i
											
										else
											table.remove(locEnTargets, 1)
											locKill = true
											
											if locRepelRoom == nil then
												enemyFigReturn(locTar)
											else
												locTar.setPositionSmooth(findSpaceOnTile(locRepelRoom, nil, true, locTar), false, true)
												if locTar.hasTag('rot180') then
													locTar.setRotation({0,180,0})
												end
											end
										end
										
									else
										if autoBurst then
											if #locEnTargets > 0 then --Logically this never runs.... not deleting yet but hmmm....
												table.remove(locEnTargets, 1)
												locKill = true
												if locEnTargets[1] != nil then
													locEnTargets[1].call("onClick")
													locBurstHits = numberAttacks - i
												end
											end
										end
									end
									
									if locKill then
										if locKillGain != nil then
											if locKillGain == 'carcass' then
												gainFromBagToPBoard(carcassBag, locPCol, 'Carcass', 1, locKillGainLimit, true)
											end
										end
									end
									
								end , locDurCock +locDurHiss + itimeAttacks[i])
								
								
							end
							
							Wait.time(function()
							
								if markedWeapon != nil then
									for _, tag in pairs (markedWeapon.getTags()) do
									
										if tag == 'burstMalf' then
											if getTaggedObjAtPos('malfunction', markedWeapon.getPosition(), 3, markedWeapon.getBounds().size) == nil then
												if malfunctionBag.getQuantity() > 0 then
													placeMalfunction(markedWeapon.getPosition() + Vector(0,2,0))
													broadcastToAll('플레이어 ' .. locPCol .. '의 무기가 손상되었습니다!', {1,1,1})
													Wait.time(function() intruderMock() end, 2)
												else
													placeFire(findSpaceOnTile(locRoom), true)
													broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
												end
											end
										end
										

										
										if purpleOneroll != 4 then
											--if tag == 'burstAdd1' then
											if tag == 'burstLifeSupport' then
												if not isInOxygenSection(gO(playerInfoTable[locPCol].figureGUID)) then
													
													local locTile = getTaggedObjAtPos('CharacterTile', locBoard.getPosition(), 0, locBoard.getBounds().size)
													
													if locTile.getName() != 'Android' then
														locTile.setVar("count", math.max(-2,locTile.getVar("count") - 1))
														locTile.call("updateDisplay")
														
														broadcastToAll('플레이어 ' .. locPCol .. '가 산소 1을 소모했습니다.', {1,1,1})
													end
												end
											-- elseif tag == 'burstMaxHit2' then
											-- elseif tag == 'burstMaxHit1' then
											-- elseif tag == 'burstMinHit2' then
											-- elseif tag == 'burstSub1' then
											end
										else
											if tag == 'burstSPFireRoom' then
												local locRoom = getRoomAtPlayer(locPCol)
												if getTaggedObjAtPos('fire', locRoom.getPosition(), 3, tileImportedSize) == nil then
													placeFire(findSpaceOnTile(locRoom), true)
													broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
													Wait.time(function() intruderMock() end, 2)
												end
											elseif tag == 'burstSPHealth2x' then
												if markedWeapon.getVar("count") > 0 then
													for i = 1, markedWeapon.getVar("count") do
														loseHealth(locPCol)
														loseHealth(locPCol)
													end
												end
												markedWeapon.call("onClick")
											--elseif tag == 'burstSPHit1' then
											elseif tag == 'burstSPMalf' then
												if getTaggedObjAtPos('malfunction', markedWeapon.getPosition(), 3, markedWeapon.getBounds().size) == nil then
													if malfunctionBag.getQuantity() > 0 then
														placeMalfunction(markedWeapon.getPosition() + Vector(0,2,0))
														broadcastToAll('플레이어 ' .. locPCol .. '의 무기가 손상되었습니다!', {1,1,1})
														Wait.time(function() intruderMock() end, 2)
													else
														placeFire(findSpaceOnTile(locRoom), true)
														broadcastToAll('플레이어 ' .. locPCol .. '가 방을 불태웠습니다!', {1,1,1})
													end
													
													
												end
											elseif tag == 'burstSPMalfRoom' then
												local locRoom = getRoomAtPlayer(locPCol)
												if locRoom.getName() != 'NEST' then
													if getTaggedObjAtPos('malfunction', locRoom.getPosition(), 3, tileImportedSize) == nil then
														placeMalfunction(findSpaceOnTile(locRoom))
														broadcastToAll('플레이어 ' .. locPCol .. '가 방을 손상시켰습니다!', {1,1,1})
														Wait.time(function() intruderMock() end, 2)
													end
												end
											elseif tag == 'burstSPSub1A' then
												if #Player[locPCol].getHandObjects() > 0 then
													broadcastToAll('플레이어 ' .. locPCol .. '는 액션 카드 1장을 버려야 합니다.',{1,1,1})
												end
											elseif tag == 'burstSPOxy' then
												
												local locTile = getTaggedObjAtPos('CharacterTile', locBoard.getPosition(), 0, locBoard.getBounds().size)
												locTile.setVar("count", math.max(-2,locTile.getVar("count") - 1))
												locTile.call("updateDisplay")
												
												local locOxyName = '산소'
												
												if locTile.getName() == 'Android' then
													locOxyName = '배터리'
												end
												
												broadcastToAll('플레이어 ' .. locPCol .. '가 ' .. locOxyName .. ' 1을 잃었습니다.', {1,1,1})
											
											end
										end
										
										if tag == 'burstToHand' then
											markedWeapon.setLock(false)
											markedWeapon.setPosition(locBoard.getPosition() + Vector(-8.6,0,0))
											markedWeapon.setRotation({0,0,0})
										end

									end
								
								local locBurstAdd = ''
								
								
								if numberAttacks > purpleOneroll then
									locBurstAdd = '+'..numberAttacks-purpleOneroll
								elseif numberAttacks < purpleOneroll then
									locBurstAdd = ''.. numberAttacks-purpleOneroll
								end
								
								broadcastToAll('플레이어 ' .. locPCol .. ' 집중사격 주사위 결과: (' .. purpleOneroll .. locBurstAdd .. ').',burstColor)
								
								
								if markedWeapon.getGMNotes() == 'grenade' then
									grenadeBag.putObject(markedWeapon)
								else
									loseAmmo(markedWeapon)
								end
									
								if markedWeapon.hasTag('mayBurst2ndNoAmmo') then
									if (#locEnTargets > 0 or enemyF.getGMNotes() == 'queen')
									and (markedWeapon.hasTag('burstSPMalf') and purpleOneroll != 4) or not markedWeapon.hasTag('burstSPMalf') then
										if markedWeapon.hasTag('TacticalSlots') then
											choiceToPlayer(locEnPos + Vector(5,1,-2), '탄약소모 없이 같은 통로에\n 집중사격 하시겠습니까 ?', 56)
											local locWeapTmp = markedWeapon
											Wait.condition(function()
												if choiceState == 1 then
													locWeapTmp.removeTag('TacticalSlots')
												end
												choiceState = 2
											end, function() return choiceState < 2 end, 999999, function() end)
										else
											markedWeapon.addTag('TacticalSlots')
										end
									else
										if not markedWeapon.hasTag('TacticalSlots') then
											markedWeapon.addTag('TacticalSlots')
										end
									end
								end
								
								
								enemyF = locEnTargets[1]
								markWeaponToggle(markedWeapon, enemyF)
								end
							end, locDurCock +locDurHiss + timeAttacks +0.5)
						end, function() return locPass end, 999999, function() end)
							
					end
				else
					broadcastToAll('스크립트는 집중사격 전에 플레이어가 무기를 표시해야 합니다.', {1,1,1})
				end
				
			--elseif OnScriptButtonSet == 1 then

			--elseif OnScriptButtonSet == 2 then

			end

		elseif index==3 then
			if OnScriptButtonSet == 0 and not onScriptButtonFailSafe then
				onScriptButtonFailSafe = true
				if R then

					
					if Player[Keypresser].getHoverObject() != nil then
						autoNoise(pointer, Player[Keypresser].getHoverObject(), false)
					else
						rolldice('yellow', math.random(1,10))
						playsounds(math.random(54,73))
						broadcastToAll(yellowOne,{0.992,0.796,0.29})
					end

				else
					rolldice('black', math.random(1,10))
					if blackOneroll == 10 then
						playsounds(3)
						playsounds(math.random(60,64))
					elseif blackOneroll != 9 then
						playsounds(math.random(54,73))
					end
					broadcastToAll( Player[Keypresser].steam_name .. " 주사위 결과: " .. "" .. blackOne .. "",{r=255, g=255, b=255})
				end
				
				
				Wait.time(function() onScriptButtonFailSafe = false end, 1)
			elseif OnScriptButtonSet == 1 then
				placeAdult(pointer)
			
			elseif OnScriptButtonSet == 2 then
				if lifeforms == 'Chytrids' then
					germinatorUpgrade(false)
				end
			end

		elseif index==4 then
			if OnScriptButtonSet == 0 then	
				rolldice('orange', math.random(1,12))
				if orangeOneroll == 10 then
					playsounds(math.random(60,64))
				elseif orangeOneroll != 9 and orangeOneroll != 11 and orangeOneroll != 12 then
					playsounds(math.random(54,73))
				end
				broadcastToAll( Player[Keypresser].steam_name .. " 주사위 결과: " .. "" .. orangeOne .. "",{r=255, g=125, b=0})

			elseif OnScriptButtonSet == 1 then
				if breederFBag.getQuantity() > 0 then
					breederFBag.takeObject({position = pointer, rotation = {0,0,0}})
				else
					broadcastToAll('보드에 추가할 드론 피규어가 더 없습니다. 드론에 대한 상황이 최악입니다.', lifeformColor)
					intruderMock()
				end
				
			elseif OnScriptButtonSet == 2 then
				if lifeforms == 'Chytrids' and germinatorWait == false then
					local obj
					if germinatorTable.greenindex > germinatorTable.purpleindex then
						if germinatorTable.purpleindex < 6 then
						
							obj = gO(germinatorTable.purpleGUID[germinatorTable.purpleindex])
							obj.setGMNotes('')
							if (obj.getStateId()+1) < 4 then
								obj.setState(obj.getStateId()+1)
							end
							germinatorWait = true
							
							Wait.time(function() obj = gO(germinatorTable.purpleGUID[germinatorTable.purpleindex])
							obj.setGMNotes('rest')
							germinatorWait = false end, 0.3)
						end
					elseif germinatorTable.greenindex < 6 then

						obj = gO(germinatorTable.greenGUID[germinatorTable.greenindex])
						obj.setGMNotes('')
						if (obj.getStateId()+1) < 4 then
							obj.setState(obj.getStateId()+1)
						end
						germinatorWait = true
						
						Wait.time(function() obj = gO(germinatorTable.greenGUID[germinatorTable.greenindex])
						obj.setGMNotes('rest')
						germinatorWait = false end, 0.3)
					end
				end
			end

		elseif index==5 then
			if OnScriptButtonSet == 0 then
				local locRot = {0,180,0}
				if lifeforms == 'Sangrevores' then
					locRot = {0,0,0}
				end
				noiseBag.takeObject({position = pointer, rotation = locRot, smooth = false})
			
			elseif OnScriptButtonSet == 1 then
				if queenFBag.getQuantity() > 0 then
					queenFBag.takeObject({
						position = pointer,
						rotation = {0,0,0},
					})
				else
					broadcastToAll('여왕이 이미 보드에 있습니다.', lifeformColor)
					intruderMock()
				end
			end

		elseif index==6 then
			if OnScriptButtonSet == 0 then
				
				if boardTable.boardindex == 5 then
					local light
					if powerTokens[5] != 0 then
						light = lightColorStart
					else
						light = Lighting.getLightColor()
					end
					fireBag.takeObject({position = pointer, smooth = false})
					lightFlicker()
					Wait.time(function() lightFire() end, 0.65)
					playsounds(179)
					
				else
					placeFire(pointer, true)
				end
			elseif OnScriptButtonSet == 1 then
			end

		elseif index==7 then
			if OnScriptButtonSet == 0 then
				if boardTable.boardindex == 5 then
					malfunctionBag.takeObject({position = pointer, smooth = false})
				else
					placeMalfunction(pointer)
				end
			elseif OnScriptButtonSet == 1 then
				if nestBag.getQuantity() > 0 then
					nestBag.takeObject({position = pointer, smooth = false,})
				else
					broadcastToAll('둥지에 알이 더 없습니다.', lifeformColor)
				end
			end

		elseif index==8 then
			if OnScriptButtonSet == 0 then
				if doorBag.getQuantity() > 0 then
					doorBag.takeObject({position = pointer, smooth = false})
				else
					broadcastToAll('더 이상 배치할 문이 없습니다.', {0.50, 0.50, 0.50})
				end
			elseif OnScriptButtonSet == 1 then

				if Player[Keypresser].getHoverObject() != nil then
					local object = Player[Keypresser].getHoverObject()
					local locGM = object.getGMNotes()
					local locDesc = object.getDescription()
					
					if object.hasTag('healthCount') then
						enemyFigReturn(object)
					elseif locGM == 'secure'then
						secureTokenRemove(object)
						
					elseif locDesc == 'door' then
						object.setLock(false)
						doorBag.putObject(object)
				
					elseif locGM == 'fire' then
						if not insiderEnable or insiderStoryGUID == '' then
							fireBag.putObject(object)
						elseif insiderStoryGUID != '' then
							local locStoryCard = gO(insiderStoryGUID)
							if locStoryCard != nil then
								if not locStoryCard.hasTag('insiderEffectFireKeep') and not locStoryCard.hasTag('insiderEffectFireKeepOxy') then
									fireBag.putObject(object)
									return true
								
								elseif locStoryCard.hasTag('insiderEffectFireKeepOxy') then
									for _, lifeSupportObj in pairs (getAllObjects()) do
										if lifeSupportObj.hasTag('LifeSupportOff') then
											if getSectionFromXPos(lifeSupportObj.getPosition().x) == getSectionFromXPos(object.getPosition().x) then
												fireBag.putObject(object)
												return true
											end
										end
									end
								end
								
								broadcastToAll(insiderWarningMsg, insiderColor)
							else
								fireBag.putObject(object)
							end
						end
						
					elseif locGM == 'malfunction' then
						if not insiderEnable or insiderStoryGUID == '' then
							malfunctionBag.putObject(object)
						elseif insiderStoryGUID != '' then
							local locStoryCard = gO(insiderStoryGUID)
							
							if locStoryCard != nil then
								if not locStoryCard.hasTag('insiderEffectArmoryNoRepair') then
									malfunctionBag.putObject(object)
								else
									local locRoom = getTaggedObjAtPos('room', object.getPosition(), 0)
									if locRoom != nil then
										if locRoom.getName() != 'ARMORY' then
											malfunctionBag.putObject(object)
										else
											broadcastToAll('병기고를 수리할 수 없습니다.', insiderColor)
										end
									end
								end
							else
								malfunctionBag.putObject(object)
							end
						end
						
					elseif locGM == 'xyrianTracer' then
						object.setLock(false)
						xyrianTracerBag.putObject(object)
					else
						intruderTokenReturn(object)
					end
				end
			end
		
		elseif index==9 then
			if OnScriptButtonSet == 0 then
				if secureBag.getQuantity() > 0 then
					local locPass = true
					if useXyrian then
						local locRoom = getTaggedObjAtPos('room', pointer, 0)
						if locRoom != nil then
							locPass = getTaggedObjAtPos('xyrian', locRoom.getPosition(), 3, tileImportedSize) == nil
						end
						if not locPass then
							broadcastToAll('자이리안 방에 보안 토큰을 추가하는 것은 금지되어 있습니다.', xyrianColor)
						end
					end
					
					if locPass then
						secureBag.takeObject({position = pointer, smooth = false})
					end
				else
					broadcastToAll('보안 토큰이 부족합니다.', {0.5,0.5,0.5})
				end
			elseif OnScriptButtonSet == 1 then
			elseif OnScriptButtonSet == 2 then
				if victoryloop < 10 then
					victoryloop = 10
				else
					victoryloop = 1
					rainbowlerp(math.random(3,6))
				end
			end
		elseif index==10 then
			OnScriptButtonSet = (OnScriptButtonSet+1)%2
			broadcastToColor('Numpad hotkeys switch to set '.. OnScriptButtonSet, Keypresser, {0.50, 0.50, 0.50})
			numpadToggle()
		end
	end
end

function secureTokenRemove(obj)
	if not scriptEnabled then
		return true
	end
	
	if obj != nil then
		if obj.getQuantity() > 1 then
			obj.takeObject({
				position = obj.getPosition() + Vector(0,10,0),
				callback_function = function(o) secureBag.putObject(o) end,
				smooth = false,
			})
		else
			secureBag.putObject(obj)
		end
	end
end

function placeAdult(pos)
	if not scriptEnabled then
		return true
	end
	
	if adultFBag.getQuantity() > 0 then
		adultFBag.takeObject({
			position = pos,
		})
	else
		broadcastToAll('보드에 추가할 성체 피규어가 더 없습니다. 성체에 대한 상황이 최악입니다.', lifeformColor)
		intruderMock()
	end
end

function encounterTimeTickDown()
	if not scriptEnabled then
		return true
	end
	
	if encounterTime > 0 then
		
		if encounterWaitTickID != nil then
			Wait.stop(encounterWaitTickID)
		end
		
		encounterWaitTickID = Wait.time(function()
			encounterTime = math.max(encounterTime - 1,0)
			encounterTimeTickDown()
		end, 1)
	end
end

queueAutoNoiseParams = {}
function queueAutoNoise()
	if not scriptEnabled then
		return true
	end
	
	Wait.condition(function()
	
		local locT = queueAutoNoiseParams
		local locTime = encounterTime + 1.5
		broadcastToAll('다음 자동 소음까지 ' .. locTime .. '초. 그때까지 사격 및 집중사격이 제한됩니다', {1,1,1})
		Wait.time(function()
			encounterTime = 0
			autoNoise(locT[1][1], locT[1][2], locT[1][3])
			table.remove(queueAutoNoiseParams, 1)
			if #queueAutoNoiseParams > 0 then
				Wait.time(function() queueAutoNoise() end, 2)
			else
				broadcastToAll('자동 소음 대기열이 종료되었습니다.', {1,1,1})
			end
		end, locTime)
		
	end, function() return not xyrianPause end, 999999, function() end)
end


encounterTime = 0
function autoNoise(rayOrigin, hoverObj, explore, dice)
	if not scriptEnabled then
		return true
	end
	
	local locWait = 0
	
	if encounterTime == 0 then
		local locChar = nil
		local locCharGUID = nil
		local locPCol = ''
		local locPlayerRooms = {}
		local locNoiseMsg = ''
		
		if hoverObj != nil then
			if hoverObj.hasTag('characterFig') then
				locChar = hoverObj
				locCharGUID = locChar.getGUID()
				for color, entry in pairs(playerInfoTable) do
					if entry.figureGUID == locCharGUID then
						locPCol = color
						locPlayerRooms = getPlayerRoomsInFirstTurnOrder()
						break
					end
				end
				
				if insiderFig != nil then
					if locChar == insiderFig then
						locPCol = 'insider'
						locPlayerRooms = getPlayerRoomsInFirstTurnOrder(true)
					end
				end
				
				if locPCol == '' then
					locChar = nil
					locPCol = Turns.turn_color
				end
			else
				locPCol = Turns.turn_color
			end
		end
		
		if locPCol != '' then
			locNoiseMsg = locPCol ..' rolled: '
		end
		
		local locCanNoise = true
		local locCautiousMove = false
		if locChar != nil then
			locCanNoise = not playerHasTag('NoNoise', 0, locCharGUID, nil)
			local locCharRot = locChar.getRotation()
			locCautiousMove = locCharRot.z > 90 and locCharRot.z < 250
			locChar.setRotation({locCharRot.x,locCharRot.y, 0})
			locChar.setLock(false)
		end
		
		local locUseSangrevores = lifeforms == 'Sangrevores'
		
		if not locCanNoise then
			broadcastToAll('플레이어가 소음을 내지 않습니다', {1,1,1})
		else
			if dice == nil then
				rolldice('yellow', math.random(1,10))
			else
				rolldice('yellow', lastDiceValue)
				resetDiceParams()
			end
			if not sound1Used then
				playsounds(math.random(54,73))
				sound1Used = false
				if sound1WaitID != nil then
					Wait.stop(sound1WaitID)
				end
			end
			
			local locRoom = nil
			if locChar != nil then
				locRoom = gO(locPlayerRooms[locPCol])
			else
				locRoom = getTaggedObjAtPos('room', rayOrigin, 0)
			end
			
			if insiderEnable and insiderStoryGUID != '' and locRoom != nil then
				insiderSequelMoveCheck(locRoom, locPCol, locCautiousMove)
			end
			
			local locRoomGUID = '0'
			if locRoom != nil then
				locRoomGUID = locRoom.getGUID()
				if locRoom.getRotation().z > 160 and locRoom.getRotation().z < 200 then
					locRoom.setRotation({0,180,0})
					locRoom.setPosition(locRoom.getPosition() + Vector(0,-0.16,0))
				end
			end
			
			local corridorTag = 'corridor4'
			local deadlyTag = 'deadly4'
			local locNoiseRolled = not locUseSangrevores or playerMoveStartRoomGUID == nil or playerMoveStartRoomGUID == locRoomGUID or shootingState != 0
			
			if locNoiseRolled then
				
				locNoiseMsg = locNoiseMsg.. yellowOne
				broadcastToAll(locNoiseMsg,{0.992,0.796,0.29})	
				if yellowOneroll == 1 then
					corridorTag = 'corridor1'
					deadlyTag = 'deadly1'
				
				elseif yellowOneroll == 2 or yellowOneroll == 3 then
					corridorTag = 'corridor2'
					deadlyTag = 'deadly2'

				elseif yellowOneroll == 4 or yellowOneroll == 5 then
					corridorTag = 'corridor3'
					deadlyTag = 'deadly3'

				elseif yellowOneroll > 8 then
					corridorTag = ''
					deadlyTag = ''
				end	
			end
			
			local locNoisePass = true

			if playerHasTag('mayNoiseReroll', 0, nil, locPCol) and choiceState == 2 and locNoiseRolled then
				local locHasAction = false

				for _, handCard in pairs (Player[locPCol].getHandObjects()) do
					if not handCard.hasTag('Contamination') and handCard.getGMNotes() == 'action' then
						locHasAction = true
						break
					end
				end

				if locHasAction then
					locNoisePass = false
					choiceToPlayer(locRoom.getPosition() + Vector(5,1,-2), '행동카드 한장을 버리고\n소음 주사위를 다시 굴리겠습니까 ?', 65)
					Wait.condition(function()
						if choiceState == 1 then
							Wait.stop(autoNoiseWaitID)
						else
							locNoisePass = true
						end
					end, function() return choiceState < 2 end, 999999, function() end)
				end
			else
				choiceState = 2
			end
			

			autoNoiseWaitID = Wait.condition(function()
				choiceState = 2
				if locRoom != nil then

					local roomSize = locRoom.getBounds().size *2 + Vector(0,4,0)
					if locRoom == hiddenRoom then
						roomSize = hiddenRoomDesiredSize*2 + Vector(0,4,0)
					end
					local locRoomPos = locRoom.getPosition()

					if locCautiousMove and not locRoom.hasTag('noSecurity') and not locRoom.hasTag('security') then
						local locSecPass = true
						
						if useXyrian then
							locSecPass = getTaggedObjAtPos('xyrian', locRoomPos, 3, tileImportedSize) == nil
						end
						
						if secureBag.getQuantity() > 0 and locSecPass then
							secureBag.takeObject({
								position = locRoomPos + Vector(tileImportedSize.x*0.4, 1, tileImportedSize.z*0.25),
								rotation = {0,180,0},
								smooth = false,
							})
						end
					end
	
					if corridorTag == '' then
						local locCanEnc = true
						if locChar != nil then
							if explore then
								locCanEnc = not playerHasTag('NoExploreEncounter', 0, locCharGUID, nil)
							else
								locCanEnc = not playerHasTag('NoNoiseEncounter', 0, locCharGUID, nil)
							end
						end
						
						if not locCanEnc then
							broadcastToAll('플레이어의 위험 소음 주사위가 무시됩니다.', {1,1,1})
						else
							encounter(locRoom, locPCol)
							encounterTime = 1.25
							encounterTimeTickDown()
						end
					else

						local locCanNoiseCor = true
						if locChar != nil then
							locCanNoiseCor = not playerHasTag('NoNoiseCorridor', 0, locCharGUID, nil)
						end
						
						if not locCanNoiseCor and locNoiseRolled then
							broadcastToAll('플레이어의 복도 소음 주사위가 무시됩니다.', {1,1,1})
						else
							local i = 0
							local locEncounterTiles = {}
							local locMovingIntruders = {}
							
							-- local locAllDoors = {}
							-- local locDoors = {}

							-- for _, obj in pairs (getAllObjects()) do
								-- if #locAllDoors == (14-#doorBag) then
									-- break
								-- end
								
								-- if obj.getDescription() == 'door' then
									-- table.insert(locAllDoors, obj)
									-- if distanceMath(obj.getPosition(), locRoom.getPosition()) < tileImportedSize.x then
										-- table.insert(locDoors, obj)
									-- end
								-- end
							-- end

							local locPassCorridor = nil
							local locStartRoomPos = nil
							
							if not locNoiseRolled then
								locStartRoomPos = gO(playerMoveStartRoomGUID).getPosition()
							end
							
							for _, entry2 in pairs(shapeCast(locRoomPos, roomSize)) do

								if entry2.hasTag('Corridors') then
									local locCorridor = entry2
									local locRforced = locCorridor.getRotation().z

									locRforced = locRforced > 170 and locRforced < 190 and locNoiseRolled
									
									if (locCorridor.hasTag(corridorTag)
									or (locCorridor.hasTag(deadlyTag) and deadlyMode)
									or not locNoiseRolled)
									and not locRforced then
									
										local locPass = true
										

										if not locNoiseRolled then
											if dotMath(normalizeMath(locRoomPos - locCorridor.getPosition()), normalizeMath(locCorridor.getPosition() - locStartRoomPos)) > 0.95 
											and distanceMath(locStartRoomPos, locRoomPos) < (tileImportedSize.x + corridorImportedSize.x)*1.1
											then
												locPass = false
												locPassCorridor = locCorridor
												playerMoveStartRoomGUID = nil
											end
											
											-- for _, roomGUID in pairs(RoomsMap[locGUID][2]) do --RoomsMap is faulty... and we knew it.
												-- if roomGUID == playerMoveStartRoomGUID then
													-- locPass = false
													-- locPassCorridor = gO(locGUID)
													-- playerMoveStartRoomGUID = nil
													-- break
												-- end
											-- end
										end

										if locPass then
											local corSize = locCorridor.getBounds().size *Vector(0.9,1,0.6) + Vector(0,9,0)
											
											local locNoise = false
											local locShadows = {}
											local locCorCrowd = 0
											
											local locBiggestIntruder = nil
											local locBiggest = 0
											local locDoor = nil
											for _, locAdd in pairs(shapeCast(locCorridor.getPosition(), corSize*Vector(1.1,1,0.95), locCorridor.getRotation())) do
												if locAdd.getName() == 'Noise' then
													if locNoiseRolled and not locNoise then
														locAdd.destruct()
														table.insert(locEncounterTiles, locCorridor)
														locNoise = true
														if not locUseSangrevores then
															break
														end
													else
														table.insert(locShadows, locAdd)
														locCorCrowd = locCorCrowd + 1
													end

												elseif locAdd.hasTag('intruder') then
													local locAddDistance = distanceMath(locAdd.getPosition(), locCorridor.getPosition())
													
													if locAddDistance < (corridorImportedSize.x * 0.5) then
														local locNotes = locAdd.getGMNotes()
														if not locNoiseRolled then
															if locNotes == 'queen' then
																locCorCrowd = locCorCrowd + 4
															else
																locCorCrowd = locCorCrowd + 1
															end
															
														else
															if intruderSizeOrder[lifeforms][locNotes] > locBiggest then
																locBiggest = intruderSizeOrder[lifeforms][locNotes]
																locBiggestIntruder = locAdd
															end
														end
													end

												elseif locAdd.getDescription() == 'door' and locNoiseRolled then
													local locCorToDoor = locAdd.getPosition()-locCorridor.getPosition()
													local locCorToRoom = locRoom.getPosition()-locCorridor.getPosition()
													if dotMath(locCorToDoor, locCorToRoom) > 0 then
														locDoor = locAdd
													end
												end
											end
											
											-- for _, door in pairs (locDoors) do
												-- local locCorToDoor = locAdd.getPosition()-locCorridor.getPosition()
												-- local locCorToRoom = locRoom.getPosition()-locCorridor.getPosition()
												-- if dotMath(locCorToDoor, locCorToRoom) > 0 then
													-- locDoor = door
													-- break
												-- end
											-- end

											if locUseSangrevores then
												if #locShadows == 3 then
													locNoise = true
													for _, shadowMarker in pairs (locShadows) do
														shadowMarker.setPosition({50,0,0})
														shadowMarker.destruct()
													end
													
													if breederFBag.getQuantity() > 0 then
														breederFBag.takeObject({
															position = findSpaceOnTile(locCorridor,nil, true),
															rotation = {0,0,0},
															callback_function = function(o) o.setLock(true) end,
														})
													end
												end
											end
											
											if not locNoise and locBiggestIntruder == nil then

												local locPos = {0,0,0}
												local locRot = {0,180,0}
												
												if locUseSangrevores then
													locPos = findSpaceOnTile(locCorridor, nil, true)
													locRot = {0,0,0}
												else
													locPos = locCorridor.getPosition() + Vector(0,1,0)
												end
												
												if locCorCrowd < 6 then
													noiseBag.takeObject({
														position = locPos,
														rotation = locRot,
														smooth = false,
													})
												end

											elseif locBiggestIntruder != nil and locDoor != nil then
												if (locBiggestIntruder.getGMNotes() != 'breeder' and lifeforms == 'Neoflesh') or lifeforms != 'Neoflesh' then
													locDoor.setState(2)
												end

											elseif locBiggestIntruder != nil then
												if (locBiggestIntruder.getGMNotes() != 'breeder' and lifeforms == 'Neoflesh') or lifeforms != 'Neoflesh' then
													table.insert(locMovingIntruders, locBiggestIntruder)
													i = i+1
													encounterTime = encounterTime + 1.25
													encounterTimeTickDown()
													
													Wait.time(function()
														locMovingIntruders[1].setPositionSmooth(findSpaceOnTile(locRoom,nil,true, locMovingIntruders[1]),false,true)
														if locMovingIntruders[1].hasTag('rot180') then
															locMovingIntruders[1].setRotation({0,180,0})
														end
														
														walksounds(locMovingIntruders[1])
														
														checkSecureRoom(locRoom, locMovingIntruders[1], locPCol)
														table.remove(locMovingIntruders, 1)
														
														
													
													end, 0.5*i )
												end
											end
										end
									end
								end
							end
							
							playerMoveStartRoomGUID = nil
							
							if locEncounterTiles[1] != nil then
								local j = 0
								local locEncParams = {}
								for _, EncTile in pairs(locEncounterTiles) do
									table.insert(locEncParams, {EncTile})
									j = j+1
								end
								encounterTime = j*1.25
								encounterTimeTickDown()
								
								encounterSequence(locEncParams)
							end
							
							if locUseSangrevores and locPassCorridor != nil and not locCautiousMove then
								local locPassShadows = {}
								locPassShadows = getTaggedObjAtPos('Noise', locPassCorridor.getPosition(), 1, locPassCorridor.getBounds().size *Vector(0.9,1,0.6) + Vector(0,9,0), locPassCorridor.getRotation(), true)
								
								if locPassShadows[1] != nil then
									local locPassShadowAmount = #locPassShadows
									if locPassShadowAmount > 0 then
										if autoEventEnable then
											for _, shadow in pairs (locPassShadows) do
												shadow.setPosition({50,0,0})
												shadow.destruct()
											end
											
											Wait.time(function()
												shadowBag.takeObject({
													position = shadowBag.getPosition() + Vector(0, 3, 4),
													rotation = {0,180,0},
													callback_function = function (o) o.setLock(true) autoShadow(o, locPassShadowAmount, locPassCorridor, locRoom, locPCol) end,
												})
											end,0.5)
											

										else
											broadcastToAll('그림자 카드를 해결하고 그림자 마커를 제거하세요.', lifeformColor)
										end
									end
								end
							end
						end
					end
				end
			end, function() return locNoisePass end, 999999, function() end)
		end
	else
		table.insert(queueAutoNoiseParams, {rayOrigin, hoverObj, explore})
		if #queueAutoNoiseParams == 1 then
			queueAutoNoise()
		end
	end
end

function insiderSequelMoveCheck(roomTile, pColor, cautiousMove, previousRoomPos)
	if not scriptEnabled then
		return true
	end
	
	local locInsiderStory = gO(insiderStoryGUID)
	if locInsiderStory != nil then
		local locInsiderStoryDesc = locInsiderStory.getDescription()
		local locChapter = string.find(locInsiderStoryDesc, 'm')  --m for move
		
		if locChapter != nil then
			local locSequelPass = true
			
			if locInsiderStory.hasTag('insiderSequelMoveWithInsider') then
				if insiderFig != nil then
					local locInsiderRoom = getTaggedObjAtPos('room', insiderFig.getPosition(), 0)
					if locInsiderRoom != nil then
						locSequelPass = locInsiderRoom == roomTile
					end
				else
					locSequelPass = false
				end
			elseif locInsiderStory.hasTag('insiderSequelMoveEscapeShuttle') then
				locSequelPass = roomTile.getName() == 'ESCAPE SHUTTLE'
			end
			
			if locSequelPass then
				if string.len(locChapter) > 1 then
					locChapter = tonumber(string.sub(locChapter,1,1))
				end
				
				locChapter = string.sub(locInsiderStoryDesc, locChapter+1, locChapter+2)
				
				for _, storyCard in pairs (insiderDeck.getObjects()) do
					if storyCard.gm_notes == locChapter then
						insiderDeck.takeObject({
							position = insiderDeck.getPosition() + Vector(0,4,4),
							guid = storyCard.guid,
							callback_function = function(o2)
									local locNewDesc = string.gsub(locInsiderStoryDesc, 'm'.. locChapter,'')
									locInsiderStory.setDescription(string.sub(locNewDesc,1,string.len(locNewDesc)))
									insiderSequel(o2, roomTile, pColor, cautiousMove, previousRoomPos)
								end,
						})
						break
					end
				end
			end
		end
	end
end

function autoShadow(shadowCard, shadowAmount, corridorTile, roomTile, pColor, explore)
	if not scriptEnabled then
		return true
	end
	
	local locCorridors = {}
	local locNoises = {}
	local locIntruders = {}
	local locPlaceGhouls = 0
	local locWait = 0
	
	local locExplore = false
	
	if explore != nil then
		locExplore = explore
	end
	
	for _, tag in pairs(shadowCard.getTags()) do
		if tag == 'shadowDiscardAOxy' then
			broadcastToAll('플레이어 ' .. pColor .. '는 액션 카드 하나를 버리거나 산소 1을 소비해야 합니다.', lifeformColor)
		elseif tag == 'shadowDoor' then
			broadcastToAll('플레이어 ' .. pColor .. '는 시설의 문 1개를 열거나 닫아야 합니다.', lifeformColor)
		elseif tag == 'shadowDraw' then
			if pColor != 'insider' then
				playerDrawActions(pColor, 1)
			end
		elseif tag == 'shadowEnc' then
			if locExplore then
				if not playerHasTag('NoExploreEncounter', 0, nil, pColor) then
					Wait.condition(function()
						encounter(roomTile, pColor)	
					end, function() return choiceState == 2 end, 999999, function() end)
				end
			else
				encounter(roomTile, pColor)	
			end
			
			locWait = locWait + 0.5
			
		elseif tag == 'shadowGainTactical' then
			broadcastToAll('플레이어 ' .. pColor .. '는 전술 장비 토큰 1개를 얻을 수 있습니다.', lifeformColor)
		elseif tag == 'shadowHit' then
			broadcastToAll('플레이어 ' .. pColor .. '는 인접한 각 복도에 타격 1회를 가할 수 있습니다.', lifeformColor)
		elseif tag == 'shadowLoseItemHealth' then
			broadcastToAll('플레이어 ' .. pColor .. '는 아이템 1개를 버리거나 체력 1을 잃어야 합니다.', lifeformColor)
		elseif tag == 'shadowNewWave' then
			for _, obj in pairs (getAllObjects()) do
				if obj.hasTag('Corridors') then
					table.insert(locCorridors, obj)
				elseif obj.getName() == 'Noise' then
					table.insert(locNoises, obj)
				elseif obj.hasTag('intruder') then
					table.insert(locIntruders, obj)
				end
			end
		end
		
		if shadowAmount == 1 then
			if tag == 'shadow1NGhoulsCor1' then
				locPlaceGhouls = 1
			elseif tag == 'shadow1NGhoulsCor2' then
				locPlaceGhouls = 2
			elseif tag == 'shadow1NGhoulsCor3' then
				locPlaceGhouls = 3
			elseif tag == 'shadow1NHealth' then
				loseHealth(pColor)
			end
			
		elseif shadowAmount == 2 then
			if tag == 'shadow2NBagDev' then
				bagDevelopment()
			elseif tag == 'shadow2NEnc' then
				if locExplore then
					if not playerHasTag('NoExploreEncounter', 0, nil, pColor) then
						Wait.condition(function()
							encounter(roomTile, pColor)	
						end, function() return choiceState == 2 end, 999999, function() end)
					end
				else
					encounter(roomTile, pColor)	
				end
				
				locWait = locWait + 0.5
				
			elseif tag == 'shadow2NGhoulsCor1' then
				locPlaceGhouls = 1
			elseif tag == 'shadow2NGhoulsCor2' then
				locPlaceGhouls = 2
			elseif tag == 'shadow2NGhoulsCor4' then
				locPlaceGhouls = 4
			end
			
		elseif shadowAmount == 3 then
			if tag == 'shadow3NBagDev' then
				Wait.condition(function() --je l'ai laissé mais je trouve ça con, je crois que Michel était fatigué et qu'il a cru que shadow2NBagDev se lancerait aussi.
					bagDevelopment()
				end, function() return choiceState == 2 end, 999999, function() end)
				
			elseif tag == 'shadow3NEnc' then
				if locExplore then
					if not playerHasTag('NoExploreEncounter', 0, nil, pColor) then
						Wait.condition(function()
							encounter(roomTile, pColor)	
						end, function() return choiceState == 2 end, 999999, function() end)
					end
				else
					encounter(roomTile, pColor)	
				end
				
				locWait = locWait + 0.5

			elseif tag == 'shadow3NGhoulsCor2' then
				locPlaceGhouls = 2
			elseif tag == 'shadow3NGhoulsCor3' then
				locPlaceGhouls = 3
			elseif tag == 'shadow3NGhoulsCor4' then
				locPlaceGhouls = 4
			elseif tag == 'shadow3NGhoulsCor5' then
				locPlaceGhouls = 5
			elseif tag == 'shadow3NGhoulsCor6' then
				locPlaceGhouls = 6
			elseif tag == 'shadow3NInfection' then
				addContamination(pColor)
				broadcastToAll('플레이어 ' .. pColor .. '가 감염 1을 얻었습니다.', lifeformColor)
			elseif tag == 'shadow3NSeriousWound' then
				seriouswoundDeck.deal(1, pColor)
				broadcastToAll('플레이어 ' .. pColor .. '가 심각한 부상 1을 입었습니다.', lifeformColor)
			end
		end
	end
	
	
	if locPlaceGhouls > 0 then
		local locCorFigures = {}
		locCorFigures = getTaggedObjAtPos('healthCount', corridorTile.getPosition(), 0, corridorImportedSize, corridorTile.getRotation(), true)
		
		local locCorSpaceAvailable = 6
		for _, corIntruder in pairs(locCorFigures) do
			if distanceMath(corIntruder.getPosition(), corridorTile.getPosition()) < corridorImportedSize.x*0.5 then
				if corIntruder.getGMNotes() == 'queen' then
					locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 4)
				else
					locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 1)
				end
			end
		end
		
		locPlaceGhouls = math.min(locCorSpaceAvailable, locPlaceGhouls)
		
		local w = locWait
		for i = 1, locPlaceGhouls do
			if adultFBag.getQuantity() > 0 then
				adultFBag.takeObject({
					position = adultFBag.getPosition() + Vector(0,6,0),
					callback_function = function(o)
						o.setLock(true)

						Wait.time(function()
							o.setPositionSmooth(findSpaceOnTile(corridorTile,nil, true), false, true)
						end, w + (i-1)*0.25)
					end,
				})
			end
		end
		locWait = locWait + locPlaceGhouls*0.4
	end
	
	
	if shadowCard.hasTag('shadowDelete') then
		shadowCard.setGMNotes('')
		shadowCard.setPosition(shadowBag.getPosition() + Vector(0,3,8))
		broadcastToAll('그림자 카드가 게임에서 제거되었습니다.', lifeformColor)
		shadowCard.setLock(false)
		
	elseif shadowCard.hasTag('shadowReshuffle') then
		for _, obj in pairs (getAllObjects()) do
			if obj.getGMNotes() == 'shadowDiscard' and obj != shadowBag then
				obj.setPosition(shadowBag.getPosition() + Vector(0,4,0))
				obj.setRotation({0,180,180})
				for i = 1, obj.getQuantity() do
					obj.takeObject({
						position = obj.getPosition() + Vector(0,i*0.3,0),
						callback_function = function(o) shadowBag.putObject(o) end,
					})
				end
				break
			end
		end
		Wait.time(function()
			shadowCard.setLock(false)
			shadowBag.putObject(shadowCard)
			shadowBag.shuffle()
			broadcastToAll('그림자 침공 카드가 뽑혔습니다. 그림자 카드를 다시 섞습니다.', lifeformColor)
		end, 2)
	
	else
		if shadowCard.hasTag('shadowNewWave') then
		
			if shadowAmount == 1 then
				for _, corridor in pairs (locCorridors) do
					local locCorPos = corridor.getPosition()
					

					if distanceMath(locCorPos, roomTile.getPosition()) < tileImportedSize.x*1.25 then 
					
						local locCorSpaceAvailable = 6
						
						for _, tbl in pairs ({locNoises, locIntruders}) do
							for _, corIntruder in pairs (tbl) do
								if distanceMath(corIntruder.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
									if corIntruder.getGMNotes() == 'queen' then
										locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 4)
									else
										locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 1)
									end
								end
							end
						end
						
						if locCorSpaceAvailable > 0 then
							for _, noiseToken in pairs (locNoises) do
								if noiseToken != nil then
									if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
										local w = locWait
										locWait = locWait + 0.25
										if adultFBag.getQuantity() > 0 then
											adultFBag.takeObject({
												position = adultFBag.getPosition() + Vector(0,6,0),
												callback_function = function(o)
													o.setLock(true)
													Wait.time(function()
														o.setPositionSmooth(findSpaceOnTile(corridor,nil, true), false, true)
													end, w)
												end,
											})
										end
										break
									end
								end
							end
						end
					end
				end
					
					
			elseif shadowAmount == 2 then
				local locSections = {}
				local locPassCorPosX = corridorTile.getPosition().x
				
				if locPassCorPosX < -4.5 then
					table.insert(locSections, {-20,-4.5})
				end
				
				if locPassCorPosX > 4.5 then
					table.insert(locSections, {4.5,20})
				end
				
				if locPassCorPosX > -6 and locPassCorPosX < 6 then
					table.insert(locSections, {-6,6})
				end
				
				for _, sectionInterval in pairs (locSections) do
					for _, corridor in pairs (locCorridors) do
						local locCorPos = corridor.getPosition()
						if locCorPos.x > sectionInterval[1] and locCorPos.x < sectionInterval[2] then
						
							local locCorSpaceAvailable = 6
							
							for _, tbl in pairs ({locNoises, locIntruders}) do
								for _, corIntruder in pairs (tbl) do
									if distanceMath(corIntruder.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
										if corIntruder.getGMNotes() == 'queen' then
											locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 4)
										else
											locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 1)
										end
									end
								end
							end
							
							if locCorSpaceAvailable > 0 then
								for _, noiseToken in pairs (locNoises) do
									if noiseToken != nil then
										if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x * 0.5 then
											local w = locWait
											locWait = locWait + 0.25
											if adultFBag.getQuantity() > 0 then
												adultFBag.takeObject({
													position = adultFBag.getPosition() + Vector(0,6,0),
													callback_function = function(o)
														o.setLock(true)
														Wait.time(function()
															o.setPositionSmooth(findSpaceOnTile(corridor,nil, true, o), false, true)
														end, w)
													end,
												})
											end
											break
										end
									end
								end
							end
						end
					end
				end
			
			
			elseif shadowAmount == 3 then
			
				for _, corridor in pairs (locCorridors) do
					local locCorPos = corridor.getPosition()
					for _, noiseToken in pairs(locNoises) do
						if noiseToken != nil then
						
							local locCorSpaceAvailable = 6
							
							for _, tbl in pairs ({locNoises, locIntruders}) do
								for _, corIntruder in pairs (tbl) do
									if distanceMath(corIntruder.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
										if corIntruder.getGMNotes() == 'queen' then
											locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 4)
										else
											locCorSpaceAvailable = math.max(0,locCorSpaceAvailable - 1)
										end
									end
								end
							end
							
							if locCorSpaceAvailable > 0 then
						
								if distanceMath(locCorPos, noiseToken.getPosition()) < corridorImportedSize.x * 0.5 then
									local w = locWait
									locWait = locWait + 0.25
									if adultFBag.getQuantity() > 0 then
										adultFBag.takeObject({
											position = adultFBag.getPosition() + Vector(0,6,0),
											callback_function = function(o)
												o.setLock(true)
												Wait.time(function()
													o.setPositionSmooth(findSpaceOnTile(corridor,nil, true), false, true)
												end, w)
											end,
										})
									end
									break
								end
							end
						end
					end
				end
			end
		end
		Wait.time(function()
			shadowCard.setLock(false)
		end, locWait + 1)
	end
end

function intruderTokenReturn(obj)
	if not scriptEnabled then
		return true
	end
	
	local locGM = obj.getGMNotes()
	if locGM == 'larvaeToken' then
		larvaeBag.putObject(obj)
	elseif locGM == 'creeperToken' then
		creeperBag.putObject(obj)
	elseif locGM == 'adultToken' then
		adultBag.putObject(obj)
	elseif locGM == 'breederToken' then
		breederBag.putObject(obj)
	elseif locGM == 'queenToken' then
		queenBag.putObject(obj)
	elseif locGM == 'ironcladToken' or locGM == 'firespitterToken' or locGM == 'slasherToken' or locGM == 'crawlmineToken' then
		adultBag.putObject(obj)
	end
end

function moveBodyTokens()
	if not scriptEnabled then
		return true
	end
	
	local locBodyFound = false
	for _, locObj in pairs(shapeCast(turnMarker.getPosition() - Vector(0,0,6), {0.5,9,12})) do
		
		if locObj.getName() == 'bodyToken' then
			local locPos = locObj.getPosition() + turnOffset + Vector(0,2,0)
			if getTaggedObjAtPos('turnMarker', locPos, 1) != nil then
				absorbBody(locObj)
			else
				locObj.setPosition(locPos)
			end
			locBodyFound = true
		end
	end
	
	if locBodyFound then
		broadcastToAll('트위칠링이 마더브레인에게 유해를 가져가고 있습니다. 모든 시신 토큰이 한 칸씩 위로 이동합니다!', lifeformColor)
	end

end

function absorbBody(obj)
	if not scriptEnabled then
		return true
	end
	
	obj.destruct()
	queenBag.takeObject({
		position = intruderBag.getPosition() + Vector(0,2,0)
	})
	broadcastToAll('마더브레인이 시신을 흡수했습니다. 마더브레인 토큰이 주머니에 추가되었습니다.', lifeformColor)
end

function enemyFigReturn(obj)
	if not scriptEnabled or obj == nil then
		return true
	end
	
	local locGM = obj.getGMNotes()
	local locB = nil
	
	if obj.hasTag('noShoot') then
		obj.removeTag('noShoot')
	end
	
	if locGM == 'larvae' then
		
		if lifeforms == 'Neoflesh' then
			local locPos = obj.getPosition()
			
			local locTiles = shapeCast(locPos)
			local moveBody = true
			for _, locTile in pairs(locTiles) do
				for _, tag in pairs(locTile.getTags()) do
					if tag == 'room' then
						moveBody = false
					elseif tag == 'Corridors' then
						moveBody = false
					elseif tag == 'CharacterTile' then
						moveBody = false
					end
					
					if not moveBody then
						break
					end
				end
				if not moveBody then
					break
				end
			end
			if moveBody then
				moveBodyTokens()
			end
		end
		locB = larvaeFBag
	elseif locGM == 'creeper' then
		if lifeforms == 'Carnomorph' then
			locB = creeperFBag
		else
		
		end
	elseif locGM == 'adult' or locGM == 'slasher' then
		locB = adultFBag
	elseif locGM == 'noise' then
		obj.destruct()
	elseif locGM == 'breeder' then
		if lifeforms == 'Neoflesh' then
			locB = cultistDeadBag
			broadcastToAll('광신도가 제거되었습니다. 처치자는 네오플레시 컬트 스킬 카드 하나를 뒤집을 수 있습니다.', lifeformColor)
		else
			locB = breederFBag
		end
	elseif locGM == 'queen' then
		locB = queenFBag
	elseif locGM == 'xyrian' then
		locB = xyrianFBag
	elseif locGM == 'crawlmine' then
		locB = crawlmineFBag
	elseif locGM == 'ironclad' then
		locB = ironcladFBag
	elseif locGM == 'firespitter' then
		locB = firespitterFBag
	elseif locGM == 'carcass' then
		obj.destruct()
	end
	
	if locB != nil then
		obj.setLock(false)
		obj.addTag('returning')
		
		locB.putObject(obj)
	end	
end

function rotateVectorAboutY(a, Deg)
	if not scriptEnabled then
		return true
	end
	
	local d = Deg/57.295779513 --Hmmm... smells like flawed math...
	
	local c = math.cos(d) --cos(90) = 0
	local s = math.sin(d) --sin(90) = 1
	local result = Vector(a[1] * c + a[3] * s,  a[2],  -a[1] * s + a[3] * c)
	--(0+0 ,a.y, -1+0)
	
	return result
	
end

function dotMath(a,b)
	if not scriptEnabled then
		return true
	end
	
	local v = Vector(a[1] * b[1], a[2] * b[2], a[3] * b[3])
	return (v[1] + v[2] + v[3])
end

function normalizeMath(vec)
	if not scriptEnabled then
		return true
	end
	
	local d = math.sqrt(dotMath(vec,vec))
	return Vector(vec[1]/d, vec[2]/d, vec[3]/d)
end


function shapeCast(pos, size, rot, shape)
	if not scriptEnabled then
		return true
	end
	
	local b =  {0.5,9,0.5}
	if size != nil then
		b = {size[1], size[2] + 9, size[3]}
	end
	
	local locRot = {0,0,0}
	if rot != nil then
		locRot = rot
	end
	
	local t = 3
	
	if shape != nil then
		t = shape
	end
	
	local locHits = 	Physics.cast({
							origin = pos,
							direction = {0,1,0},
							type = t,
							size = b,
							orientation = locRot,
							max_distance = 0.2,
							--debug = true,
						})
						
	local locObjs = {}
	
	for _, entry in pairs(locHits) do
		if entry.hit_object != boarderTile then
			table.insert(locObjs, entry.hit_object)
		end
	end
	
	return locObjs
end

function getTaggedObjAtPos(stringText, pos, stringType, boxVector, rotation, all)
	if not scriptEnabled then
		return true
	end
	
	local locObjs = {}
	local locAll = false
	
	if all != nil then
		locAll = all
	end
	
	local locRot = {0,0,0}
	
	if rotation != nil then
		locRot = rotation
	end
	
	local locVec = {0.5,30,0.5}
	
	if boxVector != nil then
		locVec = boxVector
	end
	
	for _, locObj in pairs (shapeCast(pos, locVec, locRot)) do
		if stringType == 0 then
			if locObj.hasTag(stringText) then
				if locAll then
					table.insert(locObjs, locObj)
				else
					return locObj
				end
			end
		elseif stringType == 1 then
			if locObj.getName() == stringText then
				if locAll then
					table.insert(locObjs, locObj)
				else
					return locObj
				end
			end
		elseif stringType == 2 then
			if locObj.getDescription() == stringText then
				if locAll then
					table.insert(locObjs, locObj)
				else
					return locObj
				end
			end
		elseif stringType == 3 then
			if locObj.getGMNotes() == stringText then
				if locAll then
					table.insert(locObjs, locObj)
				else
					return locObj
				end
			end
		end
	end
	
	if locAll then	
		return locObjs
	end

end

function getCorridorAtPlayer(pColor)
	if not scriptEnabled then
		return true
	end
	
	return getTaggedObjAtPos('Corridors', gO(playerInfoTable[pColor].figureGUID).getPosition(), 0)
end

function getRoomAtPlayer(pColor)
	if not scriptEnabled then
		return true
	end
	
	return getTaggedObjAtPos('room', gO(playerInfoTable[pColor].figureGUID).getPosition(), 0)
end

function findSpaceOnTile(tileObj, objSize, invert, object)
	if not scriptEnabled then
		return true
	end
	
	local ImportedSize = tileImportedSize *0.7563
	if tileObj.hasTag('Corridors') then
		ImportedSize = corridorImportedSize * Vector(0.632666,1,0.630252)
	end
	
	local tileBounds = ImportedSize * tileObj.getScale()
	
	if tileObj == hiddenRoom then
		tileBounds = hiddenRoomDesiredSize
	end
	
	local locFigSize = standeeSize
	
	if objSize != nil then
		locFigSize = objSize
	end
	
	local objBounds = Vector(locFigSize, 4, locFigSize)
	
	local locInv = false
	
	if invert != nil then
		locInv = invert
	end

	local hitlist
	local foundSpace = false
	
	local locTileRot = tileObj.getRotation()
	


	local limX = 3
	local limZ = 2
	local locMax = limX * limZ
	
	if object != nil and tileObj.hasTag('room') then
		locMax = locMax * 5
	end
	
	local locPos2 = Vector(0,0,0)
	local locDeg = locTileRot.y
	
	local locDot = 0
	local locFirstXOffset = 0.915
	local locFirstZOffset = 7
	
	local locXFix = 0.06321
	
	if tileObj.hasTag('room') then
		locDot = 2
		locFirstXOffset = 1
		locDeg = 0
	else
		if (locDeg < 10 or locDeg > 350)
		or (locDeg < 190 and locDeg > 170)
		then
			locDot = 1.5
		else
			locXFix = 0
			locFirstXOffset = 1.2
			locFirstZOffset = 4.5
		end
		--locDot = math.max(0,dotMath(rotateVectorAboutY(Vector(1,0,0),locDeg), Vector(1,0,0)))
	end
	
	
	
	
	local tilePos = tileObj.getPosition()
	
	if locTileRot.z > 170 and locTileRot.z < 190 then
		tilePos = tilePos + Vector(0,-0.16,0)
	end

	local i = 1
	
	if locInv then
		i = 4
	end
	
	for j = 1, locMax do
		locPos2 =	Vector(tileBounds.x /(limX * locFirstXOffset), 0,tileBounds.z/locFirstZOffset)	--First position
					+ Vector (tileBounds.x * ((i+limX-1)%limX) / limX, math.floor(j/7)*4, tileBounds.z * (((i+5)/limX)%limZ) / limZ ) --Step
					-- 3%3 / 3 = 0						,0, (6/3)%2 / 4 = 0/4
					-- 4%3 / 3 = 1/3					,0, (7/3)%2 / 4 = 0/4
					-- 5%3 / 3 = 2/3					,0,	(8/3)%2 / 4 = 0/4
					-- 6%3 / 3 = 0						,0, (9/3)%2 / 4 = 1/4
					-- 7%3 / 3 = 1/3					,0, (10/3)%2 / 4 = 1/4
					-- 8%3 / 3 = 2/3					,0,	(11/3)%2 / 4 = 1/4
					+ Vector(tileBounds.x * (-0.25) * math.floor(i/4) - math.max(0,(i%3)-1) *locXFix * tileBounds.x, --My rotation may be flawed so the X and Zoffsets become diagonals that I have to correct...
					0, -0.3 + 0.3 * locDot * math.max(0,(i%3)-1)) -- Z Offset for picture collision
					- Vector(tileBounds.x/2,0,tileBounds.z/2) 	--Offset to the edge
					+ Vector(0,0.45,0) --Margin for hibernatorium hidden rooms
					
		locPos2 = tilePos + rotateVectorAboutY(locPos2,locDeg+25)
		
		local locActualHit = false
		for _, hitObj in pairs(shapeCast(locPos2, objBounds, nil, 2)) do
			
			if not hitObj.hasTag('boardEdge')
			and not hitObj.hasTag('room')
			and not hitObj.hasTag('Corridors')
			and hitObj.getPosition() != Vector(0,-9,0)
			then
				if distanceMath(locPos2, hitObj.getPosition()) < locFigSize then
					locActualHit = true
					break
				end
			end
		end
		
		if not locActualHit then
			foundSpace = true
			
			if object != nil then
				object.setLock(true)
				-- if j >= 7 then
					-- object.setLock(true)
				-- else
					-- if not (lifeforms == 'Sangrevores' and object.getGMNotes() == 'queen') then
						-- object.setLock(false)
					-- end
				-- end
			end
			
			
			break
		end
		i = 1+i%6
		
		if locMax == (limX * limZ * 4) then 
			break --No idea why... but somehow putting a higher multiplier into locMax results in better placement in the upper enemy floors even though it has nothing to do with it....?
		end
	end
	
	if not foundSpace then
		locPos2	 = tileObj.getPosition() + Vector(0,5,0)
	end
	
	if tileObj == hiddenRoom then
		locPos2.y = 1.68
	end
	
	if trapCheck then
		if object != nil then
			if object.hasTag('healthCount') and tileObj.hasTag('room') and not object.hasTag('trapped') then
				for _, trap in pairs (trapsList) do
					if trap != nil then
						if trap.getRotation().z < 20 or trap.getRotation().z > 340 then
							if distanceMath(trap.getPosition(), tilePos) < returnRoomDiameter(tileObj) then
								object.call("onClick")
								object.addTag('trapped')
								trap.flip()
								
								Wait.time(function()
									trap.setLock(true)
									trap.setPosition(object.getPosition())
									trap.setScale({0.8,1,0.8})
								end, 0.25)
								break
							end
						end
					end
				end
			end
		end
	end
	
	return locPos2
end

function isQueenAlive()
	if not scriptEnabled then
		return true
	end
	
	local locCastPos = {0,0,0}
	for _, SnapP in pairs(boarderTile.getSnapPoints()) do
		if SnapP.tags[1] == 'queenHealth' then
			locCastPos = boarderTile.getPosition() + rotateVectorAboutY(SnapP.position,boarderTile.getRotation().y)*boarderTile.getScale()
			break
		end
	end
	
	return (getTaggedObjAtPos('queenHealth', locCastPos, 0) != nil)
end

function activateQueen()
	if not scriptEnabled then
		return true
	end
	
	local locQueenName = '여왕'
	if lifeforms == 'Neoflesh' then
		locQueenName = '마더브레인'
	elseif lifeforms == 'Sangrevores' then
		locQueenName = '킹'
	elseif lifeforms == 'Carnomorph' then
		locQueenName = '슬래셔'
	end
	
	
						
	local locQueen = gO(queenFigGUID)
	local locQueenTile = getTaggedObjAtPos('Corridors', locQueen.getPosition(), 0, {0.1,30,0.1})
	local locAttacked = false
	
	if locQueenTile == nil then
		locQueenTile = getTaggedObjAtPos('room', locQueen.getPosition(), 0, {0.1,30,0.1})
		if locQueenTile == nil then --if multiple encounters happen in a row both placing and activating the queen too fast.
			Wait.time(function()
				activateQueen()
			end,1)
			return true
		end
		
		local locQueenTileGUID = locQueenTile.getGUID()
		local locPlayerRooms = getPlayerRoomsInFirstTurnOrder(true)
		for color, playerRoomGUID in pairs (locPlayerRooms) do
			if locQueenTileGUID == playerRoomGUID then
				intruderAttack(locQueenTile, locQueen, color)
				locAttacked = true
				break
			end
		end
		
		if lifeforms == 'Carnomorph' and locAttacked then
			
			local locMeats = getTaggedObjAtPos('meat',locQueenTile.getPosition(), 0, tileImportedSize, {0,0,0}, true)
			
			for _, color in pairs (getPlayerColorsInFirstTurnOrder(true)) do
				local locChar = gO(playerInfoTable[color].figureGUID)
				
				if locChar != nil then
					if locChar.getRotation().z > 140 and locChar.getRotation().z < 230 then
						table.insert(locMeats, locChar)
					end
				end
			end
			
			local locBestMeat = nil
			if #locMeats > 0 then
				
				for _, meat in pairs (locMeats) do
					if meat != nil then
						if meat.hasTag('characterFig') then
							locBestMeat = meat
							break
						elseif meat.getGMNotes() == 'carcass' then
							locBestMeat = meat
						elseif meat.hasTag('intruder') then
							if locBestMeat == nil then
								locBestMeat = meat
							else
								if locBestMeat.getName() == 'Body' then
									locBestMeat = meat
								end
							end
						elseif meat.getName() == 'Body' and locBestMeat == nil then
							locBestMeat = meat
						end
					end
				end
				
				if locQueenTile.getName() == 'NEST' and nestBag.getQuantity() > 0 then
					if not locBestMeat.hasTag('characterFig') then
						locBestMeat = nil
						nestBag.takeObject({
							position = {30,3,25},
						})
					end
				end
				
				if locBestMeat != nil then
					locBestMeat.setPosition({45,-9,0})
					locBestMeat.destruct()
				end
				
				carnoFeed(locQueen)
				
			else
				if locQueenTile.getName() == 'NEST' and nestBag.getQuantity() > 0 then
					nestBag.takeObject({
						position = {30,3,25},
					})
					
					carnoFeed(locQueen)
				end
			end
		end
	end
	
	if locQueenTile != nil then
		broadcastToAll('활성화 중: '.. locQueenName..'.', lifeformColor)
	end
	
	if not locAttacked then
		if not allPassed then
			registerToRoomsMap()
		end
		autoMoveToGoal({locQueenTile}, {{locQueen}})
	end
end

function xyrianTracerReplace()
	if not scriptEnabled then
		return true
	end
	
	local locExpectedTracers = 3 - xyrianTracerBag.getQuantity()
	if locExpectedTracers > 0 and xyrianFBag.getQuantity() > 0 then
		local locTracers = {}
		for _, obj in pairs(getAllObjects()) do
			if obj.getGMNotes() == 'xyrianTracer' then
				xyrianFBag.takeObject({
					position = obj.getPosition() + Vector(0,0.5,0),
					rotation = {0,0,0},
					smooth = false,
					callback_function = function(o) o.setLock(true) end,
				})
				obj.setLock(false)
				xyrianTracerBag.putObject(obj)
				locExpectedTracers = locExpectedTracers - 1
				if locExpectedTracers == 0 or xyrianFBag.getQuantity() == 0 then
					break
				end
			end
		end
	end
end

function bagDevelopment()
	if not scriptEnabled then
		return true
	end
	
	local locPlayerRooms = getPlayerRoomsInFirstTurnOrder()
	
	intruderBag.takeObject({
		position = intruderBag.getPosition() + Vector(0,5,0),
		smooth = false,
		callback_function = function (o)

				o.setLock(true)
				o.setRotation({0,180,0})
				local locPass = true
				local locChoiceCard = nil 
				local locCharacterTile = nil
				local locXenoColor = nil
				
				for playerColor, entry in pairs (locPlayerRooms) do
					for _, card in pairs (Player[playerColor].getHandObjects()) do
						if card.hasTag('mayBagTokenIgnore') then
							locCharacterTile = getTaggedObjAtPos('CharacterTile', gO(playerInfoTable[playerColor].boardGUID).getPosition(), 0)
							locXenoColor = playerColor
							if locCharacterTile.getVar("countTissue") > 0 then
								locPass = false
								locChoiceCard = card
							end
							break
						end
					end
				end
				
				if locChoiceCard != nil then
					local locXenoChoicePos = gO(playerInfoTable[locXenoColor].figureGUID).getPosition() + Vector(5,1,-2)
					o.setPosition(locXenoChoicePos + Vector(-0.59,1.36,5.3))
					choiceToPlayer(locXenoChoicePos, xenoChoiceMsg, 60)
					Wait.condition(function()
						if choiceState == 1 then
							onObjectNumberTyped(locChoiceCard, locXenoColor, 0)
							o.setLock(false)
							intruderBag.putObject(o)
							Wait.stop(BagDevWaitID)
							locCharacterTile.setVar("countTissue", locCharacterTile.getVar("countTissue") - 1)
							locCharacterTile.call("updateDisplay")
							Wait.time(function()
								bagDevelopment()
							end, 0.3)
							
						else
							locPass = true
						end
						choiceState = 2
					end, function() return choiceState < 2 end, 999999, function() end)
				end
					
				
				
				BagDevWaitID = Wait.condition(function()
				
					local locGM = o.getGMNotes()
					o.setLock(false)
					
					if locGM == 'xyrianToken' then
						o.setPosition({42,1.53,7})
						o.setRotation({0,180,0})
						if xyrianTracerBag.getQuantity() < 3 then
							if xyrianOnBoard() then
								proceedToTracerReplace = true
							else
								xyrianTracerReplace()
							end
						end
						
					else
						
						if locGM == '' then
							if insiderEnable and insiderStoryGUID != '' then
								local locInsiderStory = gO(insiderStoryGUID)
								
								if locInsiderStory != nil then
									for _, tag in pairs (locInsiderStory.getTags()) do
										if string.find(tag, 'insiderEffectBlank') != nil then
											autoInsider(2,tag)
										end
									end
								end
							end
						end
						
						if lifeforms == 'Primebloods' then
							if locGM == '' then
						
								onObjectNumberTyped(adultBag, 'Red', 2)
								broadcastToAll('빈 토큰이 뽑혔습니다. 성체 토큰 두 개가 침입자 주머니에 추가됩니다.',lifeformColor)
								

								
							else
								local locBag = nil
								local locReturnBag = nil
								if locGM == 'larvaeToken' then
									locBag = breederBag
									locReturnBag = larvaeBag
									
								elseif locGM == 'adultToken' then
									locBag = queenBag
									
									if not isQueenAlive() then
										locBag = larvaeBag
									end
									
									locReturnBag = adultBag
									
								elseif locGM == 'breederToken' then
									locBag = queenBag
									
									if not isQueenAlive() then
										locBag = larvaeBag
									end
									
									locReturnBag = breederBag
									
								elseif locGM == 'queenToken' then
									if isQueenAlive() then
										if queenFBag.getQuantity() == 0 then
											activateQueen()
										else
											locBag = larvaeBag
										end
									else
										locBag = breederBag
									end
									locReturnBag = queenBag
								end
								
								if locBag != nil then
									for i = 1, 2 do
										if locBag.getQuantity() > 0 then
											locBag.takeObject({
												position = locBag.getPosition() + Vector(0,2+i,0),
												callback_function = function(o2) intruderBag.putObject(o2) end,
											})
										end
									end
								end
								
								
								if locReturnBag != nil then
									locReturnBag.putObject(o)
								end
								
							end
						
						elseif lifeforms == 'Neoflesh' then
							
							if locGM == '' then
								onObjectNumberTyped(adultBag, 'Red', 2)
								broadcastToAll('빈 토큰이 뽑혔습니다. 성체 토큰 두 개가 침입자 주머니에 추가됩니다.',lifeformColor)
							else
								if locGM == 'ironcladToken' or locGM == 'firespitterToken' or locGM == 'slasherToken' or locGM == 'crawlmineToken' then
									for i = 1, 2 do
										if larvaeBag.getQuantity() > 0 then
											larvaeBag.takeObject({
												position = larvaeBag.getPosition() + Vector(0,2+i,0),
												callback_function = function(o2) intruderBag.putObject(o2) end,
											})
										end
									end
									broadcastToAll('성체 토큰이 뽑혔습니다. 트위칠링 토큰 두 개가 침입자 주머니에 추가됩니다.',lifeformColor)
									adultBag.putObject(o)
								
								elseif locGM == 'larvaeToken' then
									local locStr = '모든 트위칠링을 활성화합니다.'
									if queenFBag.getQuantity() == 0 and isQueenAlive() then
											locStr = locStr .. '그리고 마더브레인도 활성화합니다.'
											activateQueen()
											Wait.time(function()
												twitchlingActivation()
											end, 1.5)
									else
									
										twitchlingActivation()
										
										if larvaeFBag.getQuantity() > 0 then
											locStr = locStr ..' 동면실에 트위칠링 1마리가 배치되었습니다.'
											larvaeFBag.takeObject({
												position = larvaeFBag.getPosition() + Vector(0,6,0),
												smooth = false,
												callback_function = function(o2)
													o2.setLock(true)
													for color, playerRoomGUID in pairs (locPlayerRooms) do
														if playerRoomGUID == hiddenRoom.getGUID() then
															checkSecureRoom(hiddenRoom, o2, color)
															break
														end
													end
													
													o2.setPositionSmooth(findSpaceOnTile(hiddenRoom, nil, true, o2), false, true)
												end,	
											})
										end
									end
										broadcastToAll(locStr, lifeformColor)
										intruderTokenReturn(o)
									
								elseif locGM == 'queenToken' then
									
									if queenFBag.getQuantity() == 0 then
										if isQueenAlive() then
											activateQueen()										
										else
											queenBag.putObject(o)
											broadcastToAll('여왕이 죽었으므로 여왕 토큰이 제거되었습니다.', lifeformColor)
										end
									else
										if isQueenAlive() then
											local locHighestRoom = getRoomHighestID(nil, false)
											queenFBag.takeObject({
												position = queenFBag.getPosition() + Vector(0,6,0),
												smooth = false,
												callback_function = function(o2)
													for color, playerRoomGUID in pairs (locPlayerRooms) do
														if playerRoomGUID == locHighestRoom.getGUID() then
															checkSecureRoom(locHighestRoom, o2, color) 
															break
														end
													end
													o2.setLock(true)
													o2.setPositionSmooth(findSpaceOnTile(locHighestRoom, nil, true, o2), false, true)
												end,	
											})
										else
											intruderTokenReturn(o)
										end
									end
								end
							end
						
						elseif lifeforms == 'Sangrevores' then
						
							if locGM == '' then
								onObjectNumberTyped(adultBag, 'Red', 2)
								broadcastToAll('빈 토큰이 뽑혔습니다. 구울 토큰 두 개가 침입자 주머니에 추가됩니다.',lifeformColor)
								
							elseif locGM == 'adultToken' then
								for i = 1, 2 do
									if breederBag.getQuantity() > 0 then
										breederBag.takeObject({
											position = breederBag.getPosition() + Vector(0,2+i,0),
											callback_function = function(o2) intruderBag.putObject(o2) end,
										})
									end
								end
								intruderTokenReturn(o)
								
							elseif locGM == 'breederToken' then
								local locBag = queenBag
								
								if not isQueenAlive() then
									locBag = adultBag
								end
								
								for i = 1, 2 do
									if locBag.getQuantity() > 0 then
										locBag.takeObject({
											position = locBag.getPosition() + Vector(0,2+i,0),
											callback_function = function(o2) intruderBag.putObject(o2) end,
										})
									end
								end
								
								bloodSpectersActivation()
								intruderTokenReturn(o)
								
							elseif locGM == 'queenToken' then
							
								if isQueenAlive() then
									if queenFBag.getQuantity() == 0 then
										activateQueen()	
									else
										local locHighestRoom = getRoomHighestID(nil, false)
										queenFBag.takeObject({
											position = queenFBag.getPosition() + Vector(0,6,0),
											callback_function = function(o2)
												for color, playerRoomGUID in pairs (locPlayerRooms) do
													if playerRoomGUID == locHighestRoom.getGUID() then
														checkSecureRoom(locHighestRoom, o2, color) 
														break
													end
												end
												
												o2.setPositionSmooth(findSpaceOnTile(locHighestRoom, nil, true, o2), false, true)
												o2.setLock(true)
												
											end,	
										})
									end
								else
									for i = 1, 2 do
										if breederBag.getQuantity() > 0 then
											breederBag.takeObject({
												position = breederBag.getPosition() + Vector(0,2+i,0),
												callback_function = function(o2) intruderBag.putObject(o2) end,
											})
										end
									end
								end
								queenBag.putObject(o)
							end
						elseif lifeforms == 'Carnomorph' then
							if locGM == '' then
								onObjectNumberTyped(creeperBag, 'Red', 3)
								broadcastToAll('빈 토큰이 뽑혔습니다. 메타고거 토큰 세 개가 침입자 주머니에 추가됩니다.',lifeformColor)
								
							elseif locGM == 'creeperToken' then
								
								local locMeats = {}
								local locRooms = {}
								local locMeatRooms = {}
								local locWait = 0
								
								countPlayers(true)
								
								for _, obj in pairs (getAllObjects()) do
									if obj.getGMNotes() == 'carcass' then
										table.insert(locMeats,obj)
									elseif obj.hasTag('room') then
										table.insert(locRooms, obj)
										if obj.getName() == 'NEST' then
											if creeperFBag.getQuantity() > 0 then
												locWait = 0.35
												creeperFBag.takeObject({
													position = creeperFBag.getPosition() + Vector(0,6,0),
													callback_function = function (o2)
														o2.setLock(true)
														o2.setPositionSmooth(findSpaceOnTile(obj, nil, true, o2), false, true)
														o2.setRotation({0,180,0})
													end,
												})
											end
										end
									end
								end
								
								
								if #locMeats > 0 then
									
									
									for _, room in pairs (locRooms) do
										
										local locRoomPos = room.getPosition()
										local locRoomDiameter = returnRoomDiameter(room)
										
										for _, meat in pairs (locMeats) do
											if distanceMath(locRoomPos, meat.getPosition()) < locRoomDiameter then
												table.insert(locMeatRooms, {room, room.getGMNotes(), meat})
												break
											end
										end
									end
									
									
									
									for i = 1, math.min(seatedPlayers,#locMeatRooms) do
										local locLowestMeatRoomTbl = {nil, 999, nil, 1}
										local locIndex = 1
										
										for _, meatRoomTbl in pairs (locMeatRooms) do
											if tonumber(meatRoomTbl[2]) < locLowestMeatRoomTbl[2] then
												locLowestMeatRoomTbl[1] = meatRoomTbl[1]
												locLowestMeatRoomTbl[2] = tonumber(meatRoomTbl[2])
												locLowestMeatRoomTbl[3] = meatRoomTbl[3]
												locLowestMeatRoomTbl[4] = locIndex
											end
											locIndex = locIndex + 1
										end
										locMeatRooms[locLowestMeatRoomTbl[4]][2] = '99'
										
										if creeperFBag.getQuantity() > 0 then
											local w = locWait
											locWait = locWait + 0.35
											
											creeperFBag.takeObject({
												position = creeperFBag.getPosition() + Vector(0,6,0),
												callback_function = function (o2)
													o2.setLock(true)
													Wait.time(function()	
														o2.setPositionSmooth(findSpaceOnTile(locLowestMeatRoomTbl[1], nil, true, o2), false, true)
														o2.setRotation({0,180,0})
													end,w)
												end,
											})
										end
									end
									
									
									
								else
									local locLowestRoom = getRoomHighestID(nil, true)
									
									for i = 1, 2 do
										if creeperFBag.getQuantity() > 0 then
											local w = locWait
											locWait = locWait + 0.35
											
											creeperFBag.takeObject({
												position = creeperFBag.getPosition() + Vector(0,6,0),
												callback_function = function(o2)
													o2.setLock(true)
													Wait.time(function()
														o2.setPositionSmooth(findSpaceOnTile(locLowestRoom, nil, true, o2), false, true)
														o2.setRotation({0,180,0})
													end,w)
												end,	
											})
										end
									end
								end
								intruderTokenReturn(o)
							else
								local locFBag = adultFBag
								if locGM == 'breederToken' then
									locFBag = breederFBag
									intruderTokenReturn(o)
									
								elseif locGM == 'queenToken' then
									locFBag = queenFBag
									
								else
									intruderTokenReturn(o)
								end
								
								if isQueenAlive() or locFBag != queenFBag then
									if locFBag.getQuantity() > 0 then
										local locHighestRoom = getRoomHighestID(nil, false)
										locFBag.takeObject({
											position = locFBag.getPosition() + Vector(0,6,0),
											callback_function = function(o2)
												for color, playerRoomGUID in pairs (locPlayerRooms) do
													if playerRoomGUID == locHighestRoom.getGUID() then
														checkSecureRoom(locHighestRoom, o2, color) 
														break
													end
												end
												
												o2.setPositionSmooth(findSpaceOnTile(locHighestRoom, nil, true, o2), false, true)
												o2.setLock(true)
												o2.setRotation({0,180,0})
												
											end,	
										})
									elseif locFBag == queenFBag then
										activateQueen()
									end
								else
									intruderTokenReturn(o)
								end
							end
						end
					end
				end, function() return locPass end, 999999, function() end)
			end
	})

end

function bloodSpectersActivation()
	if not scriptEnabled then
		return true
	end
	
	broadcastToAll('블러드 스펙터 활성화.', lifeformColor)
	
	local locCorridors = {}	
	local locRooms = {}

	local locMoveCorridors = {}
	local locMoveRooms = {}
	
	local locIntruders = {}
	local locBloodSpecters = {}
	
	local locBloodSpectersCor = {}
	local locBloodSpectersRoom = {}
	
	
	local locDoors = {}
	
	local locNoises = {}
	
	local locSecures = {}
	
	local locPlayerRooms = getPlayerRoomsInFirstTurnOrder()

	
	for _, castObj in pairs(getAllObjects()) do
		local locCastPos = castObj.getPosition()
		local locBoarderPos = boarderTile.getPosition()
		local locBoarderSize = boarderTile.getBounds().size
		
		
		for _, tag in pairs (castObj.getTags()) do
			if tag == 'Corridors' then
				table.insert(locCorridors, castObj)
			elseif tag == 'room' then
				table.insert(locRooms, castObj)
			elseif tag == 'healthCount' and castObj.getGMNotes() != 'xyrian' then
				table.insert(locIntruders, castObj)
				
				if castObj.getGMNotes() == 'breeder' then
					table.insert(locBloodSpecters, castObj)
				end
			end
		end

		if castObj.getDescription() == 'door' then
			table.insert(locDoors, castObj)
		end

	end
	
	registerToRoomsMap(locRooms, locCorridors)
	
	local locBloodSpectersCorCount = 0
	--BloodSpecters Activation
	for _, tileTable in pairs({locCorridors, locRooms}) do
		local isCorridor = tileTable == locCorridors
		
		for _, locTile in pairs(tileTable) do
			local locTilePos = locTile.getPosition()
			local locCorZVector = nil
			local locTbl = {}
			
			if isCorridor then
				locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locTile.getRotation().y)
			end
			
			local locIntrSize = #locBloodSpecters
			
			for i = 1, locIntrSize do
				local intruder = locBloodSpecters[locIntrSize-i+1]
				local locIntrPos = intruder.getPosition()
				local locPass = false
				
				if isCorridor then
					locPass = distanceMath(locIntrPos, locTilePos) <= corridorImportedSize.x *0.5
					and math.abs(dotMath(locIntrPos-locTilePos, locCorZVector)) <= corridorImportedSize.z *0.6
					if locPass then
						locBloodSpectersCorCount = locBloodSpectersCorCount + 1
					end
				else
				
					if distanceMath(locIntrPos, locTilePos) <= returnRoomDiameter(locTile)*0.506 then
						locPass = true
						
						local locTileGUID = locTile.getGUID()
						for color, playerRoomGUID in pairs (locPlayerRooms) do
							if locTileGUID == playerRoomGUID then
								locPass = false
								intruderAttack(locTile, intruder, color)
								break
							end
						end
					
					end
				end
				
				if locPass then
					table.insert(locTbl, intruder)
					table.remove(locBloodSpecters, locIntrSize-i+1)
				end
			end
			if locTbl[1] != nil then
				if isCorridor then
					table.insert(locBloodSpectersCor, locTbl)
					table.insert(locMoveCorridors, locTile)
				else
					table.insert(locBloodSpectersRoom, locTbl)
					table.insert(locMoveRooms, locTile)
				end
			end
		end
	end
	
	if locBloodSpectersCor[1] != nil then
		autoMoveToGoal(locMoveCorridors, locBloodSpectersCor, {0}, locDoors, {})
	end
	
	if locBloodSpectersRoom[1] != nil then
		Wait.time(function()
			autoMoveToGoal(locMoveRooms, locBloodSpectersRoom, locIntruders, locDoors, {})
		end, locBloodSpectersCorCount*0.25+1)
	end
end

function getRoomHighestID(section, invert)
	if not scriptEnabled then
		return true
	end
	
	local ID = 0
	
	if invert then
		ID = 999
	end
	
	local locRoom = nil
	for _, obj in pairs(getAllObjects()) do
		if obj.hasTag('room') then
			if (obj == hiddenRoom and hibUnexplored == nil) or obj != hiddenRoom then
				local locPass = true
				
				if section != nil then
					local locPosX = obj.getPosition().x
					locPass = (section == 'A' and locPosX < -5.5) or (section == 'C' and locPosX > 5.5) or (section == 'B' and locPosX > -5.5 and locPosX < 5.5)
				end
				
				if locPass then
					local ID2 = tonumber(obj.getGMNotes())
					if not invert then
						if ID2 > ID then
							ID = ID2
							locRoom = obj
						end
					else
						if ID2 < ID then
							ID = ID2
							locRoom = obj
						end
					end
				end
			end
		end
	end
	return locRoom
end

encounterSeqEnd = true
function encounterSequence(paramsList, waitTime, forceState)
	if not scriptEnabled or #paramsList == 0 then
		return true
	end
	
	encounterSeqEnd = false
	
	local locPass = true
	local locStop = false
	
	local locParamsTmp = {}
	local locParamsTmp2 = {}
	
	local locWait = 0
	
	if waitTime != nil then
		locWait = waitTime
	end
	
	for _, tbl in pairs (paramsList) do
		table.insert(locParamsTmp, tbl)
		table.insert(locParamsTmp2, tbl)
	end
	
	local locChoiceCard = nil	
	local locCharacterTile = nil
	local locXenoColor = nil

	
	for i = 1, #paramsList do
		local tbl = paramsList[i]
		if forceState == nil then
			if tbl[2] != nil then
				for _, card in pairs (Player[tbl[2]].getHandObjects()) do
					if card.hasTag('mayEncounterIgnore') then
						locPass = false
						locChoiceCard = card
						break
					end
				end
			end
			
			if locPass then --it kinda hinders very rare duplicate Contractors play but....I'd say it's fine ?
				for playerColor, entry in pairs (playerInfoTable) do
					if (Player[playerColor].seated or (not automaticSeat and entry.manualSeat)) and isPlayerAlive(playerColor) then
						for _, card in pairs (Player[playerColor].getHandObjects()) do
							if card.hasTag('mayBagTokenIgnore') then
								locCharacterTile = getTaggedObjAtPos('CharacterTile', gO(entry.boardGUID).getPosition(), 0)
								locXenoColor = playerColor
								if locCharacterTile.getVar("countTissue") > 0 then
									locPass = false
									locChoiceCard = card
								end
								break
							end
						end
					end
				end
			end
		end
		
		if locPass then
			local w = locWait
			locWait = locWait + 0.25
			
			Wait.time(function()
				if not locStop then
					if not xyrianPause then
						intruderBag.takeObject({
							position = intruderBag.getPosition() + Vector(0,3,0),
							smooth = false,
							callback_function = function(o)
								o.setLock(true)
								table.remove(locParamsTmp2, 1)
								encounter(tbl[1], tbl[2], o)
							end,
							
						})
						
						Wait.time(function()
							if #locParamsTmp2 == 0 then
								encounterSeqEnd = true
							end
						end, 1.5)
					else
						locStop = true
						Wait.condition(function()
							encounterSequence(locParamsTmp2)
						end, function() return not xyrianPause end, 999999, function() end)
					end
				end
			end, w)
				
			table.remove(locParamsTmp, 1)
		else
			break
		end
	end
	
	if not locPass then
		local locEncounterIgnore = false
		
		if locChoiceCard != nil then
			locChoiceCard.hasTag('mayEncounterIgnore')
		end
		
		
		if locEncounterIgnore then
			choiceToPlayer(locParamsTmp[1][1].getPosition() + Vector(5,1,-2), '조우를 무시하시겠습니까?', 90)
			
			Wait.condition(function()
				if choiceState == 1 then
					onObjectNumberTyped(locChoiceCard, locParamsTmp[1][2], 0)
					table.remove(locParamsTmp, 1)
				end
				
				choiceState = 2
				
				if #locParamsTmp > 0 then
					encounterSequence(locParamsTmp, nil, 1)
				end
			end, function() return choiceState < 2 end, 999999, function() end)
			
		else
			local locXenoChoicePos = locParamsTmp[1][1].getPosition() + Vector(5,1,-2)
			intruderBag.takeObject({
				position = locXenoChoicePos + Vector(-0.59,1.36,5.3),
				smooth = false,
				callback_function = function (o) 
					o.setLock(true)
					o.setRotation({0,180,0})
					
					choiceToPlayer(locXenoChoicePos,  xenoChoiceMsg, 60)
					Wait.condition(function()
						if choiceState == 1 then
							onObjectNumberTyped(locChoiceCard, locXenoColor, 0)
							o.setLock(false)
							intruderBag.putObject(o)
							locCharacterTile.setVar("countTissue", locCharacterTile.getVar("countTissue") - 1)
							locCharacterTile.call("updateDisplay")
							Wait.time(function()
								if #locParamsTmp > 0 then
									encounterSequence(locParamsTmp, nil, 1)
								end
							end, 0.25)
						else
							encounter(locParamsTmp[1][1], locParamsTmp[1][2], o)
							table.remove(locParamsTmp, 1)
							if #locParamsTmp > 0 then
								encounterSequence(locParamsTmp, 0.25)
							end
						end
						choiceState = 2

					end, function() return choiceState < 2 end, 999999, function() end)
				end,
			})
		end
	end
end

function encounter(tile, pColor, token)
	if not scriptEnabled then
		return true
	end
	
	local locPass = true
	local locToken = nil
	
	if token != nil then
		locToken = token
	end
	
	
	local locAddInsider = false
	
	if insiderEnable then
		--insiderRecall()
		if insiderFig != nil and insiderCard != nil then
			locAddInsider = insiderCard.getGMNotes() == 'active' and (insiderCard.getRotation().z < 10 or insiderCard.getRotation().z > 350)
		end
	end
	
	local locPlayerRooms = getPlayerRoomsInFirstTurnOrder(locAddInsider)
	
	local locChoiceCard = nil
	
	if tile.hasTag('room') and pColor != nil and locToken == nil  and pColor != 'insider' then
		for _, card in pairs (Player[pColor].getHandObjects()) do
			if card.hasTag('mayEncounterIgnore') then
				locPass = false
				locChoiceCard = card
				break
			end
		end
		
		if not locPass then
			choiceToPlayer(tile.getPosition() + Vector(5,1,-2), '조우를 무시하시겠습니까?', 90)
			Wait.condition(function()
				if choiceState == 1 then
					Wait.stop(encounterWaitID)
					onObjectNumberTyped(locChoiceCard, pColor, 0)
				else
					locChoiceCard = nil
					locPass = true
				end
				choiceState = 2
			end, function() return choiceState < 2 end, 999999, function() end)
		end
	end
	
	encounterWaitID = Wait.condition(function()
		local locEncGo = false
		if locToken == nil then
			intruderBag.takeObject({
				position = intruderBag.getPosition() + Vector(0,5,0),
				smooth = false,
				callback_function = function (o) 
					o.setLock(true)
					o.setRotation({0,180,0})
					locToken = o
					
					local locCharacterTile = nil
					local locXenoColor = nil
					
					if locChoiceCard == nil then
						for playerColor, entry in pairs (playerInfoTable) do
							if (Player[playerColor].seated or (not automaticSeat and entry.manualSeat)) and isPlayerAlive(playerColor) then
								for _, card in pairs (Player[playerColor].getHandObjects()) do
									if card.hasTag('mayBagTokenIgnore') then
										locCharacterTile = getTaggedObjAtPos('CharacterTile', gO(entry.boardGUID).getPosition(), 0)
										locXenoColor = playerColor
										if locCharacterTile.getVar("countTissue") > 0 then
											locChoiceCard = card
										end
										break
									end
								end
							end
						end
					end
					
					if locChoiceCard != nil then
						local locXenoChoicePos = tile.getPosition() + Vector(5,1,-2)
						o.setPosition(locXenoChoicePos + Vector(-0.59,1.36,5.3))
						choiceToPlayer(locXenoChoicePos, xenoChoiceMsg, 60)
						Wait.condition(function()
							if choiceState == 1 then
								Wait.stop(encounterWaitID2)
								onObjectNumberTyped(locChoiceCard, locXenoColor, 0)
								locToken.setLock(false)
								intruderBag.putObject(locToken)
								locCharacterTile.setVar("countTissue", locCharacterTile.getVar("countTissue") - 1)
								locCharacterTile.call("updateDisplay")
								Wait.time(function()
									encounter(tile, pColor)
								end, 0.3)
							else
								locEncGo = true
							end
							choiceState = 2
						end, function() return choiceState < 2 end, 999999, function() end)
					else
						locEncGo = true
					end
				end,
				
			})
		else
			locEncGo = true
		end
		
		encounterWaitID2 = Wait.condition(function()
			local locGM = locToken.getGMNotes() 
			local locTokenMsg = ''
			
			
			if locGM == '' then
				
				locTokenMsg = '공백'
				locToken.setLock(false)
				local locBlankBag = adultBag
				
				
				
				local locAdultName = '성체'
				if lifeforms == 'Sangrevores' then
					locAdultName = '구울'
					
				elseif lifeforms == 'Carnomorph' then
					locBlankBag = creeperBag
					locAdultName = '메타고저'
				end
				
				onObjectNumberTyped(locBlankBag, 'Red', 2)
				broadcastToAll('두 ' .. locAdultName ..' 토큰이 침입자 주머니에 추가됩니다.',lifeformColor)
				
				intruderBag.putObject(locToken)
				
				if insiderEnable and insiderStoryGUID != '' then
					local locInsiderStory = gO(insiderStoryGUID)
					
					if locInsiderStory != nil then
						for _, tag in pairs (locInsiderStory.getTags()) do
							if string.find(tag, 'insiderEffectBlank') != nil then
								autoInsider(2,tag)
							end
						end
					end
				end
				
			elseif 	locGM == 'xyrianToken' then
				locToken.setPosition({42,1.53,7})
				locToken.setRotation({0,180,0})
				locToken.setLock(false)
				
				if xyrianOnBoard() then
					if xyrianTracerBag.getQuantity() < 3 then
						proceedToTracerReplace = true
					end
					xyrianPause = true
					allegianceXyrianActivation(false)
				else
					if xyrianTracerBag.getQuantity() < 3 then
						xyrianTracerReplace()
					end
				end

			elseif locGM != '' then
				local locDesc = locToken.getDescription()
				local locFBags = {}
				
				if lifeforms == 'Primebloods' then
					if locGM == 'larvaeToken' then
						locFBags[1] = larvaeFBag
						locTokenMsg = '유충'
						
					elseif locGM == 'adultToken' then
						locFBags[1] = adultFBag
						for i =2, tonumber(locDesc) do
							locFBags[i] = adultFBag
						end
						locTokenMsg = '성체'
						
					elseif locGM == 'breederToken' then
						locFBags[1] = breederFBag
						for i = 1, tonumber(locDesc) do
							locFBags[i+1] = adultFBag
						end
						locTokenMsg = '드론'
						
					elseif locGM == 'queenToken' then					
						if isQueenAlive() then
							locFBags[1] = queenFBag
						else
							locFBags[1] = breederFBag
						end
						locTokenMsg = '여왕'
						
					end
					
				elseif lifeforms == 'Neoflesh' then
					if locGM == 'queenToken' then					
						if isQueenAlive() then
							locFBags[1] = queenFBag
						end
						
						locTokenMsg = '마더브레인'
						
					else
						for i = 1, string.len(locDesc) do
							local locS = string.sub(locDesc, i, i)
							
							if locS == 'A' then
								locFBags[i] = larvaeFBag
								locTokenMsg = '유충'
								
							elseif locS == 'B' then
								locFBags[i] = adultFBag
								locTokenMsg = '슬래셔'
								
							elseif locS == 'C' then
								locFBags[i] = ironcladFBag
								locTokenMsg = '아이언클래드'
								
							elseif locS == 'D' then
								locFBags[i] = firespitterFBag
								locTokenMsg = '파이어스피터'
								
							elseif locS == 'E' then
								locFBags[i] = crawlmineFBag
								locTokenMsg = '크롤마인'
								
							end
							
						end
					end
				
				elseif lifeforms == 'Sangrevores' then
					if locGM == 'adultToken' then
						locFBags[1] = adultFBag
						for i = 2, tonumber(locDesc) do
							locFBags[i] = adultFBag
						end
						locTokenMsg = '구울'
						
						
					elseif locGM == 'breederToken' then
						locFBags[1] = breederFBag
						locTokenMsg = '블러드스펙터'
						
					elseif locGM == 'queenToken' then
						if isQueenAlive() then
							locFBags[1] = queenFBag
						else
							locFBags[1] = breederFBag
						end
						locTokenMsg = '킹'
						
					end
					
				elseif lifeforms == 'Carnomorph' then
					if locGM == 'creeperToken' then
						locFBags[1] = creeperFBag
						for i =2, tonumber(locDesc) do
							locFBags[i] = creeperFBag
						end
						locTokenMsg = '메타고저'
						
					elseif locGM == 'adultToken' then
						locFBags[1] = adultFBag
						for i =2, tonumber(locDesc) do
							locFBags[i] = adultFBag
						end
						locTokenMsg = '섐블러'
						
					elseif locGM == 'breederToken' then
						
						if breederFBag.getQuantity() > 0 then
							locFBags[1] = breederFBag
						else
							locFBags[1] = adultFBag
						end
						locTokenMsg = '플래쉬비스트'
						
					elseif locGM == 'queenToken' then					
						if isQueenAlive() then
							locFBags[1] = queenFBag
						end
						locTokenMsg = '슬래셔'
						
						
					end
				end
				
				if locFBags[1] == queenFBag and locFBags[1].getQuantity() == 0 then
					activateQueen()
				else
				
					local locTileEnc = false
					local locDegreeToNearPlayer = 180
					
					if tile.hasTag('room') then
						locFBags = {locFBags[1]}
						locTileEnc = true
					else
						for _, roomGUID in pairs (RoomsMap[tile.getGUID()][2]) do
							for color, pRoomGUID in pairs(locPlayerRooms) do
								if roomGUID == pRoomGUID then
									local locDir = gO(roomGUID).getPosition()-tile.getPosition()
									locDegreeToNearPlayer = 90+180+180*math.atan2(locDir[3],locDir[1]*(-1))/3.1415926352
									break
								end
							end
						end
					end
					
					
					for i = 1, #locFBags do
						if locFBags[i].getQuantity() > 0 then
							locFBags[i].takeObject({
								position = locFBags[i].getPosition() + Vector(0,6,0),
								callback_function = function (o2)
									o2.setLock(true)
									Wait.time(function()
										
										
										if o2.hasTag('rot180') then
											if locTileEnc then
												o2.setRotation({0,180,0})
											else
												o2.setRotation({0,locDegreeToNearPlayer,0})
											end
										else
											o2.setRotation({0,0,0})
										end
										
										
										if locFBags[i] == queenFBag then
											if lifeforms == 'Sangrevores' and not locTileEnc then
												local locCorCount = 0
												for _, corridorObj in pairs (shapeCast(tile.getPosition(), tile.getBounds().size, tile.getRotation())) do
													if corridorObj.getName() == 'Noise' or corridorObj.hasTag('intruder') then
														locCorCount = locCorCount + 1
														if locCorCount > 2 then
															enemyFigReturn(corridorObj)
														end
													end
												end
											end
										end
										
										local locPos = {0,10,0}
										
										if locTileEnc then
											locPos = findSpaceOnTile(tile, nil, true, o2)
										else
											locPos = findSpaceOnTile(tile, nil, true)
										end
										
										o2.setPositionSmooth(locPos,false, true)
										if locTileEnc then

											local locPCol = ''
											if pColor == nil then
												local locTileGUID = tile.getGUID()
												for color, pRoomGUID in pairs(locPlayerRooms) do
													if locTileGUID == pRoomGUID then
														locPCol = color
														break
													end
												end
											else
												locPCol = pColor
											end
											if locPCol != '' then
												checkSecureRoom(tile, o2, locPCol)
											end
										end
										
									end, (i-1) * 0.25)
								end,
							})
						end
					end
				end
				
				Wait.time(function() 
					locToken.setLock(false)
					if locGM == 'queenToken' and (lifeforms == 'Neoflesh' or lifeforms == 'Sangrevores' or lifeforms == 'Carnomorph' ) then
						if not isQueenAlive() then
							local locQueenName = '마더브레인'
							if lifeforms == 'Sangrevores' then
								locQueenName = '킹'
							else
								intruderTokenReturn(locToken)
							end
							broadcastToAll(locQueenName.. '이(가) 죽었으므로 ' ..locQueenName..' 토큰이 제거되었습니다.', lifeformColor)
						elseif lifeforms == 'Neoflesh' or lifeforms == 'Carnomorph' then
							intruderBag.putObject(locToken)
						end
					end
					if (lifeforms != 'Neoflesh' and lifeforms != 'Carnomorph') or ((lifeforms == 'Neoflesh' or lifeforms == 'Carnomorph') and locGM != 'queenToken') then
						intruderTokenReturn(locToken)
					end
				end, #locFBags *0.25)
			end	
			
			if locTokenMsg != '' then
				broadcastToAll(locTokenMsg .. ' 토큰이 뽑혔습니다.', lifeformColor)
			end
			
		end, function() return locEncGo end, 999999, function() end)
	end, function() return locPass end, 999999, function() end)
end

function playsounds(soundID)
	if soundEnable and scriptEnabled then
		local locSoundBox = nil
		local soundIDOffset = 0
		local soundWait = 3
		if soundDuration[soundID+1] != nil then
			soundWait = math.min(soundDuration[soundID+1], 10)
		end
		
		if soundID >= 99 and soundID <= 197 then
			soundIDOffset = 99
			if not sound3Used then
				locSoundBox = soundboard3
				sound3WaitID = Wait.time(function() sound3Used = false 
				end, soundWait)
				sound3Used = true
				
			else
				locSoundBox = soundboard4
				if not sound4Used then
					sound4WaitID = Wait.time(function() sound4Used = false
					end, soundWait)
				end
				sound4Used = true
			end
		elseif soundID <= 98 then
			if not sound1Used then
				locSoundBox = soundboard1
				sound1WaitID = Wait.time(function() sound1Used = false
				end, soundWait)
				
				sound1Used = true
			else
				locSoundBox = soundboard2
				if not sound2Used then
					sound2WaitID = Wait.time(function() sound2Used = false
					end, soundWait)
				end
				sound2Used = true
			end
		else
			soundIDOffset = 99*2
			if not sound5Used then
				locSoundBox = soundboard5
				sound5WaitID = Wait.time(function() sound5Used = false
				end, soundWait)
				
				sound5Used = true
			else
				locSoundBox = soundboard6
				if not sound6Used then
					sound6WaitID = Wait.time(function() sound6Used = false
					end, soundWait)
				end
				sound6Used = true
			end
		end
		
		if soundID == (-1) then
			for i = 1, 6 do
				stopSoundBoard(i)
			end
			
		else
			locSoundBox.AssetBundle.playTriggerEffect(soundID - soundIDOffset)
		end
	end
end

function stopSoundBoard(soundBoardNumber)
	if not scriptEnabled then
		return true
	end
	
	local locString = tostring(soundBoardNumber)
	local locWaitID = _G['sound'.. locString .. 'WaitID']
	_G['soundboard'..locString].AssetBundle.playLoopingEffect(0)
	_G['sound'..locString..'Used'] = false
	if locWaitID != nil then
		Wait.stop(locWaitID)
	end
end

function walksounds(intruder)
	if not scriptEnabled then
		return true
	end
	
	local locEnGM = intruder.getGMNotes()
	if (not sound3Used and lifeforms != 'Neoflesh') or (not sound5Used and lifeforms == 'Neoflesh') or locEnGM == 'queen' then
		local walktime = 0
		local steps = math.random(3,6)
		
		
		local sound = 121
		local locNumberSounds = 4
		
		if locEnGM == 'larvae' then --average time for one step is 0.21s
			walktime = math.random()*0.4 + 0.75
			steps = math.random(6,8)
			
			if lifeforms == 'Neoflesh' then
				sound = 243
				locNumberSounds = 2
			end
		
		elseif locEnGM == 'breeder' or locEnGM == 'xyrian' then
			walktime = math.random()+1.5
			
		elseif locEnGM == 'queen' then
			walktime = math.random()+3
			
			if lifeforms == 'Neoflesh' then
				sound = 241
				locNumberSounds = 2
			end
			
		elseif intruder.getName() == 'insiderFig' then
			walktime = math.random()+3.4
			steps = math.random(3,6)
			sound = 261
			locNumberSounds = 2
		else
			walktime = math.random()+1
			
			if lifeforms == 'Neoflesh' then
				if locEnGM == 'slasher' or locEnGM == 'crawlmine' then
					sound = 247
					locNumberSounds = 2
					
				elseif locEnGM == 'firespitter' or locEnGM == 'ironclad' then
					sound = 245
					locNumberSounds = 2
				end
			end

		end
		
		
		if locEnGM == 'queen' then
			stopSoundBoard(5)
			stopSoundBoard(6)
		end
		
		local delay = 0
		local spacing = walktime/steps
		delay = delay + spacing
		for i = 2, steps do
			Wait.time(function() playsounds(sound + (locNumberSounds-1-(i%locNumberSounds))) end, delay)
			delay = delay + spacing
		end
	end
end

intruderBurning = false
function intruderBurn()
	if not scriptEnabled then
		return true
	end
	
	local locWait = 0
	
	if lifeforms != 'Neoflesh' then
		local burnStarted = false
		if not intruderBurning and fireBag.getQuantity() < 9 then
			
			local locFires = {}
			local locRooms = {}
			local locIntruders = {}
			for _, obj in pairs(getAllObjects()) do
				if obj.getGMNotes() == 'fire' then
					table.insert(locFires, obj)
				elseif obj.hasTag('room') then
					table.insert(locRooms, obj)
				elseif obj.hasTag('intruder') and obj.hasTag('healthCount') then
					table.insert(locIntruders, obj)
				end
			end
			
			for _, fire in pairs(locFires) do
				local locRemoveRooms = {}
				local locRoomsSize = #locRooms
				for j = 1, locRoomsSize do
					local room = locRooms[locRoomsSize-j+1]
					local locRoomPos = room.getPosition()
					if distanceMath(locRoomPos, fire.getPosition()) < returnRoomDiameter(locRoom)*0.75 then
					
						if room.hasTag('nest') and nestBag.getQuantity() > 0 then
							burnStarted = true
							broadcastToAll('둥지에서 알 하나가 타버렸습니다', lifeformColor)
							nestBag.takeObject({
								position = nestBag.getPosition() + Vector(0,5,0),
								callback_function = function(o) o.destruct() end,
							})
						end
						
						local locRemoveIntrs = {} --XX
						local locIntrSize = #locIntruders
						for i = 1, locIntrSize do
							local intruder = locIntruders[locIntrSize-i+1]
							if distanceMath(intruder.getPosition(), locRoomPos) < returnRoomDiameter(room)*0.506 then
								intruder.call("onClick")
								burnStarted = true
								table.remove(locIntruders, locIntrSize-i+1)
							end
						end
						table.remove(locRooms, locRoomsSize-j+1)
					end
				end
			end
			
			if burnStarted then
				broadcastToAll('자동 연소 단계 완료', {1,0.5,0})
				intruderBurning = true
			end
			
			Wait.time(function() intruderBurning = false end, 10)
		end	
	end

	local locCorridors = {}
	local locMoveCorridors = {}
	local locRooms = {}
	local locMoveRooms = {}

	local locIntruders = {}
	local locIntrudersCopy = {}
	local locIntrudersAttack = {}
	local locLarvaeCorridor = {}
	local locLarvaeCorCount = 0
	local locLarvaeRoom = {}
	
	local locDoors = {}
	local locNoises = {}
	local locSecures = {}
	
	local locCarnoMenu = {{}, {}, {}, {}} --menu is PlayerBody, Egg not listed, Carcass, Metagorger, Body
	
	for _, castObj in pairs(getAllObjects()) do
		local locCastPos = castObj.getPosition()
		local locBoarderPos = boarderTile.getPosition()
		local locBoarderSize = boarderTile.getBounds().size
		if math.abs(locCastPos.x - locBoarderPos.x) < locBoarderSize.x and math.abs(locCastPos.z - locBoarderPos.z) < locBoarderSize.z then
			local locGM = castObj.getGMNotes()
			local locName = castObj.getName()
			for _, tag in pairs(castObj.getTags()) do
				if tag == 'intruder' then
					table.insert(locIntruders, castObj)
					table.insert(locIntrudersAttack, castObj)
					if lifeforms == 'Carnomorph' then
						if locGM == 'creeper' then
							table.insert(locCarnoMenu[3], castObj)
						end
					end
					break
				elseif tag == 'room' then
					table.insert(locRooms, castObj)
					break
				elseif tag == 'Corridors' then
					table.insert(locCorridors, castObj)
					break
				end
			end
			
			if lifeforms == 'Neoflesh' then
				if locName == 'Noise' then
					table.insert(locNoises, castObj)
				elseif castObj.getDescription() == 'door' then
					table.insert(locDoors, castObj)
				end
			elseif lifeforms == 'Carnomorph' then
				if locGM == 'carcass' then
					table.insert(locCarnoMenu[2], castObj)
				elseif locName == 'Body' then
					table.insert(locCarnoMenu[4], castObj)
				end
			end
		end
	end
	
	registerToRoomsMap(locRooms, locCorridors)
	
	local locPlayerRooms = getPlayerRoomsInFirstTurnOrder(true)
	local locQueenAttacked = false
	
	for color, playerRoomGUID in pairs(locPlayerRooms) do
		for _, room in pairs(locRooms) do
			if room.getGUID() == playerRoomGUID then
				local locRoomPos = room.getPosition()
				local locTblSize = #locIntrudersAttack
				for j=1, locTblSize do
					local intruder = locIntrudersAttack[locTblSize-j+1]
					if distanceMath(intruder.getPosition(), locRoomPos) <= returnRoomDiameter(locTile)*0.506 then
						if intruder.getGMNotes() == 'queen' then
							locQueenAttacked = true
						end
						
						intruderAttack(room, intruder, color)
						table.remove(locIntrudersAttack, locTblSize-j+1)
					end
				end
			end
		end
	end
	

	
	if lifeforms == 'Neoflesh' then
		twitchlingActivation(locCorridors, locRooms, locIntruders, locDoors, locNoises)
		
	elseif lifeforms == 'Carnomorph' then
		if isQueenAlive() and queenFBag.getQuantity() == 0 and locQueenAttacked then
			local locFig = gO(queenFigGUID)
			table.insert(locIntrudersAttack, locFig)
		end
		
		
		for _, color in pairs (getPlayerColorsInFirstTurnOrder(true)) do
			local locChar = gO(playerInfoTable[color].figureGUID)
			
			if locChar != nil then
				if locChar.getRotation().z > 140 and locChar.getRotation().z < 220 then
					table.insert(locCarnoMenu[1],1, locChar) --because Carnomorph eat in reverse afterwards
				end
			end
		end
		
		local locGuests = {butcher = {}, fleshbeast = {}, shambler = {}, metagorger = {}}
		
		for _, intruder in pairs (locIntrudersAttack) do
			local locGM = intruder.getGMNotes()
			local locT = nil
			if locGM == 'queen' then
				locT = locGuests.butcher
			elseif locGM == 'breeder' then
				locT = locGuests.fleshbeast
			elseif locGM == 'adult' then
				locT = locGuests.shambler
			elseif locGM == 'creeper' then
				locT = locGuests.metagorger
			end
			table.insert(locT,intruder)
		end
		
		for guestType, guestTbl in pairs (locGuests) do
			for _, guest in pairs (guestTbl) do
				if guest != nil then
					if not guest.hasTag('eaten') then
						local locGuestPos = guest.getPosition()
						local locDishFound = false
						local locDishTypeIndex = 0
						
						for _, room in pairs (locRooms) do
							local locRoomPos = room.getPosition()
							if distanceMath(locGuestPos, locRoomPos) < returnRoomDiameter(room)*0.506 then
								
								for _, dishTbl in pairs (locCarnoMenu) do
									locDishTypeIndex = locDishTypeIndex + 1
									for i = 1, #dishTbl do
										
										local locDish = dishTbl[#dishTbl-i+1]
										
										if locDish != nil then
											if not locDish.hasTag('eaten') and locDish != guest then
												local locDishPos = dishTbl[#dishTbl-i+1].getPosition()
												
												if distanceMath(locDishPos, locRoomPos) < returnRoomDiameter(room)*0.506 then
													locDishFound = true
													if locDishTypeIndex == 3 then
														locDish.addTag('eaten')
														enemyFigReturn(locDish)
													else											
														locDish.setPosition({45,-9,0})
														locDish.destruct()
													end
													
													if guest.hasTag('meat') then
														guest.addTag('eaten')
													end
													
													break
												end
											end
										end
									end
									
									if locDishTypeIndex == 1 and not locDishFound and nestBag.getQuantity() > 0 then
										if room.getName() == 'NEST' then
											if distanceMath(locGuestPos, locRoomPos) < returnRoomDiameter(room)*0.506 then
												nestBag.takeObject({position = {30,2,25}})
												locDishFound = true
											end
											break
										end
									end
									
									if locDishFound then
										break
									end
								end
								
								if locDishFound then
									local w = locWait
									locWait = locWait + 0.5
									Wait.time(function()
										carnoFeed(guest)
									end, w)
								end
					
						
								break
							end
						end


	
					end
				end
			end
		end
	end
	
	if insiderEnable and insiderStoryGUID != '' then
		local locInsiderStory = gO(insiderStoryGUID)
		
		if locInsiderStory != nil then
			for _, tag in pairs (locInsiderStory.getTags()) do
				if string.find(tag, 'insiderEffectEventBurn') != nil then
					autoInsider(2, tag)
				end
			end
		end
	end
end

function carnoFeed(intruder)
	if intruder != nil then
	
		
		local locGM = intruder.getGMNotes()
		intruder.setVar("count", 0)
		intruder.call("updateDisplay")
		local locPos = intruder.getPosition()
		local locFBag = nil
		local locBag = nil
		
		if locGM == 'creeper' then
			locBag = adultBag
			locFBag = adultFBag
			
		elseif locGM == 'adult' then
			locBag = breederBag
			locFBag = breederFBag
			
			
		elseif locGM == 'breeder' then
			locBag = queenBag
			locFBag = queenFBag
			
		elseif locGM == 'queen' then
			activateQueen()
		end
		
		if locFBag != nil then
			if locFBag.getQuantity() > 0 then
				onObjectNumberTyped(locBag, 'Red', 1)
				enemyFigReturn(intruder)
				locFBag.takeObject({
					position = locPos,
					rotation = {0,180,0},
					callback_function = function(o)
						o.setLock(true)
					end
				})
			end
		end
	end
end

function twitchlingActivation(corridors, rooms, intruders, doors, noises)
	if not scriptEnabled then
		return true
	end

	local locSearchCompletes = {0,{}}
	
	local locCorridors = {}
	
	if corridors != nil then
		locCorridors = corridors
	else
		locSearchCompletes[1] = locSearchCompletes[1] +1
		locSearchCompletes[2]['Corridors'] = 0
	end
	
	
	local locRooms = {}
	if rooms != nil then
		locRooms = rooms
	else
		locSearchCompletes[1] = locSearchCompletes[1] +1
		locSearchCompletes[2]['room'] = 0
	end
	
	local locMoveCorridors = {}
	local locMoveRooms = {}
	
	local locIntruders = {}
	local locIntrudersCopy = {}
	if intruders != nil then
		locIntruders = intruders
		for _, intruder in pairs (intruders) do
			if intruder.getGMNotes() == 'larvae' then
				table.insert(locIntrudersCopy, intruder)
			end
		end
	else
		locSearchCompletes[1] = locSearchCompletes[1] +1
		locSearchCompletes[2]['intruder'] = 0
	end

	local locLarvaeCorridor = {}
	local locLarvaeCorCount = 0
	local locLarvaeRoom = {}
	
	
	local locDoors = {}
	if doors != nil then
		locDoors = doors
	else
		locSearchCompletes[1] = locSearchCompletes[1] +1
		locSearchCompletes[2]['door'] = 0
	end
	
	local locNoises = {}
	if noises != nil then
		locNoises = noises
	else
		locSearchCompletes[1] = locSearchCompletes[1] +1
		locSearchCompletes[2]['Noise'] = 0
	end
	
	if locSearchCompletes[1] > 0 then
		for _, castObj in pairs(getAllObjects()) do
			local locCastPos = castObj.getPosition()
			local locBoarderPos = boarderTile.getPosition()
			local locBoarderSize = boarderTile.getBounds().size
			
			if locSearchCompletes[2]['Corridors'] != nil then
				if castObj.hasTag('Corridors') then
					table.insert(locCorridors, castObj)
				end
			end
			
			if locSearchCompletes[2]['room'] != nil then
				if castObj.hasTag('room') then
					table.insert(locRooms, castObj)
				end
			end
			
			if locSearchCompletes[2]['intruder'] != nil then
				if castObj.hasTag('intruder') then
					table.insert(locIntruders, castObj)
					if castObj.getGMNotes() == 'larvae' then
						table.insert(locIntrudersCopy, castObj)
						--print('adding larvae to locIntrudersCopy')
					end
				end
			end
			
			if locSearchCompletes[2]['door'] != nil then
				if castObj.getDescription() == 'door' then
					table.insert(locDoors, castObj)
				end
			end
			
			if locSearchCompletes[2]['Noise'] != nil then
				if castObj.getName() == 'Noise' then
					table.insert(locNoises, castObj)
				end
			end
		end
	end
	

	Wait.condition(function()
			
			--Twitchling Activation
			for _, tileTable in pairs({locCorridors, locRooms}) do
				local isCorridor = tileTable == locCorridors
				
				for _, locTile in pairs(tileTable) do
					local locTilePos = locTile.getPosition()
					local locCorZVector = nil
					local locTbl = {}
					
					if isCorridor then
						locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locTile.getRotation().y)
					end
					
					local locIntrSize = #locIntrudersCopy
					
					for i = 1, locIntrSize do
						local intruder = locIntrudersCopy[locIntrSize-i+1]
						local locIntrPos = intruder.getPosition()
						local locPass = false
						
						if isCorridor then
							locPass = distanceMath(locIntrPos, locTilePos) <= corridorImportedSize.x *0.5
							and math.abs(dotMath(locIntrPos-locTilePos, locCorZVector)) <= corridorImportedSize.z *0.6
							if locPass then
								locLarvaeCorCount = locLarvaeCorCount + 1
							end
						else
							locPass = distanceMath(locIntrPos, locTilePos) <= returnRoomDiameter(locTile)*0.506
							--print('returnRoomDiameter *0.506 = ' .. returnRoomDiameter(locTile)*0.506)
						end
						
						if locPass then
							table.insert(locTbl, intruder)
							table.remove(locIntrudersCopy, locIntrSize-i+1)
							--print('adding larvae to locTbl')
						end
					end
					if locTbl[1] != nil then
						if isCorridor then
							table.insert(locLarvaeCorridor, locTbl)
							table.insert(locMoveCorridors, locTile)
							--print('Adding larvae to locLarvaeCorridor')
						else
							table.insert(locLarvaeRoom, locTbl)
							table.insert(locMoveRooms, locTile)
							--print('Adding larvae to locLarvaeRoom')
						end
					end
				end
			end
			
			if locLarvaeCorridor[1] != nil then
				--print('starting autoMoveToGoal from corridors')
				autoMoveToGoal(locMoveCorridors, locLarvaeCorridor, {0}, locDoors, locNoises, 'twitchlingUnexplored')
			end
			
			if locLarvaeRoom[1] != nil then
				Wait.time(function()
					--print('starting autoMoveToGoal from rooms')
					autoMoveToGoal(locMoveRooms, locLarvaeRoom, locIntruders, locDoors, locNoises, 'twitchlingUnexplored')
				end, locLarvaeCorCount*0.25+1)
			end

	end, function() return proceedToNextPhase end, 999999, function() end)
end

function registerToRoomsMap(inRooms, inCorridors)
	if not scriptEnabled then
		return true
	end
	
	local locRooms = {}
	if inRooms != nil then
		locRooms = inRooms
	end
	
	local locCorridors = {}
	if inCorridors != nil then
		locCorridors = inCorridors
	end
	
	if inRooms == nil or inCorridors == nil then
		for _, obj in pairs (getAllObjects()) do
			if obj.hasTag('Corridors') and inCorridors == nil then
				table.insert(locCorridors, obj)
				
			elseif obj.hasTag('room') and inRooms == nil then
				table.insert(locRooms, obj)
			end
		end
	end

	for i = 1, #locRooms do
		local locRoomGUID = locRooms[i].getGUID()
		if RoomsMap[locRoomGUID] == nil then
			RoomsMap[locRoomGUID] = {'room', {}}
		end
		
		for _, locCor in pairs(locCorridors) do
			
			local locCorGUID = locCor.getGUID()
			local corKeyExist = RoomsMap[locCorGUID] != nil
			local locPass = false
			
			if corKeyExist then
				if #RoomsMap[locCorGUID][2] < 2 then
					locPass = true
				end
			else
				locPass = true
			end
			
			if locPass then
				local locVecCorToRoom = locRooms[i].getPosition() - locCor.getPosition()
				local locDistance = distanceMath(locRooms[i].getPosition(), locCor.getPosition()) 
				local locDot = math.abs(dotMath(normalizeMath(locVecCorToRoom), rotateVectorAboutY({1,0,0}, locCor.getRotation().y)))
				
				if locDistance < (returnRoomDiameter(locRooms[i])*0.630252 + corridorImportedSize.x*0.630252) and locDot > 0.9 then --I guess my first measurements were a bit bad ? oh well let's tweak..
					

					if not corKeyExist then
						RoomsMap[locCorGUID] = {'corridor', {}}
						table.insert(RoomsMap[locRoomGUID][2], locCorGUID)
						table.insert(RoomsMap[locCorGUID][2], locRoomGUID)
					elseif RoomsMap[locCorGUID][2][1] != locRoomGUID then
						table.insert(RoomsMap[locRoomGUID][2], locCorGUID)
						table.insert(RoomsMap[locCorGUID][2], locRoomGUID)
					end
				end
			end
		end
	end

end

function returnDiscardToDeck (discard, deck)
	if not scriptEnabled then
		return true
	end
	
	discard.shuffle()
	deck.setRotation({0,180,0})
	discard.setPosition(deck.getPosition() + Vector(0,1,0))
	
	Wait.time(	function()
					deck.setRotation({0,180,180})
				end, 0.5)
end

function onObjectStateChange(object, old_state_guid)
	if scriptEnabled then
		if object.getDescription() == 'door' then

			
			playsounds(math.random(77,79))
			object.setLock(true)

		elseif object.getDescription() == 'destroyedDoor' then
			local locExplosionSound = 32
			
			if math.random() > 0.5 then
				locExplosionSound = 189
			end
			
			playsounds(locExplosionSound)
			object.setLock(true)
			lightAlert()
		elseif object.getGMNotes() == 'ammo' then
			if (shootingState != 0 and sound1Used and not sound2Used) or shootingState == 0 or sound3Used or sound5Used then
				playsounds(math.random(84,89))
			end
		end
	end
end		

previousHCountObj = nil
previousNoiseObj = nil
function onObjectHover(player_color, object)
	
	if object != nil and scriptEnabled then
	
		local locInteractible = false
		local locNoiseObj = nil
		local locPlayerHasAlarm = false
		local locPlayerHasMotionTracker = false
		
		if object.getName() == 'Noise' and player_color == Turns.turn_color then
			if object != previousNoiseObj then
				locInteractible = true

				if playerHasTag('모션 추적기', 2, nil, player_color) then
					locPlayerHasMotionTracker = true
					locNoiseObj = object
				end
				
				if getTaggedObjAtPos('ALARM ROOM', gO(playerInfoTable[player_color].figureGUID).getPosition(), 1) != nil then
					locPlayerHasAlarm = true
					locNoiseObj = object
				end
				
				if locPlayerHasMotionTracker then
					object.createButton({
						click_function = 'motionTrackerAction',
						function_owner = Global,
						label          = '모션 추적기',
						position       = {0,0.5,1},
						scale          = {2,2,2},
						rotation = {0,0,0},
						width          = 400,
						height         = 100,
						font_size      = 40,
						color          = {0,0,0},
						font_color     = {1,1,1,1},
						tooltip = motionTrackerMsg,
					})
				end
				
				if locPlayerHasAlarm then
					object.createButton({
						click_function = 'alarmRoomAction',
						function_owner = Global,
						label          = '경보실로\n 해결하기',
						position       = {0,0.5,2},
						scale          = {2,2,2},
						rotation = {0,0,0},
						width          = 400,
						height         = 100,
						font_size      = 25,
						color          = {0,0,0},
						font_color     = {1,1,1,1},
						tooltip = alarmRoomMsg,
					})
				end
			end
		end
		
		if object.hasTag('characterFig') and useXyrian then
			locInteractible = true
			if playerHasTag('ENTANGLED', 1, object.getGUID(), nil) then
				local locEntangledFig = object
				locEntangledFig.setLock(true)
				
				if entangledWaitID != nil then
					Wait.stop(entangledWaitID)
				end
				
				entangledWaitID = Wait.time( function()
					locEntangledFig.setLock(false)
				end, 5)
				
				broadcastToColor('This character is Entangled and cannot move.', player_color, xyrianColor)
				
			end
		

			
		
		elseif ((weaponCol and player_color == Turns.turn_color) or (not weaponCol)) and proceedToNextPhase then
			
			local locOldPos = Vector(0,0.11,-0.5)
			
			if object.hasTag('rot180') then
				locOldPos = Vector(0,0.75,-1.25)
			end
			
			local locOldScale = Vector(0.7,0.7,0.7)
			

			
			if object.hasTag('healthCount') and canEnlarge then
				locInteractible = true
				if previousHCountObj != object then
					if previousHCountObj != nil then
						if previousHCountObj.hasTag('healthCount') then
							previousHCountObj.editButton({index = 0, position = locOldPos, scale = locOldScale, color = {r=0,g=0,b=0,a=0}})
							local i = 0
							for _, entry in pairs (previousHCountObj.getButtons()) do
								if i > 0 then
									previousHCountObj.removeButton(i)
								end
								i = i +1
							end
						end
					end
					
					if shootingState == 0 then
						previousHCountObj = object
						local locScaleO = 0.28/object.getScale().y
						
						if object.getName() == 'Noise' then
							locScaleO = 0.5
						end
						
						local locScale = locOldScale * 4*locScaleO
						local locBounds = object.getBounds().size
						local locOff = 0.1*locBounds.y

						local locSizeY = locBounds.y + locOff
						
						local locObjPos = object.getPosition()
						local locBigObjs = getTaggedObjAtPos('healthCount', locObjPos + rotateVectorAboutY(Vector(0,locSizeY*0.5+0.25,3.84*0.5/2.75),object.getRotation().y), 0, {locBounds.x,0.5,3.84/2.75}, object.getRotation(), true)
						
						if locBigObjs != nil then
							local lastSizeY = 0
							for _, bigObj in pairs (locBigObjs) do							
								local locBigBounds = bigObj.getBounds().size
								if lastSizeY < locBigBounds.y then
									locSizeY = locBigBounds.y + locOff
									lastSizeY = locBigBounds.y
								end
							end
						end
						
						
						local locPos = Vector(0,0.11,-0.5) + Vector(0, locSizeY/object.getScale().y, locScale.z*0.8)
						
						local locRotY = object.getRotation().y
					
						object.editButton({index = 0, position = rotateVectorAboutY(locPos, locRotY), scale = locScale, rotation = {0,180-locRotY,0}, color = {r=0.25, g=0.12, b=0.06, a=1}})
					
						local locCor = getTaggedObjAtPos('Corridors', object.getPosition(), 0)
						
						if locCor != nil then
							locCor = (distanceMath(object.getPosition(), locCor.getPosition()) < corridorImportedSize.x*0.5)
						else
							locCor = false
						end
						
						local locRollCol
						local locRollFunc = ''
							
						if locCor then
							locRollCol = burstColor
							locRollFunc = 'rollBurst'
						else
							locRollCol = shootColor
							locRollFunc = 'rollShoot'
						end
						
						local locBoard = gO(playerInfoTable[player_color].boardGUID)
						local locBoardPos = locBoard.getPosition()
						local locSize = locBoard.getBounds().size + Vector(0,5,0)
						
						if #object.getButtons() == 1 then
							
							local i = 0
							local locWeaponFound = false
							local locMarkedGUID = ''
							
							
							
							if markedWeapon != nil then
								locMarkedGUID = markedWeapon.getGUID()
							end
							
							for _, locWeap in pairs (shapeCast(locBoardPos + locSize*Vector(-0.25,0,0), locSize*Vector(0.4,1,1))) do
								
								
								if locWeap.hasTag('weapon') then
									local locWeapGUID = locWeap.getGUID()
									local locWeapDesc = locWeap.getDescription()
									if (not locCor and locWeapDesc != 'SECURITY SYSTEM CONTROL' and locWeapDesc != 'GRENADE') or (locCor and not locWeap.hasTag('melee')) then
										local locLabel = locWeap.getDescription()
										local locF =  math.min(0.8*2*800/string.len(locLabel),100)
										local locCol = {0,0,0,1}
										
										if markedWeapon != nil then
											if locMarkedGUID == locWeapGUID and not locWeaponFound then
												locCol = locRollCol
												locWeaponFound = true
											end
										end

										
										object.createButton({
											click_function = 'selectLeftWeapon' .. i,
											function_owner = Global,
											label          = locLabel,
											position       =  rotateVectorAboutY(locPos + Vector(4.55*locScaleO,0, (1-i*1.34)*locScaleO),locRotY),
											scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
											rotation = {0,180-locRotY,0},
											width          = 800,
											height         = 200,
											font_size      = locF,
											color          = locCol,
											font_color     = {1,1,1,1},
											tooltip        = locWeapGUID,
										})
										
										local locFunc = function(obj, pColor, alt_click)
											if shootingState == 0 then
												local locBoard = gO(playerInfoTable[pColor].boardGUID)
												if locBoard != nil then
													local locSize = locBoard.getBounds().size
													local locObj = gO(locWeap.getGUID())
													if locObj != nil then
														markWeaponToggle(locObj, obj, not locCor)
													end
												end
											end
										end
										_G['selectLeftWeapon' .. i] = locFunc
										i = i +1
									end
								end
							end
							
							i = 0
							locWeaponFound = false
							for _, locWeap in pairs (shapeCast(locBoardPos + locSize*Vector(0.25,0,-0.5), locSize*Vector(0.4,1,1))) do
								
								if locWeap.hasTag('weapon') then
									local locWeapGUID = locWeap.getGUID()
									local locWeapDesc = locWeap.getDescription()
									if (not locCor and locWeapDesc != 'SECURITY SYSTEM CONTROL' and locWeapDesc != 'GRENADE')  or (locCor and not locWeap.hasTag('melee')) then
										local locLabel = locWeap.getDescription()
										local locF = math.min(0.8*2*800/string.len(locLabel),100)
										local locCol = {0,0,0,1}
										
										if markedWeapon != nil then
											if locMarkedGUID == locWeapGUID and not locWeaponFound then
												locCol = locRollCol
												locWeaponFound = true
											end
										end
										
										object.createButton({
											click_function = 'selectRightWeapon' .. i,
											function_owner = Global,
											label          = locLabel,
											position       =  rotateVectorAboutY(locPos + Vector(-4.55*locScaleO,0, (1-i*1.34)*locScaleO),locRotY),
											scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
											rotation = {0,180-locRotY,0},
											width          = 800,
											height         = 200,
											font_size      = locF,
											color          = locCol,
											font_color     = {1,1,1,1},
											tooltip        = locWeapGUID,
										})
										
										local locFunc = function(obj, pColor, alt_click)
											if shootingState == 0 then
												local locBoard = gO(playerInfoTable[pColor].boardGUID)	
												if locBoard != nil then
													local locSize = locBoard.getBounds().size
													local locObj = gO(locWeap.getGUID())
													if locObj != nil then
														markWeaponToggle(locObj, obj, not locCor)
													end
												end
											end
										end
										_G['selectRightWeapon' .. i] = locFunc
										i = i +1
									end
								end
							end
							
							local locCol = {0,0,0,1}
							if markedWeapon != nil then
								if markedWeapon.hasTag('melee') and not markedWeapon.hasTag('weapon') then
									locCol = locRollCol
								end
							end
							
							local locLabel = '근접'
							local locLabel2 = '사격 굴림'
							local locW = 400
							
							if locCor then
								locLabel = '방/로봇'
								locW = 800
								locLabel2 = '집중사격 굴림'
							end
							
							object.createButton({
								click_function = 'meleeMark',
								function_owner = Global,
								label          = locLabel,
								position       = rotateVectorAboutY(locPos + Vector(0,0,(2.4+1.34)*locScaleO), locRotY),
								scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
								rotation = {0,180-locRotY,0},
								width          = locW,
								height         = 200,
								font_size      = 100,
								color          = locCol,
								font_color     = {1,1,1,1},
								tooltip        = locBoard.getGUID(),
							})
							
							if lifeforms == 'Sangrevores' and object.getName() == 'Noise' then
								if locPlayerHasMotionTracker then
									object.createButton({
										click_function = 'motionTrackerAction',
										function_owner = Global,
										label          = '모션 추적기',
										position       = rotateVectorAboutY(locPos + Vector(0,0,(2.4 + 1.34*2)*locScaleO), locRotY),
										scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
										rotation = {0,180-locRotY,0},
										width          = locW,
										height         = 200,
										font_size      = 100,
										color          = {0,0,0},
										font_color     = {1,1,1,1},
										tooltip = motionTrackerMsg,
									})
								end
								
								if locPlayerHasAlarm then
									object.createButton({
										click_function = 'alarmRoomAction',
										function_owner = Global,
										label          = '경보실로\n 해결하기',
										position       = rotateVectorAboutY(locPos + Vector(0,0,(2.4 - 1.34)*locScaleO), locRotY),
										scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
										rotation = {0,180-locRotY,0},
										width          = locW,
										height         = 200,
										font_size      = 100,
										color          = {0,0,0},
										font_color     = {1,1,1,1},
										tooltip = alarmRoomMsg,
									})
								end
							end
							
							object.createButton({
								click_function = locRollFunc,
								function_owner = Global,
								label          = locLabel2,
								position       = rotateVectorAboutY(locPos + Vector(0,0,2.4*locScaleO),locRotY),
								scale          = {4*locScaleO,4*locScaleO,4*locScaleO},
								rotation = {0,180-locRotY,0},
								width          = 700,
								height         = 200,
								font_size      = 100,
								color          = locRollCol,
								font_color     = {1,1,1,1},
								tooltip        = locBoard.getGUID(),
							})
							

						end
					end
				end
				
				
				if scaleHealthWaitID != nil then
					Wait.stop(scaleHealthWaitID)
				end
				
				if scaleHealthWaitID2 != nil then
					Wait.stop(scaleHealthWaitID2)
				end
				
				scaleHealthWaitID = Wait.time(	function()

							if previousHCountObj == object and not isHovered(object)
							then
								scaleHealthWaitID2 = Wait.time(function ()
									if object != nil then
										object.editButton({index = 0, position = locOldPos, scale = locOldScale, rotation = {0,180,0}, color = {r=0,g=0,b=0,a=0}})
										previousHCountObj = nil
										local i = 0
										for _, entry in pairs (object.getButtons()) do
											if i > 0 then
												object.removeButton(i)
											end
											i = i +1
										end
									end
								end, 0.5)
							else
								onObjectHover(player_color, object)
							end
				end, 0.2)
				
			end
		end
		
		if lifeforms != 'Sangrevores' then
			if locInteractible then
				if previousNoiseObj != nil and object != previousNoiseObj then
					previousNoiseObj.clearButtons()
					previousNoiseObj = nil
				end
			end
			
			if locNoiseObj != nil then
				previousNoiseObj = locNoiseObj
			end
		end
	end
end

function motionTrackerAction(noiseMarker)
	if not scriptEnabled then
		return true
	end
	
	local locValue = math.random(1,10)
	
	if rollAnimationEnable and lastDiceValue != 0 then
		locValue = lastDiceValue
	end
	
	rolldice('yellow', locValue)
	
	local corridorTag = 'corridor4'
	local deadlyTag = 'deadly4'
	
	if yellowOneroll == 1 then
		corridorTag = 'corridor1'
		deadlyTag = 'deadly1'
	
	elseif yellowOneroll == 2 or yellowOneroll == 3 then
		corridorTag = 'corridor2'
		deadlyTag = 'deadly2'

	elseif yellowOneroll == 4 or yellowOneroll == 5 then
		corridorTag = 'corridor3'
		deadlyTag = 'deadly3'

	elseif yellowOneroll > 8 then
		corridorTag = ''
		deadlyTag = ''
	end	
	
	if not rollAnimationEnable then
		broadcastToAll(yellowOne,{0.992,0.796,0.29})	
	end
	
	if not rollAnimationEnable or (rollAnimationEnable and lastDiceParams != nil) then

		local locCor = getTaggedObjAtPos('Corridors', noiseMarker.getPosition(), 0)
		
		if locCor.hasTag(corridorTag) or (deadlyMode and locCor.hasTag(deadlyTag)) then
			encounter(locCor)
			noiseMarker.destruct()
		else
			noiseMarker.destruct()
		end
		resetDiceParams()
	else
		if lastDiceParams == nil then
			lastDiceParams = noiseMarker
			lastDiceParamsType = 'object'
			local locPos = noiseMarker.getPosition() + Vector(4,4,0)
			rollBowl.setPosition(locPos)
			noiseRollDice.setPosition(locPos+Vector(0,1,0))
			
			if rollMode then
				broadcastToAll('복도의 위험을 확인하기 위해 소음 주사위를 굴리세요.', {1,1,1})
				
			else
				for i = 1, math.random(2,3) do
					noiseRollDice.roll()
				end
				Wait.time(function() returnDiceValue(noiseRollDice, lastDiceParams, 'noise') end, 0.25)
			end

		end
	end
end

function alarmRoomAction(noiseMarker, pColor, alt_click)
	if not scriptEnabled then
		return true
	end
	
	if alt_click then
		noiseMarker.destruct()
	else
		local locCor = getTaggedObjAtPos('Corridors', noiseMarker.getPosition(), 0)
		if locCor != nil then
			encounter(locCor)
			noiseMarker.destruct()
		end
	end
end

function isHovered(object)
	if not scriptEnabled then
		return true
	end
	
	for _, entry in pairs(Player.getPlayers()) do
		if entry.getHoverObject() != nil then
			if entry.getHoverObject() == object then
				return true
			end
		end
	end
	return false
end

function onObjectEnterContainer(container, enter_object)
	if scriptEnabled then
		local locContainNotes = container.getGMNotes()
		local locEnterNotes = enter_object.getGMNotes()
		
		local locUseSangrevores = lifeforms == 'Sangrevores'
		
		
		if locEnterNotes == 'action' and container.getName() == '' then
			container.setGMNotes('actionDiscard')
			if locUseSangrevores then
				if enter_object.hasTag('Infection') and enter_object.getRotation().z > 175 and enter_object.getRotation().z < 185 then
					container.shuffle()
				end
			end
	 

		elseif container == intruderBag then
			if not sound1Used and not sound2Used then
				playsounds(34)
			end
			
		elseif container == ammoBag then
			if not sound1Used then
				playsounds(math.random(84,89))
			end
			
		elseif container == secureBag then
			if not sound1Used then
				playsounds(52)
			end
			
		elseif container.getGMNotes() == 'secure' then
			if container.getQuantity() > 3 then
				for i = 1, (container.getQuantity() - 3) do
					container.takeObject({
						position = secureBag.getPosition() + Vector(0,2+i,0),
					})
				end
				
				broadcastToAll('보안 토큰이 주머니로 반환되었습니다. 방 당 최대 3개의 보안 토큰만 허용됩니다.',{1,1,1})
				
			end
			
		elseif locEnterNotes == 'greenitem' then
			container.setGMNotes('greenitemDiscard')
			
		elseif locEnterNotes == 'reditem' then
			container.setGMNotes('reditemDiscard')
			
		elseif locEnterNotes == 'yellowitem' then
			container.setGMNotes('yellowitemDiscard')
			
			
		elseif locEnterNotes == 'attack' then
			container.setGMNotes('attackDiscard')
		
		elseif locEnterNotes == 'shadow' and container != shadowBag then
			container.setGMNotes('shadowDiscard')
		
		elseif container == doorBag then
			local locDoorSound = 23
			
			if math.random() > 0.5 then
				locDoorSound = 183
			end
			
			playsounds(locDoorSound)
			
		elseif container == malfunctionBag then
			playsounds(math.random(77,79))
			
		elseif container == fireBag then
			playsounds(math.random(97,98))
					
		elseif locEnterNotes == 'wound' then
			container.setGMNotes('seriouswoundDiscard')
		
		elseif locEnterNotes == 'event' then
			container.setGMNotes('eventDiscard')
			
		elseif locEnterNotes == 'exploration' then
			container.setGMNotes('explorationDiscard')
		
		
		elseif container == nestBag then
			nestBag.setColorTint(Color(1,1,1))
			
		elseif (locContainNotes == 'actionDiscard' and enter_object.getName() == 'Shared Contractor') or (container.getName() == 'Shared Contractor' and locEnterNotes == 'actionDiscard') then
			container.shuffle()
			container.setName('')
			
		-- elseif locEnterNotes == 'xyrianActivation' and (locContainNotes == 'xyrianActivation' or locContainNotes == 'xyrianActivationDiscard') then
			-- container.setGMNotes('xyrianActivationDiscard')
		end
	end
end


canEnlarge = true
canEnlargeWaitID = nil

function canEnlargeToggle()
	if not scriptEnabled then
		return true
	end
	
	canEnlarge = false
	if canEnlargeWaitID != nil then
		Wait.stop(canEnlargeWaitID)
	end
	canEnlargeWaitID = Wait.time(function() canEnlarge = true end, 2)
end

function xyrianOnBoard()
	if not scriptEnabled then
		return true
	end
	
	if useXyrian then
		for _, castObj in pairs(getAllObjects()) do
			local locCastPos = castObj.getPosition()
			local locBoarderPos = boarderTile.getPosition()
			local locBoarderSize = boarderTile.getBounds().size
			if math.abs(locCastPos.x - locBoarderPos.x) < locBoarderSize.x and math.abs(locCastPos.z - locBoarderPos.z) < locBoarderSize.z then
				if castObj.getGMNotes() == 'xyrian' then
					return true
				end
			end
		end
	end
	
	return false
end

function onObjectLeaveContainer(container, object)
	if scriptEnabled then
	
		local locEnemyFig = false
	
		if object.hasTag('healthCount') then
			local locReset = 0
			
			if lifeforms == 'Neoflesh' then
				if container == queenFBag then
					locReset = 0-2*(3-queenBag.getQuantity())
				end
			end
			Wait.frames(function()
				object.setVar("count",locReset)
				object.call("updateDisplay")
			end, 1)
			
			if trapCheck then
				if object.hasTag('trapped') then
					object.removeTag('trapped')
				end
			end
			
		end
		
		if container == intruderBag then
		
			if object.getGMNotes() == 'xyrianToken' then
				broadcastToAll('자이리안 토큰이 뽑혔습니다. 자이리안 활성화를 해결하고 추적자를 새 자이리안으로 교체하세요.', xyrianColor)
				if not sound4Used then
					playsounds(math.random(167,178))
				end
			end
			
			canEnlargeToggle()
		
		elseif container == larvaeFBag then
			locEnemyFig = true
			
			if lifeforms == 'Neoflesh' then
				
				if math.random() > 0.7 then
					newSeed()
					playsounds(math.random(219,221))
				else
					newSeed()
					playsounds(math.random(214,215))
				end
			else
				if not sound4Used then
					playsounds(119)
				end
				
				if lifeforms == 'Carnomorph' then
					if object.hasTag('eaten') then
						object.removeTag('eaten')
					end
				end
			end
			
			canEnlargeToggle()
			
		elseif container == adultFBag or container == breederFBag then
			locEnemyFig = true
			
			if lifeforms == 'Neoflesh' then
				if container == adultFBag then
					playsounds(math.random(234, 235))
				else
					playsounds(math.random(219,221))
				end
			else
				playsounds(math.random(0,3))
			end
			
			canEnlargeToggle()
			
		elseif container == firespitterFBag then
			locEnemyFig = true
			
			playsounds(math.random(219,221))
			
			canEnlargeToggle()
			
			
		elseif container == ironcladFBag then
			locEnemyFig = true
			
			if math.random() > 0.7 then
				newSeed()
				playsounds(math.random(219,221))
			else
				newSeed()
				playsounds(math.random(211, 212))
			end
		
			canEnlargeToggle()
			
		elseif container == crawlmineFBag then
			locEnemyFig = true
			
			if math.random() > 0.7 then
				newSeed()
				playsounds(math.random(219,221))
			else
				newSeed()
				playsounds(math.random(207, 208))
			end
		
			canEnlargeToggle()
			
		elseif container == queenFBag then
			locEnemyFig = true
			
			if lifeforms != 'Neoflesh' then
				for _, waitID in pairs ({sound1WaitID, sound2WaitID}) do
					if waitID != nil then
						Wait.stop(waitID)
					end
				end
				
				for i = 1, 2 do
					stopSoundBoard(i)
				end
				
				playsounds(4)
				
				sound2Used = true
				Wait.time(function()
					sound2Used = false
				end, soundDuration[4+1])
				
			else
			
				local locQueenSound = math.random(193,199)
				for _, waitID in pairs ({sound3WaitID, sound4WaitID, sound5WaitID, sound6WaitID}) do
					if waitID != nil then
						Wait.stop(waitID)
					end
				end
				
				for i = 1, 4 do
					stopSoundBoard(i+2)
				end
			
				playsounds(locQueenSound)
				sound4Used = true
				sound6Used = true
				
				Wait.time(function()
					sound4Used = false
					sound6Used = false
				end, soundDuration[locQueenSound+1])
				
			end

			
			canEnlargeToggle()
			
		elseif container == secureBag then
			if not sound2Used then
				playsounds(math.random(84,89))
			end

		elseif container == queenHealthDeck then
			if lifeforms == 'Neoflesh' then
				playsounds(math.random(200,206))
			else
				playsounds(math.random(1,3))
			end

		elseif container == greenItemsDeck or container == redItemsDeck or container == yellowItemsDeck or container == startItemDeck then
			playsounds(math.random(108,115))
			if object.getName() == 'ductTape' then
				object.use_snap_points = false
			end
			
			if object.hasTag('StartItem') or object.hasTag('StartItem2') then
				setupEquipment(object)
			end

		elseif container == contaminationDeck then
			if lifeforms == 'Sangrevores' then
				playsounds(math.random(135,138))
			else
				playsounds(19)
			end

		elseif container == ammoBag or container == grenadeBag or container == oxygenBag or container == medpackBag then
			object.setRotation({0,180,0})
			playsounds(math.random(108,115))
			
			if container == ammoBag then
				if object.getStateId() == 2 then
					Wait.time(function() object.setState(1) end, 1.75)
				end
			end
			
		elseif container == malfunctionBag then
			if not sound1Used and not sound2Used then
				playsounds(46)
			end
			
		elseif container == doorBag then
			if not sound2Used then
				playsounds(24)
			end
			
		elseif container == fireBag then
			local locExplosionSound = math.random(32,33)
			
			newSeed()
			if math.random() > 0.66 then
				locExplosionSound = 189
			end
			
			playsounds(locExplosionSound)
			lightFire()

		elseif container == seriouswoundDeck then
			playsounds(math.random(6,10))
			playsounds(math.random(118,120))
		

		elseif 	container == xyrianTracerBag then
			playsounds(240)
			
		elseif container == xyrianFBag or container == xyrianInjuryBag then
			locEnemyFig = true
			
			playsounds(math.random(167,178))
		
		elseif container == eventDeck then
			
			if useXyrian then
				if not xyrianActivationRound and xyrianOnBoard() then
					object.setPositionSmooth(eventDeck.getPosition() + Vector(0,5,0))
					object.setLock(true)
					broadcastToAll('이벤트 카드를 뽑기 전에 모든 플레이어가 패스, 턴 종료를 누르고 자이리안 단계를 해결해야 합니다.', xyrianColor)
					
					Wait.time(function()
						object.setLock(false)
						object.drop()
					end, 2)
				end
			end
		
		elseif container == nestBag then
			playsounds(math.random(25,28))
			if nestBag.getQuantity() == 0 then
				nestBag.setColorTint(Color(0.39,0.39,0.39,0.39))
				broadcastToAll('둥지가 파괴되었습니다!', lifeformColor)
			end

			
		elseif container == eggBag then
			playsounds(math.random(25,28))
		
		elseif container == dataTokenBag then
		
			if insiderEnable and insiderStoryGUID != '' then
				local locInsiderStory = gO(insiderStoryGUID)
				
				if locInsiderStory != nil then
					if locInsiderStory.hasTag('insiderEffectNoData') then
						dataTokenBag.putObject(object)
						broadcastToAll(insiderWarningMsg, insiderColor)
						return true
					end
				end
			end

			playsounds(math.random(12,18))
			
		elseif container == trapBag then
			table.insert(trapsList, object)
		end
		
		if locEnemyFig then
			if object.hasTag('returning') then
				object.removeTag('returning')
			end
		end
	end
end

playerMoveStartRoomGUID = nil
playerMoveFigureGUID = ''
function onObjectPickUp(player_color, object)
	if scriptEnabled then
	
		local locGM = object.getGMNotes()
		
		if object.getDescription() == 'UAV' then
			playsounds(153)
		elseif object == shuttleFigure then
			playsounds(180)
		elseif object == lastPickedDice or object == noiseRollDice then
			rollBowl.setPosition({0,-7,0})
			
		elseif locGM == 'dog' then
			playsounds(math.random(148,152))
			
		elseif lifeforms == 'Sangrevores' then
			local locFigGUID = object.getGUID()
			if playerMoveStartRoomGUID == nil or locFigGUID != playerMoveFigureGUID then
				if object.hasTag('characterFig') then
					local locRoom = getTaggedObjAtPos('room', object.getPosition(), 0)
					if locRoom != nil then
						playerMoveStartRoomGUID = locRoom.getGUID()
						playerMoveFigureGUID = locFigGUID
					end
				end
			end
		end
	end
end

doorDropping = false
walkSoundState = 0
function onObjectDrop(player_color, object)

	if scriptEnabled then
		local locGM = object.getGMNotes()
		local locDesc = object.getDescription()
		
		if object == autoDestructionToken or object == ventToken or object == alertToken then
			playsounds(5)
			lightAlert()
		
		elseif object.hasTag('intruder') or locGM == 'xyrian' or object.getName() == 'insiderFig' then
			if walkSoundState == 0 then
				walkSoundState = 1
				Wait.time(function() walkSoundState = 0 end, 1)
				for _, castObj in pairs (shapeCast(object.getPosition(),{0.5,18,0.5})) do
					if castObj.hasTag('room') or castObj.hasTag('Corridors') then
						walkSoundState = 2
						walksounds(object)
						break
					end
				end
			elseif walkSoundState == 2 then
				walksounds(object)
			end
		elseif locDesc == 'door' then
			doorDropping = true
		elseif object.hasTag('Corridors') or object.hasTag('room') then
			Wait.time(function() object.setLock(true) end, 1.5)
		elseif object == turnMarker then
			playbombticks(math.random(2,7))
			broadcastToAll('라운드 마커가 이동했습니다.', {1,1,1})
		elseif locDesc == 'UAV' then
			playsounds(-1)
			playsounds(154)
			
		elseif locGM == 'dog' then
			playsounds(-1)
			playsounds(math.random(140,147))
			
		elseif locGM == 'trap' then
			playsounds(-1)
			playsounds(163)
			
		elseif object == shuttleFigure then
			playsounds(-1)
			playsounds(181)
			
			if insiderEnable and insiderStoryGUID != '' then
				local locInsiderStory = gO(insiderStoryGUID)
				
				if locInsiderStory != nil then
					for _, tag in pairs (locInsiderStory.getTags()) do
						if string.find(tag, 'insiderEffectLanderDrop') != nil then
							autoInsider(2, tag)
						end
					end
				end
			end
			
		elseif object == lastPickedDice then
			returnDiceValue(object, lastDiceParams)
			
		elseif object == noiseRollDice then
			if rollAnimationEnable then
				if lastDiceParamsType != nil then
					
					if lastDiceParamsType == 'object' then
						if lastDiceParams.getName() == 'Noise' then
							returnDiceValue(object, lastDiceParams, 'noise')
							if not rollMode then
								object.roll()
							end
						end
					end
				else
					local locFigGUID = playerInfoTable[player_color].figureGUID
					if locFigGUID != '' then
						lastDiceParams = gO(locFigGUID)
						returnDiceValue(object, lastDiceParams, 'GUID')
						if not rollMode then
							object.roll()
						end
					end
				end
			end
		elseif object == robot and setupComplete then
			if locGM == '' then
				if getTaggedObjAtPos('room', robot.getPosition(), 0) != hiddenRoom then
					for _, entry in pairs(getAllObjects()) do
						if entry.hasTag('RobotCard') then
							entry.flip()
							broadcastToAll(entry.getName() .. '이(가) 활성화되어 공개되었습니다.', lifeformColor)
							break
						end
					end
					
					robot.setGMNotes('active')
					if robotToken != nil then
						robotToken.setState(1)
					end
				end
			end
		elseif object.hasTag('Infection') then
			if lifeforms == 'Sangrevores' and object.getPosition().z > contaminationDeck.getPosition().z then
				sendToBottomDeck(object,contaminationDeck)
			end
		
		elseif insiderEnable and insiderStoryGUID != '' then
			local locInsiderStory = gO(insiderStoryGUID)
			if locInsiderStory != nil then
				if object.hasTag('characterFig') then
					local locPlayerFig = false
					local locPlayerColor = ''
					
					for color, entry in pairs (playerInfoTable) do
						if entry.figureGUID == object.getGUID() then
							locPlayerFig = true
							locPlayerColor = color
							break
						end
					end
					
					if locPlayerFig then
						for _, tag in pairs (locInsiderStory.getTags()) do
							if string.find(tag, 'insiderEffectMove') != nil then
								autoInsider(2, tag, nil, locPlayerColor)
							end
						end
					end
				end
			else
				if insiderDeck != nil then
					print('내부자 스토리 카드를 찾을 수 없습니다. 가방이나 덱에 넣지 마시고 삭제하지 마세요. :(')
				else
					insiderStoryGUID = ''
					insiderEnable = false
					broadcastToAll('인사이더 덱이 상자 안에 있습니다. 스크립트는 인사이더 모드가 비활성화된 것으로 간주합니다.', insiderColor)
				end
			end
		-- elseif locDesc == 'signal' then
			-- playsounds(95)
		-- elseif locDesc == 'slime' then
			-- playsounds(96)
		end
	end
end

function auditDiceRoll(dice)
	if not scriptEnabled then
		return true
	end
	
	returnDiceValue(dice, lastDiceParams)
	local locPos = dice.getPosition()
	Wait.frames(function()
		local locVector = (dice.getPosition() - locPos)* Vector(1,1,0)
		local locSpeed = dotMath(locVector, locVector)/Time.delta_time
		
		if locSpeed < 0.35 then
			dice.roll()
		end
	end, 1)
end

function onObjectNumberTyped(object, player_color, number)
	if scriptEnabled then
		local locPCol = player_color
		
		if actCol then
			locPCol = getNearestPColor(object.getPosition().x)
		end
		
		local locGM = object.getGMNotes()
		
		if number == 0 then
		
			local pos
			local rot = {0,180,180}
			local match = false
			if locGM == 'action' then
				match = true
				pos = gO(playerInfoTable[locPCol].boardGUID).getPosition() + Vector(6.17, 3, 1.64)
				rot = {0,180,0}
				
				mayRerollNextShoot = object.hasTag('mayShootRerollAction')
				mayRerollNextBurst = object.hasTag('mayBurstRerollAction')
				
			elseif locGM == 'actionDiscard' then
				match = true

				pos = gO(playerInfoTable[locPCol].boardGUID).getPosition() + Vector(-6.12, 3, 1.64)
				rot = {0,180,180}
				object.shuffle()	
				
			elseif locGM == 'ammo' then
				ammoBag.putObject(object)
				
			elseif locGM == 'grenade' then
				grenadeBag.putObject(object)
				
			elseif locGM == 'oxygen' then
				oxygenBag.putObject(object)
				
			elseif locGM == 'medpack' then
				medpackBag.putObject(object)
			
			elseif locGM == 'greenitem' then
				sendToBottomDeck(object, greenItemsDeck)
				playsounds(math.random(108,115))
			
			elseif locGM == 'reditem' then
				sendToBottomDeck(object, redItemsDeck)
				playsounds(math.random(108,115))
				
			elseif locGM == 'yellowitem' then
				sendToBottomDeck(object, yellowItemsDeck)
				playsounds(math.random(108,115))
				
			elseif locGM == 'attack' then
				match = true
				pos = {23,3,7}
				rot = {0,180,0}
			
			elseif locGM == 'wound' then
				match = true
				pos = {29, 5, 7}
				rot = {0,180,0}
				playsounds(math.random(6,10))
				playsounds(math.random(118,120))
			
			elseif locGM == 'seriouswoundDiscard' then
				returnDiscardToDeck(object,seriouswoundDeck)
			
			elseif locGM == 'attackDiscard' then
				if attacksDeck != nil then
					returnDiscardToDeck(object, attacksDeck)
				else
					attacksDeck = object
					object.setPosition({23,3,3})
					object.setRotation({0,180,180})
				end
				
				Wait.time(function() attacksDeck.shuffle() end, 1)
							
			elseif locGM == 'eventDiscard' then
				returnDiscardToDeck(object,eventDeck)

			elseif locGM == 'greenitemDiscard' then
				returnDiscardToDeck(object,greenItemsDeck)
							
			elseif locGM == 'reditemDiscard' then
				returnDiscardToDeck(object,redItemsDeck)
							
			elseif locGM == 'yellowitemDiscard' then
				returnDiscardToDeck(object,yellowItemsDeck)		
			
			elseif locGM == 'explorationDiscard' then
				match = true
				pos = {-24,2,0}
				rot = {0,180,180}
				object.shuffle()
			
			elseif locGM == 'xyrianActivation' then
				sendToBottomDeck(object, xyrianActivationDeck)
				
			elseif locGM == 'xyrianStatus' then
				xyrianStatusBag.putObject(object)
			end
				

			
			if match then
				object.setPosition(pos)
				object.setRotation(rot)
			end
		
		elseif number > 0 and locGM == 'enemybag' then
			local locPos = intruderBag.getPosition() + Vector(0,2,0)
			local locNumber = math.min(number, object.getQuantity())
			for i = 1, locNumber do
				object.takeObject({
					position = {locPos.x, locPos.y + i, locPos.z},
					smooth = false,
					callback_function = function(o) intruderBag.putObject(o) end,
				})
			end
			return true
			
		elseif number > 0 and actCol and (locGM == 'actionDiscard' or locGM == 'action') then
			object.deal(number,locPCol)
			return true
			
		elseif number > 0 and (locGM == 'ammo' or locGM == 'grenade' or locGM == 'oxygen' or locGM == 'medpack' or object == ammoBag or  object == grenadeBag or object == oxygenBag or object == medpackBag) then
		
			if object.hasTag('Bag') then
				local locNumber = math.min(number, object.getQuantity())
				for i = 1, locNumber do
					object.takeObject({position = object.getPosition() + Vector(0,2+i,0),
						callback_function = function(obj) obj.setLock(true) Wait.frames(function() addTacticalItem(obj, player_color) end,(i-1)*6) end,
					})
				end
			else
				object.setLock(true)
				addTacticalItem(object, player_color)
			end
			return true

		end
	end
end

canSendToDeck = true
function sendToBottomDeck(obj, deck)
	if not scriptEnabled then
		return true
	end
	
	if canSendToDeck then
		canSendToDeck = false
		local locPos = deck.getPosition()
		
		deck.setPosition(locPos + Vector(0,1,0))
		obj.setPosition(locPos)
		obj.setRotation(deck.getRotation())
		Wait.time(function() canSendToDeck = true end, 0.5)
	end
end

function addTacticalItem(obj, player)
	if not scriptEnabled then
		return true
	end
	
	local locResPos = zoneHide.getPosition()
	local locBoardPos = gO(playerInfoTable[player].boardGUID).getPosition()
	zoneHide.setPosition(locBoardPos  + Vector(-4.09, 0.38, 1.875))
	zoneHide.setScale({0.5,0.12,3})

	local locSlots = {3.18,2.31,1.43,0.56}
	local locID = 1
	local locDist = 1
	Wait.frames(function()
		if #zoneHide.getObjects(true) == 0 then
			obj.setPosition(locBoardPos+Vector(-4.09,0.38,locSlots[1]))
			obj.setRotation({0,180,0})
		elseif #zoneHide.getObjects(true) < 4 then
			local locEquippedSlots = {}
			
			for _, obj2 in pairs(zoneHide.getObjects(true)) do
				for i = 1, 4 do
					locDist = math.abs(obj2.getPosition().z - (locBoardPos.z + locSlots[i]))
					if locDist > 0 and locDist < 0.5 then
						table.insert(locEquippedSlots,i)
						break
					end
				end
			end
			
			for _, index in pairs(locEquippedSlots) do
				locSlots[index]=0
			end
			for i = 1, 4 do
				if locSlots[i] != 0 then
					locID = i
					break
				end
			end
			obj.setPosition(locBoardPos + Vector(-4.09,0.38,locSlots[locID]))
			obj.setRotation({0,180,0})
		end
		obj.setLock(false)
		zoneHide.setPosition(locResPos)
	end,3)
end

function getNearestPColor(XPos)
	if not scriptEnabled then
		return true
	end
	
	
	local locPCol = ''
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and entry.manualSeat) then
			local locPos = gO(entry.boardGUID).getPosition()
			if XPos > locPos.x - 8 and XPos < locPos.x + 8 then
				locPCol = color
				return locPCol
			end
		end
	end
	
	return locPCol
end

function addContamination(pColor)
	if not scriptEnabled then
		return true
	end
	
	if contaminationDeck != nil and pColor != 'insider' then
		local locPos = Vector(6.17,1,1.76)
		local locRot = {0,180,0}
		local locContMsg = '플레이어 ' .. pColor .. '이(가) '
		
		if lifeforms == 'Sangrevores' then
			locPos = Vector(-6.34,1,1.76)
			locRot = {0,180,180}
			locContMsg = locContMsg .. '감염 카드를 1장 획득했습니다.'
		else
			locContMsg = locContMsg .. '오염 카드를 1장 획득했습니다.'
		end
		
		if lifeforms != 'Sangrevores' and playerHasTag('BiohazardArmor', 0, nil, pColor) then
			loseHealth(pColor)
			broadcastToAll('플레이어 ' .. pColor .. '가 화생방 보호의로 인해 오염 대신 체력 1을 잃었습니다.', lifeformColor)
		else
			if contaminationDeck.getQuantity() > 0 then
				contaminationDeck.takeObject({
					position = gO(playerInfoTable[pColor].boardGUID).getPosition() + locPos,
					rotation = locRot,
					smooth = false,
				})
				broadcastToAll(locContMsg, lifeformColor)
			end
		end
	end		
	
end

function loseHealth(pColor)
	if not scriptEnabled then
		return true
	end
	
	if pColor != 'insider' then
		local locBoard = gO(playerInfoTable[pColor].boardGUID)
		local locHealthObj = gO(playerInfoTable[pColor].healthGUID)
		local locPosX = -4.5
		
		if playerHealthLocalPosX[returnPlayerHealth(pColor) - 1] != nil then
			locPosX = playerHealthLocalPosX[returnPlayerHealth(pColor) - 1]
			broadcastToAll('플레이어 ' .. pColor .. '가 체력 1을 잃었습니다.', lifeformColor)
			
		else
			broadcastToAll('플레이어 ' .. pColor .. '가 체력이 없어 사망했습니다.', lifeformColor)
		end
		
		locHealthObj.setPosition({locBoard.getPosition().x + locPosX,1.99, -15.09}) 
	else
		if insiderCard != nil then
			insiderHealth.setPosition(insiderHealth.getPosition() + Vector(0.62,0,0))
			if insiderHealth.getPosition().x - insiderCard.getPosition().x > 1.47 then
				broadcastToAll('인사이더가 체력이 없어 사망했습니다.', lifeformColor)
				insiderCard.setGMNotes('')
			else
				broadcastToAll('인사이더가 체력 1을 잃었습니다.', lifeformColor)
				playsounds(math.random(249,256))
			end
		end
	end
end

function isInsiderFriendlyAlive()
	if not scriptEnabled then
		return true
	end
	
	insiderRecall()
	
	if insiderFig == nil then
		return false
	end
	
	if insiderCard != nil then
		if insiderCard.getGMNotes() == 'active' and (insiderCard.getRotation().z < 10 or insider.getRotation().z > 350) then
			return not (insiderHealth.getPosition().x - insiderCard.getPosition().x > 1.47)
		end
	end
	
	return false
end

reinforceTurn = true
xyrianEventEffect = true
function onObjectRotate(object, spin, flip, player_color, old_spin, old_flip)
	local locGM = object.getGMNotes()
	
	if spin == old_spin and scriptEnabled then
		if object.hasTag('characterFig') and flip == 180 then
			object.setLock(true)
			object.setRotation({0,object.getRotation().y, 180})
		
		elseif object.hasTag('playerHelp') and flip == 180 then
			local locNearCol = getNearestPColor(object.getPosition().x)
			if isPlayerAlive(locNearCol) then
				
				
				local locBoard = gO(playerInfoTable[locNearCol].boardGUID)
				
				local locLungs = true
				local locGuts = true
				local locBleeding = true
				
				
				local locBoardObjs = shapeCast( locBoard.getPosition(), locBoard.getBounds().size)
				
				for _, locObj in pairs(locBoardObjs) do
					local locRotZ = locObj.getRotation().z 
					local locActive = locRotZ < 10 or locRotZ > 350
					
					for _, tag in pairs (locObj.getTags()) do
						if tag == 'PassLungs' and locActive and locLungs then
						
							locLungs = false
							for _, locObj2 in pairs (locBoardObjs) do
								
								if locObj2.hasTag('CharacterTile') then
									if locObj2.getName() != 'Android' then
										if locObj2.getVar("count") <= 0 then
											loseHealth(locNearCol)
											loseHealth(locNearCol)
											broadcastToAll('플레이어 ' .. locNearCol .. '가 폐 심각 부상으로 체력 2를 잃었습니다', lifeformColor)
										else
											locObj2.setVar("count", math.max(0,locObj2.getVar("count") -1))
											locObj2.call("updateDisplay")
											broadcastToAll('플레이어 ' .. locNearCol .. '가 폐 심각 부상으로 산소 1을 잃었습니다', lifeformColor)
											break
										end
									end
								end
							end
						elseif tag == 'PassGuts' and (locActive or locObj.hasTag('insiderStory')) and locGuts then
						
							if lifeforms != 'Sangrevores' then
								locGuts = false
								addContamination(locNearCol)
							end
							
						elseif tag == 'PassBleeding' and locActive and locBleeding then
							
							locBleeding = false
							loseHealth(locNearCol)
							broadcastToAll('플레이어 ' .. locNearCol .. '가 출혈 심각 부상으로 체력 1을 잃었습니다.', lifeformColor)
							
						
						elseif tag == 'PassNBCSuit' then
						
							for _, locObj2 in pairs (locBoardObjs) do
								if locObj2.hasTag('CharacterTile') then
									locObj2.setVar("count", math.min(7,locObj2.getVar("count") + 1))
									locObj2.call("updateDisplay")
									broadcastToAll('플레이어 ' .. locNearCol .. '가 NBC 방호복으로 산소 1을 얻었습니다.', {1,1,1})
									break
								end
							end
							
						elseif tag == 'PassLifeSupportTech' then
						
							for _, locObj2 in pairs (locBoardObjs) do
								if locObj2.hasTag('CharacterTile') then
									locObj2.setVar("count", math.min(7,locObj2.getVar("count") + 7))
									locObj2.call("updateDisplay")
									broadcastToAll('플레이어 ' .. locNearCol .. '가 자이리안 생명 유지 기술로 산소 7을 얻었습니다.', xyrianColor)
									break
								end
							end
							
						elseif tag == 'PassOxy' then
							for _, locObj2 in pairs (locBoardObjs) do
								
								if locObj2.hasTag('CharacterTile') then
									
									local locOxyName = '산소'
									
									if locObj2.getName() == 'Android' then
										locOxyName = '배터리'
									end
									
									locObj2.setVar("count", math.max(0,locObj2.getVar("count") -1))
									locObj2.call("updateDisplay")
									broadcastToAll('플레이어 ' .. locNearCol .. '가 ' .. locOxyName .. ' 1을 잃었습니다.', lifeformColor)
									break
								end
							end
						elseif tag == 'PassCEOWound' then
						
							for _, locObj2 in pairs (locBoardObjs) do
								if locObj2.getGMNotes() == 'malfunction' then
									
									if locObj2.getPosition().z > locBoard.getPosition().z + 3 then
										loseHealth(locNearCol)
										addContamination(locNearCol)
										break
									end
									
								end
							end
							
						end	
					end
					
					local locName = locObj.getName()
					
					if locName == 'ENVENOMED' then
					
						for _, locObj2 in pairs (locBoardObjs) do
							if locObj2.hasTag('CharacterTile') then
								if locObj2.getName() != 'Android' then
									locObj2.setVar("count", math.max(-2,locObj2.getVar("count") - 1))
									locObj2.call("updateDisplay")
									break
								end
							end
						end
						loseHealth(locNearCol)
						broadcastToAll('플레이어 ' .. locNearCol .. '가 자이리안 독으로 산소 1과 체력 1을 잃었습니다.', xyrianColor)
						
					elseif locName == 'MARKED' then
						registerToRoomsMap() --:(
						local locXyrians = {}
						local locExpectedXyrians = 3-xyrianFBag.getQuantity()
						local locIntruders = {}
						
						if locExpectedXyrians > 0 then
							for _, obj in pairs (getAllObjects()) do
								if obj.getGMNotes() == 'xyrian' then
									table.insert(locXyrians, obj)
								elseif obj.hasTag('intruder') then
									table.insert(locIntruders, obj)
								end
							end
							
							local locMarkedRoomGUID = nil
							for color, playerRoomGUID in pairs (getPlayerRoomsInFirstTurnOrder()) do
								if color == locNearCol then
									locMarkedRoomGUID = playerRoomGUID
									break
								end
							end
							
							local locMoveGroups = {}
							local locStartTiles = {}
							for i = 1, #locXyrians do
								
								local locStartTile = getTaggedObjAtPos('room', locXyrians[i].getPosition(), 0)
								local locUnique = true
								
								for _, startTile in pairs (locStartTiles) do
									if locStartTile == startTile then
										locUnique = false
										break
									end
								end
								
								if locUnique and locStartTile.getGUID() != locMarkedRoomGUID then
									table.insert(locStartTiles, locStartTile)
								
									for j = 1, #locXyrians do
										if distanceMath(locXyrians[j].getPosition(), locStartTile.getPosition()) < tileImportedSize.x then
											if locMoveGroups[#locStartTiles] == nil then
												locMoveGroups[#locStartTiles] = {}
											end
											table.insert(locMoveGroups[#locStartTiles], locXyrians[j])
										end
									end
								end
							end
							

							
							if #locStartTiles > 0 then
								autoMoveToGoal(locStartTiles, locMoveGroups, locIntruders, {}, {}, {locMarkedRoomGUID})
								Wait.time(function()
								
									locStartTiles = {}
									local locMoveGroups2 = {}
									for i = 1, #locMoveGroups do
										local locNewRoom = getTaggedObjAtPos('room', locMoveGroups[i][1].getPosition(), 0)
										
										if locNewRoom.getGUID() != locMarkedRoomGUID and locNewRoom != nil then
											table.insert(locStartTiles, locNewRoom)
											table.insert(locMoveGroups2, locMoveGroups[i])
										end
									end
									
									if #locStartTiles > 0 then
										autoMoveToGoal(locStartTiles, locMoveGroups2, locIntruders, {}, {}, {locMarkedRoomGUID})
									end
								end, #locMoveGroups)
							end
							
						end
					end
					
				end
				
				if insiderEnable and insiderStoryGUID != '' then
					local locInsiderStory = gO(insiderStoryGUID)
					
					if locInsiderStory != nil then
						for _, tag in pairs (locInsiderStory.getTags()) do
							if string.find(tag, 'insiderEffectPass') != nil then
								autoInsider(2,tag, nil, locNearCol)
							end
						end
					end
				end
				Wait.time(function() object.setLock(true) end, 1)
			end
		elseif object.hasTag('Corridors') then
			if flip == 0 then
			
				sound1Used = false
				playsounds(46)
				playsounds(74)
				
				
			else


				if seatedPlayers < 6 or reinforceTurn then
					sound1Used = false
					playsounds(76)
					playsounds(77)
					reinforceTurn = false
				else
					local locPos = object.getPosition()
					object.setLock(true)
					local locRot = object.getRotation()
					locRot[3] = 0
					object.setRotation(locRot)
					object.setPosition(locPos)
					broadcastToAll('5명 초과 플레이어의 게임 균형을 위해, 복도 강화는 턴당 한 번으로 제한됩니다.', {1,1,1}) --Seems fair right ?
				end
			end
		
		elseif (locGM == 'tainted' or locGM == 'mutation') and flip == 0 then
			if setupComplete then
				playsounds(139)
			end
		
		elseif locGM == 'exploration' and flip == 0 then
			if setupComplete then
				autoExplore(object)
			end
			
		elseif locGM == 'attack' and flip == 0 then
			playsounds(math.random(1,3))
		
		elseif locGM == 'event' and flip == 0 then
			playsounds(53)
			local locWait = 0
			
			if lifeforms == 'Neoflesh' then
				--broadcastToAll('Proceed to Twitchling Activation.', lifeformColor)
				broadcastToAll((5-cultistDeadBag.getQuantity())..'명의 광신도가 아직 살아 있습니다.', lifeformColor)
			end
					
			if autoEventEnable then
				if not allPassed then
					broadcastToAll('자동 이벤트가 작동하려면 모든 플레이어가 패스(플레이어 도움 카드 뒤집기)를 누르고 턴 종료를 클릭해야 합니다.', {1,1,1})
				elseif attackButtonCount > 0 then
						broadcastToAll('남은 ' .. attackButtonCount .. '개의 침입자 공격 버튼을 처리한 후 이벤트 카드를 뒤집어 자동 이벤트를 시작하세요.', {1,1,1})
				else
					
					proceedToNextPhase = false
					object.setLock(true)
					object.setRotation({0,180,0})
					
					if useXyrian then --rest of xyrian phase
						
						if xyrianOnBoard() then
							
							local locXyrians = {}
							local locIntruders = {}
							local locXyrianChecked = false --There are only 3 xyrians, so 2 scenarios are possible for true, either we find a group of 2 or a group of 3.
							
							local locXyrianToken = gO(xyrianTokenGUID)
							if locXyrianToken != nil then
								intruderBag.putObject(locXyrianToken)
							end
							
							for _, entry in pairs(getAllObjects()) do
								local locGM2 = entry.getGMNotes()
								if locGM2 == 'xyrian' then
									table.insert(locXyrians, entry)
									
									
								elseif entry.hasTag('intruder') then
									table.insert(locIntruders, entry)
								end
							end
							
							local locXyrianEventName = ''
							for _, xyrianEventGUID in pairs (xyrianEventGUIDs) do
								local locXyrianEvent = gO(xyrianEventGUID)
								
								if locXyrianEvent != nil then
									locXyrianEventName = locXyrianEvent.getName()
									break
								end
							end
							
							
							
							if locXyrianEventName == 'QUEEN TRACKING' and xyrianEventEffect then
								locWait = locWait + #locXyrians*1.5 + 2.5
								Wait.time(function()
									xyrianHuntQueen(locXyrians, locIntruders, true)
								end, 2)
							
							elseif locXyrianEventName == 'SERVANT HUNT' then
								if (xyrianAllegiance.getRotation().z < 5 or xyrianAllegiance.getRotation().z > 355) and xyrianEventEffect then
									locWait = locWait + #locXyrians +2
									local locWait2 = 0
									Wait.time(function()
										
										local locAllegiancePlayer = getNearestPColor(xyrianAllegiance.getPosition().x)
										local locAllegianceRoomGUID = getRoomAtPlayer(locAllegiancePlayer).getGUID()
										
										for _, xyrian in pairs (locXyrians) do
											if xyrian != nil then
												local locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
												
												if locXyrianRoom.getGUID() != locAllegianceRoomGUID then
													local w = locWait2
													locWait2 = locWait2 + 0.6
													Wait.time(function()
														autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locAllegianceRoomGUID})
														
														Wait.time(function()
															locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
															if locXyrianRoom.getGUID() != locAllegianceRoomGUID then
																autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locAllegianceRoomGUID})
															end
														end, 0.3)
													end, w)
													
													
												end
												
											end
										end
										
									end,2)
								end
							end
							
							
							Wait.time(function()
								for _, xyrian in pairs (locXyrians) do
									if xyrian != nil then
										if not locXyrianChecked then
											local locRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
											
											local locXyrianStats = {}
											local j = 1
											for _, locObj in pairs (shapeCast(locRoom.getPosition(), locRoom.getBounds().size)) do
												if locObj.getGMNotes() == 'xyrian' then
													
													local locInjured = 0
													if locObj.getName() == 'injured' then
														locInjured = 100
													end
													
													locXyrianStats[j] = {locObj, locObj.getVar("count") + locInjured}
													j = j + 1
													
												end
											end
											
											if j > 2 then
												locXyrianChecked = true
												
												local locMinIndex = 1
												local locMinCount = 1000
												j = 1
												
												for _, entry3 in pairs (locXyrianStats) do
													local locMin = locMinCount
													locMinCount = math.min(entry3[2], locMinCount)
													
													
													if locMin != locMinCount then
														locMinIndex = j
													end
													j = j+1
												end
												
												local locXyrian = locXyrianStats[locMinIndex][1]
												if locXyrian.getName() == 'injured' then
													local locInjuryToken = getTaggedObjAtPos('xyrianInjury', locRoom.getPosition(), 3, locRoom.getBounds().size)
													if locInjuryToken != nil then
														locInjuryToken.setLock(false)
														xyrianInjuryBag.putObject(locInjuryToken)
													end
													locXyrian.setName('')
												end
												local locXyrPos = locXyrian.getPosition()
												xyrianTracerBag.takeObject({
													position = xyrianTracerBag.getPosition() + Vector(0,5,0),
													callback_function = function(o)
														o.setPositionSmooth(locXyrPos, false, false)
													end,
												})
												enemyFigReturn(locXyrian)
												
											end
										end
									end
								end
							end, locWait+1)
						end
					end
					
					Wait.time(function()
						proceedToNextPhase = true
						autoEvent(object)
					end, locWait+1.5)
					
				end
			end
			
			
		elseif locGM == 'trap' and flip == 180 then
			playsounds(-1)
			playsounds(162)
			
			
		elseif string.find(locGM,'xyrian') != nil and flip == 0 then
			if flip == 0 then
				playsounds(math.random(167,178))
				if locGM == 'xyrianActivation' and autoEventEnable then
					xyrianActivationSeq(object)
				elseif locGM == 'xyrianExplore' then
					registerToRoomsMap() --that's because of manually placed corridors :(
					
					local locXyrianToken = gO(xyrianTokenGUID)
					if locXyrianToken != nil then
						intruderBag.putObject(locXyrianToken)
					end
					broadcastToAll(removeWarning,xyrianColor)
					object.drop()
					object.setPosition({-27,3,-0.41})
					object.setRotation({0,180,0})
					

					
					if object.hasTag('xyrianExploreAdd') then
						if xyrianTracerBag.getQuantity() > 0 then
							
							for _, obj in pairs(getAllObjects()) do
								if obj.hasTag('characterFig') then
									local locCor = getTaggedObjAtPos('Corridors', obj.getPosition(), 0)
									
									if locCor != nil then
										xyrianTracerBag.takeObject({
											position = xyrianTracerBag.getPosition() + Vector(0,1,0),
											rotation = {0,180,0},
											callback_function = function(o)
												o.setPositionSmooth(findSpaceOnTile(gO(RoomsMap[locCor.getGUID()][2][1]), nil, true), false, false)
											end,
										})
										break
									end
								end
							end
							

						end
					else
						--xyrianTracerReplace()
						xyrianAllegianceToken.setGMNotes('x')
					end
				elseif locGM == 'xyrianEvent'  and autoEventEnable then
					
					if object.getName() == 'NEW COMMANDS' then
						
						local locCurrentRound = 2 + math.floor ( ((14.58 - turnMarker.getPosition().z) / turnOffset.z) )
						if locCurrentRound <= 5 then
						
							object.setLock(true)
							object.setPositionSmooth({-17.89,1.69,-1.19}, false, true)
							object.setRotation({0,180,0})
							broadcastToAll('분대, 미션 과제 NEW COMMANDS가 이제 목록에 추가되었습니다.', xyrianColor)
						end
						
						if xyrianFBag.getQuantity() > 0 then
							xyrianFBag.takeObject({
								position = findSpaceOnTile(hiddenRoom, nil, true),
								rotation = {0,0,0},
								callback_function = function(o)
									o.setLock(true)
									o.setGMNotes('')
									Wait.condition(function()
										o.setGMNotes('xyrian')
									end, function() return proceedToNextPhase end, 999999, function () end)
								end,
							})
							
							broadcastToAll('자이리안이 동면실에 나타났습니다!', xyrianColor)
						end
					else
						if xyrianTracerBag.getQuantity() > 0 then
							xyrianTracerBag.takeObject({
								position = findSpaceOnTile(hiddenRoom, nil, true),
								rotation = {0,180,0},
							})
							broadcastToAll('자이리안 추적자가 동면실에 추가되었습니다.', xyrianColor)
						end
						
						xyrianEventEffect = false
						object.setLock(true)
						xyrianPhase.setPosition({35,1.57,10.87})
						xyrianPhase.setLock(true)
						object.setPosition({35,1.53,9.37})
						object.setRotation({0,180,0})
						object.drop()
					end
					
					
				end
				
			end
		end
	end
	
end

function getPlayerColorsInFirstTurnOrder(all)
	if not scriptEnabled then
		return true
	end
	
	local locOverride = false
	
	if all != nil then
		locOverride = all
	end
	
	local locFirstColor = getFirstPlayerColor()
	local locColors = {}
	local locFirstColorFound = false
	local locFirstPlayers = 0
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and entry.manualSeat) then	
			if color == locFirstColor then
				locFirstColorFound = true
			end
			if locFirstColorFound then
				if isPlayerAlive(color) or locOverride then
					table.insert(locColors, 1+locFirstPlayers, color)
					locFirstPlayers = locFirstPlayers +1
				end
			else
				if isPlayerAlive(color) or locOverride then
					table.insert(locColors, color)
				end
			end
		end
	end
	return locColors
end

function getPlayerRoomsInFirstTurnOrder(addInsider)
	if not scriptEnabled then
		return true
	end
	
	local locInsider = false
	
	if addInsider != nil then
		locInsider = addInsider
	end
	
	local locColors = getPlayerColorsInFirstTurnOrder()
	local locPlayerTiles = {}
	for _, color in pairs(locColors) do
		local locPlayerPos = gO(playerInfoTable[color].figureGUID).getPosition()
		for key, roomMap in pairs (RoomsMap) do
			local locRoom = nil
			if roomMap[1] == 'room' then
				locRoom = gO(key)
				
				if locRoom != nil then
					local locRoomPos = locRoom.getPosition()
					if distanceMath(locRoomPos, locPlayerPos) <= returnRoomDiameter(locRoom) then
						locPlayerTiles[color] = key
						--print('locPlayerTiles['..color..'] = ' .. key)

						break
					end
				end
			end
		end
	end
	
	if insiderEnable then
		insiderRecall()
		if locInsider and insiderFig != nil and insiderCard != nil then
			if insiderStoryGUID != '' and insiderFig.hasTag('characterFig') and insiderCard.getGMNotes() == 'active' and (insiderCard.getRotation().z < 10 or insiderCard.getRotation().z > 350) then
				local locInsiderPos = insiderFig.getPosition()
				
				for key, roomMap in pairs (RoomsMap) do
					local locRoom = nil
					if roomMap[1] == 'room' then
						locRoom = gO(key)
						
						if locRoom != nil then
							local locRoomPos = locRoom.getPosition()
							if distanceMath(locRoomPos, locInsiderPos) <= returnRoomDiameter(locRoom) then
								locPlayerTiles['insider'] = key
								break
							end
						end
					end
				end
			end
		end
	end
	return locPlayerTiles
end

function getLowestNeighbourRoom(tileGUID, isCorridor)
	
	local locLowestRoom = nil
	
	if isCorridor then
		for _, roomTileGUID in pairs (RoomsMap[tileGUID][2]) do
			local locRoom = gO(roomTileGUID)
			
			if locLowestRoom == nil then
				locLowestRoom = locRoom
			else
				if tonumber(locLowestRoom.getGMNotes()) > tonumber(locRoom.getGMNotes()) then
					locLowestRoom = locRoom
				end
			end
		end
	else
		
		for _, corridorGUID in pairs (RoomsMap[tileGUID][2]) do
		
			for _, roomTileGUID in pairs (RoomsMap[corridorGUID][2]) do
				
				if tileGUID != roomTileGUID then
					local locRoom = gO(roomTileGUID)
					
					if locLowestRoom == nil then
						locLowestRoom = locRoom
					else
						if tonumber(locLowestRoom.getGMNotes()) > tonumber(locRoom.getGMNotes()) then
							locLowestRoom = locRoom
						end
					end
				end
			end
		end
	end
	
	return locLowestRoom
end

function getLowestCorridorAroundRoom(roomTileGUID, connected)
	if not scriptEnabled then
		return true
	end
	
	local lowestCorridor = nil
	local locConnected = true
	
	if connected != nil then
		locConnected = connected
	end
	
	for _, corridorGUID in pairs(RoomsMap[roomTileGUID][2]) do
		if #RoomsMap[corridorGUID][2] > 1 or not locConnected then
			local locCor = gO(corridorGUID)
			if lowestCorridor == nil then
				lowestCorridor = locCor
			else
				local lowestIDNumber = tonumber(lowestCorridor.getGMNotes())

		
				local targetIDNumber = tonumber(locCor.getGMNotes())
				
				if targetIDNumber < lowestIDNumber then
					lowestCorridor = locCor
				end
			end
		end
	end
	return lowestCorridor
end

function getLowestNoiseCorridorsAroundRoom(roomTileGUID, connected)
	if not scriptEnabled then
		return true
	end
	
	local corridorList = { ['corridor1'] = {}, ['corridor2'] = {}, ['corridor3'] = {}, ['corridor4'] = {} }
	
	local locConnected = true
	
	if connected != nil then
		locConnected = connected
	end
	
	for _, corridorGUID in pairs(RoomsMap[roomTileGUID][2]) do
		if #RoomsMap[corridorGUID][2] > 1 or not locConnected then
			local locCor = gO(corridorGUID)
			
			for _, tag in pairs (locCor.getTags()) do
				if tag == 'corridor1' or tag == 'corridor2' or tag == 'corridor3' or tag == 'corridor4' then
					table.insert(corridorList[tag], locCor)
					break
				end
			end
			
		end
	end
	
	for tag, corList in pairs (corridorList) do
		if #corList > 0 then
			return corList
		end
	end
	
	return nil
end

proceedToNextPhase = true
proceedToNextPhase2 = true
function autoEvent(eventCard)
	if not scriptEnabled then
		return true
	end
	
	if autoEventEnable and proceedToNextPhase and allPassed then
		proceedToNextPhase2 = false
		eventCard.drop()
		eventCard.setLock(true)
		eventCard.setRotation({0,180,0})
		eventCard.setPosition({20,3,7})
		
		local locIntruders = {}
		local locIntrudersCopy = {}
		local locIntrudersType = {}
		local locIntruderTypeGM = ''
						
		local locCorridors = {}
		local locCorridorsCopy = {}
		local locRooms = {}
		local locMoveCorridors = {}
		
		local locDoors = {}
		local locDestroyedDoors = {}
		local locDoorsPos = {}
		
		
		local locNoises = {}
		local locSecuresGUID = {}
		
		local locFires = {}
		local locMalfunctions = {}
		local locMeats = {}
		local locFoods = {}

		local locMoveType = -1
		for _, tag in pairs(eventCard.getTags()) do
			if tag == 'eventMoveCorridorA' then
				locMoveType = 0
			elseif tag == 'eventMoveCorridorB' then
				locMoveType = 1
			elseif tag == 'eventMoveCorridorC' then
				locMoveType = 2
			elseif tag == 'eventMoveCorridor' then
				locMoveType = 3
			elseif tag == 'eventMoveFirespitter' then
				locMoveType = 4
				locIntruderTypeGM = 'firespitter'
			elseif tag == 'eventMoveIronclad' then
				locMoveType = 5
				locIntruderTypeGM = 'ironclad'
			elseif tag == 'eventMoveCrawlmine' then
				locMoveType = 6
				locIntruderTypeGM = 'crawlmine'
			elseif tag == 'eventMoveSlasher' then
				locMoveType = 7
				locIntruderTypeGM = 'slasher'
			elseif tag == 'eventMoveCultist' then
				locMoveType = 8
				locIntruderTypeGM = 'breeder'
			elseif tag == 'eventMoveQueen' then
				locMoveType = 9
				locIntruderTypeGM = 'queen'
			end
		end
		--print('locMoveType = ' .. locMoveType)


		--boxCast corridors, rooms, intruders

		for _, locObj in pairs(getAllObjects()) do
			local locCastPos = locObj.getPosition()
			local locBoarderPos = boarderTile.getPosition()
			local locBoarderSize = boarderTile.getBounds().size
			if math.abs(locCastPos.x - locBoarderPos.x) < locBoarderSize.x and math.abs(locCastPos.z - locBoarderPos.z) < locBoarderSize.z then
				local locGM = locObj.getGMNotes()
				local locDesc = locObj.getDescription() 
				local locGUID = locObj.getGUID()
				if locObj.hasTag('Corridors') or locObj.hasTag('room') then
				
					if locObj.hasTag('room') then
						table.insert(locRooms, locObj)
					else
						table.insert(locCorridors, locObj)
						--print('add to locCorridors')
					end
					
				elseif locObj.hasTag('intruder') or (locObj.hasTag('healthCount') and lifeforms == 'Sangrevores' and locObj.getGMNotes() != 'xyrian') then
					
					if locObj.getName() != 'Noise' then
						table.insert(locIntruders, locObj)
						table.insert(locIntrudersCopy, locObj)
						if locGM == locIntruderTypeGM then
							table.insert(locIntrudersType,locObj)
						end
					else
						table.insert(locNoises, locObj)
					end
					
					if lifeforms == 'Carnomorph' then
						if locObj.hasTag('meat') then
							table.insert(locFoods, locObj)
						end
					end
					
				elseif locDesc == 'door' then
					table.insert(locDoors, locObj)
					table.insert(locDoorsPos, locCastPos)
				elseif locDesc == 'destroyedDoor' then
					table.insert(locDestroyedDoors, locObj)
					table.insert(locDoorsPos, locCastPos)
				elseif locObj.getName() == 'Noise' then
					table.insert(locNoises, locObj)
				elseif locGM == 'fire' then
					table.insert(locFires, locObj)
				elseif locGM == 'malfunction' then
					table.insert(locMalfunctions, locObj)
				elseif locGM == 'secure' then
					table.insert(locSecuresGUID, locGUID)
				elseif locGM == 'carcass' then
					table.insert(locMeats, locObj)
					table.insert(locFoods, locObj)
				elseif locObj.hasTag('meat') then
					table.insert(locFoods, locObj)
				elseif locObj.hasTag('characterFig') and locObj.getRotation().z > 170 and locObj.getRotation().z < 190 then
					table.insert(locFoods, locObj)
				end
			end
		end
		
		--Sorting for rooms and corridors

		local locMinStats = {['corridor'] = {}, ['room'] = {}}
		

		for _, entry in pairs({locCorridors, locRooms}) do
			local locLabel = 'corridor'
			if entry == locRooms then
				locLabel = 'room'
			end

			for i=1, #entry do
				local locXZ = entry[i].getPosition()
				locMinStats[locLabel][i] = {x = locXZ[1], z=locXZ[3], index=i} 		--{x =0, z=0, index =1}
			end
		end

		for label, minStatsTbl in pairs(locMinStats) do 
			for i=1, #minStatsTbl do
				local locMinElem = minStatsTbl[i]
				local locMinIndex = i
				for j = i, #minStatsTbl do
					local elem = minStatsTbl[j]
					if elem.z > locMinElem.z or (locMinElem.z == elem.z and elem.x <= locMinElem.x) then --left to right, top to bottom
			  
						locMinElem = elem
						locMinIndex = j

					end
				end
				table.remove(locMinStats[label], locMinIndex)
				table.insert(locMinStats[label], i, locMinElem)
				
				if label == 'corridor' then
					local locCorElem = locCorridors[locMinIndex]
					table.remove(locCorridors, locMinIndex)
					table.insert(locCorridors, i, locCorElem)
					if locMoveType > 3 then
						table.insert(locCorridorsCopy, locCorElem)
					elseif locMoveType == 3 then
						table.insert(locMoveCorridors, locCorElem)
					end
					
				else
					local locRoomElem = locRooms[locMinIndex]
					table.remove(locRooms, locMinIndex)
					table.insert(locRooms, i, locRoomElem)
				end
				
			end
		end
		
		locMinStats = {} --cleanUp
		
		--mapping each room with corridors linked to them, from data only ...? Sure.
		
		registerToRoomsMap(locRooms, locCorridors)
		
		--write down players rooms in order of first player, if any group of enemies was found, only using data we already have.
		
		local locPlayerTiles = getPlayerRoomsInFirstTurnOrder()
		
		--finding corridors with moving enemies, if enemies should move.

		--print('#locCorridors = ' .. #locCorridors)
		local locWait = 1.5
		if locMoveType >= 0 then
			
			if locMoveType <= 2 then

				for _, corridor in pairs (locCorridors) do
					local Y = corridor.getRotation().y
					local locPass = false
					if locMoveType == 0 then
						locPass = (Y < 10 or Y > 350) or (Y > 170 and Y < 190)

					elseif locMoveType == 1 then
						locPass = (Y > 50 and Y < 70) or (Y > 230 and Y < 250)
					elseif  locMoveType == 2 then
						locPass = (Y > 110 and Y < 130) or (Y > 290 and Y < 310)
					end
					
					if locPass then
						table.insert(locMoveCorridors,corridor)
						--print('add locMoveCorridor')
					end
				end
			elseif locMoveType > 3 then
			
				for _, intruder in pairs (locIntrudersType) do
					local locIntrPos = intruder.getPosition()	
					local locCorSize = #locCorridorsCopy
					for i=1, locCorSize do
						local corridor = locCorridors[locCorSize-i+1]
						local locCorPos = corridor.getPosition()
						

						local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridor.getRotation().y)
						
						if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
						and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6
						then
							table.insert(locMoveCorridors, locCorridors[locCorSize-i+1])
							break
						end
					end
				end
			end
		

			--making group of enemies from related Corridors, if any such corridor was found, with DATA ONLY !
			local locMoveIntruders = {}
			local locRemoveCor = {}
			for j = 1, #locMoveCorridors do
				
				local corridor = locMoveCorridors[j]
				local locCorPos = corridor.getPosition()
				
				local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridor.getRotation().y)
				
				local locTbl = {}
				local locIntrSize = #locIntrudersCopy
				for i = 1, #locIntrudersCopy do
					local intruder = locIntrudersCopy[locIntrSize-i+1]
					local locIntrGM = intruder.getGMNotes()
					if (lifeforms != 'Neoflesh' and intruder.getName() != 'Noise') or (lifeforms == 'Neoflesh' and locIntrGM != 'larvae' and locIntrGM != 'breeder' ) then
						local locIntrPos = intruder.getPosition()
						if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
						and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6
						then
							if locIntrGM != 'queen' then
								intruder.setVar("count", 0)
								intruder.call("updateDisplay")
							end
							
							table.insert(locTbl, intruder)
							table.remove(locIntrudersCopy, locIntrSize-i+1)
							locWait = locWait + 0.25
							--print('Adding intruder to locMoveIntruders, GUID = ' .. intruder.getGUID())
						end
					end
				end
				
				if locTbl[1] != nil then
					table.insert(locMoveIntruders, locTbl)
				else
					table.insert(locRemoveCor, j)
				end
			end
			
			local locRemoveSize = #locRemoveCor
			for i = 1, locRemoveSize do
				table.remove(locMoveCorridors, locRemoveCor[locRemoveSize-i+1])
			end
			
			locRemoveCor = {}

			--find shortest route to a player
			
			if locMoveCorridors[1] != nil then
				autoMoveToGoal(locMoveCorridors, locMoveIntruders, locIntruders, locDoors, locNoises)
			end
		end
		
		
		if eventCard.hasTag('eventRoomMoveAll') then
			Wait.time(function()
				--print('Start of eventRoomMoveAll')
				locWait = 1.5
				locMoveIntruders = {}
				local locMoveRooms = {}
				for _, room in pairs(locRooms) do --finding rooms where intruders would move.
					--print('checking out room from locRooms')
					local locRoomGUID = room.getGUID()
					local locTblTmp = {}
					local locPlayerFound = false
					local locRoomSizeX = corridorImportedSize.x
					local locRoomPos = room.getPosition()
					
					if room == hiddenRoom then	 --it's because of the hibernatorium hidden room....
						locRoomSizeX = room.getBounds().size.x
					end
					
					for i = 1, #locIntruders do
						local intruder = locIntruders[i]
						local locIntrGM = intruder.getGMNotes()

						if (lifeforms != 'Neoflesh' and intruder.getName() != 'Noise' and not intruder.hasTag('meat')) or (lifeforms == 'Neoflesh' and locIntrGM != 'larvae' and locIntrGM != 'breeder' ) then
							if distanceMath(intruder.getPosition(), locRoomPos) < locRoomSizeX*0.5 then
								--print('found an intruder in a room')
								for color, playerRoom in pairs(locPlayerTiles) do
									if locRoomGUID == playerRoom then
										locPlayerFound = true
									--	print('found an intruder in a room with a player, not adding this one to the list')
										break
									end
								end
								
								if not locPlayerFound then
									table.insert(locTblTmp, intruder)
									locWait = locWait + 0.25
								end
							end
						end
					end
					if #locTblTmp > 0 then
						table.insert(locMoveIntruders, locTblTmp)
						table.insert(locMoveRooms, room)
					end
				end
				
				if locMoveRooms[1] != nil then
					autoMoveToGoal(locMoveRooms, locMoveIntruders, locIntruders, locDoors, locNoises)
				end
				Wait.time(function() proceedToNextPhase2 = true end, locWait)
			end, locWait+1)
		else
			locWait = locWait+1
			Wait.time(function() proceedToNextPhase2 = true end, locWait)
		end
		
		Wait.time(function ()
			
			Wait.condition(function()
				--main effect
				proceedToNextPhase2 = false
				
				local locPassMain = true
				local locPassSecondary = true
				
				

				
				local locEventTags = eventCard.getTags()				
				if lifeforms == 'Neoflesh' then
					local locCultistSecondary = false
					local locCultistNeeded = 0
					local locCultistAlive = 5 - cultistDeadBag.getQuantity()
					for _, tag in pairs(locEventTags) do
						if tag == 'eventCultistSecondary' then
							locCultistSecondary = true
						elseif tag == 'eventCultist1' then
							locCultistNeeded = 1
						elseif tag == 'eventCultist2' then
							locCultistNeeded = 2
						elseif tag == 'eventCultist3' then
							locCultistNeeded = 3
						elseif tag == 'eventCultist4' then
							locCultistNeeded = 4
						elseif tag == 'eventCultist5' then
							locCultistNeeded = 5
						end
					end
					locPassMain = locCultistSecondary or locCultistAlive >= locCultistNeeded
					locPassSecondary = not locCultistSecondary or locCultistAlive >= locCultistNeeded
				end
				
				if locPassMain then
					local locTagFound = false
					for _, tag in pairs(eventCard.getTags()) do --Oh my god.
						
						if tag == 'eventMainAddAdultCorAdult' then
							locTagFound = true
							local locWait2 = 0
							
							for _, corridor in pairs (locCorridors) do
								local locCorPos = corridor.getPosition()
								local locSpaceAvailable = 6
								local locAdultFound = false
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(),locCorPos) < corridorImportedSize.x * 0.5 then
											
											local locIntrGM = intruder.getGMNotes()
											if locIntrGM == 'queen' then
												locSpaceAvailable = locSpaceAvailable - 4
											else
												locSpaceAvailable = locSpaceAvailable - 1
												
												if not locAdultFound then
													if intruder.getGMNotes() == 'adult' then
														locAdultFound = true
													end
												end
											end
											if locSpaceAvailable <= 0 then
												break
											end
										end
									end
								end
								
								if locSpaceAvailable > 0 and lifeforms == 'Sangrevores' then
									for _, noiseToken in pairs(locNoises) do
										if noiseToken != nil then
											if distanceMath(noiseToken.getPosition(),locCorPos) < corridorImportedSize.x * 0.5 then
												locSpaceAvailable = locSpaceAvailable - 1
												if locSpaceAvailable <= 0 then
													break
												end
											end
										end
									end
								end
								
								
								if locSpaceAvailable > 0 and locAdultFound then
									local w = locWait2
									locWait2 = locWait2 + 0.25
									
									Wait.time(function()
										if adultFBag.getQuantity() > 0 then
											adultFBag.takeObject({
												position = findSpaceOnTile(corridor, nil, true),
												callback_function = function(o)
													o.setLock(true)
													
													if o.hasTag('rot180') then
														o.setRotation({0,(corridor.getRotation().y+90),0})
													else
														o.setRotation({0,0,0})
													end
												end,
											})
										end
									end, w)
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+1)
						
						elseif tag == 'eventMainAddQueenTokens' then
							locTagFound = true
							
							if isQueenAlive() then
								onObjectNumberTyped(queenBag, 'Red', queenBag.getQuantity())
							end
							
							
							if lifeforms == 'Sangrevores' then
								for color, playerRoomGUID in pairs(locPlayerTiles) do
									for _, card in pairs(Player[color].getHandObjects()) do
										if card.hasTag('Infection') then
											seriouswoundDeck.deal(1,color)
											broadcastToAll('플레이어 ' .. color .. '가 심각한 부상을 입었습니다.', lifeformColor)
											break
										end
									end
								end
							end
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						
						elseif tag == 'eventMainAirlockYellow' then
							locTagFound = true
							
							local locWait2 = 0
							local locWait3 = 0
							local locYellowCount = 0
							local locYellowRooms = {}
							
							
							for _, roomTile in pairs (locRooms) do
								
								local locD = roomTile.getDescription()
								local locPass = false
								
								if string.find(locD, 'YYY') != nil then
									if locYellowCount != 3 then
										locYellowCount = 3
										locYellowRooms = {}
									end
									locPass = true
									
								elseif locYellowCount < 3 then
									if string.find(locD, 'YY') != nil then
										if locYellowCount != 2 then
											locYellowCount = 2
											locYellowRooms = {}
										end
										locPass = true
										
									end
									
									if locYellowCount < 2 then
								
										if string.find(locD, 'Y') != nil then
											if locYellowCount != 1 then
												locYellowCount = 1
											end
											locPass = true
											
										end
									end
								end
								
								if locPass then
									table.insert(locYellowRooms, {roomTile, nil, {}, false})
								end
								
							end
							if #locYellowRooms > 0 then
								airlockToken.setGMNotes('active')
								playsounds(5)
								lightAlert()
								
								broadcastToAll('노란색 아이템이 가장 많은 방에서 에어락 절차를 시작합니다. 접근 가능한 문이 변경되면 내부의 에어락 토큰을 제거하세요.', lifeformColor)
								
								for _, tblRoom in pairs (locYellowRooms) do
									roomTile = tblRoom[1]
									local locRoomPos = roomTile.getPosition()
									
									local locAirClone = airlockToken.clone()
									locAirClone.setLock(true)
									locAirClone.setPositionSmooth(roomTile.getPosition(), false, true)
									tblRoom[2] = locAirClone

									local locCancel = false
									
									for _, corridorGUID in pairs (RoomsMap[roomTile.getGUID()][2]) do
										local locCorDoor = gO(corridorGUID)

										
										
										for _, SnapP in pairs(locCorDoor.getSnapPoints()) do
											local SnapPos = SnapP.position
											local locScale = locCorDoor.getScale()
											
											local SnapPosWorld = rotateVectorAboutY(SnapPos*locScale, locCorDoor.getRotation().y) + locCorDoor.getPosition()
											local roomDoorDistance = distanceMath(locRoomPos, SnapPosWorld)

											if roomDoorDistance < returnRoomDiameter(roomTile) then
												local locDoorFound = false
												local i = 0
												
												for _, tbl in pairs ({locDoors, locDestroyedDoors}) do
													i = i + 1
													for _, door in pairs(tbl) do
														if distanceMath(door.getPosition(), SnapPosWorld) < 1 then
															locDoorFound = true
															locCancel = i == 2
															break
														end
													end
												end
												
												if not locDoorFound then
													local w = locWait2
													locWait2 = locWait2 + 0.2
													Wait.time(function()
														if doorBag.getQuantity() > 0 then
															doorBag.takeObject({
																position = SnapPosWorld + Vector(0,1,0),
																rotation = {0, locCorDoor.getRotation().y + 90, 0},
																callback_function = function(o)
																	o.setLock(true)
																	o.setPositionSmooth(SnapPosWorld, false, true)
																	table.insert(tblRoom[3], o)
																end,
																smooth = false,
															})
														else
															tblRoom[4] = true
														end
													end, w)
												end
												break
											end
										end
										if locCancel then
											tblRoom[4] = true
											locWait3 = locWait3 + (0.2* #RoomsMap[roomTile.getGUID()][2])
											break
										end
									end
								end
								
								Wait.time(function()
									for _, tblRoom2 in pairs (locYellowRooms) do
										if tblRoom2[4] then
											for _, placedDoor in pairs (tblRoom2[3]) do
												doorBag.putObject(placedDoor)
											end
											tblRoom2[2].destruct()
										end
									end
									
								end, locWait3 + locWait2 + 1)
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait3+locWait2+2.5)

						elseif tag == 'eventMainAutodestruction' then
							locTagFound = true
							
							local locTurnPos = turnMarker.getPosition()
							local locAutoDPos = Vector(locTurnPos.x, 3, math.max(2.57,locTurnPos.z- 5*turnOffset.z))
							if lifeforms != 'Neoflesh' then
								local locEventRooms = {}
								local locAutoDTrigger = false
								local locRoomsFound = 0
								for _, roomTile in pairs(locRooms) do
									local locName = roomTile.getName()
									
									if locName == 'REACTOR' or locName == 'COOLING SYSTEM' then
										locRoomsFound = locRoomsFound +1
										local locRoomPos = roomTile.getPosition()
										
										local locMalfFound = false
										for _, malfunctionToken in pairs(locMalfunctions) do
											if distanceMath(malfunctionToken.getPosition(), locRoomPos) <= tileImportedSize.x then
												locMalfFound = true
												if not locAutoDTrigger then
													if autoDestructionToken != nil then
														if autoDestructionToken.getPosition().z > 15 then
															autoDestructionToken.setPosition(locAutoDPos)
															locAutoDTrigger = true
															playsounds(-1)
															onObjectDrop('Red', autoDestructionToken)
															broadcastToAll(autoDestructionWarning, lifeformColor)
														end
													end
												end
												break
											end
										end
										
										if not locMalfFound then
											table.insert(locEventRooms, roomTile)
										end
										
										if locRoomsFound == 2 then
											break
										end
									end
								end
								
								for _, roomTile in pairs(locEventRooms) do
									placeMalfunction(roomTile.getPosition() + Vector(0,0,-1.05))
								end
								
								
							else
								if autoDestructionToken != nil then
									if autoDestructionToken.getPosition().z > 15 then
										autoDestructionToken.setPosition(locAutoDPos)
										playsounds(-1)
										onObjectDrop('Red', autoDestructionToken)
										broadcastToAll(autoDestructionWarning, lifeformColor)
									end
								end
								
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						
						elseif tag == 'eventMainBigOnslaught' then
							locTagFound = true
							
							local locCorOnce = {}
							local locWait2 = 0
							
							for color, playerRoomGUID in pairs (locPlayerTiles) do
								
								local locPlayerRoom = gO(playerRoomGUID)
								local locPRoomPos = locPlayerRoom.getPosition()
								local locPRoomDiameter = returnRoomDiameter(locPlayerRoom)
								
								for _, corGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									
									if locCorOnce[corGUID] == nil then
										locCorOnce[corGUID] = 0
										local locCor = gO(corGUID)
										local locPos = locCor.getPosition()
										
										
										for _, intruder in pairs (locIntruders) do
											if intruder != nil then
												if intruderSizeOrder[lifeforms][intruder.getGMNotes()] > 3 then
													if distanceMath(locPos, intruder.getPosition()) < corridorImportedSize.x*0.5 then
													
														local locDoorFound = false
														
														for i = 1, #locDoors do
															local door = locDoors[#locDoors-i+1]
															if door != nil then	
																local locDPos = door.getPosition()
																local locCorToDoor = normalizeMath(locDPos - locPos)
																local locCorToRoom = normalizeMath(locPRoomPos - locPos)
																
																if distanceMath(door.getPosition(), locPRoomPos) < locPRoomDiameter*0.75
																and dotMath(locCorToDoor, locCorToRoom) > 0.9
																then
																	locDoorFound = true
																	door.setState(2)
																	table.remove(locDoors, #locDoors-i+1)
																	break
																end
															end
														end
														
														if not locDoorFound then
															local w = locWait2
															locWait2 = locWait2 + 0.25
															Wait.time(function()
																
																intruder.setPositionSmooth(findSpaceOnTile(locPlayerRoom, nil, true, intruder), false, true)
																
																if intruder.hasTag('rot180') then
																	intruder.setRotation({0,180,0})
																end
																
																checkSecureRoom(locPlayerRoom, intruder, color)
															
															end, w)
														end
													end
												end
											end
										end
									end
								end								
							end
						
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 2)
							
						elseif tag == 'eventMainBreakComputer' then
						
							locTagFound = true
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.hasTag('computer') then
									local locMalfFound = false
									local locRoomPos = roomTile.getPosition()
									for _, malfunctionToken in pairs(locMalfunctions) do
										if distanceMath(malfunctionToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) * 0.7 then
											locMalfFound = true
											break
										end
									end
									
									if not locMalfFound then
										placeMalfunction(locRoomPos + Vector(0,0,-1.05))
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainBreakFireSpreadLow' then
							locTagFound = true
							
							local locWait2 = 0
							
							local locRoomsAmount = #locRooms
							local locRoomsAddedFire = {}
							for _, roomTile in pairs(locRooms) do
								local locRoomPos = roomTile.getPosition()
								for _, fireToken in pairs(locFires) do
									if distanceMath(fireToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) * 0.7 then
										
										if roomTile.getName() != 'NEST' then
											local locMalfFound = false
											for _, malfunctionToken in pairs(locMalfunctions) do
												if distanceMath(malfunctionToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) * 0.7 then
													locMalfFound = true
													break
												end
											end
											
											if not locMalfFound then
												placeMalfunction(locRoomPos + Vector(0,0,-1.05))
											end
										end
										
										local corList = nil
										local locRoomTileGUID = roomTile.getGUID()
										corList = getLowestNoiseCorridorsAroundRoom(locRoomTileGUID)
										
										if corList != nil then
											for _, lowestCorridor in pairs (corList) do
												local locOtherRoomGUID = ''
												for _, otherRoomGUID in pairs(RoomsMap[lowestCorridor.getGUID()][2]) do
													if otherRoomGUID != locRoomTileGUID then
														locOtherRoomGUID = otherRoomGUID
														break
													end
												end
												
												if locOtherRoomGUID != '' then
													if locRoomsAddedFire[locOtherRoomGUID] == nil then
														local locOtherRoom = gO(locOtherRoomGUID)
														local locOtherRoomPos = locOtherRoom.getPosition()
														local locDoorFound = false
														for _, door in pairs(locDoors) do
															if door != nil then
																local locDoorPos = door.getPosition()
																if distanceMath(lowestCorridor.getPosition(), locDoorPos) < corridorImportedSize.x*0.55
																and dotMath(normalizeMath(locDoorPos-locRoomPos), normalizeMath(locOtherRoomPos-locRoomPos)) > 0.9
																then
																	locDoorFound = true
																	break
																end
															end
														end
														
														if not locDoorFound then
															local locFireFound = false
															for _, fireToken2 in pairs(locFires) do
																if distanceMath(fireToken2.getPosition(), locOtherRoomPos) <= returnRoomDiameter(locOtherRoom) * 0.7 then
																	locFireFound = true
																	break
																end
															end
															
															if not locFireFound then
																local w = locWait2
																locWait2 = locWait2 + 1
																locRoomsAddedFire[locOtherRoomGUID] = 1
																Wait.time(function()
																	
																	placeFire(locOtherRoomPos +Vector(0.35,0,-1.3), false)
																	
																end, w)
															end
														end
													end
												end
											end
										end
										break
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+1)
								
							
							
						elseif tag == 'eventMainBreakRobot' then
							locTagFound = true
							
							if robot.getGMNotes() == 'active' then
								local locRobotPos = robot.getPosition()
								if getTaggedObjAtPos('malfunction', robotDeckPos, 3, {2,9,2}) == nil then
									placeMalfunction(robotDeckPos)
								end
								for _, roomTile in pairs(locRooms) do
									local locRoomTilePos = roomTile.getPosition()
									if distanceMath(locRoomTilePos, locRobotPos) <= returnRoomDiameter(roomTile) * 0.7 then
										local locRoomTileGUID = roomTile.getGUID()
										
										if roomTile.getName() != 'NEST' then
											local locMalfFound = false
											for _, malfunctionToken in pairs(locMalfunctions) do
												if distanceMath(malfunctionToken.getPosition(), locRoomTilePos) <= returnRoomDiameter(roomTile) * 0.7 then
													locMalfFound = true
													break
												end
											end
											
											if not locMalfFound then
												placeMalfunction(locRoomTilePos + Vector(0,0,-1.05))
											end
										end
										
										for color, playerRoomGUID in pairs(locPlayerTiles) do
											if playerRoomGUID == locRoomTileGUID then
												loseHealth(color)
												loseHealth(color)
											end
										end
										
										playsounds(32)
										lightAlert()
										
										broadcastToAll(robotWarning, lifeformColor)
										break
									end
								end
							else
								broadcastToAll(robotSkipMsg, lifeformColor)
							end
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainBreakRoom3GhoulsCor' then
							locTagFound = true
							
							for _, roomTile in pairs (locRooms) do
								if roomTile.getName() != 'NEST' then
									local locGhoulCount = 0
									local locMalfFound = false
									local locRoomPos = roomTile.getPosition()
									local locRoomDiameter = returnRoomDiameter(roomTile)
									
									for _, malfunctionToken in pairs (locMalfunctions) do
										if distanceMath(locRoomPos, malfunctionToken.getPosition()) < locRoomDiameter then
											locMalfFound = true
											break
										end
									end
									
									
									if not locMalfFound then
										for _, corridorGUID in pairs (RoomsMap[roomTile.getGUID()][2]) do
											local locCorPos = gO(corridorGUID).getPosition()
											
											for _, intruder in pairs (locIntruders) do
												if intruder != nil then
													if distanceMath(intruder.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
														locGhoulCount = locGhoulCount + 1
														if locGhoulCount == 3 then
															break
														end
													end
												end
											end
											if locGhoulCount == 3 then
												break
											end
										end
										
										if locGhoulCount == 3 then
											placeMalfunction(locRoomPos + Vector(0,0,-1.05))
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainBurnComputerCharaFireDoor' then
							locTagFound = true
							local locWait2 = 0
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.hasTag('computer') then
									local locRoomPos = roomTile.getPosition()
									local locRoomGUID = roomTile.getGUID()
									local locFireFound = false
									
									for _, fireToken in pairs(locFires) do
										if distanceMath(fireToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) * 0.7 then
											locFireFound = true
											break
										end
									end
									
									if not locFireFound then
										local w = locWait2
										locWait2 = locWait2 + 1
										Wait.time(function()
										
											placeFire(locRoomPos + Vector(0.35,0,-1.3),false)
											
										end, w)
									end
									
									for color, playerRoomGUID in pairs(locPlayerTiles) do
										if playerRoomGUID == locRoomGUID then
										
											for _, corridorGUID in pairs(RoomsMap[locRoomGUID][2]) do
												local locCorDoor = gO(corridorGUID)
												for _, SnapP in pairs(locCorDoor.getSnapPoints()) do
													if SnapP.tags[1] == 'doorSlot' then
														local SnapPos = SnapP.position
														local locScale = locCorDoor.getScale()
														
														local SnapPosWorld = rotateVectorAboutY(SnapPos*locScale, locCorDoor.getRotation().y) + locCorDoor.getPosition()
														local roomDoorDistance = distanceMath(locRoomPos, SnapPosWorld)

														if roomDoorDistance < returnRoomDiameter(roomTile) then
															local locDoorFound = false
															
															for _, doorPos in pairs (locDoorsPos) do
																if distanceMath(doorPos, SnapPosWorld) < 1 then
																	locDoorFound = true
																	break
																end
															end
															
															if not locDoorFound then
																local w = locWait2
																locWait2 = locWait2 + 0.2
																Wait.time(function()
																	if doorBag.getQuantity() > 0 then
																		doorBag.takeObject({
																			position = SnapPosWorld + Vector(0,1,0),
																			rotation = {0, locCorDoor.getRotation().y + 90, 0},
																			callback_function = function(o)
																				o.setLock(true)
																				o.setPositionSmooth(SnapPosWorld, false, false)
																			end,
																			smooth = false,
																		})
																	end
																end, w)
															end
															break
														end
													end
												end
											end
											break
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						elseif tag == 'eventMainBurnRobot' then
							locTagFound = true
							
							if robot.getGMNotes() == 'active' then
								local locRobotPos = robot.getPosition()
								if getTaggedObjAtPos('malfunction', robotDeckPos, 3, {2,9,2}) == nil then
									placeMalfunction(robotDeckPos)
								end

								for _, roomTile in pairs(locRooms) do
									local locRoomTilePos = roomTile.getPosition()
									if distanceMath(locRoomTilePos, locRobotPos) <= returnRoomDiameter(roomTile) * 0.7 then
										local locRoomTileGUID = roomTile.getGUID()
										local locFireFound = false
										for _, fireToken in pairs(locFires) do
											if distanceMath(fireToken.getPosition(), locRoomTilePos) <= returnRoomDiameter(roomTile) * 0.7 then
												locFireFound = true
												break
											end
										end
										
										if not locFireFound then
											placeFire(locRoomTilePos + Vector(0.35,0,-1.3), false)
										end
										
										for color, playerRoomGUID in pairs(locPlayerTiles) do
											if playerRoomGUID == locRoomTileGUID then
												loseHealth(color)
												loseHealth(color)
											end
										end
										
										
										broadcastToAll(robotWarning, lifeformColor)
										break
									end
								end
							else
								broadcastToAll(robotSkipMsg, lifeformColor)
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainBurnRoomIntruder' then
							locTagFound = true
							
							for _, roomTile in pairs (locRooms) do
								local locFireFound = false
								local locRoomPos = roomTile.getPosition()
								
								
								for _, fireToken in pairs (locFires) do
									if distanceMath(fireToken.getPosition(), locRoomPos) < tileImportedSize.x then	
										locFireFound = true
										break
									end
								end
							
							
							
								if not locFireFound then
									for _, intruder in pairs (locIntruders) do
										if intruder != nil then
											if distanceMath(intruder.getPosition(), locRoomPos) < tileImportedSize.x *0.5 then
												placeFire(locRoomPos + Vector(0.35,0,-1.3))
												break
											end
										end
									end
								end
							end
						
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainChar3ShadowCorInfection' then						
							locTagFound = true
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								local locShadowCount = 0
								
								for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									local locCor = gO(corridorGUID)
									local locCorPos = locCor.getPosition()

									for _, noiseToken in pairs (locNoises) do
										if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
											locShadowCount = locShadowCount + 1
											if locShadowCount == 3 then
												break
											end
										end
									end
									if locShadowCount == 3 then
										addContamination(color)
										break
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainCharActionDealEvent' then						
							locTagFound = true
							
							local locHighCardColor = ''
							local locCardCount = 0
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								local locColorCardCount = 0
								for _, card in pairs (Player[color].getHandObjects()) do
									if card.getGMNotes() == 'action' then
										locColorCardCount = locColorCardCount + 1
									end
								end
								
								
								if locCardCount < locColorCardCount then
									locCardCount = locColorCardCount
									locHighCardColor = color
								end
							end
							
							if locHighCardColor != '' then
								eventCard.setLock(false)
								eventCard.deal(1, locHighCardColor)
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainCharInjuredInfection' then						
							locTagFound = true
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								local locHealthMarker = gO(playerInfoTable[color].healthGUID)
								local locBoard = gO(playerInfoTable[color].boardGUID)
								if (locHealthMarker.getPosition().x - locBoard.getPosition().x) < playerHealthLocalPosX[8] - 0.2 then
									addContamination(color)
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainCharTaintedAddShadow' then						
							locTagFound = true
							local locWait2 = 0
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								if playerHasTag('tainted', 3, nil, color) then
									for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
										local locCor = gO(corridorGUID)
										
										local w = locWait2
										locWait2 = locWait2 + 0.25
										Wait.time(function()
											local locCorCrowd = getTaggedObjAtPos('healthCount', locCor.getPosition(), 0, locCor.getBounds().size *Vector(0.99,1,0.57) + Vector(0,9,0), locCor.getRotation(), true)
											
											local locCorCrowdSize = 0
											
											for _, intruder in pairs (locCorCrowd) do
												if distanceMath(intruder.getPosition(), locCor.getPosition()) < corridorImportedSize.x * 0.5 then
													locCorCrowdSize = locCorCrowdSize + 1
												end
											end
											
											if locCorCrowdSize < 6 then
												local locShadows = {}
												for _, entry in pairs (locCorCrowd) do
													if entry.getName() == 'Noise' then
														table.insert(locShadows, entry)
														if #locShadows == 3 then
															break
														end
													end
												end
												
												if #locShadows == 3 then
													if breederFBag.getQuantity() > 0 then
														for _, shadowMarker in pairs (locShadows) do
															shadowMarker.setPosition({50,0,0})
															shadowMarker.destruct()
														end
														
														breederFBag.takeObject({
															position = findSpaceOnTile(locCor, nil, true),
															rotation = {0,0,0},
															callback_function = function(o) o.setLock(true) end,
														})
														
													end
												else
													noiseBag.takeObject({
														position = findSpaceOnTile(locCor, nil, true),
														rotation = {0,0,0},
														smooth = false,
													})
												end
											end
										end, w)
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						
						elseif tag == 'eventMainCombatFleeMeat' then
							locTagFound = true
							
							local locIntrOnce = {}
							local locWait2 = 0
							
							for color, playerRoomGUID in pairs (locPlayerTiles) do
								local locRoom = gO(playerRoomGUID)
								local locRoomPos = locRoom.getPosition()
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										local locIntrGUID = intruder.getGUID()
										
										if locIntrOnce[locIntrGUID] == nil then
											if distanceMath(intruder.getPosition(), locRoomPos) < tileImportedSize.x*0.5 then
												
												locIntrOnce[locIntrGUID] = 0
												
												loseHealth(color)
												
												local locLowestRoom = getLowestNeighbourRoom(playerRoomGUID, false)
												local locLowestPos = locLowestRoom.getPosition()
												local locDoorsNum = #locDoors
												
												
												for i = 1, locDoorsNum do
													local door = locDoors[locDoorsNum-i+1]
													
													if door != nil then
														local locDoorPos = door.getPosition()
														
														local locRoomToDoor = normalizeMath(locDoorPos-locRoomPos)
														local locDoorToLowest = normalizeMath(locLowestPos-locDoorPos)
														
														if dotMath(locRoomToDoor, locDoorToLowest) > 0.9 then
															door.setState(2)
															table.remove(locDoors, locDoorsNum-i+1)
														end
													end
													
												end
												
												local w = locWait2
												locWait2 = locWait2 + 0.3
												
												Wait.time(function()
													intruder.setPositionSmooth(findSpaceOnTile(locLowestRoom, nil, true, intruder), false, true)
													carcassBag.takeObject({
														position = locLowestPos + Vector(0,1,-1.05),
													})
												end, w)
												
											end
										end
									end
								end
								
							end
						
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 2)
						
						elseif tag == 'eventMainCrawlmineExplode' then
							locTagFound = true
							for _, roomTile in pairs(locRooms) do
								local locExploded = false
								for _, intruder in pairs(locIntruders) do
									if intruder != nil then
										if intruder.getGMNotes() == 'crawlmine' then
											local locCrawlminePos = intruder.getPosition()
											local locRoomPos = roomTile.getPosition()
											
											if distanceMath(locCrawlminePos,locRoomPos) < returnRoomDiameter(roomTile)*0.5 then
											
												if not locExploded then
													locExploded = true
													local locMalfFound = false
													for _, malfunctionToken in pairs(locMalfunctions) do
														if distanceMath(malfunctionToken.getPosition(), locRoomPos) < returnRoomDiameter(roomTile)*0.7 then
															locMalfFound = true
															break
														end
													end
													
													local locFireFound = false
													for _, fireToken in pairs(locFires) do
														if distanceMath(fireToken.getPosition(), locRoomPos) < returnRoomDiameter(roomTile)*0.7 then
															locFireFound = true
															break
														end
													end
													
													if not locMalfFound and roomTile.getName() != 'NEST' then
														placeMalfunction(locRoomPos + Vector(0,0,-1.05))
													end
													
													if not locFireFound then
														placeFire(locRoomPos + Vector(0.35,0,-1.3), false)
													end
													
													local locRoomTileGUID = roomTile.getGUID()
													for color, playerRoomGUID in pairs(locPlayerTiles) do
														if playerRoomGUID == locRoomTileGUID then
															for n = 1, 3 do
																loseHealth(color)
															end
														end
													end
													broadcastToAll('크롤마인이 폭발하여 주변 캐릭터들이 부상을 입었습니다!', lifeformColor)
												end
												enemyFigReturn(intruder)
											end
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainCultistAddSlasher' then
							locTagFound = true
							local locCultistOnBoard = 5 - breederFBag.getQuantity() - cultistDeadBag.getQuantity()
							local locCultistChecked = 0
							for _, roomTile in pairs(locRooms) do
								if locCultistChecked == locCultistOnBoard then
									break
								else
									for _, intruder in pairs(locIntruders) do
										if intruder.getGMNotes() == 'breeder' then
											local locCultistPos = intruder.getPosition()
											local locRoomPos = roomTile.getPosition()
											
											
											if distanceMath(locCultistPos,locRoomPos) < returnRoomDiameter(roomTile)*0.5 then
												 locCultistChecked = locCultistChecked + 1
												 local locRoomTileGUID = roomTile.getGUID()
												 
												 adultFBag.takeObject({
													position = adultFBag.getPosition() + Vector(0,6,0),
													rotation = {0,0,0},
													callback_function = function(o)
														o.setLock(true)
														for color, playerRoomGUID in pairs(locPlayerTiles) do
															if playerRoomGUID == locRoomTileGUID then
																checkSecureRoom(roomTile, o, color)
																break
															end
														end
														o.setPositionSmooth(findSpaceOnTile(roomTile, nil, true,o),false,true)
													end,
												 })
											end
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						

						
						elseif tag == 'eventMainDoorInjured' then
							locTagFound = true
							
							local locRoomOnce = {}
							local locWait2 = 0
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								local locBoardPosX = gO(playerInfoTable[color].boardGUID).getPosition().x
								local locPosX = gO(playerInfoTable[color].healthGUID).getPosition().x - locBoardPosX
								local locRoom = gO(playerRoomGUID)
								local locRoomPos = locRoom.getPosition()
								
								if locPosX > playerHealthLocalPosX[4]+0.2 and locPosX < playerHealthLocalPosX[8]-0.2 and locRoomOnce[playerRoomGUID] == nil then
									locRoomOnce[playerRoomGUID] = 0
									
									for _, corridorGUID in pairs(RoomsMap[playerRoomGUID][2]) do
										local locCorDoor = gO(corridorGUID)
										for _, SnapP in pairs(locCorDoor.getSnapPoints()) do
											if SnapP.tags[1] == 'doorSlot' then
												local SnapPos = SnapP.position
												local locScale = locCorDoor.getScale()
												
												local SnapPosWorld = rotateVectorAboutY(SnapPos*locScale, locCorDoor.getRotation().y) + locCorDoor.getPosition()
												local roomDoorDistance = distanceMath(locRoomPos, SnapPosWorld)

												if roomDoorDistance < returnRoomDiameter(locRoom) then
													local locDoorFound = false
													
													for _, doorPos in pairs (locDoorsPos) do
														if distanceMath(doorPos, SnapPosWorld) < 1 then
															locDoorFound = true
															break
														end
													end
													
													if not locDoorFound then
														local w = locWait2
														locWait2 = locWait2 + 0.2
														Wait.time(function()
															if doorBag.getQuantity() > 0 then
																doorBag.takeObject({
																	position = SnapPosWorld + Vector(0,1,0),
																	rotation = {0, locCorDoor.getRotation().y + 90, 0},
																	callback_function = function(o)
																		o.setLock(true)
																		o.setPositionSmooth(SnapPosWorld, false, false)
																	end,
																	smooth = false,
																})
															end
														end, w)
													end
													break
												end
											end
										end
									end
								end
							end
							
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
							
						elseif tag == 'eventMainEarlyLander' then
							locTagFound = true
							local locWait2 = 0
							local locSkip = false
							
							if shuttleFigure != nil then
								
								if math.abs(shuttleFigure.getPosition().x - (-16.55)) < 0.5 then
									if math.abs(shuttleFigure.getPosition().z - turnMarker.getPosition().z) < turnOffset.z*2.75 then
										landerCheck()
										
										Wait.condition(function()
											if shuttleFigure != nil then
												local locLowRoom = nil
												local locNbr = 99
												
												
												
												for _, roomTile in pairs (locRooms) do
													local roomTileNbr = tonumber(roomTile.getGMNotes())
													if roomTileNbr < locNbr then
														locNbr = roomTileNbr
														locLowRoom = roomTile
													end
												end
												
												shuttleFigure.setPosition(locLowRoom.getPosition() + Vector(0,4,0))
												shuttleFigure.setPositionSmooth(locLowRoom.getPosition()+Vector(0,0.2,0), false, false)
												
												local locRepelled = {}
												local lowestCor = getLowestCorridorAroundRoom(locLowRoom.getGUID(), false)
												
												for _, obj in pairs (shapeCast(locLowRoom.getPosition(), tileImportedSize)) do
													for _, tag in pairs (obj.getTags()) do
														if tag == 'characterFig' then
															obj.setLock(true)
															for color, entry in pairs (playerInfoTable) do
																if obj.getGUID() == entry.figureGUID then
																	loseHealth(color)
																	obj.setLock(true)
																	break
																end
															end
														elseif tag == 'intruder' then
															local w = locWait2
															locWait2 = locWait2 + 0.25
															Wait.time(function()
																autoMoveToGoal({locLowRoom}, {{obj}}, locIntruders, locDoors, locNoises, {lowestCor.getGUID()})
															end, w)
														end
													end
												end
											end
											Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
										end, function() return proceedToNextPhase end, 9999, function() end)
									else
										shuttleFigure.setPosition(shuttleFigure.getPosition() + turnOffset)
										broadcastToAll('착륙선 토큰이 한 라운드 앞으로 이동했습니다.', lifeformColor)
										locSkip = true
									end
								else
									locSkip = true
								end
							else
								locSkip = true
							end
							
							if locSkip then
								Wait.time(function() proceedToNextPhase2 = true end, 1)
							end
							
							
						elseif tag == 'eventMainFirespitterShootChar' then
							locTagFound = true
							local playersFound = {}
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								local locPlayerRoom = gO(playerRoomGUID)
								local locPlayerRoomPos = locPlayerRoom.getPosition()
								local locLoopBreak = false
								
								for _, adjacentCorridorGUID in pairs(RoomsMap[playerRoomGUID][2]) do
									if locLoopBreak then
										break
									else
									
										local locCor = gO(adjacentCorridorGUID)
										local locCorPos = locCor.getPosition()
										for _, intruder in pairs(locIntruders) do
											if locLoopBreak then
												break
											else
												
												if intruder.getGMNotes() == 'firespitter' then
													local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locCor.getRotation().y)
													local locIntrPos = intruder.getPosition()
													
													if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
													and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6 then
													
														local locDoorFound = false
														
														for _, door in pairs(locDoors) do
															if door != nil then
																local locDoorPos = door.getPosition()
																if distanceMath(locPlayerRoomPos, locDoorPos) < returnRoomDiameter(locPlayerRoom)*0.7
																and dotMath(normalizeMath(locDoorPos-locPlayerRoomPos), normalizeMath(locCorPos-locPlayerRoomPos)) > 0.9
																then
																	locDoorFound = true
																	break
																end
															end
														end
														locLoopBreak = true
														if not locDoorFound then
															loseHealth(color)
															loseHealth(color)
															table.insert(playersFound, color)
															break
														end
													end
												end
											end
										end
									end
								end
							end
							
							if #playersFound > 0 then
								local locCock = math.random(84,89)
								playsounds(locCock)
								
								local locShoot = math.random(90,91)
								Wait.time(function()
									for _, color in pairs (playersFound) do
										broadcastToAll('플레이어 ' .. color .. '가 파이어스피터에게 사격을 받고 있습니다!', lifeformColor)
									end
									playsounds(locShoot)
								end, soundDuration[locCock+1])
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
							
						elseif tag == 'eventMainFireSpreadOxy' then
							locTagFound = true
							local locWait2 = 0
							
							local locRoomsAmount = #locRooms
							local locRoomsAddedFire = {}
							local locOffsets = {-6.6,3.88,15.22}
							local locSections = {0,0,0}
							
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									local locPosX = obj.getPosition().x
									if math.abs(locPosX-locOffsets[1]) < 1 then
										locSections[1] = 1
									elseif math.abs(locPosX-locOffsets[2]) < 1 then
										locSections[2] = 1
									elseif math.abs(locPosX-locOffsets[3]) < 1 then
										locSections[3] = 1
									end
								end
							end
							
							
							for _, roomTile in pairs (locRooms) do
								local roomTileGUID = roomTile.getGUID()
								local locRoomPos = roomTile.getPosition()
								for _, fireToken in pairs(locFires) do
									if distanceMath(fireToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) * 0.7 then
										local locRoomTileGUID = roomTile.getGUID()
										
										for _, corridorGUID in pairs(RoomsMap[locRoomTileGUID][2]) do
											if #RoomsMap[corridorGUID][2] > 1 then
												local locCor = gO(corridorGUID)
												
												for _, neighbourRoomGUID in pairs(RoomsMap[corridorGUID][2]) do
													
													if roomTileGUID != neighbourRoomGUID and locRoomsAddedFire[neighbourRoomGUID] == nil then
														local locOtherRoom = gO(neighbourRoomGUID)
														local locOtherRoomPos = locOtherRoom.getPosition()
														local locDoorFound = false
														for _, door in pairs(locDoors) do
															if door != nil then
																local locDoorPos = door.getPosition()
																if distanceMath(locCor.getPosition(), locDoorPos) < corridorImportedSize.x*0.55
																and dotMath(normalizeMath(locDoorPos-locRoomPos), normalizeMath(locOtherRoomPos-locRoomPos)) > 0.9
																then
																	locDoorFound = true
																	break
																end
															end
														end
														
														if not locDoorFound then
															local locSectionIndex = 2
															
															if locOtherRoomPos.x < -5.5 then
																locSectionIndex = 1
															elseif locOtherRoomPos.x > 5.5 then
																locSectionIndex = 3
															end
															
															if locSections[locSectionIndex] == 1 then
																local locFireFound = false
																for _, fireToken in pairs (locFires) do
																	if distanceMath(fireToken.getPosition(), locOtherRoomPos) < returnRoomDiameter(locOtherRoom) * 0.7 then
																		locFireFound = true
																		break
																	end
																end
																
																if not locFireFound then
																	local w = locWait2
																	locWait2 = locWait2 + 1
																	Wait.time(function()
																		placeFire(locOtherRoomPos + Vector(0.35,0,-1.3), false)
																	end, w)
																	locRoomsAddedFire[neighbourRoomGUID] = 1
																end
															end
														end
													end
												end
											end
										end
										break
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+1)
							
						elseif tag == 'eventMainHealIntruders' then
							locTagFound = true
							
							for _, intruder in pairs (locIntruders) do
								if intruder != nil then
									intruder.setVar("count", 0)
									intruder.call("updateDisplay")
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						elseif tag == 'eventMainHibernatoriumBurnBreak' then
							locTagFound = true
							
							if hibUnexplored == nil then
								local locFireFound = false
								local locMalfFound = false
								
								local locHibernatoriumPos = hiddenRoom.getPosition()
								local locHibernatoriumSize = hiddenRoom.getBounds().size.x
								
								for _, fireToken in pairs(locFires) do
									if distanceMath(fireToken.getPosition(), locHibernatoriumPos) <= locHibernatoriumSize * 0.7 then
										locFireFound = true
										break
									end
								end
								
								for _, malfunctionToken in pairs(locMalfunctions) do
									if distanceMath(malfunctionToken.getPosition(), locHibernatoriumPos) <= locHibernatoriumSize * 0.7 then
										locMalfFound = true
										break
									end
								end
								
								if not locFireFound then
									placeFire(locHibernatoriumPos + Vector(0.35,0,-1.3), false)
								end
								
								if not locMalfFound then
									placeMalfunction(locHibernatoriumPos + Vector(0,0,-1.05))
								end
							end
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						
						elseif tag == 'eventMainHibEscapeBreak' then
							locTagFound = true
							
							for _, roomTile in pairs (locRooms) do
								if (roomTile.getName() == 'HIBERNATORIUM' and hibUnexplored == nil) or roomTile.getName() == 'ESCAPE SHUTTLE' then
									local locMalfFound = false
									local locRoomPos = roomTile.getPosition()
									
									for _, malfunctionToken in pairs(locMalfunctions) do
										if distanceMath(malfunctionToken.getPosition(), locRoomPos) <= returnRoomDiameter(roomTile) then
											locMalfFound = true
											break
										end
									end
									
									if not locMalfFound then
										placeMalfunction(locRoomPos + Vector(0,0,-1.05))
									end
								end
							end
						
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						elseif tag == 'eventMainInGreenBrokenDamage' then
							locTagFound = true
							
							for _, roomTile in pairs (locRooms) do
								if string.find(roomTile.getDescription(), 'G') != nil then
									local locRoomPos = roomTile.getPosition()
									for _, malfunctionToken in pairs (locMalfunctions) do
										if distanceMath(malfunctionToken.getPosition(), locRoomPos) < tileImportedSize.x then
											
											for _, intruder in pairs (locIntruders) do
												if intruder != nil then
													if distanceMath(intruder.getPosition(), locRoomPos) < tileImportedSize.x *0.5 then
														if intruder.getVar("count") >= 4 then
															critOnIntruder(intruder, roomTile)
														else
															intruder.setVar("count", intruder.getVar("count") + 2)
															intruder.call("updateDisplay")
														end
													end
												end
											end
											
											local locRoomGUID = roomTile.getGUID()
											
											for color, playerRoomGUID in pairs(locPlayerTiles) do
												if playerRoomGUID == locRoomGUID then
													loseHealth(color)
													loseHealth(color)
												end
											end
											
											
											break
										end
									end
									
								end
							end
							
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						elseif tag == 'eventMainInOxyBurnMalfunction' then

							locTagFound = true
							
							local locWait2 = 0
							local locOffsets = {-6.6,3.79,15.09}
							local locSections = {0,0,0}
							
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									local locPosX = obj.getPosition().x
									if math.abs(locPosX-locOffsets[1]) < 1 then
										locSections[1] = 1
									elseif math.abs(locPosX-locOffsets[2]) < 1 then
										locSections[2] = 1
									elseif math.abs(locPosX-locOffsets[3]) < 1 then
										locSections[3] = 1
									end
								end
							end

							for _, roomTile in pairs (locRooms) do
								local locRoomPos = roomTile.getPosition()
								local locRoomSize = returnRoomDiameter(roomTile)
								local locMalfFound = false

							 
								for _, malfunctionToken in pairs(locMalfunctions) do
									if distanceMath(malfunctionToken.getPosition(), locRoomPos) < locRoomSize*0.7 then
										locMalfFound = true
										break
									end
								end

								if locMalfFound then
									local locFireFound = false

									for _, fireToken in pairs(locFires) do
										if distanceMath(fireToken.getPosition(), locRoomPos) < locRoomSize * 0.7 then
											locFireFound = true
											break
										end
									end

									if not locFireFound then
										local locSectionIndex = 2
										
										if locRoomPos.x < -5.5 then
											locSectionIndex = 1
										elseif locRoomPos.x > 5.5 then
											locSectionIndex = 3
										end
										
										
										if locSections[locSectionIndex] == 1 then
											local w = locWait2
											locWait2 = locWait2 + 0.25
											Wait.time(function()
												placeFire(locRoomPos + Vector(0.35,0,-1.3), false)
											end, w)
										end
									end
								end

							end
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						elseif tag == 'eventMainInAmmo2Burn' then
							locTagFound = true
							
							
							-- for _, roomTile in pairs (locRooms) do
								-- if string.find(roomTile.getDescription(), 'RR') != nil then
									-- local locPos = roomTile.getPosition()
									-- local locFireFound = false
									
									-- for _, fireToken in pairs (locFires) do
										-- if distanceMath(fireToken.getPosition(), locPos) < tileImportedSize.x then
											-- locFireFound = true
											-- break
										-- end
									-- end
									
									-- if not locFireFound then
										-- placeFire(locPos + Vector(0.35,0,-1.3))
									-- end
								-- end
							-- end
							
							local locAmmoRoomTbl = {}
							local locRobotRoom = nil
							local i = 0
							
							for color, pRoomGUID in pairs (locPlayerTiles) do
								local locPBoardPos = gO(playerInfoTable[color].boardGUID).getPosition()
								
								if locAmmoRoomTbl[pRoomGUID] == nil then
									locAmmoRoomTbl[pRoomGUID] = 0
								end
								
								if locAmmoRoomTbl[pRoomGUID] < 2 then
									
									Wait.time(function()
										if locAmmoRoomTbl[pRoomGUID] < 2 then
											for _, token in pairs (shapeCast(locPBoardPos + Vector(-2.44,0,2.01), {3.34,10,4.36})) do
												if token.getGMNotes() == 'ammo' then
													locAmmoRoomTbl[pRoomGUID] = locAmmoRoomTbl[pRoomGUID] + 1
												end
											end
										end
									end, i * 0.5)
									i = i + 1
								end
							end
							
							if robot != nil then
								locRobotRoom = getTaggedObjAtPos('room', robot.getPosition(), 0)
								
								if locRobotRoom != nil then
									local locRobotRoomGUID = locRobotRoom.getGUID()
									
									if locAmmoRoomTbl[locRobotRoomGUID] == nil then
										locAmmoRoomTbl[locRobotRoomGUID] = 0
									end								
									
									if locAmmoRoomTbl[locRobotRoomGUID] < 2 then
										
										Wait.time(function()
											if locAmmoRoomTbl[locRobotRoomGUID] < 2 then
												for _, token in pairs (shapeCast({-10,1.7,20.48}, {1,11,2})) do
													if token.getGMNotes() == 'ammo' then
														locAmmoRoomTbl[locRobotRoomGUID] = locAmmoRoomTbl[locRobotRoomGUID] + 1
													end
												end
											end
										end, i * 0.5)
										i = i + 1
									end
								end
							end
							
							Wait.time(function()
								for roomGUID, ammoAmount in pairs (locAmmoRoomTbl) do
									
									if ammoAmount > 1 then
										local locRoomToBurn = gO(roomGUID)
										local locFireFound = false
										
										for _, fireToken in pairs (locFires) do
											if distanceMath(fireToken.getPosition(), locRoomToBurn.getPosition()) < returnRoomDiameter(locRoomToBurn) then
												locFireFound = true
												break
											end
										end
										
										if not locFireFound then
											placeFire(locRoomToBurn.getPosition() + Vector(0.35,0,-1.3), false)
										end
									end
								end
							end, i*0.5 + 1)
							
							Wait.time(function() proceedToNextPhase2 = true end, i*0.5 + 1)
						elseif tag == 'eventMainIntruderBreak' then
							locTagFound = true
							local locBrokenTiles = {}

							for _, intruder in pairs(locIntruders) do
								local locTileFound = false
								local locPos = intruder.getPosition()
								
								
								--New version does not unreinforce corridors anymore.
								
								--intruder.setPosition(locPos + Vector(0,1,0))
								--intruder.setRotation({0,0,0})
								
								-- for _, corridor in pairs(locCorridors) do
									-- local locCorGUID = corridor.getGUID()
									-- if locBrokenTiles[locCorGUID] == nil then
										
										-- local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridor.getRotation().y)
										-- local locIntrPos = intruder.getPosition()
										-- local locCorPos = corridor.getPosition()
										
										-- if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
										-- and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6 then
											-- locTileFound = true
											-- local locCorRot = corridor.getRotation()
											-- corridor.setRotation({locCorRot.x, locCorRot.y, 0})
											-- locBrokenTiles[locCorGUID] = 1
											-- break

										-- end
									-- end
								-- end

								if not locTileFound then
									for _, roomTile in pairs(locRooms) do
										if roomTile.getName() != 'NEST' then
											local locRoomGUID = roomTile.getGUID()

											if locBrokenTiles[locRoomGUID] == nil then
												local locRoomPos = roomTile.getPosition()
												local locRoomSize = returnRoomDiameter(roomTile)
												if distanceMath(locRoomPos, locPos) < locRoomSize * 0.5 then
													locBrokenTiles[locRoomGUID] = 1
													local locMalfFound = false

													for _, malfunctionToken in pairs(locMalfunctions) do
														if distanceMath(locRoomPos, malfunctionToken.getPosition()) < locRoomSize * 0.7 then
															locMalfFound = true
															break
														end
													end

													if not locMalfFound then
														placeMalfunction(locRoomPos + Vector(0,0,-1.05))
													end

												end 

											end
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)

						elseif tag == 'eventMainLandBurnBreak' then
							locTagFound = true

							local locFireFound = false
							local locMalfFound = false
							local locLZPos = landingZone.getPosition()
							local locLZSize = tileImportedSize.x
							for _, fireToken in pairs(locFires) do
								if distanceMath(fireToken.getPosition(), locLZPos) <= locLZSize * 0.7 then
									locFireFound = true
									break
								end
							end
							
							for _, malfunctionToken in pairs(locMalfunctions) do
								if distanceMath(malfunctionToken.getPosition(), locLZPos) <= locLZSize * 0.7 then
									locMalfFound = true
									break
								end
							end
							
							if not locFireFound then
								placeFire(locLZPos + Vector(0.35,0,-1.3), false)
							end
							
							if not locMalfFound then
								placeMalfunction(locLZPos + Vector(0,0,-1.05))
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)

						elseif tag == 'eventMainLanderLate' then
							locTagFound = true
							
							if shuttleFigure != nil then
								local locLanderPos = shuttleFigure.getPosition()
								local locTurnPos = turnMarker.getPosition()

								if math.abs(locLanderPos.x - locTurnPos.x) < 0.3 then

									if math.abs (locLanderPos.z - 2.57) < 0.3 then
										shuttleFigure.destruct()
										broadcastToAll('네오플레시가 착륙선을 파괴했습니다!', lifeformColor)
										playsounds(-1)
										playsounds(math.random(190,192))
										lightAlert()
									else
										local locLatePos = Vector(locLanderPos.x, 3, math.max(2.57,locLanderPos.z- 5*turnOffset.z))
										shuttleFigure.setPosition(locLatePos)
										broadcastToAll('네오플레시가 착륙선 도착을 지연시켰습니다.', lifeformColor)
										playsounds(-1)
										playsounds(181)
										
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)

						elseif tag == 'eventMainLandingCorAdults' then
							locTagFound = true
							
							local locWait2 = 0
							for _, landingCorGUID in pairs(RoomsMap[landingZone.getGUID()][2]) do
								local locCor = gO(landingCorGUID)
								local locRotZ = locCor.getRotation().z
								if not (locRotZ > 178 and locRotZ < 182) then

									local locIntrAmount = 0
									local locCorPos = locCor.getPosition()
									local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locCor.getRotation().y)
									for _, intruder in pairs(locIntruders) do
										
										local locIntrPos = intruder.getPosition()
										
										
										if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
										and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6 then

											if intruder.getGMNotes() == 'queen' then
												locIntrAmount = locIntrAmount + 4
											else
												locIntrAmount = locIntrAmount +1
											end
											
											if locIntrAmount >= 6 then
												break
											end
										end
									end
									
									if locIntrAmount == 0 then
										for n = 1, #locNoises do
											local noiseToken = locNoises[n]
											if noiseToken != nil then
												if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
													noiseToken.destruct()
													table.remove(locNoises, n)
													break
												end
											end
										end
									end

									if locIntrAmount < 6 then
										
										for j = 1,  math.min(6-locIntrAmount, 4) do
											local w = locWait2
											locWait2 = locWait2 + 0.25
											
											if adultFBag.getQuantity() > 0  then
												adultFBag.takeObject({
													position = adultFBag.getPosition() + Vector(0,6,0),
													rotation = {0,0,0},
													callback_function = function(o)
														o.setLock(true)
														if o.hasTag('rot180') then
															o.setRotation({0,(locCor.getRotation().y+90),0})
														else
															o.setRotation({0,0,0})
														end
														
														Wait.time(function()
															o.setPositionSmooth(findSpaceOnTile(locCor, nil, true), false, true)
														end, w)
														

													end,
												})
											end
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						elseif tag == 'eventMainLandingTacticalRemove1' then
							locTagFound = true
							
							local tacticalRemove = {0,0,0,0}
							local maxRemove = 1
							
							local landPos = landingZone.getPosition()
							local hibernatoriumPos = hiddenRoom.getPosition()
							for _, obj in pairs(getAllObjects()) do
								local objPos = obj.getPosition()
								if objPos.z > landPos.z and objPos.z < (hibernatoriumPos.z - tileImportedSize.x) then
									local locGM = obj.getGMNotes()
									if locGM == 'ammo' and tacticalRemove[1] != maxRemove then
										obj.destruct()
										tacticalRemove[1] = tacticalRemove[1] +1

									elseif locGM == 'grenade' and tacticalRemove[2] != maxRemove then
										obj.destruct()
										tacticalRemove[2] = tacticalRemove[2] +1

									elseif locGM == 'oxygen' and tacticalRemove[3] != maxRemove then
										obj.destruct()
										tacticalRemove[3] = tacticalRemove[3] +1

									elseif locGM == 'medpack' and tacticalRemove[4] != maxRemove then
										obj.destruct()
										tacticalRemove[4] = tacticalRemove[4] +1
									end
								end
							end
							
							for _, count in pairs (tacticalRemove) do
								if count != 0 then
									broadcastToAll('각 유형의 전술 장비 토큰 1개가 착륙 구역에서 제거되었습니다!', lifeformColor)
									break
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainLarvaComputerChar' then
							locTagFound = true
						
							local locWait2 = 0
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.hasTag('computer') then
									local roomTileGUID = roomTile.getGUID()
									local locPCol = ''
									for color, playerRoomGUID in pairs(locPlayerTiles) do
										if playerRoomGUID == roomTileGUID then
											locPCol = color
											break
										end
									end
									if larvaeFBag.getQuantity() > 0 and locPCol != '' then
										local w = locWait2
										locWait2 = locWait2 + 0.25
										Wait.time(function()
											larvaeFBag.takeObject({
												position = larvaeFBag.getPosition() + Vector(0,6,0),
												rotation = {0,0,0},
												callback_function = function(o)
													o.setLock(true)
													checkSecureRoom(roomTile, o, locPCol)
													o.setPositionSmooth(findSpaceOnTile(roomTile, nil, true, o), false, true)
												end,
											})
										end, w)
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+1)

						elseif tag == 'eventMainLarvaDiscardSecurity' then
							locTagFound = true
							
							-- local locWait2 = 0
							-- local locSecureRemoves = { ['A'] = 0, ['B'] = 0, ['C'] = 0}
							-- local locSecuresGUID = {}
							-- for _, secureToken in pairs(locSecures) do
								-- table.insert(locSecuresGUID, secureToken.getGUID())
							-- end

							-- for _, intruder in pairs(locIntruders) do
								-- local locPosX = intruder.getPosition().x
								-- if intruder.getGMNotes() == 'larvae' then
									-- locSecureRemoves[getSectionFromXPos(locPosX)] = locSecureRemoves[getSectionFromXPos(locPosX)] + 1
									-- enemyFigReturn(intruder)
								-- end
							-- end

							-- for _, roomTile in pairs(locRooms) do

								-- local locPos = roomTile.getPosition()
								-- local locSection = getSectionFromXPos(locPos.x)
								-- for _, secureTokenGUID in pairs(locSecuresGUID) do
									-- local locSecureToken = gO(secureTokenGUID)
									-- if locSecureToken != nil then
										-- if distanceMath(locSecureToken.getPosition(), locPos) < tileImportedSize.x then
											-- for j = 1, locSecureRemoves[locSection] do
												-- local w = locWait2
												-- locWait2 = locWait2 + 0.25
												-- Wait.time(function()
													-- locSecureToken = gO(secureTokenGUID)
													-- if locSecureToken != nil then
														-- secureTokenRemove(locSecureToken)
													-- end
												-- end, w)
											-- end
										-- end
									-- end
								-- end
							-- end
							
							for _, section in pairs ({'A', 'B', 'C'}) do
								local locRoom = getRoomHighestID(section, false)
								if locRoom != nil then
									local locPos = locRoom.getPosition()
									local roomTileGUID = locRoom.getGUID()
									local locPCol = ''
									for color, playerRoomGUID in pairs(locPlayerTiles) do
										if playerRoomGUID == roomTileGUID then
											locPCol = color
											break
										end
									end
									for _, secureTokenGUID in pairs(locSecuresGUID) do
										local locSecureToken = gO(secureTokenGUID)
										if locSecureToken != nil then
											if distanceMath(locSecureToken.getPosition(), locPos) < tileImportedSize.x then
												secureTokenRemove(locSecureToken)
												break
											end
										end
									end
									if larvaeFBag.getQuantity() > 0 then
										larvaeFBag.takeObject({
											position = larvaeFBag.getPosition() + Vector(0,6,0),
											rotation = {0,0,0},
											callback_function = function(o) 
												o.setLock(true)
												if locPCol != '' then
													checkSecureRoom(locRoom, o, locPCol)
												end
												o.setPositionSmooth(findSpaceOnTile(locRoom, nil, true, o), false, true)
											end,
										})
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)

						elseif tag == 'eventMainLarvaNestChar' then
							locTagFound = true
							
							local locWait2 = 0
							if larvaeFBag.getQuantity()  > 0 then

								for _, roomTile in pairs(locRooms) do
									if roomTile.getName() == 'NEST' then
										local locRoomGUID = roomTile.getGUID()
										local locPCol = ''
										for color, playerRoomGUID in pairs(locPlayerTiles) do
											if locRoomGUID == playerRoomGUID then
												locPCol = color
												break
											end
										end

										larvaeFBag.takeObject({
											position = larvaeFBag.getPosition() + vector(0,6,0),
											rotation = {0,0,0},
											callback_function = function(o)
												if locPCol != '' then
													intruderAttack(roomTile, o, locPCol)
												end
												
												o.setPositionSmooth(findSpaceOnTile(roomTile, nil, true, o), false, true)
												
												o.setLock(true)
												if o.hasTag('rot180') then
													o.setRotation({0,180,0})
												else
													o.setRotation({0,0,0})
												end
											end,
										})
										break
									end
								end

								locWait2 = 0.2
								local locUniqueCorGUID = {}
								for color, playerRoomGUID in pairs(locPlayerTiles) do
									for _, corridorGUID in pairs(RoomsMap[playerRoomGUID][2]) do
										if #RoomsMap[corridorGUID][2] == 1 and locUniqueCorGUID[corridorGUID] == nil and larvaeFBag.getQuantity() > 0 then
											locUniqueCorGUID[corridorGUID] = 1
											local locCor = gO(corridorGUID)
											local locPos = locCor.getPosition()
											local locIntrAmount = 0
											for _, intruder in pairs (locIntruders) do
												if intruder != nil then
													local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locCor.getRotation().y)
													local locIntrPos = intruder.getPosition()
													
													if distanceMath(locIntrPos, locPos) <= corridorImportedSize.x *0.5
													and math.abs(dotMath(locIntrPos-locPos, locCorZVector)) <= corridorImportedSize.z *0.6 then

														locIntrAmount = locIntrAmount +1
														if locIntrAmount == 6 then
															break
														end
													end
												end
											end
											
											if locIntrAmount == 0 then
												for n = 1, #locNoises do
													local noiseToken = locNoises[n]
													if noiseToken != nil then
														if distanceMath(noiseToken.getPosition(), locPos) < corridorImportedSize.x *0.5 then
															noiseToken.destruct()
															table.remove(locNoises,n)
															break
														end
													end
												end
											end
											
											if locIntrAmount < 6 then
												local w = locWait2
												locWait2 = locWait2 + 0.25
												Wait.time(function()
													if larvaeFBag.getQuantity() > 0 then
														larvaeFBag.takeObject({
															position = findSpaceOnTile(locCor, nil, true),
															rotation = {0,0,0},
															callback_function = function(o)
																o.setLock(true)
																if o.hasTag('rot180') then
																	o.setRotation({0,(locCor.getRotation().y+90+180),0}) --unless corridor was placed manually the rotation should be good.
																end
															end,
														})
													end
												end, w)
											end
										end
									end
								end
							end 
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)

						elseif tag == 'eventMainLarvaStealLandingZone' then
							locTagFound = true
							
							local larvaCount = 0

							for _, intruder in pairs(locIntruders) do
								if intruder.getGMNotes() == 'larvae' then
									local locPos = intruder.getPosition()
									local locPCol = ''
									local larvaFound = false

									for _, roomTile in pairs (locRooms) do

										if distanceMath(locPos, roomTile.getPosition()) < returnRoomDiameter(roomTile) * 0.5 then

											for color, playerRoomGUID in pairs(locPlayerTiles) do
												if playerRoomGUID == roomTile.getGUID() then
													locPCol = color
													break 
												end
											end
											if locPCol != '' then
												break
											else
												locPCol = 'Red'
												larvaFound = true
												break
											end
										end
									end

									if locPCol == '' then
										for _, corridor in pairs (locCorridors) do
											local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridor.getRotation().y)
											local locCorPos = corridor.getPosition()
											
											if distanceMath(locPos, locCorPos) <= corridorImportedSize.x *0.5
											and math.abs(dotMath(locPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6 then

												if #RoomsMap[corridor.getGUID()][2] == 2 then
													larvaFound = true
													break
												end
											end
										end
									end
									
									if larvaFound then
										local w = larvaCount *0.25
										larvaCount = larvaCount +1
										Wait.time(function()
											intruder.SetPositionSmooth(findSpaceOnTile(landingZone, nil, true, intruder), false, true)
											for color, playerRoomGUID in pairs (locPlayerTiles) do
												if playerRoomGUID == landingZone.getGUID() then
													checkSecureRoom(landingZone, intruder, color)
													break
												end
											end
										end, w)
									end
								end
							end

							local tacticalRemove = {0,0,0,0}
							local maxRemove = math.min(4, larvaCount)

							Wait.time(function()
								local landPos = landingZone.getPosition()
								local hibernatoriumPos = hiddenRoom.getPosition()
								for _, obj in pairs(getAllObjects()) do
									local objPos = obj.getPosition()
									if objPos.z > landPos.z and objPos.z < (hibernatoriumPos.z - tileImportedSize.x) then
										local locGM = obj.getGMNotes()
										if locGM == 'ammo' and tacticalRemove[1] != maxRemove then
											obj.destruct()
											tacticalRemove[1] = tacticalRemove[1] +1

										elseif locGM == 'grenade' and tacticalRemove[2] != maxRemove then
											obj.destruct()
											tacticalRemove[2] = tacticalRemove[2] +1

										elseif locGM == 'oxygen' and tacticalRemove[3] != maxRemove then
											obj.destruct()
											tacticalRemove[3] = tacticalRemove[3] +1

										elseif locGM == 'medpack' and tacticalRemove[4] != maxRemove then
											obj.destruct()
											tacticalRemove[4] = tacticalRemove[4] +1
										end
									end
								end

							end, larvaCount * 0.25 + 0.5)
							
							Wait.time(function() proceedToNextPhase2 = true end, larvaCount * 0.25 + 0.5 + 1)
						
						elseif tag == 'eventMainLifeSBreak' then
							locTagFound = true
						
						
							for _, obj in pairs(getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									obj.setState(2)
									broadcastToAll('생명 유지 장치가 비활성화되었습니다.', lifeformColor)
									
								elseif obj.getName() == 'LIFE SUPPORT CONTROL' and obj.hasTag('room') then
									local locMalfFound = false
									for _, malfunctionToken in pairs(locMalfunctions) do
										if distanceMath(malfunctionToken.getPosition(), obj.getPosition()) < tileImportedSize.x then
											locMalfFound = true
											break
										end
									end
									
									if not locMalfFound then
										placeMalfunction(obj.getPosition() + Vector(0,0,-1.05))
									end									
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)

						elseif tag == 'eventMainLifeSBurnBreak' then
							locTagFound = true
							local locWait2 = 0
							local locOffsets = {-6.6,3.88,15.22}
							local locSections = {0,0,0}
							
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									local locPosX = obj.getPosition().x
									if math.abs(locPosX-locOffsets[1]) < 1 then
										locSections[1] = 1
									elseif math.abs(locPosX-locOffsets[2]) < 1 then
										locSections[2] = 1
									elseif math.abs(locPosX-locOffsets[3]) < 1 then
										locSections[3] = 1
									end
								end
							end
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.getName() == 'LIFE SUPPORT CONTROL' then
									local locRoomPos = roomTile.getPosition()
									local locSectionIndex = 2
									
									if locRoomPos.x < -5.5 then
										locSectionIndex = 1
									elseif locRoomPos.x > 5.5 then
										locSectionIndex = 3
									end
									
									if locSections[locSectionIndex] == 1 then
										local locFireFound = false
										
										for _, fireToken in pairs(locFires) do
											if distanceMath(locRoomPos, fireToken.getPosition()) < tileImportedSize.x then
												locFireFound = true
												break
											end
										end
										
										if not locFireFound then
											local w = locWait2
											locWait2 = locWait2 + 1
											Wait.time(function()
												placeFire(locRoomPos + Vector(0.35,0,-1.3), false)
											end, w)
										end
									else
										local locMalfFound = false
										
										for _, malfunctionToken in pairs(locMalfunctions) do
											if distanceMath(locRoomPos, malfunctionToken.getPosition()) < tileImportedSize.x then
												locMalfFound = true
												break
											end
										end
										
										if not locMalfFound then
											local w = locWait2
											locWait2 = locWait2 + 0.5
											Wait.time(function()
												placeMalfunction( locRoomPos + Vector(0, 0, -1.05))
											end, w)
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						
						
						elseif tag == 'eventMainMeatAdult' then
							locTagFound = true
							for _, roomTile in pairs (locRooms) do
								
								local locRoomPos = roomTile.getPosition()
								
								if adultFBag.getQuantity() > 0 then
									
									for _, meat in pairs (locMeats) do
										
										if meat != nil then
											local locPos = meat.getPosition()
											if distanceMath(locPos, locRoomPos) < tileImportedSize.x then
												meat.setPosition({45,-9,0})
												meat.destruct()
												
												adultFBag.takeObject({
													position = locPos,
													rotation = {0,0,0},
													callback_function = function(o)
														o.setLock(true)
														if o.hasTag('rot180') then
															o.setRotation({0,180,0})
														end
														local locRoomGUID = roomTile.getGUID()
														
														for color, pRoomGUID in pairs (locPlayerTiles) do
															if locRoomGUID == pRoomGUID then
																checkSecureRoom(roomTile, o, color)
																break
															end
														end
													end,
												})
												break
											end
										end
									end
								else
									break
								end
							
							end
							
						
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						elseif tag == 'eventMainNestDroneC' then
							locTagFound = true
							local locWait2 = 0
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.getName() == 'NEST' then
									local locRoomGUID = roomTile.getGUID()
									for j = 1, 2 do
										if breederFBag.getQuantity() > 0 then

											local w = locWait2
											locWait2 = locWait2 + 0.25
											breederFBag.takeObject({
												position = breederFBag.getPosition() + Vector(0,6,0),
												rotation = {0,0,0},
												callback_function = function(o)
													o.setLock(true)
													
													Wait.time(function()
														o.setPositionSmooth(findSpaceOnTile(roomTile, nil, true, o),false, true)
														for color, playerRoomGUID in pairs(locPlayerTiles) do
															if playerRoomGUID == locRoomGUID then
																intruderAttack(roomTile, o, color)
																break
															end
														end
														
														
														if o.hasTag('rot180') then
															o.setRotation({0,180,0})
														else
															o.setRotation({0,0,0})
														end
													end, w)
												end,
											})
										end
									end
									break
								end
							end
							
							for _, corridorTile in pairs(locCorridors) do
								local locCorGUID = corridorTile.getGUID()
								local locCorPos = corridorTile.getPosition()
								if locCorPos.x > 5 and #RoomsMap[locCorGUID][2] == 1 then
									if breederFBag.getQuantity() > 0 then
										local w = locWait2
										locWait2 = locWait2 + 0.25
										Wait.time(function()
											breederFBag.takeObject({
												position =  findSpaceOnTile(corridorTile, nil, true),
												rotation = {0,0,0},
												callback_function = function(o)
													o.setLock(true)
													if o.hasTag('rot180') then
														o.setRotation({0,(corridorTile.getRotation().y+90+180),0})
													end
												end,
											})
										end, w)
										
										for n = 1, #locNoises do
											local noiseToken = locNoises[n]
											if noiseToken != nil then
												if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
													noiseToken.destruct()
													table.remove(locNoises,n)
													break
												end
											end
										end
									end
									
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
							
						elseif tag == 'eventMainNestAdultC' then
							locTagFound = true
							local locWait2 = 0
							
							for _, roomTile in pairs(locRooms) do
								if roomTile.getName() == 'NEST' then
									local locRoomGUID = roomTile.getGUID()
									for j = 1, 4 do
										if adultFBag.getQuantity() > 0 then

											local w = locWait2
											locWait2 = locWait2 + 0.25
											
											adultFBag.takeObject({
												position = adultFBag.getPosition() + Vector(0,6,0),
												rotation = {0,0,0},
												callback_function = function(o)
													o.setLock(true)
													
													Wait.time(function()
														o.setPositionSmooth(findSpaceOnTile(roomTile, nil, true, o), false, true)
														for color, playerRoomGUID in pairs(locPlayerTiles) do
															if playerRoomGUID == locRoomGUID then
																intruderAttack(roomTile, o, color)
																break
															end
														end
														
														o.setRotation({0,0,0})
													end, w)
												end,
											})
										end
									end
									break
								end
							end
							
							for _, corridorTile in pairs(locCorridors) do
								local locCorGUID = corridorTile.getGUID()
								local locCorPos = corridorTile.getPosition()
								if locCorPos.x > 4.5 then
									if adultFBag.getQuantity() > 0 then
										local w = locWait2
										locWait2 = locWait2 + 0.25
										Wait.time(function()
											local locCorCrowd = getTaggedObjAtPos('healthCount', locCorPos, 0, corridorTile.getBounds().size *Vector(0.99,1,0.57) + Vector(0,9,0), corridorTile.getRotation(), true)
											
											local locCorCrowdSize = 0
											
											for _, intruder in pairs (locCorCrowd) do
												if distanceMath(intruder.getPosition(), locCorPos) < corridorImportedSize.x * 0.5 then
													if intruder.getGMNotes() == 'queen' then
														locCorCrowdSize = locCorCrowdSize + 4
													else
														locCorCrowdSize = locCorCrowdSize + 1
													end
												end
											end
											
											if locCorCrowdSize < 6 then
												adultFBag.takeObject({
													position =  findSpaceOnTile(corridorTile, nil, true),
													rotation = {0,0,0},
													callback_function = function(o) o.setLock(true) end,
												})
											end
										end, w)
									end
									
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						elseif tag == 'eventMainNoiseCharDrone' then
							locTagFound = true
							
							local locWait2 = 0
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									local locCor = gO(corridorGUID)
									for n = 1, #locNoises do
										local noiseToken = locNoises[n]
										if noiseToken != nil then
											if distanceMath(noiseToken.getPosition(), locCor.getPosition()) < corridorImportedSize.x *0.5 then
												if breederFBag.getQuantity() > 0 then
													local locDir = gO(playerRoomGUID).getPosition()-locCor.getPosition()
													local locDegreeToNearPlayer = 180
													locDegreeToNearPlayer = 90+180+180*math.atan2(locDir[3],locDir[1]*(-1))/3.1415926352
													noiseToken.destruct()
													table.remove(locNoises, n)
													local w = locWait2
													locWait2 = locWait2 + 0.25
													Wait.time(function()
														breederFBag.takeObject({
															position =  findSpaceOnTile(locCor, nil, true),
															rotation = {0,0,0},
															callback_function = function(o)
																o.setLock(true)
																if o.hasTag('rot180') then
																	o.setRotation({0,locDegreeToNearPlayer,0})
																end
															end,
														})
													end, w)
												end
												break
											end
										end
									end
								end
							end
							
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						
						elseif tag == 'eventMainNoiseCharEnc' then
							locTagFound = true
							
							local locWait2 = 0
							local locEncParams = {}
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									local locCor = gO(corridorGUID)
									for n = 1, #locNoises do
										local noiseToken = locNoises[n]
										if noiseToken != nil then
											if distanceMath(noiseToken.getPosition(), locCor.getPosition()) < corridorImportedSize.x *0.5 then
													noiseToken.destruct()
													table.remove(locNoises,n)
													table.insert(locEncParams, {locCor})
													locWait2 = locWait2 + 0.25
												break
											end
										end
									end
								end
							end
							
							encounterSequence(locEncParams)
							
							
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+2.5)
						
						
						elseif tag == 'eventMainNoiseCharLarva' then
							locTagFound = true
							
							local locWait2 = 0
							local locFBag = larvaeFBag
							
							for color, playerRoomGUID in pairs(locPlayerTiles) do
								for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									local locCor = gO(corridorGUID)
									for n = 1, #locNoises do
										local noiseToken = locNoises[n]
										if noiseToken != nil then
											if distanceMath(noiseToken.getPosition(), locCor.getPosition()) < corridorImportedSize.x *0.5 then
												if locFBag.getQuantity() > 0 then
													local locDir = gO(playerRoomGUID).getPosition()-locCor.getPosition()
													local locDegreeToNearPlayer = 180
													locDegreeToNearPlayer = 90+180+180*math.atan2(locDir[3],locDir[1]*(-1))/3.1415926352
													noiseToken.destruct()
													table.remove(locNoises, n)
													local w = locWait2
													locWait2 = locWait2 + 0.25
													Wait.time(function()
														locFBag.takeObject({
															position =  findSpaceOnTile(locCor, nil, true),
															rotation = {0,0,0},
															callback_function = function(o)
																o.setLock(true)
																if o.hasTag('rot180') then
																	o.setRotation({0,locDegreeToNearPlayer,0})
																end
															end,
														})
													end, w)
												end
												break
											end
										end
									end
								end
							end
							
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
							
						elseif tag == 'eventMainNoiseInjured' then
							locTagFound = true
							local locCorOnce = {}
							
							for color, playerRoomGUID in pairs (locPlayerTiles) do
								
								
								local locPosX = gO(playerInfoTable[color].healthGUID).getPosition().x - gO(playerInfoTable[color].boardGUID).getPosition().x 
								
								if locPosX > playerHealthLocalPosX[4] + 0.2 and locPosX < playerHealthLocalPosX[8] - 0.2 then
									
									for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
									
										if locCorOnce[corridorGUID] == nil then
										
											locCorOnce[corridorGUID] = 0
											
											local locCor = gO(corridorGUID)
											local locCorPos = locCor.getPosition()
											
											local locIntruderFound = false
											
											for _, intruder2 in pairs (locIntruders) do
												if distanceMath(intruder2.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
													locIntruderFound = true
													break
												end
											end
											
											if not locIntruderFound then
												local locNoiseFound = false
												
												for _, noise in pairs (locNoises) do
													if distanceMath(noise.getPosition(), locCorPos) < corridorImportedSize.x*0.25 then
														locNoiseFound = true
														break
													end
												end
												
												if not locNoiseFound then
													noiseBag.takeObject({
														position = locCorPos + Vector(0,1,0),
														callback_function = function(o) table.insert(locNoises, o) end,
													})
												end
											end
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 3)
							
						elseif tag == 'eventMainNoiseIntruder' then
							locTagFound = true
							local locCorOnce = {}
							
							for _, roomTile in pairs (locRooms) do
								local locRoomPos = roomTile.getPosition()
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(), locRoomPos) < tileImportedSize.x*0.5 then
											
											for _, corridorGUID in pairs (RoomsMap[roomTile.getGUID()][2]) do
												
												if locCorOnce[corridorGUID] == nil then
												
													locCorOnce[corridorGUID] = 0
													
													local locCor = gO(corridorGUID)
													local locCorPos = locCor.getPosition()
													local locIntruderFound = false
													
													for _, intruder2 in pairs (locIntruders) do
														if distanceMath(intruder2.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
															locIntruderFound = true
															break
														end
													end
													
													if not locIntruderFound then
														local locNoiseFound = false
														
														for _, noise in pairs (locNoises) do
															if distanceMath(noise.getPosition(), locCorPos) < corridorImportedSize.x*0.25 then
																locNoiseFound = true
																break
															end
														end
														
														if not locNoiseFound then
															noiseBag.takeObject({
																position = locCorPos + Vector(0,1,0),
																callback_function = function(o) table.insert(locNoises, o) end,
															})
														end
													end
												end
											end
											break
										end
									end
								end
								
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 3)
						
						
						elseif tag == 'eventMainOxyOff' then
							locTagFound = true
							
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									obj.setState(2)
									broadcastToAll('생명 유지 장치가 비활성화되었습니다.', lifeformColor)
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						elseif tag == 'eventMainOxyRemove' then
							locTagFound = true
						
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									obj.setState(2)
									broadcastToAll('생명 유지 장치가 비활성화되었습니다.', lifeformColor)
								elseif obj.hasTag('LifeSupportOff') then
									obj.destruct()
									broadcastToAll('생명 유지 장치 토큰이 제거되었습니다.', lifeformColor)
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainQueenAdd2Drone' then
							locTagFound = true
						
							local locWait2 = 0
							local locQueenAlive = isQueenAlive()
							
							if queenFBag.getQuantity() == 1 or not locQueenAlive then
								onObjectNumberTyped(breederBag, 'Red', 2)
							
							elseif queenFBag.getQuantity() == 0 and locQueenAlive then
								local locQueenTile = nil
								local locQueenSpace = 2
								local locQueenFig = gO(queenFigGUID)
								
								local locQueenPos = locQueenFig.getPosition()
								
								for _, roomTile in pairs(locRooms) do
									if distanceMath(locQueenPos, roomTile.getPosition()) < returnRoomDiameter(roomTile) *0.5 then
										locQueenTile = roomTile
										break
									end
								end
								
								if locQueenTile == nil then
									for _, corridorTile in pairs (locCorridors) do
										local locCorPos = corridorTile.getPosition()
										local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridorTile.getRotation().y)
										
										if distanceMath(locQueenPos, locCorPos) <= corridorImportedSize.x *0.5
										and math.abs(dotMath(locQueenPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6
										then
											locQueenTile = corridorTile
											break
										end
									end
									
									local locCorPos2 = locQueenTile.getPosition()
									local locCorZVector2 = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locQueenTile.getRotation().y)
									
									for _, intruder in pairs (locIntruders) do
										if intruder != nil then
											if intruder.getGMNotes() != 'queen' then
												local locIntrPos = intruder.getPosition()
												if distanceMath(locIntrPos, locCorPos2) <= corridorImportedSize.x *0.5
												and math.abs(dotMath(locIntrPos-locCorPos2, locCorZVector2)) <= corridorImportedSize.z *0.6
												then
													locQueenSpace = locQueenSpace - 1
													
													if locQueenSpace == 0 then
														break
													end
												end
											end
										end
									end
								end
								
								if locQueenTile != nil then
									for j = 1, locQueenSpace do
										if breederFBag.getQuantity() > 0 then
											local w = locWait2
											locWait2 = locWait2 + 0.25
											breederFBag.takeObject({
												position =  breederFBag.getPosition() + Vector(0,6,0),
												rotation = {0,0,0},
												callback_function = function(o)
													o.setLock(true)
													
													Wait.time(function()
														for color, playerRoomGUID in pairs (locPlayerTiles) do
															if playerRoomGUID == locQueenTile.getGUID() then
																checkSecureRoom(locQueenTile, o, color)
																break
															end
														end
														
														
														local locPos = {0,0,0}
														
														if locQueenTile.hasTag('room') then
															locPos = findSpaceOnTile(locQueenTile, nil, true, o)
															if o.hasTag('rot180') then
																o.setRotation({0,180,0})
															end
														else
															locPos = findSpaceOnTile(locQueenTile, nil, true)
															if o.hasTag('rot180') then
																o.setRotation(locQueenFig.getRotation())
															else
																o.setRotation({0,0,0})
															end
														end
														
														o.setPositionSmooth(locPos, false, true)
													end, w)
												end,
												
											})
										end
									end
								end
								
								
								
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2 + 1)
						
						
						
						elseif tag == 'eventMainQueenToInjured' then
							locTagFound = true
							
							local locWait2 = 0
							
							
							if isQueenAlive() and queenFBag.getQuantity() == 0 then
								
								local locQueenFig = gO(queenFigGUID)
								local locQueenPos = locQueenFig.getPosition()
								local locQueenInCombat = false
								
								for color, playerRoomGUID in pairs(locPlayerTiles) do
									local locRoomPos = gO(playerRoomGUID).getPosition()
									
									if distanceMath(locQueenPos, locRoomPos) < tileImportedSize.x*0.5 then
										locQueenInCombat = true
										break
									end
								end
								
								if not locQueenInCombat then
									for color, playerRoomGUID in pairs(locPlayerTiles) do
										local locHealthMarker = gO(playerInfoTable[color].healthGUID)
										local locBoard = gO(playerInfoTable[color].boardGUID)
										if (locHealthMarker.getPosition().x - locBoard.getPosition().x) < playerHealthLocalPosX[8]-0.2 then
											local locPlayerRoom = gO(playerRoomGUID)
											
											locQueenFig.setPositionSmooth(findSpaceOnTile(locPlayerRoom, nil, true, locQueenFig), false, true)
											
											
											checkSecureRoom(locPlayerRoom, locQueenFig, color)
											
											if locQueenFig.hasTag('rot180') then
												locQueenFig.setRotation({0,180,0})
											end
											
											break
										end
									end
								end
								
							else
							
								for color, playerRoomGUID in pairs(locPlayerTiles) do
									local locHealthMarker = gO(playerInfoTable[color].healthGUID)
									local locBoard = gO(playerInfoTable[color].boardGUID)
									if (locHealthMarker.getPosition().x - locBoard.getPosition().x) < playerHealthLocalPosX[8]-0.2 then
										local locFig = gO(playerInfoTable[color].figureGUID)
										
										if locFig != nil then
											local w = locWait2
											locWait2 = locWait2 + 0.25
											Wait.time(function()
												autoNoise({0,0,0}, locFig, false)
											end, w)
										end
									end
								end
							
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, locWait2+1)
							
						elseif tag == 'eventMainRemove1Security' then
							locTagFound = true
							
							for _, roomTile in pairs(locRooms) do
								local locRoomPos = roomTile.getPosition()
								
								for _, secureGUID in pairs(locSecuresGUID) do
									local locSecureToken = gO(secureGUID)
									if locSecureToken != nil then
										if distanceMath(locSecureToken.getPosition(), locRoomPos) < tileImportedSize.x then
											secureTokenRemove(locSecureToken)
											break
										end
									end
								end
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
						
						elseif tag == 'eventMainSlasherLanderRemove' then
							locTagFound = true
							
							local locAddSlasher = true
							
							if shuttleFigure != nil then
								if distanceMath(shuttleFigure.getPosition(), landingZone.getPosition()) < tileImportedSize.x and shuttleFigure.getScale().x > 0.5 then
									for _, intruder in pairs(locIntruders) do
										if intruder.getGMNotes() == 'slasher' then
											if distanceMath(intruder.getPosition(), landingZone.getPosition()) < tileImportedSize.x *0.5 then
												shuttleFigure.destruct()
												broadcastToAll('네오플레시가 착륙선을 파괴했습니다!', lifeformColor)
												playsounds(-1)
												playsounds(math.random(190,192))
												lightAlert()
												locAddSlasher = false
												break
											end
										end
									end
								end
							end
							
							if locAddSlasher then
								adultFBag.takeObject({
									position = adultFBag.getPosition() + Vector(0,6,0),
									rotation = {0,0,0},
									callback_function = function(o)
										for color, playerRoomGUID in pairs (locPlayerTiles) do
											if playerRoomGUID == landingZone.getGUID() then
												checkSecureRoom(landingZone, o, color)
												break
											end
										end
										o.setLock(true)
										o.setPositionSmooth(findSpaceOnTile(landingZone, nil, true, o), false, true)
									end,
								})
								
							end
							
							Wait.time(function() proceedToNextPhase2 = true end, 1)
							
						
						elseif tag == 'eventMainSlasherRobot' then
							locTagFound = true
							
							if robot.getGMNotes() == 'active' then
								local locRobotRoom = nil
								local locRobotRoomGUID = ''
								local locRobotPos = robot.getPosition()
								local locRobotWithPlayer = false
								rolldice('purple', math.random(1,6))
								
								broadcastToAll('로봇이 가장 가까운 캐릭터를 추격하고 있습니다!', lifeformColor)
								
								local locHealthMsg = '로봇이 체력을 ' .. purpleOneroll .. ' 만큼 깎습니다. 대상: 플레이어 '
								
								if getTaggedObjAtPos('malfunction', robotDeckPos, 3, {2,9,2}) == nil then
									placeMalfunction(robotDeckPos)
								end
								
								for _, roomTile in pairs (locRooms) do
									if distanceMath(roomTile.getPosition(), locRobotPos) < returnRoomDiameter(roomTile) * 0.7 then
										locRobotRoom = roomTile
										locRobotRoomGUID = roomTile.getGUID()
										break
									end
								end
								
								local locAttackedColor = ''
								for color, playerRoomGUID in pairs (locPlayerTiles) do
									if playerRoomGUID == locRobotRoomGUID then
										locRobotWithPlayer = true
										for i = 1, purpleOneroll do
											loseHealth(color)
										end
										broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
									end
								end
								
								
								
								if locRobotWithPlayer then
									--intruderAttack(locRobotRoom, robot, locAttackedColor)
									Wait.time(function() proceedToNextPhase2 = true end, 1)
								else
									autoMoveToGoal({locRobotRoom}, {{robot}}, {}, locDoors, locNoises)
									playsounds(163)
									
									Wait.time(function()
										locRobotPos = robot.getPosition()
										for _, roomTile in pairs (locRooms) do
											if distanceMath(roomTile.getPosition(), locRobotPos) < returnRoomDiameter(roomTile) * 0.7 then
												locRobotRoom = roomTile
												locRobotRoomGUID = roomTile.getGUID()
												break
											end
										end
										
										for color, playerRoomGUID in pairs (locPlayerTiles) do
											if playerRoomGUID == locRobotRoomGUID then
												locRobotWithPlayer = true
												for i = 1, purpleOneroll do
													loseHealth(color)
												end
												broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
											end
										end
										
										if locRobotWithPlayer then
											--intruderAttack(locRobotRoom, robot, locAttackedColor)
											Wait.time(function() proceedToNextPhase2 = true end, 1)
										else
											autoMoveToGoal({locRobotRoom}, {{robot}}, {}, locDoors, locNoises)
											Wait.time(function()
												locRobotPos = robot.getPosition()
												for _, roomTile in pairs (locRooms) do
													if distanceMath(roomTile.getPosition(), locRobotPos) < returnRoomDiameter(roomTile) * 0.7 then
														locRobotRoom = roomTile
														locRobotRoomGUID = roomTile.getGUID()
														break
													end
												end
												
												for color, playerRoomGUID in pairs (locPlayerTiles) do
													if playerRoomGUID == locRobotRoomGUID then
														locRobotWithPlayer = true
														for i = 1, purpleOneroll do
															loseHealth(color)
														end
														broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
													end
												end
												-- if locRobotWithPlayer then
													-- intruderAttack(locRobotRoom, robot, locAttackedColor)
												-- end
												Wait.time(function() proceedToNextPhase2 = true end, 1)
											end, 1) 
										end
									end, 1) 
								end
							else
								broadcastToAll(robotSkipMsg, lifeformColor)
								Wait.time(function() proceedToNextPhase2 = true end, 1)
							end
						end	
					end
					
					if not locTagFound then
						broadcastToAll('이벤트 태그를 찾을 수 없습니다. 이벤트의 주요 효과를 수동으로 해결하세요.', lifeformColor)
						proceedToNextPhase = false
						createNextPhaseButton()
						proceedToNextPhase2 = true
					end
				else
					proceedToNextPhase2 = true
				end
				
				Wait.time(function()
					---DEBUG---
					-- if not proceedToNextPhase then
						-- print('not proceedToNextPhase BAAAD!!!')
					-- end
					
					-- if not proceedToNextPhase2 then
						-- print('not proceedToNextPhase2 BAAAAD !!!')
					-- end
					
					-- if xyrianPause then
						-- print('xyrianPause BAAAD!!')
					-- end
					
					-- if choiceState != 2 then
						-- print('choiceState is not 2 BAAAD!!!')
					-- end
					
					-- if not encounterSeqEnd then
						-- print('encounterSeqEnd is FALSE BAD !!!')
					-- end
					---
					
					Wait.condition(function()
						--secondary effect
						eventCard.setLock(false)
						if locPassSecondary then
							locPlayerTiles = getPlayerRoomsInFirstTurnOrder() --redo in case players died during main event phase.
							
							for _, tag in pairs(eventCard.getTags()) do --Oh my god.
							
								if tag == 'eventSecond3GhoulsReplaceSpecter' then
								
									for _, corridor in pairs (locCorridors) do
										local locCorPos = corridor.getPosition()
										local locGhoulCount = 0
										for _, intruder in pairs (locIntruders) do
											if intruder != nil then
												local locIntrPos = intruder.getPosition()
												if distanceMath(locIntrPos, locCorPos) < corridorImportedSize.x *0.5 then
													if intruder.getGMNotes() == 'adult' then
														locGhoulCount = locGhoulCount + 1
														
														if locGhoulCount == 3 then
															if breederFBag.getQuantity() > 0 then
																enemyFigReturn(intruder)
																breederFBag.takeObject({
																	position = locIntrPos,
																	rotation = {0,0,0},
																	callback_function = function(o) o.setLock(true) end,
																})
																break
															end
														end
													end
												end
											end
										end
									end
								
								elseif tag == 'eventSecondCharEnc' then
									-- local locWait2 = 0
									-- for color, playerRoomGUID in pairs (locPlayerTiles) do
										-- local w = locWait2
										-- locWait2 = locWait2 + 1.25
										-- Wait.time(function ()
											-- encounter(gO(playerRoomGUID), color)
										-- end, w)
									-- end
									
									local locEncParams = {}
									for color, playerRoomGUID in pairs (locPlayerTiles) do
										table.insert(locEncParams, {gO(playerRoomGUID), color})
									end
									
									encounterSequence(locEncParams)
									
								elseif tag == 'eventSecondCharAddShadowNoSecurity' then
									local locWait2 = 0
									
									for color, playerRoomGUID in pairs (locPlayerTiles) do
										local locPlayerTile = gO(playerRoomGUID)
										if not locPlayerTile.hasTag('security') then
											local locSecureFound = false
											
											for _, secureTokenGUID in pairs(locSecuresGUID) do
												local locSecureToken = gO(secureTokenGUID)
												if locSecureToken != nil then
													if distanceMath(locSecureToken.getPosition(), locPlayerTile.getPosition()) < tileImportedSize.x then
														locSecureFound = true
														break
													end
												end
											end
											
											if not locSecureFound then
												for _, corridorGUID in pairs (RoomsMap[playerRoomGUID][2]) do
													local locCor = gO(corridorGUID)
												
													local w = locWait2
													locWait2 = locWait2 + 0.25
													Wait.time(function()
														local locCorCrowd = getTaggedObjAtPos('healthCount', locCor.getPosition(), 0, locCor.getBounds().size *Vector(0.99,1,0.57) + Vector(0,9,0), locCor.getRotation(), true)
														
														local locCorCrowdSize = 0
														
														for _, intruder in pairs (locCorCrowd) do
															if distanceMath(intruder.getPosition(), locCor.getPosition()) < corridorImportedSize.x * 0.5 then
																if intruder.getGMNotes() == 'queen' then
																	locCorCrowdSize = locCorCrowdSize + 4
																else
																	locCorCrowdSize = locCorCrowdSize + 1
																end
															end
														end
														
														if locCorCrowdSize < 6 then
															local locShadows = {}
															for _, entry in pairs (locCorCrowd) do
																if entry.getName() == 'Noise' then
																	table.insert(locShadows, entry)
																	if #locShadows == 3 then
																		break
																	end
																end
															end
															
															if #locShadows == 3 then
																if breederFBag.getQuantity() > 0 then
																	for _, shadowMarker in pairs (locShadows) do
																		shadowMarker.setPosition({50,0,0})
																		shadowMarker.destruct()
																	end
																	
																	breederFBag.takeObject({
																		position = findSpaceOnTile(locCor, nil, true),
																		rotation = {0,0,0},
																		callback_function = function(o) o.setLock(true) end,
																	})
																	
																end
															else
																noiseBag.takeObject({
																	position = findSpaceOnTile(locCor, nil, true),
																	rotation = {0,0,0},
																	smooth = false,
																})
															end
														end
													end, w)
												end
											end
										end
									end
									
								
								elseif tag == 'eventSecondCharEncNoSecurity' then
								
									local locEncParams = {}
									
									for color, playerRoomGUID in pairs (locPlayerTiles) do
										local locPlayerTile = gO(playerRoomGUID)
										if not locPlayerTile.hasTag('security') then
											local locSecureFound = false
											
											for _, secureTokenGUID in pairs(locSecuresGUID) do
												local locSecureToken = gO(secureTokenGUID)
												if locSecureToken != nil then
													if distanceMath(locSecureToken.getPosition(), locPlayerTile.getPosition()) < tileImportedSize.x then
														locSecureFound = true
														break
													end
												end
											end
											
											if not locSecureFound then
												table.insert(locEncParams, {locPlayerTile, color})
											end
										end
									end
									
									encounterSequence(locEncParams)
									
								elseif tag == 'eventSecondCharInfectionNoSecurity' then
								
									for color, playerRoomGUID in pairs (locPlayerTiles) do
										local locPlayerTile = gO(playerRoomGUID)
										if not locPlayerTile.hasTag('security') then
											local locSecureFound = false
											
											for _, secureTokenGUID in pairs(locSecuresGUID) do
												local locSecureToken = gO(secureTokenGUID)
												if locSecureToken != nil then
													if distanceMath(locSecureToken.getPosition(), locPlayerTile.getPosition()) < tileImportedSize.x then
														locSecureFound = true
														break
													end
												end
											end
											
											if not locSecureFound then
												addContamination(color)
											end
										end
									end
								
								elseif tag == 'eventSecondCharNoiseRoll' then
									
									local w = 0
									for color, playerRoomGUID in pairs(locPlayerTiles) do
										Wait.time(function()
											autoNoise({0,0,0}, gO(playerInfoTable[color].figureGUID), false)
										end, w)
										w = w + 0.25
									end
								
								
								elseif tag == 'eventSecondMoveNearFood' then
								
									local locWait2 = 0
									local locGoals = {}
									local locMoveCors = {}
									local locMoveCorIntruders = {}
									local locMoveRooms = {}
									local locMoveRoomIntruders = {}
									
									if nestBag.getQuantity() > 0 then
										for _, roomTile in pairs (locRooms) do
											if roomTile.getName() == 'NEST' then
												table.insert(locGoals, roomTile.getGUID())
											end
										end
									end
									
									for _, roomTile in pairs (locRooms) do
										local locFoodCount = 0
										local locRoomPos = roomTile.getPosition()
										
										for _, food in pairs (locFoods) do
											if distanceMath(food.getPosition(), locRoomPos) < tileImportedSize.x*0.7 then
												if food.hasTag('intruder') then
													locFoodCount = locFoodCount + 1
												else
													locFoodCount = 2
												end
												
												if locFoodCount == 2 then --this should fix lone metagorger waiting in the same room to eat itself but cannot.
													table.insert(locGoals, roomTile.getGUID())
													break
												end
											end
										end
									end
									
									for _, corridorTile in pairs (locCorridors) do
										local locCorPos = corridorTile.getPosition()
										local locCorGroup = #locMoveCorIntruders + 1
										locMoveCorIntruders[locCorGroup] = {}
										
										for _, intruder in pairs(locIntruders) do
											if distanceMath(intruder.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
												table.insert(locMoveCorIntruders[locCorGroup], intruder)
												locWait2 = locWait2 + 0.25
											end
										end
										
										if #locMoveCorIntruders[locCorGroup] == 0 then
											locMoveCorIntruders[locCorGroup] = nil
										else
											table.insert(locMoveCors, corridorTile)
										end
									end
									
									for _, roomTile in pairs (locRooms) do
										
										local locGoalRoom = false
										local locGUID = roomTile.getGUID()
										
										for _, goalRoomGUID in pairs (locGoals) do
											if goalRoomGUID == locGUID then
												locGoalRoom = true
												break
											end
										end
										
										if not locGoalRoom then
											local locRoomPos = roomTile.getPosition()
											local locRoomGroup = #locMoveRoomIntruders + 1
											locMoveRoomIntruders[locRoomGroup] = {}
											
											for _, intruder in pairs(locIntruders) do
												if distanceMath(intruder.getPosition(), locRoomPos) < returnRoomDiameter(roomTile)*0.5 then
													table.insert(locMoveRoomIntruders[locRoomGroup], intruder)
												end
											end
											
											if #locMoveRoomIntruders[locRoomGroup] == 0 then
												locMoveRoomIntruders[locRoomGroup] = nil
											else
												table.insert(locMoveRooms, roomTile)
											end
										end
									end
									
									if #locMoveCors > 0 then
										autoMoveToGoal(locMoveCors, locMoveCorIntruders, locIntruders, locDoors, locNoises, locGoals)
									end
									
									if #locMoveRooms > 0 then
										Wait.time(function()
											autoMoveToGoal(locMoveRooms, locMoveRoomIntruders, locIntruders, locDoors, locNoises, locGoals)
										end, locWait2 +1)
									end
								
								elseif tag == 'eventSecondShuffleDeck' or tag == 'eventSecondShuffleDeckOnly' then
                                    
                                    for _, obj in pairs(getAllObjects()) do
                                        --if obj != nil then
                                            local locRotZ = obj.getRotation().z
                                            if obj.getGMNotes() == 'eventDiscard' and (locRotZ > 350 or locRotZ < 10) then
                                                if eventDeck == nil then
                                                    eventDeck = obj
                                                else
                                                    local newDeck = eventDeck.putObject(obj)
                                                    if newDeck ~= nil then
                                                        eventDeck = newDeck
                                                    end
                                                end
                                                break
                                            end
                                        --end
                                    end
                                    
                                    if eventCard.getPosition().z > eventDeck.getPosition().z then
                                        local newDeck = eventDeck.putObject(eventCard)
                                        if newDeck ~= nil then
                                            eventDeck = newDeck
                                        end
                                    end
									
									
									eventDeck.setPosition({20,1.6,3})
									eventDeck.setRotation({0,180,180})
									Wait.time(function() eventDeck.shuffle() end, 1)
									

								elseif tag == 'eventSecondShuffleEvent' then
									
									
									if eventDeck == nil then
										for _, obj in pairs(getAllObjects()) do
											local locRotZ = obj.getRotation().z
											if obj.getGMNotes() == 'eventDiscard' and (locRotZ > 350 or locRotZ < 10) then
												eventDeck = obj
												break
											end
										end
									end
									
									eventDeck.putObject(eventCard)
									
									eventDeck.setPosition({20,1.6,3})
									eventDeck.setRotation({0,180,180})
									Wait.time(function() eventDeck.shuffle() end, 1)
									
								elseif tag == 'eventSecondUnexpAdult' then
								
									local locWait2 = 0
									
									for _, corridor in pairs(locCorridors) do
										local locCorPos = corridor.getPosition()
										if #RoomsMap[corridor.getGUID()][2] == 1 and (RoomsMap[corridor.getGUID()][2][1] != hiddenRoom.getGUID() or hibUnexplored == nil) then
											local locSpaceAvailable = 6
											for _, intruder in pairs (locIntruders) do
												if intruder != nil then
													if distanceMath(intruder.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
														
														
														if intruder.getGMNotes() == 'queen' then
															locSpaceAvailable = locSpaceAvailable-4
														else
															locSpaceAvailable = locSpaceAvailable-1
														end
														
														if locSpaceAvailable <= 0 then
															break
														end
													end
												end
											end
											
											if lifeforms == 'Sangrevores' and locSpaceAvailable > 0 then
												for _, noiseToken in pairs (locNoises) do
													if noiseToken != nil then
														if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x *0.5 then
															locSpaceAvailable = locSpaceAvailable-1
															if locSpaceAvailable <= 0 then
																break
															end
														end
													end
												end
											end
											
											if locSpaceAvailable > 0 then
												local w = locWait2
												locWait2 = locWait2 + 0.25
												Wait.time(function()
													if adultFBag.getQuantity() > 0 then
														adultFBag.takeObject({
															position = findSpaceOnTile(corridor, nil, true),
															callback_function = function(o)
																o.setLock(true)
																if o.hasTag('rot180') then
																	o.setRotation({0,(corridor.getRotation().y+90),0})
																else
																	o.setRotation({0,0,0})
																end
															end,
														})
													end
												end, w)
											end
										end
									end
								
								elseif tag == 'eventSecondUnexpEncNoise' then
								
									local locWait2 = 0
									local locEncParams = {}
									
									for _, corridor in pairs(locCorridors) do
									
										if #RoomsMap[corridor.getGUID()][2] == 1 then
											for n = 1, #locNoises do
												local noiseToken = locNoises[n]
												if noiseToken != nil then --maybe removed ?
													if distanceMath(noiseToken.getPosition(), corridor.getPosition()) < corridorImportedSize.x *0.5 then
														noiseToken.destruct()
														table.remove(locNoises, n)
														table.insert(locEncParams, {corridor, nil})
														break
													end
												end
											end
										end
									end
									
									encounterSequence(locEncParams)
								
								elseif tag == 'eventSecondUnexpNoise' then
								
									for _, corridor in pairs(locCorridors) do
										local locRot = corridor.getRotation()
										
										--if not (locRot.z > 150 and locRot.z < 210) or lifeforms == 'Sangrevores' then --Technically not needed ?
										
											local locCorGUID = corridor.getGUID()
											local locHidGUID = hiddenRoom.getGUID()
											if #RoomsMap[locCorGUID][2] == 1
											and ((RoomsMap[locCorGUID][2][1] == locHidGUID and hibUnexplored == nil) or RoomsMap[locCorGUID][2][1] != locHidGUID)
											then
												
												local locNoiseFound = false
												local locIntruderFound = false
												
												local locCorPos = corridor.getPosition()
												local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locRot.y)
												
												for _, noiseToken in pairs (locNoises) do
													if noiseToken != nil then
														if distanceMath(noiseToken.getPosition(), corridor.getPosition()) < corridorImportedSize.x *0.5 then
															locNoiseFound = true
															break
														end
													end
												end
												
												if not locNoiseFound then
													for _, intruder in pairs (locIntruders) do
														if intruder != nil then
															local locIntrPos = intruder.getPosition()
															
															if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
															and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6
															then
																locIntruderFound = true
																break
															end
														end
													end
												
													if not locIntruderFound then
														noiseBag.takeObject({
															position = corridor.getPosition() + Vector(0,1,0),
															smooth = false,
														})
													end
												end
											end
											
										-- end 
									end
								end
							end
						end
					end, function() return proceedToNextPhase and proceedToNextPhase2 and choiceState == 2 and encounterSeqEnd and not xyrianPause end, 9999, function() end)
				end, 1)

			end, function() return proceedToNextPhase and proceedToNextPhase2 end, 9999, function() end)

		end, locWait+1.5)
		
		
	end
end

function autoMoveToGoal(startMoveTiles, moveFigureGroups, intrudersList, doorsList, noisesList, goals, doorsDestroyedList)
	if not scriptEnabled then
		return true
	end
	
	local locFirstName = moveFigureGroups[1][1].getName()
	local locHostileInsider = locFirstName == 'insiderFig' and moveFigureGroups[1][1].hasTag('healthCount')
	
	local locInsiderStory = nil
	if insiderEnable then
		if insiderStoryGUID != '' and locFirstName == 'insiderFig' then
			locInsiderStory = gO(insiderStoryGUID)
		end
	end
	
	local locDoorsDestroyed = {}
	
	if doorsDestroyedList != nil then
		for _, obj in pairs (doorsDestroyedList) do
			table.insert(locDoorsDestroyed, obj)
		end
	end
	
	local locWait = 0
	local checkRooms = false
	if startMoveTiles[1].hasTag('room') then
		checkRooms = true
		--print('checkRooms = true')
	end
	
	local locIntruders = {}
	
	local locSearchCompletes = {0,{}}
	
	if checkRooms then
		if intrudersList != nil then
			locIntruders = intrudersList
			--print('locIntruders = intrudersList')
		else
			locSearchCompletes[2]['intruder'] = 0
			locSearchCompletes[1] = locSearchCompletes[1] +1
			--locIntruders = getTaggedObjAtPos('intruder', boarderTile.getPosition(), 0, boarderTile.getBounds().size, {0,0,0}, true)
		end
	end
	
	local locDoors = {}
	
	if doorsList != nil then
		locDoors = doorsList
	else
		locSearchCompletes[2]['door'] = 2
		locSearchCompletes[1] = locSearchCompletes[1] +1
		
		--locDoors = getTaggedObjAtPos('door', boarderTile.getPosition(), 2, boarderTile.getBounds().size, {0,0,0}, true)
	end
	
	local locDoorsRemove = {}
	
	local locNoises = {}
	if noisesList != nil then
		locNoises = noisesList
	else
		locSearchCompletes[2]['Noise'] = 1
		locSearchCompletes[1] = locSearchCompletes[1] +1
		--locNoises = getTaggedObjAtPos('Noise', boarderTile.getPosition(), 1, boarderTile.getBounds().size, {0,0,0}, true)
	end
	
	if locSearchCompletes[1] > 0 then
		for _, obj in pairs (getAllObjects()) do
		
			if locSearchCompletes[2]['intruder'] != nil then
				if obj.hasTag('intruder') then
					table.insert(locIntruders, obj)
				end
			end
			
			if locSearchCompletes[2]['Noise'] != nil then
				if obj.getName() == 'Noise' then
					table.insert(locNoises, obj)
				end
			end
			
			if locSearchCompletes[2]['door'] != nil then
				if obj.getDescription() == 'door' then
					table.insert(locDoors, obj)
				end
			end
		end
	end
	

	
	local locPlayerRooms = getPlayerRoomsInFirstTurnOrder()
	local locGoals = {}
	local locSeekPlayer = true
	local seekRoom = true
	
	if goals == nil then
		locGoals = locPlayerRooms
	elseif goals == 'twitchlingUnexplored' then
		seekRoom = false
		locSeekPlayer = false
	else
		local locFirstChecked = false
		locSeekPlayer = false
		
		for color, entry in pairs (goals) do
			table.insert(locGoals, entry)
			
			if not locFirstChecked then
				locFirstChecked = true
				seekRoom = gO(entry).hasTag('room')
			end
		end
		
	end
	
	if moveFigureGroups[1][1].getGMNotes() == 'xyrian' then
	
		for i = 1, #moveFigureGroups do
			local locGroup = moveFigureGroups[i]
			
			for _, xyrianObj in pairs (locGroup) do
				if xyrianObj.getName() == 'injured' then
					
					local locInjuries = {}
					locInjuries = getTaggedObjAtPos('xyrianInjury', startMoveTiles[i].getPosition(), 3, tileImportedSize, {0,0,0}, true)
					
					if #locInjuries > 0 then
						for _, xyrInj in pairs (locInjuries) do
							table.insert(moveFigureGroups[i], xyrInj)
						end
					end
					break
				end
			end
		end
	end
	
	local figureIsIntruder = moveFigureGroups[1][1].hasTag('intruder')
	local avoidDoor = moveFigureGroups[1][1] == robot

	
	local goalCorridors = {}
	local maxGoalCorridors = {}
	
	if seekRoom then
		for color, seekedTileGUID in pairs (locGoals) do
			if goalCorridors[seekedTileGUID] == nil then
				goalCorridors[seekedTileGUID] = {0,{}}
				
				maxGoalCorridors[seekedTileGUID] = 0
				for _, mapCorridorGUID in pairs(RoomsMap[seekedTileGUID][2]) do
					if #RoomsMap[mapCorridorGUID][2] == 2 then
						maxGoalCorridors[seekedTileGUID] = maxGoalCorridors[seekedTileGUID] + 1
					end
				end
				--print('maxGoalCor ' .. seekedTileGUID .. ' = ' .. maxGoalCorridors[seekedTileGUID])
			end
		end
	end
	
	
	
	for i = 1, #startMoveTiles do
		
		local locShortestPaths = {0,{}} 
		local locStartMoveTileGUID = ''
		local locStartMoveTile = nil
		
		if startMoveTiles[i].getGUID() == nil then
			locStartMoveTileGUID = startMoveTiles[i]
			locStartMoveTile = gO(locStartMoveTileGUID)
			--print('startMoveTiles i is not an object, it is most likely a GUID')
		else
			locStartMoveTile = startMoveTiles[i]
			locStartMoveTileGUID = locStartMoveTile.getGUID()
			--print('startMoveTiles i is an object.')
			--print('locStartMoveTileGUID = ' .. locStartMoveTileGUID)
		end
		
		local locPaths = {}
		local connectedCorridors = {}
		local connectedRooms = {}
		local nextLoopCorridors = {locStartMoveTileGUID}
		if checkRooms then
			nextLoopCorridors = RoomsMap[locStartMoveTileGUID][2]
			
			-- locPaths[locStartMoveTileGUID] = {}
			-- for _, corridorGUID in pairs (nextLoopCorridors) do
				-- locPaths[locStartMoveTileGUID][corridorGUID] = 1
				-- locPaths[corridorGUID] = {}
				-- locPaths[corridorGUID][locStartMoveTileGUID] = 1
			-- end
		end
		
		
		local blockedCorridors = {}
		

		for k = 1, 23 do
			local loopBreak = false
			
			local locTmpNext = {}
			local locSeekedTileGUID = ''
			
			for _, corridorGUID in pairs(nextLoopCorridors) do
				local locColorFound = ''
				
				

				if not seekRoom then
					if goals != 'twitchlingUnexplored' then
						for color, seekedTileGUID in pairs (locGoals) do
							if seekedTileGUID == corridorGUID then
								loopBreak = true
								locAddNext = false
								locColorFound = color
								locSeekedTileGUID = seekedTileGUID
								
								local parentSeekedTileGUID = ''
								if k == 1 then
									parentSeekedTileGUID = startMoveTiles[i].getGUID()
								else
									for _, tileGUID in pairs (RoomsMap[seekedTileGUID][2]) do
										if locPaths[tileGUID] != nil then
											parentSeekedTileGUID = tileGUID
											break
										end
									end
								end
								
								if goalCorridors[parentSeekedTileGUID] == nil then
									goalCorridors[parentSeekedTileGUID] = {0,{}}
									maxGoalCorridors[parentSeekedTileGUID] = 0
									for _, mapCorridorGUID in pairs(RoomsMap[parentSeekedTileGUID][2]) do
										if #RoomsMap[mapCorridorGUID][2] == 2 then
											maxGoalCorridors[parentSeekedTileGUID] = maxGoalCorridors[parentSeekedTileGUID] + 1
										end
									end
									
								end
								break
							end
							if loopBreak then
								break
							end
						end
					elseif #RoomsMap[corridorGUID][2] == 1 then
						loopBreak = true
						locAddNext = false
						locColorFound = 'Red'
						locSeekedTileGUID = corridorGUID
						local locParentTileGUID = RoomsMap[corridorGUID][2][1]
						
						if goalCorridors[locParentTileGUID] == nil then
								
							goalCorridors[locParentTileGUID] = {0,{}}
							maxGoalCorridors[locParentTileGUID] = 0
							for _, mapCorridorGUID in pairs(RoomsMap[locParentTileGUID][2]) do
								if #RoomsMap[mapCorridorGUID][2] == 2 then
									maxGoalCorridors[locParentTileGUID] = maxGoalCorridors[locParentTileGUID] + 1
								end
							end

						end
						if locGoals['Red'] == nil then
							locGoals['Red'] = {}
						end
						table.insert(locGoals['Red'], locSeekedTileGUID)
					end
				end
				
				connectedRooms = RoomsMap[corridorGUID][2]
				for _, roomGUID in pairs(connectedRooms) do
					local locAddNext = true
					local locPass = true
					local locSeekedTileGUID2 = ''
					
					if seekRoom then
						locColorFound = ''
						-- if avoidDoor then
							-- local locCor = gO(corridorGUID)
							-- local locCorAvoidPos = locCor.getPosition()
							-- for _, door in pairs (locDoors) do
								-- if door != nil then
									-- if distanceMath(door.getPosition(), locCorAvoidPos) < corridorImportedSize.x *0.5
									-- and math.abs(dotMath(normalizeMath(door.getPosition() - locCorAvoidPos), rotateVectorAboutY({1,0,0}, locCor.getRotation().y))) > 0.925
									-- then
										-- blockedCorridors[corridorGUID] = 1
										-- break
									-- end
								-- end
							-- end
						-- end
						
						for color, seekedTileGUID in pairs (locGoals) do
							if seekedTileGUID == roomGUID then
								loopBreak = true
								locAddNext = false
								locColorFound = color
								locSeekedTileGUID = roomGUID
								locSeekedTileGUID2 = roomGUID
								break
							end
						end
					end
					
					local uniqueWay = true
					if locPaths[roomGUID] != nil and locSeekedTileGUID2 == '' then
						for pathCorridorGUID, kLoop in pairs(locPaths[roomGUID]) do
							if kLoop < k then
								uniqueWay = false
								break
							end
						end
					end
					
					if uniqueWay then
						if locPaths[corridorGUID] == nil  then
							locPaths[corridorGUID] = {}
							
							locPaths[corridorGUID][roomGUID] = k
							
							-- if blockedCorridors[corridorGUID] != nil then
								-- locPaths[corridorGUID][roomGUID] = 99
							-- end
							
						elseif not checkRooms and locStartMoveTileGUID == corridorGUID and k == 1 then
							locPaths[corridorGUID][roomGUID] = k
							
						else
							if locPaths[corridorGUID][roomGUID] != nil then
								if locPaths[corridorGUID][roomGUID] != k then
									locPass = false
								end
							end
						end
					else
						locPass = false
					end

					if locPass or (locColorFound != '' and goals == 'twitchlingUnexplored') then
						
						if locPaths[roomGUID] == nil then
							locPaths[roomGUID] = {}
						end
						
						if locPass then
							if locPaths[roomGUID][corridorGUID] == nil then
								locPaths[roomGUID][corridorGUID] = k
								
								-- if blockedCorridors[corridorGUID] != nil then
									-- locPaths[roomGUID][corridorGUID] = 99
								-- end
							end
						end
						
						if locColorFound != '' then
							if locShortestPaths[2][locColorFound] == nil then
								locShortestPaths[2][locColorFound] = {}
								locShortestPaths[1] = locShortestPaths[1]+1
							end
							
							local finalPath = {locSeekedTileGUID}
							
							local locOffset = 0
							if goals == 'twitchlingUnexplored' and k != 1 then
								table.insert(finalPath, 1, roomGUID) --Oh boy....
								locSeekedTileGUID = roomGUID
								locOffset = 1
							end
							
							local locRoomGUID = ''
							
							if k == 1 and checkRooms and not seekRoom then
								locRoomGUID = startMoveTiles[i].getGUID()
							else
								locRoomGUID = roomGUID
							end
							
							if maxGoalCorridors[locRoomGUID] == goalCorridors[locRoomGUID][1] then
								goalCorridors[locRoomGUID] = {0, {}}
							end
							
							if k != 1 or seekRoom == checkRooms then
								local locK = k-locOffset
								for a = 1, locK do
									local invK = locK-a+1
									local lastGUID = finalPath[1]
									

									
									if RoomsMap[finalPath[1]][1] == 'room' then
									
										local corCount = 0
										local lastCorridor = ''
										for finalPathCorridorGUID, kLoop in pairs(locPaths[lastGUID]) do
											corCount = corCount + 1
											if kLoop == invK and lastGUID == finalPath[1] then
												lastCorridor = finalPathCorridorGUID
												if goalCorridors[locRoomGUID][2][lastCorridor] == nil then
													table.insert(finalPath, 1, lastCorridor)
												end
											end
										end
										
										if lastGUID == locSeekedTileGUID and lastGUID == finalPath[1] then
											goalCorridors[locRoomGUID] = {0, {}}
											table.insert(finalPath, 1, lastCorridor)
										end
										
										if corCount > 1 and finalPath[1] != lastGUID then
											if lastGUID != locSeekedTileGUID then
												locPaths[lastGUID][finalPath[1]] = nil
											end
										end
										
										if lastGUID == locSeekedTileGUID then
											goalCorridors[locRoomGUID][2][finalPath[1]] = 0
											goalCorridors[locRoomGUID][1] = goalCorridors[locRoomGUID][1] + 1
										end
										
										for _, finalPathRoomGUID in pairs (RoomsMap[finalPath[1]][2]) do
											if finalPath[2] != finalPathRoomGUID then
												table.insert(finalPath, 1, finalPathRoomGUID)
												break
											end
										end
										
									else
										if seekRoom then
											table.remove(finalPath, 1)
											break
										end
									end
								end
							end

							if goals == 'twitchlingUnexplored' and #finalPath == 2 and checkRooms then
								table.remove(finalPath, 1) --Oh boy....
							end
							
							
							--debug
							-- for _, finalPathGuid in pairs(finalPath) do
								-- print('finalPathGuid = ' .. finalPathGuid)
							-- end
							--debug
							
							-- if avoidDoor then
								-- local locBlockTileGUID = ''
								-- local locBlockID = 0
								-- for j = 1, #finalPath do
									-- if blockedCorridors[finalPath[#finalPath-j+1]] != nil then
										-- locBlockID = j
										-- loopBreak = false
										-- locAddNext = false
										
										-- break
									-- end
								-- end
								
								-- if locBlockID != 0 then
									-- for j = 1, 25-locBlockID do
										
										
										-- if blockedCorridors[finalPath[j]] != nil and j != 1 and locBlockTileGUID == '' then
											-- locBlockTileGUID = finalPath[j-1]
										-- end
										
										-- if locBlockTileGUID != '' then
											-- finalPath[j] = locBlockTileGUID
										-- end
									-- end
								-- end
							-- end
							
							
							--print('locColorFound final path = ' .. locColorFound)
							table.insert(locShortestPaths[2][locColorFound], finalPath)
							
							--debug
							-- for _, finalPathGuid in pairs(finalPath) do
								-- print('finalPathGuid = ' .. finalPathGuid)
							-- end
							--debug
							
							locColorFound = ''
							
						end
						--else
						if locAddNext then
							connectedCorridors = RoomsMap[roomGUID][2]
							
							for _, nextCorridorGUID in pairs(connectedCorridors) do
								table.insert(locTmpNext, nextCorridorGUID)
							end
						end
					end
				end
			end	
			if loopBreak then
				break
			else
				nextLoopCorridors = locTmpNext
			end
		end
		
		if locShortestPaths[1] > 0 then
			local locValidPaths = {}
			local locMinPathLength = 0
			
			--debug
			-- for color, goalTileGUID in pairs(locGoals) do
				-- if locShortestPaths[2][color] != nil then
					-- for _, path in pairs(locShortestPaths[2][color]) do
						-- for _, GUID in pairs(path) do
							-- print('color path GUID = ' .. color .. ' ' .. GUID)
						-- end
					-- end
				-- end
			-- end
			--debug
			
			
			for color, goalTileGUID in pairs(locGoals) do --sorting shortest on sorted first color order.
				if locShortestPaths[2][color] != nil then
					locValidPaths[color] = {}
					for _, path in pairs(locShortestPaths[2][color]) do
						if locMinPathLength == 0 then
							locMinPathLength = #path
						end
						
						if locMinPathLength > #path then 
							locValidPaths = {}
							locMinPathLength = #path
							
							locValidPaths[color] = {}
						end
						table.insert(locValidPaths[color], path)
					end
				end
			end
			
			local locCheckMinIndex = 3
			
			if checkRooms then
				locCheckMinIndex = 2
			end
			
			-- if checkRooms then --sorting  ID numbers among the shortest.
				locShortestPaths = {}
				for color, colorTable in pairs(locValidPaths) do
					if locShortestPaths[color] == nil then
						locShortestPaths[color] = {}
					end
					
					if #colorTable > 1 then
					
						for _, path in pairs(colorTable) do
							local locID = math.min(#path,locCheckMinIndex)
							local pathMin = {999, {}}
							local locIndexRemove = 0
							--we removed the corridor check, assuming this works for RoomIDs too...seems t work.
							
							local locGMNotes1 = gO(path[locID]).getGMNotes()
							if locGMNotes1 != '' then
								pathMin[1] = tonumber(locGMNotes1)
								pathMin[2] = path
								
								-- print('#colorTable = ' .. #colorTable)
								-- print('#locShortestPaths[color]+1 = ' .. #locShortestPaths[color]+1)
								
								for j = (#locShortestPaths[color]+1), #colorTable do
									local path2 = colorTable[j]
									local locObj2 = gO(path2[locID])
									if locObj2 != nil then
										local locGMNotes2 = locObj2.getGMNotes()
										if locGMNotes2 != '' then
											local locGMNumber = tonumber(locGMNotes2)
											if locGMNumber < pathMin[1] then
												pathMin[1] = locGMNumber
												pathMin[2] = path2
												locIndexRemove = j
												
												-- print('locGMNumber = ' .. locGMNumber)
												
											end
										end
									end
								end
								
								-- print('added pathMin 2 with ID = ' .. pathMin[1])
								
								if colorTable[locIndexRemove] != nil then
									table.remove(colorTable, locIndexRemove)
									table.insert(colorTable,1,{})
								end
							end
							table.insert(locShortestPaths[color], pathMin[2])
							
						end
					else
						locShortestPaths[color] = colorTable
						
						-- print('override locShortestPaths')
					end
				end
			-- else
				-- locShortestPaths = locValidPaths
			-- end
			
			

			
			if goals == 'twitchlingUnexplored' then
				locGoals = {}
			end
			
			if goals != nil then
				if locFirstName == 'insiderFig' and #goals > 1 then --nil is player rooms by default
				
					--When targeting the queen, it's easy. One room. When targeting players, it's easy, priority to first player room.
					--Here we need corridor GMNotes for each path because no intruder has the priority like players did.
					
					local locMinNum = 999
					local locMinNumPath = {}
					
					for color, colorTable in pairs (locShortestPaths) do
						for _, path in pairs (colorTable) do
							local locNum = tonumber(gO(path[2]).getGMNotes())
							if locNum < locMinNum then
								locMinNum = math.min(locMinNum, locNum)
								
								locMinNumPath = {}
								for _, tileGUID in pairs (path) do
									table.insert(locMinNumPath, tileGUID)
								end
							end
						end
					end
					
					locShortestPaths = {}
					locShortestPaths[1] = {}
					locShortestPaths[1][1] = {}
					
					for _, tileGUID in pairs (locMinNumPath) do
						table.insert(locShortestPaths[1][1], tileGUID)
					end
					
				end
			end
			
			local locBiggest = 0
			local locBiggestIntruders = {}
			
			if checkRooms and figureIsIntruder and goals != 'twitchlingUnexplored' then
				for intruderType, intruderWeight in pairs(intruderSizeOrder[lifeforms]) do
					for _, intruderMove in pairs (moveFigureGroups[i]) do
						if intruderMove.getGMNotes() == intruderType then
							table.insert(locBiggestIntruders, intruderMove)
						end
					end
				end
			else
				locBiggestIntruders = moveFigureGroups[i]
			end
			
			loopBreak = false
			local intruderCorridorCount = {}
			local locCorSizeTbl = {}
			
			
			for color, colorTable in pairs(locShortestPaths) do
				if loopBreak then
					break
				end
				for _, path in pairs(colorTable) do
					--debug
					-- for _, guid in pairs(path) do
						-- print('path guid = ' .. guid)
					-- end
					--debug
					local locTile = nil
					local locTileGUID = ''
					if #locBiggestIntruders > 0 then
						local locIntrSize = #locBiggestIntruders
						local locWalked = false
						
						if #path == 1 then
							locTileGUID = path[1]
							locTile = gO(path[1])
						else
							local locID = 3
							if checkRooms or (not checkRooms and RoomsMap[path[locID]][1] == 'corridor') then
								locID = 2
							end
							locTileGUID = path[locID]
							locTile = gO(locTileGUID)
							
							--print ('locTileGUID = ' .. locTileGUID)
							
						end
						
						
						if #path == 1 and goals == 'twitchlingUnexplored' and not checkRooms then
							for j=1, locIntrSize do
								local intruderMove = locBiggestIntruders[locIntrSize-j+1]
								local w = locWait
								locWait = locWait + 0.25
								
								Wait.time(function() 
									intruderMove.setPosition(intruderMove.getPosition() + Vector(0,12,0))
									if not locWalked then
										locWalked = true
										walksounds(intruderMove)
									end
									enemyFigReturn(intruderMove)
								end, w)
							end
							loopBreak = true
							break
						else
							local locDoor = nil
							
							if figureIsIntruder or locHostileInsider then
								local locDoorSize = #locDoors
								for j = 1, locDoorSize do
									if locDoors[locDoorSize-j+1] != nil then
										local door = locDoors[locDoorSize-j+1]
										if door != nil then
											if (distanceMath(door.getPosition(), locStartMoveTile.getPosition()) < returnRoomDiameter(locStartMoveTile)*0.7
											and dotMath(normalizeMath(door.getPosition()-locStartMoveTile.getPosition()), normalizeMath(locTile.getPosition()-locStartMoveTile.getPosition())) > 0.9)
											then
												locDoor = gO(door.getGUID())
												table.insert(locDoorsRemove, door.getGUID())
												table.remove(locDoors, locDoorSize-j+1)
												
												break
											end
										end
									end
								end
								
								if #locDoorsRemove == 0 and locHostileInsider then
									for j = 1, locDoorSize do
										if locDoors[locDoorSize-j+1] != nil then
											local door = locDoors[locDoorSize-j+1]
											if door != nil then
												if (distanceMath(door.getPosition(), locStartMoveTile.getPosition()) < (returnRoomDiameter(locStartMoveTile)*0.7 + corridorImportedSize.x)
												and dotMath(normalizeMath(door.getPosition()-locStartMoveTile.getPosition()), normalizeMath(locTile.getPosition()-locStartMoveTile.getPosition())) > 0.9)
												then
													locDoor = gO(door.getGUID())
													table.insert(locDoorsRemove, door.getGUID())
													table.remove(locDoors, locDoorSize-j+1)
													break
												end
											end
										end
									end
								end
							elseif avoidDoor then
								local locDoorSize = #locDoors
								for j = 1, locDoorSize do
									if locDoors[locDoorSize-j+1] != nil then
										local door = locDoors[locDoorSize-j+1]
										if door != nil then
											if (distanceMath(door.getPosition(), locTile.getPosition()) < corridorImportedSize.x*0.5)
											then
												locDoor = gO(door.getGUID())											
												break
											end
										end
									end
								end
							end
							
							if locDoor == nil then

								if checkRooms then
									if figureIsIntruder then
										local locCorPos = locTile.getPosition()
										
										local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locTile.getRotation().y)
										
										local locIntruderNumber = 6
										
										if locCorSizeTbl[locTileGUID] == nil then
											for _, intruderCor in pairs(locIntruders) do
												if intruderCor != nil then
													local locIntrPos = intruderCor.getPosition()
													
													
													if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x *0.5
													and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6
													then
														local locWeight = 1
														if intruderCor.getGMNotes() == 'queen' then
															locWeight = 4
														end
														locIntruderNumber = math.max(0,locIntruderNumber - locWeight)
														
														if locIntruderNumber == 0 then
															break
														end
													end
												end
											end
											
											if lifeforms == 'Sangrevores' and locIntruderNumber > 0 then
												for _, shadowMarker in pairs(locNoises) do
													local locShadowPos = shadowMarker.getPosition()
													
													if distanceMath(locShadowPos, locCorPos) <= corridorImportedSize.x *0.5 then

														locIntruderNumber = math.max(0,locIntruderNumber - 1)
														
														if locIntruderNumber == 0 then
															break
														end
													end
													
												end
											end
										else
											locIntruderNumber = locCorSizeTbl[locTileGUID]
										end
										
										
										if locIntruderNumber > 0  and #locBiggestIntruders > 0 then
										
											local offset = 1
											local weight = 1
											

											
											if locIntruderNumber-4 < 0 and locBiggestIntruders[1].getGMNotes() == 'queen' then
												offset = 2
											end
											
											if lifeforms != 'Sangrevores' then
												local locNoiseSize = #locNoises
												for j = 1, locNoiseSize do
													if locNoises[locNoiseSize-j+1] != nil then
														local noise = locNoises[locNoiseSize-j+1]
														if distanceMath(noise.getPosition(), locTile.getPosition()) < corridorImportedSize.x*0.5 then
															noise.destruct()
															table.remove(locNoises,locNoiseSize-j+1)
															break
														end
													end
												end
											end
											
											local locDegreeToTile = 180
											
											if locBiggestIntruders[1].hasTag('rot180') then
												local locDirToTile = locCorPos-locBiggestIntruders[1].getPosition()
												locDegreeToTile = 90+180+180*math.atan2(locDirToTile[3],locDirToTile[1]*(-1))/3.1415926352
											end
											
											for j = 1, locIntruderNumber do
												if locBiggestIntruders[offset] != nil then
													local locBigIntruder = locBiggestIntruders[offset]
													if locBigIntruder.getGMNotes() == 'queen' then
														weight = 4
													else
														weight = 1
													end
													if locIntruderNumber - weight >= 0  and not locBigIntruder.hasTag('trapped') then
														
														local w = locWait
														locWait = locWait + 0.25
														Wait.time(function()
															
															locBigIntruder.setPositionSmooth(findSpaceOnTile(locTile,nil,true),false,true)
															locBigIntruder.setRotation({0,0,0})

															if locBigIntruder.hasTag('rot180') then
																locBigIntruder.setRotation({0,locDegreeToTile,0})
															end
															
															if not locWalked then
																locWalked = true
																walksounds(locBigIntruder)
															end
															
															if locBigIntruder.getGMNotes() != 'queen' then
																locBigIntruder.setVar("count", 0)
																locBigIntruder.call("updateDisplay")															
															end
														end, w)
														table.remove(locBiggestIntruders, offset)
														locIntruderNumber = math.max(0,locIntruderNumber - weight)
													end
												end
											end
											
											locCorSizeTbl[locTileGUID] = locIntruderNumber
										end
									else
										
										local locMinPath = math.min(3, #path)
										locTileGUID = path[locMinPath]
										locTile = gO(locTileGUID)
										
										local locXyrianTargets = {}
										
										if locMinPath == 3 then
											local locXyrianCor = gO(path[2])
											local locXyrianCorPos = locXyrianCor.getPosition()
											local locXyrianCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, locXyrianCor.getRotation().y)
											
											local locIron = ironcladBuffCheck()
											
											if locBiggestIntruders[1].getGMNotes() == 'xyrian' then
												
												
												
												for _, intruder in pairs (locIntruders) do
													if intruder != nil then
													
														local locIntrPos = intruder.getPosition()
															
														if distanceMath(locIntrPos, locXyrianCorPos) < corridorImportedSize.x*0.5
														and	math.abs(dotMath(locIntrPos-locXyrianCorPos, locXyrianCorZVector)) <= corridorImportedSize.z *0.6
														then
															
															
															if #locXyrianTargets == 0 then
																table.insert(locXyrianTargets, intruder)
															elseif intruder.getGMNotes() == 'ironclad' and locIron then
																table.insert(locXyrianTargets, 1, intruder)
															else 
																local locXyrBigTarget = false
																
																for j = 1, #locXyrianTargets do
																	local target = locXyrianTargets[#locXyrianTargets-j+1]
																	if intruderSizeOrder[lifeforms][intruder.getGMNotes()] >= intruderSizeOrder[lifeforms][target.getGMNotes()] then
																		table.insert(locXyrianTargets, #locXyrianTargets-j+1, intruder)
																		locXyrBigTarget = true
																		break
																	end
																end
																
																if not locXyrBigTarget then
																	table.insert(locXyrianTargets, intruder)
																end
															end
														end
													end
												end
											elseif locBiggestIntruders[1].getName() == 'insiderFig' then
												if locInsiderStory != nil then
													if locInsiderStory.hasTag('insiderEffectRoundInsiderRunToLander')
													and not locBiggestIntruders[1].hasTag('trapped')
													then
														for _, SnapP in pairs(locXyrianCor.getSnapPoints()) do
															if SnapP.tags[1] == 'doorSlot' then
																local SnapPos = SnapP.position
																local locScale = locXyrianCor.getScale()
																
																local SnapPosWorld = rotateVectorAboutY(SnapPos*locScale, locXyrianCor.getRotation().y) + locXyrianCor.getPosition()
																
																local locDoor2Found = false
																
																for _, door in pairs (locDoors) do
																	if distanceMath(door.getPosition(), SnapPosWorld) < corridorImportedSize.x*0.25 then
																		locDoor2Found = true
																	end
																end
																
																if not locDoor2Found then
																	
																	for _, doorBroken in pairs (locDoorsDestroyed) do
																		if doorBroken != nil then
																			if distanceMath(doorBroken.getPosition(), SnapPosWorld) < corridorImportedSize.x*0.25 then
																				locDoor2Found = true
																				--doorBroken.setState(1) --Could be quite fun but reading the manual it sounds like Insider is not supposed to closed Destroyed doors.
																				break
																			end
																		end
																	end
																	
																	if doorBag.getQuantity() > 0 and not locDoor2Found then
																		doorBag.takeObject({
																			position = SnapPosWorld + Vector(0,1,0),
																			rotation = {0, locXyrianCor.getRotation().y + 90, 0},
																			callback_function = function(o)
																				o.setLock(true)
																				o.setPositionSmooth(SnapPosWorld, false, false)
																			end,
																			smooth = false,
																		})
																	end
																end
															end
														end
													end
												end
											end
										end
										
										for j = 1, #locBiggestIntruders do
											local nonIntruder = locBiggestIntruders[j]
											
											if not nonIntruder.hasTag('trapped') then
												local w = locWait
												locWait = locWait + 0.25
												Wait.time(function()
												
													nonIntruder.setPositionSmooth(findSpaceOnTile(locTile,nil,true, nonIntruder),false,true)
													if not locWalked then
														locWalked = true
														walksounds(nonIntruder)
													end
													if nonIntruder.getGMNotes() != 'xyrianInjury' then
														nonIntruder.setRotation({0,0,0})
														
														for t = 1, #locXyrianTargets do
															local locTarget = locXyrianTargets[t]
															if locTarget != nil then
																if not locTarget.hasTag('returning') then
																	
																	critOnIntruder(locTarget, nil, 'xyrian')
																
																	break
																end
															end
														end
													end

												end, w)
											end
										end
										loopBreak = true
										break
									end
								else
									if #path == 1 and locSeekPlayer then
										local locBiggest = 0
										local locBiggestIntruder = nil
										for _, intruder in pairs (locBiggestIntruders) do
											local locGM = intruder.getGMNotes()
											if intruderSizeOrder[lifeforms][locGM] > locBiggest then
												locBiggest = intruderSizeOrder[lifeforms][locGM]
												locBiggestIntruder = intruder
											end
										end
										
										if locBiggestIntruder != nil then
											local w = locWait
											locWait = locWait + 0.25
											
											Wait.time(function() 
												locBiggestIntruder.setPositionSmooth(findSpaceOnTile(locTile,nil,true, locBiggestIntruder),false,true)
												locBiggestIntruder.setRotation({0,0,0})
												
												if locBiggestIntruder.hasTag('rot180') then
													locBiggestIntruder.setRotation({0,180,0})
												end
												
												if not locWalked then
													locWalked = true
													walksounds(locBiggestIntruder)
												end
												
												if figureIsIntruder then
													for color, playerRoomGUID in pairs(locPlayerRooms) do
														if playerRoomGUID == locTileGUID then
															checkSecureRoom(locTile, locBiggestIntruder, color)
															break
														end
													end
													if locBiggestIntruder.getGMNotes() != 'queen' then
														locBiggestIntruder.setVar("count", 0)
														locBiggestIntruder.call("updateDisplay")				
													end
													
												end

											end, w)
										end
										loopBreak = true
										break 
									else
										
										if trapCheck then
											local locBiggest = 0
											local locBiggestIntruder = nil
											
											for _, intruder in pairs (locBiggestIntruders) do
												local locGM = intruder.getGMNotes()
												if intruderSizeOrder[lifeforms][locGM] > locBiggest then
													locBiggest = intruderSizeOrder[lifeforms][locGM]
													locBiggestIntruder = intruder
												end
											end
										
											for _, trap in pairs (trapsList) do
												if trap != nil then
													if distanceMath(trap.getPosition(), locTile.getPosition()) < returnRoomDiameter(locTile) then
														if trap.getRotation().z < 20 or trap.getRotation().z > 340 then
														
															trap.flip()	
															locBiggestIntruder.call("onClick")
															locBiggestIntruder.addTag('trapped')
															
															local w = locWait + 0.5
															
															Wait.time(function()
																trap.setLock(true)
																trap.setPosition(locBiggestIntruder.getPosition())
																trap.setScale({0.8,1,0.8})
															end, w)
															break
														end
													end
												end
											end
										end
										
										for j = 1, locIntrSize do
											local intruder = locBiggestIntruders[locIntrSize-j+1]

											
											local w = locWait
											locWait = locWait + 0.25
											
											Wait.time(function() 
												intruder.setPositionSmooth(findSpaceOnTile(locTile,nil,true, intruder),false,true)
												intruder.setRotation({0,0,0})
												
												if intruder.hasTag('rot180') then
													intruder.setRotation({0,180,0})
												end
												
												if locIntrSize == 1 then
													walksounds(intruder)
												end
												
												if figureIsIntruder then
													for color, playerRoomGUID in pairs(locPlayerRooms) do
														if playerRoomGUID == locTileGUID then
															checkSecureRoom(locTile, intruder, color)
															break
														end
													end
													if intruder.getGMNotes() != 'queen' then
														intruder.setVar("count", 0)
														intruder.call("updateDisplay")														
													end
												end
												

												--print('moving intruder')
											end, w)
											table.remove(locBiggestIntruders, locIntrSize-j+1)
										end	
									end
								end
							else
								loopBreak = true
								break
							end
						end
					else
						loopBreak = true
						break
					end
				end
			end
		end
	end
	
	Wait.time(function()
		for j=1, #locDoorsRemove do
			local doorGUID = locDoorsRemove[j]
			Wait.time(function()
				gO(doorGUID).setState(2)
			end, j*0.1)
		end
	end, locWait+0.1)
end

function checkSecureRoom(tile, intruder, attackedPlayerColor)
	if not scriptEnabled then
		return true
	end
	
	local locScale = 1
	if tile == hiddenRoom then
		locScale = 1.37
	end
	
	local locTilePos = tile.getPosition()
	
	if attackedPlayerColor != nil then
		if not tile.hasTag('security') then
			local locSecure = getTaggedObjAtPos('secure', locTilePos, 3, (tileImportedSize*locScale + Vector(0,1,0)))
			
			
			if locSecure != nil then
				locSecureFound = true
				secureTokenRemove(locSecure)
				broadcastToAll(secureRemove,lifeformColor)
			else
				broadcastToAll(secureWarning,lifeformColor)
				intruderAttack(tile, intruder, attackedPlayerColor)
			end
		end
		
		if insiderEnable and insiderStoryGUID != '' then
			local locStoryCard = gO(insiderStoryGUID)
			if locStoryCard != nil then
				for _, tag in pairs (locStoryCard.getTags()) do
					if string.find(tag, 'insiderEffectIntruderEnter') != nil then
						autoInsider(2, tag, tile, nil, nil, nil, intruder)
					end
				end
			end
		end
	end
end

function containTag(customTag, tagsList)
	if not scriptEnabled then
		return true
	end
	
	for _, tag in pairs (tagsList) do
		if tag == customTag then
			return true
		end
	end
	
	return false
end

attackButtonCount = 0
uniqueID = 1
allPassed = false

function checkAllPassed()
	if not scriptEnabled then
		return true
	end
	
	local locHelpFound = false
	for color, entry in pairs(playerInfoTable) do
		if Player[color].seated or (not automaticSeat and playerInfoTable[color].manualSeat) then
			if isPlayerAlive(color) then
				local locBoard2 = gO(entry.boardGUID)
				local locObj = getTaggedObjAtPos('playerHelp', locBoard2.getPosition(), 0, locBoard2.getBounds().size)
				
				if locObj != nil then
					if locObj.getRotation().z > 350 or locObj.getRotation().z < 10 then
						locHelpFound = true
						break
					end
				end
			end
		end
	end
	
	if not locHelpFound then
		allPassed = true
	end
end

function intruderAttack(tile, intruder, attackedPlayerColor, tag)
	if not scriptEnabled or attackedPlayerColor == nil then
		return true
	end

	local locScale = tile.getScale()
	local locButtons = tile.getButtons()
	local locButtonCount = 0
	local locButtonLastPos = Vector(0,4/locScale.y,0)
	local locButtonOffset = Vector(0,0,0)
	if locButtons != nil then
		
		
		locButtonCount = #tile.getButtons()
		
		if locButtonCount > 1 then
			locButtonLastPos = locButtons[locButtonCount].position
			locButtonOffset = Vector(0,0.2/locScale.y,-0.5/locScale.z)
		end
		
		-- for i = 2, #locButtons do
			-- tile.editButton({index = i - 1, position = locButtons[i].position + locButtonOffset })
		-- end
		
		
	end
	local locIntruderName = intruder.getGMNotes()
	
	if not (lifeforms == 'Neoflesh' and locIntruderName == 'breeder') then --Cultist never attacks.
		if locIntruderName == 'breeder' and lifeforms == 'Primebloods' then
			locIntruderName = '드론'
		elseif lifeforms == 'Sangrevores' then
			if locIntruderName == 'adult' then
				locIntruderName = '구울'
			elseif locIntruderName == 'breeder' then
				locIntruderName = '스펙터'
			elseif locIntruderName == 'queen' then
				locIntruderName = '킹'
			end
		elseif lifeforms == 'Carnomorph' then
			if locIntruderName == 'creeper' then
				locIntruderName = '메타고저'
			elseif locIntruderName == 'adult' then
				locIntruderName = '섐블러'
			elseif locIntruderName == 'breeder' then
				locIntruderName = '플래쉬비스트'
			elseif locIntruderName == 'queen' then
				locIntruderName = '슬래셔'
			end
		end
		
		if intruder == robot then
			locIntruderName = '슬래셔 로봇'
		end
	
	
		locIntruderName = string.upper(locIntruderName)
		
		local t = {0,0,0}
		
		if attackedPlayerColor != 'insider' then
			t = playerInfoTable[attackedPlayerColor].tint
		end
		
		tile.createButton({
			click_function = 'drawAttack' .. uniqueID,
			function_owner = Global,
			label          = '공격 ' .. locButtonCount .. ' ' .. locIntruderName,
			position       = locButtonLastPos+locButtonOffset,
			scale          = {1,1,1},
			width          = 700,
			height         = 200,
			font_size      = 100,
			color          = {t[1] * 0.75, t[2] * 0.75 , t[3] * 0.75},
			font_color     = {1,1,1,1},
			tooltip        = '좌클릭하여 공격을 수락합니다. 우클릭하여 공격을 취소합니다.',
		})
		setFontSizeToButton(tile, locButtonCount)
		
		attackButtonCount = attackButtonCount +1
		
		if attackButtonCount == 1 then
			broadcastToAll('침입자 공격 버튼이 플레이어 입력을 기다리고 있습니다.', lifeformColor)
		end
		
		proceedToNextPhase = false
		local func3 = function(obj, pColor, alt_click)
		
			local locPlayerBoard = nil
			if attackedPlayerColor != 'insider' then
				locPlayerBoard = gO(playerInfoTable[attackedPlayerColor].boardGUID)
			else
				locPlayerBoard = insiderCard
			end
			
			local locPlayerBoardPos = locPlayerBoard.getPosition()
			
			if not alt_click then
				if intruder.getGMNotes() == 'larvae' and attackedPlayerColor != 'insider' then
					addContamination(attackedPlayerColor)
					if lifeforms == 'Primebloods' then
						local locPlayerLarvae = getTaggedObjAtPos('larvae', locPlayerBoardPos, 3, locPlayerBoard.getBounds().size)
						
						if locPlayerLarvae != nil then
							enemyFigReturn(locPlayerLarvae)
						end
						intruder.setPositionSmooth(locPlayerBoardPos + Vector(0,1,1.5),false, true)
					end
				elseif intruder.getGMNotes() == 'xyrian' and tag != nil then
				
					local locPlayerShot = false
					local locPlayerShotMsg = 'lost 2 Health !'
					
					if tag == 'xyrianActPlayerHealth' or tag == 'xyrianActPlayerNoiseLarva' then
						locPlayerShot = true
						loseHealth(attackedPlayerColor)
						loseHealth(attackedPlayerColor)
				
					elseif tag == 'xyrianActPlayerStatus' or tag == 'xyrianActOther3Health' or tag == 'xyrianActOther3Serious' then
						
						if attackedPlayerColor != 'insider' then
							if not playerHasTag('xyrianStatus', 3, nil, attackedPlayerColor) and xyrianStatusBag.getQuantity() > 0 then
								xyrianStatusBag.takeObject({
									position = locPlayerBoardPos + Vector(0,1,0),
									rotation = {0,180,0},
								})
								playsounds(math.random(167,178))
								
							elseif tag == 'xyrianActOther3Health' then
								locPlayerShot = true
								loseHealth(attackedPlayerColor)
								loseHealth(attackedPlayerColor)
								
							else
								seriouswoundDeck.deal(1, pColor)
								locPlayerShot = true
								locPlayerShotMsg = 'gain 1 Serious Wound !'
							end	
						else
							locPlayerShot = true
							loseHealth(attackedPlayerColor)
							loseHealth(attackedPlayerColor)
						end
					end
					
					if locPlayerShot then
						local locSound = math.random(125,130)
						playsounds(locSound)
						-- Wait.time(function()
							-- playsounds(math.random(99,101)) --it's fun but annoying after a while...?
						-- end, soundDuration[locSound+1] *0.7)
						broadcastToAll('플레이어 ' .. attackedPlayerColor .. '가 자이리안에게 사격당했습니다, ' .. locPlayerShotMsg, xyrianColor)
					end
				
				elseif lifeforms == 'Carnomorph' and intruder.getGMNotes() == 'creeper' then
					
					
					enemyFigReturn(intruder)
					onObjectNumberTyped(adultBag, 'Red', 1)
					broadcastToAll('샴블러 토큰이 침입자 주머니에 추가됩니다.', lifeformColor)
					
					if attackedPlayerColor != 'insider' then
						addContamination(attackedPlayerColor)
						
						if mutationDeck != nil then
							if mutationDeck.getQuantity() > 0 then
								if not playerHasTag('mutation', 3, nil, attackedPlayerColor) then
									mutationDeck.deal(2,pColor)
									playsounds(139)
								end
							end
						end
					else
						loseHealth(attackedPlayerColor)
					end
						
				else
					attacksDeck.deal(1, pColor)
					playsounds(math.random(1,3))
				end
			end
			
			attackButtonCount = math.max(0,attackButtonCount - 1)
			
			if attackButtonCount == 0 and allPassed and autoEventEnable then
				createNextPhaseButton()
			elseif attackButtonCount == 0 then
				proceedToNextPhase = true
			end
			
			tile.removeButton(1)
			
			local locButtons2 = tile.getButtons()
			
			for i = 2, #locButtons2 do
				if locButtons2[i] != nil then
					tile.editButton({index = i - 1, position = locButtons2[i].position - locButtonOffset })
				end
			end
		end
		_G['drawAttack' .. uniqueID] = func3
		uniqueID = uniqueID + 1
	end
end

function createNextPhaseButton()
	if not scriptEnabled then
		return true
	end
	
	boarderTile.createButton({
		click_function = 'nextPhase',
		function_owner = Global,
		label          = '다음 단계 허용',
		position       = {0, 4, 0},
		scale          = {1,1,1},
		width          = 1400,
		height         = 200,
		font_size      = 100,
		color          = lifeformColor,
		font_color     = {1,1,1,1},
		tooltip        = '',
	})
end

function nextPhase()
	if not scriptEnabled then
		return true
	end
	
	proceedToNextPhase = true
	local locButtons = boarderTile.getButtons()
	
	for i = 1, 10 do
		if locButtons[i].label == '다음 단계 허용' then
			boarderTile.removeButton(i-1)
			break
		end
	end
	
end

function returnRoomDiameter(room)
	if not scriptEnabled then
		return true
	end
	
	if room == hiddenRoom then
		return tileImportedSize.x * 1.37
	end
	return tileImportedSize.x
end

function critOnIntruder(intruder, tile, shooterType)
	if not scriptEnabled then
		return true
	end
	
	local locShooterName = '자이리안' --most of this function is for xyrian so... ye.
	
	if shooterType == 'xyrian' then
		playsounds(math.random(125,130))
	elseif shooterType == 'insider' then
		playsounds(math.random(90,91))
		locShooterName = '내부자'
	elseif shooterType == 'explosion' then
		locShooterName = '로봇 폭발'
	end
	
	playsounds(math.random(20,22))
	
	local isRoom = false
	if tile != nil then
		isRoom = tile.hasTag('room')
	end
	
	local locGM = intruder.getGMNotes()
	local locPos = intruder.getPosition()
	
	if locGM == 'queen' then
		local locReset = 0
		

		local locName = '여왕'
		if lifeforms == 'Neoflesh' then
			locName = '마더브레인'
			locReset = 0-2*(3-queenBag.getQuantity())
		elseif lifeforms == 'Sangrevores' then
			locName = '킹'
		end
		
		intruder.setVar("count", locReset)
		intruder.call("updateDisplay")
		
		broadcastToAll(locShooterName ..'가 '.. locName ..' !', lifeformColor)
		
		if proceedToNextPhase and shooterType != 'insider' then --I had a bug with insider crit on queen once, I had this fake "pause" mostly for events/xyrians here I think it's not necessary for insider.
			proceedToNextPhase = false
			createNextPhaseButton()
		end
		
	elseif locGM == 'ironclad' and isRoom then
		if ironcladBuffCheck() then
			local lowestCor = getLowestCorridorAroundRoom(tile.getGUID(), false)
			
			autoMoveToGoal({tile}, {{intruder}}, nil, nil, nil, {lowestCor.getGUID()})
			intruder.setVar("count", 0)
			intruder.call("updateDisplay")
		else
			enemyFigReturn(intruder)
		end
	
	elseif locGM == 'breeder' then
		if lifeforms == 'Neoflesh' then
			local locBuffs = shapeCast({20,1.7,15.71}, {0.5,9, 18})
			local latestBuffFound = false
			
			for _, GMNotes in pairs ({'cultistBuff', 'twitchlingBuff', 'firespitterBuff', 'ironcladBuff', 'crawlmineBuff', 'slasherBuff'}) do
				if latestBuffFound then
					break
				else
					for _, buff in pairs (locBuffs) do
						local locGM2 = buff.getGMNotes()
						if GMNotes == locGM2 then
							if buff.getRotation().z < 5 or buff.getRotation().z > 355 then
								latestBuffFound = true
								buff.setRotation({0,180,180})
								broadcastToAll(locShooterName .. '가 최신 네오플레시 스킬을 비활성화했습니다.', xyrianColor)
							end
							break
						end
					end
				end
			end
		
		elseif lifeforms == 'Carnomorph' then
			
			if adultFBag.getQuantity() > 0 then
				adultFBag.takeObject({
					position = adultFBag.getPosition() + Vector(0,6,0),
					callback_function = function (o)
						o.setLock(true)
						o.setRotation({0,math.random(0,360),0})
						
						if tile != nil then
							o.setPositionSmooth(findSpaceOnTile(tile,nil, true, o), false, true)
						else
							o.setPositionSmooth(locPos, false, true)
						end
					end,
				})
			end
			
			if isRoom then
				carcassBag.takeObject({
					position = locPos,
				})
			end
			
		end
		enemyFigReturn(intruder)
	else
		
		if lifeforms == 'Carnomorph' then
			if isRoom then
				carcassBag.takeObject({
					position = locPos,
				})
			end
		end
		
		enemyFigReturn(intruder)
	end
end

proceedToTracerReplace = false
xyrianActivationRound = false
xyrianPause = false

function xyrianActivationSeq(xyrianCard, allegianceActivated)
	if not scriptEnabled then
		return true
	end
	
	if attackButtonCount == 0 then
		proceedToNextPhase = true
	end
	
	
	-- if not allPassed then --I am going to trust the players to handle things correctly.
		-- checkAllPassed()
	-- end
	
	xyrianActivationRound = allPassed
	
	if proceedToNextPhase then
		
		if insiderEnable then
			insiderRecall()
		end
		
		local locReshuffle = false
		
		if previousXyrianCard != nil then
			
			if previousXyrianCard.hasTag('xyrianActOther3Reshuffle') then
				locReshuffle = true
				xyrianCard.drop()
				xyrianCard.setPosition({32,5,7})
				for _, card in pairs({previousXyrianCard, xyrianCard}) do
					xyrianActivationDeck.putObject(card)
				end
			else
				sendToBottomDeck(previousXyrianCard, xyrianActivationDeck)
			end
		end
		
		
		local locRooms = {}
		local locCorridors = {}
		local locIntruders = {}
		local locXyrians = {}
		local locOtherXyrians = {}
		local locWoundedXyrians = {}
		local locSecuresGUID = {}
		local locNoises = {}
		local locFires = {}
		local locMalfunctions = {}
		local locNestRoom = nil
		local locTechnicalRoom = nil
		local locXyrianRoomsCompleted = {}
		
		local locQueenFig = gO(queenFigGUID)
		local locQueenTile = nil
		
		if not locReshuffle then
			for _, obj in pairs (getAllObjects()) do
			
				for _, tag in pairs (obj.getTags()) do
					
					if tag == 'Corridors' then
						table.insert(locCorridors, obj)
						break
					elseif tag == 'room' then
						table.insert(locRooms, obj)
						if obj.getName() == 'NEST' then
							locNestRoom = obj
						elseif obj.getName() == 'TECHNICAL CORRIDOR ENTRANCE' then
							locTechnicalRoom = obj
						end
						break
					elseif tag == 'intruder' then
						table.insert(locIntruders, obj)
						break
					end
				end
				
				local locGM = obj.getGMNotes()
				
				if locGM == 'xyrian' then
					table.insert(locXyrians, obj)
					if obj.getName() == 'injured' then
						table.insert(locWoundedXyrians, obj)
					end
					
				elseif locGM == 'fire' then
					table.insert(locFires, obj)
					
				elseif locGM == 'malfunction' then
					table.insert(locMalfunctions, obj)
					
				elseif locGM == 'secure' then
					table.insert(locSecuresGUID, obj.getGUID())
				
				elseif obj.getName() == 'Noise' then
					table.insert(locNoises, obj)
				end
			end
			
			registerToRoomsMap(locRooms, locCorridors) 
		
		else
			Wait.time(function()
				previousXyrianCard = nil
				xyrianActivationDeck.shuffle()
				Wait.time(function()
					xyrianActivationDeck.takeObject({
						position = {32,4,7},
						callback_function = function(o) xyrianActivationSeq(o, allegianceActivated) end,
					})
				end,1)
			end, 1)
		end
		
		if #locXyrians > 0 and not locReshuffle then
			xyrianCard.setLock(true)
			xyrianCard.drop()
			xyrianCard.setPosition({32,4,7})
			xyrianCard.setRotation({0,180,0})
			
			--proceedToNextPhase2 = false
			local locNextPhase2 = false
			local locNextPhase3 = false --it's tricky ...
			
			local locOxyCheck = xyrianCard.hasTag('xyrianActPlayerOxygen')
			local locPlayerRooms = getPlayerRoomsInFirstTurnOrder(true)
			local locPlayerRoomsOther = getPlayerRoomsInFirstTurnOrder()
			local locXyrianAllegianceOn = false
			local locAllegianceColor = ''
			
			if xyrianAllegiance.getRotation().z < 10 or xyrianAllegiance.getRotation().z > 350 then
				locAllegianceColor = getNearestPColor(xyrianAllegiance.getPosition().x)
				locXyrianAllegianceOn = true
				
				local locPlayerRooms2 = {}
				
				for color, playerRoomGUID in pairs (locPlayerRooms) do
					if color != locAllegianceColor then
						locPlayerRooms2[color] = playerRoomGUID
					end
				end
				
				locPlayerRoomsOther = locPlayerRooms2
				if allegianceActivated != nil then
					if allegianceActivated then
						locPlayerRooms = locPlayerRooms2
					end
				end
			end
			
			local locWait = 0
			local locBrokenRobot = getTaggedObjAtPos('malfunction', robotDeckPos, 3, {2,9,2}) != nil
			local locDoOnce = false
			local locDoOnce2 = false
			local locColorOnce = {}
			local locRoomOnce = {}
			local locUseSangrevores = lifeforms == 'Sangrevores'
			
			
			for _, xyrian in pairs (locXyrians) do
				if xyrian.getName() == '' then
					local locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
					local locXyrianRoomPos = locXyrianRoom.getPosition()
					local locXyrianRoomGUID = locXyrianRoom.getGUID()
					local locPass = true
					
					local locInPlayerRoom = false
					
					if locOxyCheck then
						locPass = isInOxygenSection(xyrian)
					end
					
					local locDoOnce3 = false
					for color, playerRoomGUID in pairs (locPlayerRooms) do

						if locXyrianRoomGUID == playerRoomGUID then
							locInPlayerRoom = true
							
							if locPass then
								if xyrianCard.hasTag('xyrianActPlayerHealth') or xyrianCard.hasTag('xyrianActPlayerStatus') then
								
									for _, tag in pairs (xyrianCard.getTags()) do
										if tag == 'xyrianActPlayerHealth' or tag == 'xyrianActPlayerStatus' then
											intruderAttack(locXyrianRoom, xyrian, color, tag)
											break
										end
									end
									
									for _, intruder in pairs (locIntruders) do
										if intruder != nil then
											if distanceMath(locXyrianRoomPos, intruder.getPosition()) < tileImportedSize.x*0.7 then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function ()
												if intruder != nil then
													critOnIntruder(intruder, locXyrianRoom, 'xyrian')
												end
											end, w)
											end
										end
									end
									
								elseif xyrianCard.hasTag('xyrianActPlayerNoiseLarva') then
									if locRoomOnce[locXyrianRoomGUID] == nil then
										locRoomOnce[locXyrianRoomGUID] = 1
										
										local w = locWait
										locWait = locWait + 0.35
										
										Wait.time(function()
											for _, corridorGUID in pairs (RoomsMap[locXyrianRoomGUID][2]) do
												local locCor = gO(corridorGUID)
												
													
												local locCorPos = locCor.getPosition()
												local locNoisesFound = {}
												
												for _, noiseToken in pairs (locNoises) do
													if noiseToken != nil then
														if distanceMath(noiseToken.getPosition(), locCorPos) < corridorImportedSize.x*0.5 then
															table.insert(locNoisesFound, noiseToken)
														end
													end
												end
												local locPos = locCorPos + Vector(0,1,0)
												local locRot = {0,180,0}
												

												local locCrowd = 0
												
												if locUseSangrevores then
													locPos = findSpaceOnTile(locCor,nil,true)
													locRot = {0,0,0}
													
													if #locNoisesFound > 0 then
														locCrowd = #locNoisesFound
													end
													
													
													for _, intruder in pairs (locIntruders) do
														if intruder != nil then
															if distanceMath(locCorPos, intruder.getPosition()) < corridorImportedSize.x*0.5 then
																if intruder.getGMNotes() == 'queen' then
																	locCrowd = locCrowd + 4
																else
																	locCrowd = locCrowd + 1
																end
															end
														end
													end
													
													
												end
												
												
												--6 enemies can't add Noise
												--2 Noise + 4 enemies can't add noise
												if #locNoisesFound == 0 or (#locNoisesFound < 3 and locUseSangrevores and locCrowd < 6) then
													noiseBag.takeObject({
														position = locPos,
														rotation = locRot,
														smooth = false,
														callback_function = function(o) table.insert(locNoises, o) end,
													})
												elseif locUseSangrevores and #locNoisesFound == 3 then
												
													for _, noiseToken in pairs (locNoisesFound) do
														noiseToken.destruct()
													end
													
													if breederFBag.getQuantity() > 0 then
														breederFBag.takeObject({
															position = findSpaceOnTile(locCor, nil, true),
															rotation = {0,0,0},
															callback_function = function(o) o.setLock(true) end,
														})
													end
												end
											end
										end, w)
										
										for color, playerRoomGUID in pairs (locPlayerRooms) do  
											if locColorOnce[color] == nil then
												if playerRoomGUID == locXyrianRoomGUID and color != 'insider' then
													local locPlayerBoard = gO(playerInfoTable[color].boardGUID)
													local locLarva = getTaggedObjAtPos('larvae', locPlayerBoard.getPosition(), 3, locPlayerBoard.getBounds().size)
													
													locColorOnce[color] = 0
													if locLarva != nil then
														critOnIntruder(locLarva, nil, 'xyrian')
														intruderAttack(locXyrianRoom, xyrian, color, 'xyrianActPlayerNoiseLarva')
													end
													
												end
											end
										end
									end
									
								
								elseif xyrianCard.hasTag('xyrianActPlayerKidnap') then
								
									local lowestCorridor = getLowestCorridorAroundRoom(locXyrianRoomGUID, false)
									local locNextRoomGUID = nil
									local locKidnapOnce = locDoOnce3
									
									local locDoors = getTaggedObjAtPos('door', lowestCorridor.getPosition(), 2, (corridorImportedSize*Vector(1,1,0.5)) + Vector(0,5,0), lowestCorridor.getRotation(), true)
									
									for _, door in pairs (locDoors) do
										if door != nil then
											door.setState(2)
										end
									end
									
									if locColorOnce[color] == nil then
										locColorOnce[color] = 0
										
										local locChar = nil
										if color != 'insider' then
											locChar = gO(playerInfoTable[color].figureGUID)
										else
											locChar = insiderFig
										end
										
										local w = locWait
										
										
										if #RoomsMap[lowestCorridor.getGUID()][2] == 1 and not locDoOnce3 then
										
											locDoOnce3 = true
											locWait = locWait + 3
											locChar.setPosition(lowestCorridor.getPosition() + Vector(0,1,0))
											
											for _, castObj in pairs (shapeCast({-24,1.55,0})) do
												local locGM = castObj.getGMNotes()
												if locGM == 'explorationDiscard' then
													castObj.takeObject({
														position = castObj.getPosition() + Vector(0,4,4),
														rotation = {0,180,0},
														callback_function = function(o)
															autoExplore(o)
														end,
													})
													break
												elseif locGM == 'exploration' then
													castObj.setPosition(castObj.getPosition() + Vector(0,4,4))
													castObj.setRotation({0,180,0})
													autoExplore(castObj)
													break
												end
											end
											
										else
											locWait = locWait + 1
											Wait.time(function()
												for _, roomGUID in pairs (RoomsMap[lowestCorridor.getGUID()][2]) do
													if roomGUID != locXyrianRoomGUID then
														locNextRoomGUID = roomGUID
														break
													end
												end
												locChar.setPositionSmooth(findSpaceOnTile(gO(locNextRoomGUID)), false,true)
												locChar.setRotation({0,0,0})
												Wait.time(function()
													autoNoise(nil, locChar, false)
												end,1)
											end, w)
										end
									end
									
									if not locKidnapOnce then
										locKidnapOnce = true
										
										local w2 = locWait
										locWait = locWait + 0.3
										Wait.time(function()

											Wait.time(function()
												for _, roomGUID in pairs (RoomsMap[lowestCorridor.getGUID()][2]) do
													if roomGUID != locXyrianRoomGUID then
														locNextRoomGUID = roomGUID
														break
													end
												end
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locNextRoomGUID})
											end, 0.3)
											
										end, w2)
									end
								elseif xyrianCard.hasTag('xyrianActPlayerTechnical') then
									
									if locTechnicalRoom != nil then
										
										
										if locXyrianRoomGUID == playerRoomGUID then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function()
												local locChar = nil
												if color != 'insider' then
													locChar = gO(playerInfoTable[color].figureGUID)
												else
													locChar = insiderFig
												end
												locChar.setPositionSmooth(findSpaceOnTile(locTechnicalRoom), false, true)
											end, w)
										end
										
										if not locDoOnce3 then
											xyrian.setPositionSmooth(findSpaceOnTile(locTechnicalRoom, nil, true, xyrian), false, true)
											locDoOnce3 = true
										end
									end
								end
							end
						end
					end
					if locUseSangrevores then
						locRoomOnce = {}
					end
					
					if not locInPlayerRoom then
						if locXyrianAllegianceOn then
							local locPlayerRooms2 = getPlayerRoomsInFirstTurnOrder()
							locPlayerRoomsOther = {}
							
							for color, playerRoomGUID in pairs (locPlayerRooms2) do
								if color != locAllegianceColor then
									
									locPlayerRoomsOther[color] = playerRoomGUID
								end
							end						
						end
						
						table.insert(locOtherXyrians, xyrian)
						locXyrianRoomPos = locXyrianRoom.getPosition()
						--Phase1
						for _, tag in pairs (xyrianCard.getTags()) do
							if tag == 'xyrianActOther1Break' then
								if locXyrianRoomsCompleted[locXyrianRoomGUID] == nil then
									locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
									
									if locXyrianRoom.getName() != 'NEST' then
										local locMalfunctionFound = false
										for _, malfunctionToken in pairs (locMalfunctions) do
											if distanceMath(malfunctionToken.getPosition(), locXyrianRoomPos) < tileImportedSize.x then
												locMalfunctionFound = true
												break
											end
										end
										
										if not locMalfunctionFound then
											placeMalfunction(locXyrianRoomPos + Vector(0,0,-1,05))
										end
									end
									
									if not locBrokenRobot then
										if distanceMath(robot.getPosition(), locXyrianRoomPos) < tileImportedSize.x then
											placeMalfunction(robotDeckPos)
											locBrokenRobot = true
										end
									end
								end
								
								break
							elseif tag == 'xyrianActOther1Closest' then
								local w = locWait
								locWait = locWait + 0.3
								Wait.time(function()
									autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {},locPlayerRoomsOther)
								end, w)
								
								break
							elseif tag == 'xyrianActOther1Crit' then							
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(), locXyrianRoomPos) < tileImportedSize.x*0.5 then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function ()
												if intruder != nil then
													critOnIntruder(intruder, locXyrianRoom, 'xyrian')
												end
											end, w)
										end
									end
								end
								break
							elseif tag == 'xyrianActOther1Escape' then
								if locXyrianRoomsCompleted[locXyrianRoomGUID] == nil then
									locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
									local locEscapePos = {-16.54, 1.9, 19.89}
									if locXyrianRoom.getName() == 'ESCAPE SHUTTLE' then
									
										local locShuttleAvailable = true
										
										for _, passenger in pairs (shapeCast(locEscapePos)) do
											if passenger.hasTag('characterFig') or passenger.hasTag('healthCount') then
												locShuttleAvailable = false
												break
											end
										end
										
										if locShuttleAvailable then
											local locMalfFound = false
											
											-- for _, malfunctionToken in pairs (locMalfunctions) do
												-- if distanceMath(malfunctionToken.getPosition(), locXyrianRoomPos) < tileImportedSize.x then
													-- locMalfFound = true
													-- break
												-- end
											-- end
											
											if not locMalfFound then
												xyrian.setPositionSmooth(locEscapePos, false,true)
												xyrian.setGMNotes('')
												broadcastToAll('자이리안이 탈출 셔틀로 이륙했습니다.', xyrianColor)
												playsounds(181)
												Wait.time(function() xyrian.setLock(true) end, 1)
												
											end
										end
									end
								end
								
								break
							elseif tag == 'xyrianActOther1Lander' then
								local w = locWait
								locWait = locWait + 0.6
								local locLZGUID = landingZone.getGUID()
								
								Wait.time(function()
									if locXyrianRoomGUID != locLZGUID then
										autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locLZGUID})
									end
									
									Wait.time(function()
										locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
										if locXyrianRoom != nil then
											if locXyrianRoom.getGUID() != locLZGUID then
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locLZGUID})
											end
										end
									end, 0.3)
									
								end, w)
								
								local w2 = locWait
								locWait = locWait + 0.3
								Wait.time(function()
									if shuttleFigure != nil then
										w2 = 0
										if landerCheckWaitTime != 0 then
											w2 = landerCheckWaitTime + 1
										end
										
										Wait.time(function()
											if shuttleFigure != nil then
												
												if distanceMath(xyrian.getPosition(), landingZone.getPosition()) < tileImportedSize.x then
													if math.abs(shuttleFigure.getPosition().x - turnMarker.getPosition().x) < 0.5 then
														

														if math.abs(shuttleFigure.getPosition().z -turnMarker.getPosition().z) < turnOffset.z*1.5 then
															if landerCheckWaitTime == 0 then
																landerCheck()
															else
																Wait.time(function()
																	if shuttleFigure != nil then
																		shuttleFigure.destruct()
																		broadcastToAll('자이리안이 착륙선을 파괴했습니다!', xyrianColor)
																		playsounds(-1)
																		playsounds(math.random(190,192))
																		lightAlert()
																	end
																end, landerCheckWaitTime+2)
															end
														else
															shuttleFigure.setPosition(shuttleFigure.getPosition() + Vector(0,2,turnOffset.z))
														end
													else
														if distanceMath(shuttleFigure.getPosition(), landingZone.getPosition()) < tileImportedSize.x and shuttleFigure.getScale().x > 0.5 then
															shuttleFigure.destruct()
															broadcastToAll('자이리안이 착륙선을 파괴했습니다!', xyrianColor)
															playsounds(-1)
															playsounds(math.random(190,192))
															lightAlert()
														end
													end
												end
											end
										end, w2)
									end
								end, w2)
								
								-- if not locDoOnce2 then
									-- locDoOnce2 = true
									-- Wait.time(function()
										-- xyrianActivationDeck.putObject(xyrianCard)
										-- Wait.time(function()
											-- xyrianActivationDeck.shuffle()
										-- end, 1)
									-- end, w2 +2)
								-- end
								break
								
							elseif tag == 'xyrianActOther1LandingZone' then
								local w = locWait
								locWait = locWait + 0.9
								local locLZGUID = landingZone.getGUID()
								
								Wait.time(function()
									autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locLZGUID})
									
									Wait.time(function()
										locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
										if locXyrianRoom != nil then
											if locXyrianRoom.getGUID() != locLZGUID then
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locLZGUID})
											end
											Wait.time(function() 
												locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
												
												if locXyrianRoomsCompleted[locXyrianRoom.getGUID()] == nil then
													locXyrianRoomsCompleted[locXyrianRoom.getGUID()] = 0
													local locFireFound = false
													locXyrianRoomPos = locXyrianRoom.getPosition()
													for _, fireToken in pairs (locFires) do
														if distanceMath(locXyrianRoomPos, fireToken.getPosition()) < tileImportedSize.x then
															locFireFound = true
															break
														end
													end
													
													if not locFireFound then
														placeFire(locXyrianRoomPos + Vector(0.35,0,-1.3), false)
														locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
													end
													
													if locXyrianRoom == landingZone then
														local locTacticalFound = false
														for _, obj in pairs (getAllObjects()) do
															local locGM = obj.getGMNotes()
															if locGM == 'ammo' or locGM == 'grenade' or locGM == 'medpack' or locGM == 'oxygen' then
																if distanceMath(obj.getPosition(), locXyrianRoomPos) < tileImportedSize.x*2.5 then
																	obj.destruct()
																	locTacticalFound = true
																end
															end
														end
														
														if locTacticalFound then
															broadcastToAll('자이리안이 착륙 구역의 남은 전술 장비를 파괴했습니다!', xyrianColor)
														end
													end
												end
												
											end, 0.3)
										end
									end, 0.3)
								end, w)
								
								
								
								break
							elseif tag == 'xyrianActOther1LifeHiber' then
								if locXyrianRoomsCompleted[locXyrianRoomGUID] == nil then
									locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
									if locXyrianRoom.getName() == 'LIFE SUPPORT CONTROL' then
										local locMalfFound = false
										
										-- for _, malfunctionToken in pairs (locMalfunctions) do
											-- if distanceMath(malfunctionToken.getPosition(), locXyrianRoomPos) < tileImportedSize.x then
												-- locMalfFound = true
												-- break
											-- end
										-- end
										
										if not locMalfFound then
											for _, obj in pairs (getAllObjects()) do
												if obj.hasTag('LifeSupport') or obj.hasTag('LifeSupportOff') then
													local locObjPosX = obj.getPosition().x
													
													if (locObjPosX < -5.5 and locXyrianRoomPos.x < -5.5)
													or
													(locObjPosX > 5.5 and locXyrianRoomPos.x > 5.5)
													or
													(locObjPosX < 5.5 and locObjPosX > -5.5 and locXyrianRoomPos.x < 5.5 and locXyrianRoomPos.x > -5.5)
													then
														if obj.hasTag('LifeSupport') then
															obj.setState(2)
														else
															obj.setState(1)
														end
														broadcastToAll('자이리안이 생명 유지 장치를 전환했습니다.', xyrianColor)
														break
													end
												end
											end
										end
									elseif locXyrianRoom == hiddenRoom then
										
										locXyrianRoomPos = locXyrianRoom.getPosition()
										
										local locHiberToggle = nil
										
										for _, obj in pairs (getAllObjects()) do
											if obj.getGMNotes() == 'hibernatoriumOn' then
												locHiberToggle = obj
												break
											end
										end
										
										if locHiberToggle != nil then
											choiceToPlayer(locXyrianRoomPos + Vector(5,1,-5), 'Did a Character\nHibernate yet?', 85)
											broadcastToAll('동면실 근처의 플레이어들에게 질문이 제시됩니다.',xyrianColor)
										else
											choiceState = 0
										end
										
										Wait.condition(function()
											
											if choiceState == 0 then
												local locMalfFound2 = false
												
												for _, malfunctionToken in pairs (locMalfunctions) do
													if distanceMath(locXyrianRoomPos, malfunctionToken.getPosition()) < tileImportedSize.x then
														locMalfFound2 = true
														break
													end
												end
												
												if not locMalfFound2 then
													placeMalfunction(locXyrianRoomPos+ Vector(0,0,-1.05))
												end
											else
												locHiberToggle.setState(2)
												broadcastToAll('자이리안이 동면실을 껐습니다!', xyrianColor)
											end
											choiceState = 2
										end, function() return choiceState < 2 end, 999999, function() end)
									end
								end
								
								if locXyrianRoom != hiddenRoom then
									local w = locWait
									locWait = locWait + 0.9
									
									
									Wait.time(function()
										autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {hiddenRoom.getGUID()})
										
										Wait.time(function()
											locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
											locXyrianRoomGUID = locXyrianRoom.getGUID()
											
											if locXyrianRoomsCompleted[locXyrianRoomGUID] == nil and locXyrianRoom.getName() != 'NEST' then
												locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
											
												locXyrianRoomPos = locXyrianRoom.getPosition()
												
												local locMalfFound2 = false
												
												for _, malfunctionToken in pairs (locMalfunctions) do
													if distanceMath(locXyrianRoomPos, malfunctionToken.getPosition()) < tileImportedSize.x then
														locMalfFound2 = true
														break
													end
												end
												
												if not locMalfFound2 then
													placeMalfunction(locXyrianRoomPos+ Vector(0,0,-1.05))
												end
											end
											
											if locXyrianRoom != hiddenRoom then
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {hiddenRoom.getGUID()})
											end
											Wait.time(function()
												locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
												locXyrianRoomGUID = locXyrianRoom.getGUID()
												
												if locXyrianRoomsCompleted[locXyrianRoomGUID] == nil and locXyrianRoom.getName() != 'NEST' then
													locXyrianRoomsCompleted[locXyrianRoomGUID] = 0
												
													locXyrianRoomPos = locXyrianRoom.getPosition()
													
													local locMalfFound3 = false
													
													for _, malfunctionToken in pairs (locMalfunctions) do
														if distanceMath(locXyrianRoomPos, malfunctionToken.getPosition()) < tileImportedSize.x then
															locMalfFound3 = true
															break
														end
													end
													
													if not locMalfFound3 then
														placeMalfunction(locXyrianRoomPos+ Vector(0,0,-1.05))
													end
												end
											end, 0.3)
											
										end, 0.3)
									end, w)
								end
								
								break
							elseif tag == 'xyrianActOther1Nest' then
								if locXyrianRoom != locNestRoom and locNestRoom != nil then
									local w = locWait
									locWait = locWait + 1.2
									
									Wait.time(function()
										autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locNestRoom.getGUID()})
										Wait.time(function()
											locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)									
											if locXyrianRoom != locNestRoom then
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locNestRoom.getGUID()})
											end
											Wait.time(function()
												locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)									
												if locXyrianRoom != locNestRoom then
													autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, {locNestRoom.getGUID()})
												end
											end, 0.6)
										end, 0.3)
									end, w)
								end
								
								Wait.time(function()
									locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
									if locXyrianRoom == locNestRoom then
										for i = 1, 2 do
											if nestBag.getQuantity() > 0 then
												nestBag.takeObject({
													position = nestBag.getPosition() + Vector(0,2,2),
												})
											end
										end
									end
								end, locWait + 0.6)
								break
							elseif tag == 'xyrianActOther1Queen' then
								
								
								if locQueenFig != nil then
									local w = locWait
									locWait = locWait + 1.2
									Wait.time(function()
										xyrianHuntQueen({xyrian}, locIntruders)
									end, w)
								else
									local w = locWait
									locWait = locWait + 1.2
									
									Wait.time(function()
										autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, locPlayerRoomsOther)
										
										Wait.time(function()
											local locPlayerRoomFound = false
											
											locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
											locXyrianRoomGUID = locXyrianRoom.getGUID()
											for color, playerRoomGUID in pairs (locPlayerRoomsOther) do
												if playerRoomGUID == locXyrianRoomGUID then
													locPlayerRoomFound = true
													break
												end
											end
											
											if not locPlayerRoomFound then
												autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, locPlayerRoomsOther)
											end
										end, 0.3)
										
									end, w)
								end
								
								Wait.time(function()
									locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
									locXyrianRoomGUID = locXyrianRoom.getGUID()
									for color, playerRoomGUID in pairs (locPlayerRoomsOther) do
										if playerRoomGUID == locXyrianRoomGUID then
											intruderAttack(locXyrianRoom, xyrian, color, 'xyrianActOther3Health')
										end
									end
									
									if insiderEnable then
										if insiderFig != nil then
											if insiderFig.hasTag('characterFig') then
												if distanceMath(insiderFig.getPosition(), locXyrianRoom.getPosition()) < tileImportedSize.x then
													intruderAttack(locXyrianRoom, xyrian, 'insider', 'xyrianActOther3Health')
												end
											end
										end
									end
								end, locWait +1.2)
								break
							end
						end
					end
				end
			end	
			Wait.time(function()
				locDoOnce = false
				locDoOnce2 = false
				locWait = 0
				
				--Phase2

				
				for _, xyrian in pairs (locOtherXyrians) do
				
					if xyrian.getGMNotes() != '' and xyrian.getName() == '' then --in case one took off in the shuttle
						local locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
						local locXyrianRoomGUID = locXyrianRoom.getGUID()
						local locXyrianRoomPos = locXyrianRoom.getPosition()
						
						for _, tag in pairs (xyrianCard.getTags()) do
							if tag == 'xyrianActOther2Closest' then
								local w = locWait
								locWait = locWait + 0.3
								
								Wait.time(function()
									autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, locPlayerRoomsOther)
								end, w)
								break
							elseif tag == 'xyrianActOther2Crit' then
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(), locXyrianRoomPos) < tileImportedSize.x*0.5 then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function ()
												if intruder != nil then
													critOnIntruder(intruder, locXyrianRoom, 'xyrian')
												end
											end, w)
										end
									end
								end
								break
							
						
							
							elseif tag == 'xyrianActOther2Security' then
								local w = locWait
								locWait = locWait
								
								local locCheckTiles = {}
								locXyrianRoomGUID = locXyrianRoom.getGUID()
								table.insert(locCheckTiles, locXyrianRoomGUID)
								
								
								for _, xyrianCorridorGUID in pairs (RoomsMap[locXyrianRoomGUID][2]) do
									for _, otherRoomGUID in pairs (RoomsMap[xyrianCorridorGUID][2]) do
										if otherRoomGUID != locXyrianRoomGUID then
											table.insert(locCheckTiles, otherRoomGUID)
										end
									end
								end
								
								
								for _, secureGUID in pairs (locSecuresGUID) do
									local locSecureToken = gO(secureGUID)
									if locSecureToken != nil then
										local locSecurePos = locSecureToken.getPosition()
										
										
										for _, tileGUID in pairs (locCheckTiles) do
											local locTile = gO(tileGUID)
											if distanceMath(locSecurePos, locTile.getPosition()) < tileImportedSize.x then
												w = locWait
												locWait = locWait + 0.75
												for j = 1, 3 do
													Wait.time(function()
														secureTokenRemove(gO(secureGUID))
													end, j*0.25 + w)
												end
											end
										end
									end
								end
								
								for color, playerRoomGUID in pairs (locPlayerRoomsOther) do
									if playerRoomGUID == locXyrianRoomGUID then
										intruderAttack(locXyrianRoom, xyrian, color, 'xyrianActPlayerHealth')
									end
								end
								
								if insiderEnable then
									if insiderFig != nil then
										if insiderFig.hasTag('characterFig') then
											if distanceMath(insiderFig.getPosition(), locXyrianRoom.getPosition()) < tileImportedSize.x then
												intruderAttack(locXyrianRoom, xyrian, 'insider', 'xyrianActPlayerHealth')
											end
										end
									end
								end
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(), locXyrianRoomPos) < tileImportedSize.x*0.5 then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function ()
												if intruder != nil then
													critOnIntruder(intruder, locXyrianRoom, 'xyrian')
												end
											end, w)
										end
									end
								end
								
								break
							end
						end	
					end
				end
				Wait.time(function()
					locNextPhase2 = true
				end, locWait+1)
			end, locWait+1)
			
			Wait.condition(function()
				--Phase3
				locWait = 0
				
				for _, xyrian in pairs (locOtherXyrians) do
					if xyrian.getGMNotes() != '' and xyrian.getName() == '' then --in case one took off in the shuttle
						local locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
						local locXyrianRoomGUID = locXyrianRoom.getGUID()
						local locXyrianRoomPos = locXyrianRoom.getPosition()
						
						for _, tag in pairs (xyrianCard.getTags()) do
							
							if tag == 'xyrianActOther3Health' then
								for color, playerRoomGUID in pairs (locPlayerRoomsOther) do
									if playerRoomGUID == locXyrianRoomGUID then
										intruderAttack(locXyrianRoom, xyrian, color, tag)
									end
								end
								
								if insiderEnable then
									if insiderFig != nil then
										if insiderFig.hasTag('characterFig') then
											if distanceMath(insiderFig.getPosition(), locXyrianRoom.getPosition()) < tileImportedSize.x then
												intruderAttack(locXyrianRoom, xyrian, 'insider', tag)
											end
										end
									end
								end
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										if distanceMath(intruder.getPosition(), locXyrianRoomPos) < tileImportedSize.x*0.5 then
											local w = locWait
											locWait = locWait + 0.3
											Wait.time(function ()
												if intruder != nil then
													critOnIntruder(intruder, locXyrianRoom, 'xyrian')
												end
											end, w)
										end
									end
								end
								
								break
							elseif tag == 'xyrianActOther3Autodestruction' then
								if locXyrianRoom.getName() == 'COOLING SYSTEM' then
									local locAutoDPos = Vector(turnMarker.getPosition().x, 3, math.max(2.57,turnMarker.getPosition().z- 5*turnOffset.z))
									if autoDestructionToken != nil then
										if autoDestructionToken.getPosition().z > 15 then
											autoDestructionToken.setPosition(locAutoDPos)
											playsounds(-1)
											onObjectDrop('Red', autoDestructionToken)
											broadcastToAll(autoDestructionWarning, lifeformColor)
										end
									end
								end
							end
						end
					end
				end
				
				Wait.time(function()
					locNextPhase3 = true
				end, locWait + 1)
				
			end, function() return locNextPhase2 end, 999999, function() end)
			
			--After End
			Wait.condition(function()
				Wait.time(function()
					locWait = 0
					for _, xyrian in pairs(locWoundedXyrians) do
						local w = locWait
						locWait = locWait + 0.5
						Wait.time(function()
							xyrian.setName('')
							broadcastToAll('자이리안이 부상을 치유했습니다!', xyrianColor)
							playsounds(math.random(167,178))
							
							local locInj = getTaggedObjAtPos('xyrianInjury', xyrian.getPosition(), 3, tileImportedSize*1.260504)
							if locInj != nil then
								if locInj.getRotation().z > 170 and locInj.getRotation().z < 190 then
									locInj.setLock(false)
									xyrianInjuryBag.putObject(locInj)
								end
							end
						end, w)
					end
					
					xyrianCard.setLock(false)
					if proceedToTracerReplace then
						proceedToTracerReplace = false
						xyrianTracerReplace()
					end
					previousXyrianCard = xyrianCard
					prevXyrianCardGUID = xyrianCard.getGUID()
					
					xyrianPause = false
					broadcastToAll('자이리안 활성화 시퀀스가 종료되었습니다.', xyrianColor)
				end, 1)
				
			end, function() return locNextPhase2 and locNextPhase3 end, 999999, function() end)
		end
	else
		broadcastToAll('침입자 공격이 플레이어 입력을 기다리고 있습니다.', xyrianColor)
	end
end

function xyrianHuntQueen(xyrians, intruders, event)
	if not scriptEnabled then
		return true
	end
	
	local locIntruders = {}
	
	if intruders != nil then
		locIntruders = intruders
	else
		for _, obj in pairs (getAllObjects()) do
			if obj.hasTag('intruder') then
				table.insert(locIntruders, obj)
			end
		end
	end
	
	local locEvent = false
	
	if event != nil then
		locEvent = event
	end
	
	local locWait = 0
	local locQueenGoals = {}
	local locQueenFig = gO(queenFigGUID)
	local locQueenTile = nil
	
	if locQueenFig != nil then

		for _, castObj in pairs (shapeCast(locQueenFig.getPosition())) do
			if castObj.hasTag('room') then
				locQueenTile = castObj
				table.insert(locQueenGoals, locQueenTile.getGUID())
				break
			elseif castObj.hasTag('Corridors') then
				locQueenTile = castObj
				for _, queenRoomGUID in pairs (RoomsMap[locQueenTile.getGUID()][2]) do
					table.insert(locQueenGoals, queenRoomGUID)
				end
				break
			end
		end
	end
	
	if #locQueenGoals > 0 then
		for _, xyrian in pairs (xyrians) do
			if xyrian != nil then
				local locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
				local locXyrianRoomGUID = locXyrianRoom.getGUID()
				local locQueenTileFound = false
				
				for _, queenTileGUID in pairs (locQueenGoals) do
				
					if queenTileGUID == locXyrianRoomGUID then
						locQueenTileFound = true
						break
					else
						for _, tileGUID in pairs (RoomsMap[locXyrianRoomGUID][2]) do
							if queenTileGUID == tileGUID then
								locQueenTileFound = true
								break
							end
						end
					end
					
					if locQueenTileFound then
						break
					end
				end
				
				if not locQueenTileFound then
					local w = locWait
					locWait = locWait + 0.6
					Wait.time(function()
						autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, locQueenGoals)
						
						if not locEvent then
							Wait.time(function()
								locXyrianRoom = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
								locXyrianRoomGUID = locXyrianRoom.getGUID()
								
								for _, queenTileGUID in pairs (locQueenGoals) do
								
									if queenTileGUID == locXyrianRoomGUID then
										locQueenTileFound = true
										break
									else
										for _, tileGUID in pairs (RoomsMap[locXyrianRoomGUID][2]) do
											if queenTileGUID == tileGUID then
												locQueenTileFound = true
												break
											end
										end
									end
									
									if locQueenTileFound then
										break
									end
								end
								
								if not locQueenTileFound then
									autoMoveToGoal({locXyrianRoom}, {{xyrian}}, locIntruders, {}, {}, locQueenGoals)
								end
							end, 0.3)
						end
					end, w)
				end
			end
		end
			
			
		Wait.time(function()
			local locWait2 = 0
			for _, xyrian in pairs (xyrians) do
				if xyrian != nil then
					local locXyrianRoom2 = getTaggedObjAtPos('room', xyrian.getPosition(), 0)
					local locXyrianRoom2GUID = locXyrianRoom2.getGUID()
					
					for _, queenTileGUID in pairs (locQueenGoals) do
						if locXyrianRoom2GUID == queenTileGUID then
							local w2 = locWait2
							locWait2 = locWait2 + 0.3
							Wait.time(function()
								critOnIntruder(locQueenFig, nil, 'xyrian')
							end, w2)
							break
						end
					end
					
					if locEvent then
						if locXyrianRoom2 == locQueenTile then
							local w2 = locWait2
							locWait2 = locWait2 + 0.3
							Wait.time(function()
								critOnXyrian(xyrian)
							end, w2)
						end
					end
				end
			end
			
		end, locWait+0.3)
	end
end

function onObjectDestroy(object)
	if not scriptEnabled then return end
	local objGUID = nil
	local objPos = nil
	pcall(function()
		objGUID = object.guid
		objPos = object.getPosition()
	end)
	if objGUID == nil or objPos == nil then return end
	-- Check if destroyed object is a tracked health token by GUID (avoids calling getGMNotes on destroyed object)
	local matchedColor = nil
	for color, entry in pairs(playerInfoTable) do
		if entry.healthGUID == objGUID then
			matchedColor = color
			break
		end
	end
	if matchedColor == nil then return end
	-- Defer to next frame: during menu exit, this callback will never execute
	local savedPos = {objPos.x, objPos.y, objPos.z}
	Wait.frames(function()
		if healthBag ~= nil and playerInfoTable[matchedColor] ~= nil then
			healthBag.takeObject({
				position = Vector(savedPos[1], savedPos[2] + 1, savedPos[3]),
				callback_function = function (o)
					if o ~= nil and playerInfoTable[matchedColor] ~= nil then
						playerInfoTable[matchedColor].healthGUID = o.getGUID()
						o.setGMNotes('playerHealth')
					end
				end,
				smooth = false,
			})
		end
	end, 1)
end

function getFirstPlayerColor()
	if not scriptEnabled then
		return true
	end
	
	return getNearestPColor(firstPlayerToken.getPosition().x)
end

function createClickableSign(pos, msg)
	if not scriptEnabled then
		return true
	end
	
	local locPos = Vector(0,4,1)
	local locScale = Vector(4,4,4)
	local locFSize = 100
	local locW = 700
	local locH = 200
	
	if pos != nil then		
		locPos = pos + Vector(0,4,-8)
	end
	
	if msg != nil then
		local locJumps = string.find(msg, '\n')
		locW = locFSize*0.4375
		
		if locJumps != nil then
			locH = 200 + 100*string.len(locJumps)
			locW = tonumber(locJumps)*locW
		else
			locW = string.len(msg)*locW
		end
		
		
	end
	
	centerCube.createButton({
		click_function = 'none2',
		function_owner = Global,
		label          = msg,
		position       = locPos,
		scale          = locScale,
		width          = locW,
		height         = locH,
		font_size      = locFSize,
		color          = lifeformColor,
		font_color     = {1,1,1,1},
		tooltip        = '',
	})
	
end

function autoInsider(insiderTagType, insiderEffectTag, inputRoomTile, pColor, cautiousMove, previousRoomPos, intruderFig)
	if not scriptEnabled then
		return true
	end
	
	insiderRecall()
	
	if insiderDeck == nil then
		return true --bye bye
	end
		
	local locInputRoomTile = nil
	local locInputRoomPos = Vector(0,0,0)
	local locInputRoomName = ''
	
	if inputRoomTile != nil then
		locInputRoomTile = inputRoomTile
		locInputRoomPos = inputRoomTile.getPosition()
		locInputRoomName = inputRoomTile.getName()
	end
	

	

	
	local locPCol = nil
	if pColor != nil then
		locPCol = pColor
	end
	
	local locCautiousMove = false
	
	if cautiousMove != nil then
		locCautiousMove = cautiousMove
	end
	
	local locBoard = nil
	local locChar = nil
	
	if locPCol != nil then
		if locPCol != 'insider' then
			locBoard = gO(playerInfoTable[locPCol].boardGUID)
			locChar = gO(playerInfoTable[locPCol].figureGUID)
		else
			locBoard = insiderCard
			if insiderFig != nil then
				locChar = insiderFig
			end
		end
	end
	
	
	if insiderStoryGUID == '' then
		
		if locInputRoomTile != nil then
			
			
			for _, storyCard in pairs (insiderDeck.getObjects()) do
				if string.find(storyCard.name, locInputRoomName) != nil and storyCard.gm_notes == '1' then
					insiderDeck.takeObject({
						position = insiderDeck.getPosition() + Vector(0,0,4),
						guid = storyCard.guid,
						callback_function = function(o)
								insiderSequel(o, inputRoomTile, locPCol, locCautiousMove, previousRoomPos)
							end,
						
					})
					break
				end
			end
		end
	
	else
		registerToRoomsMap() --Aaaaw...
		local locInsiderStory = gO(insiderStoryGUID)
		local locInsiderStoryDesc = locInsiderStory.getDescription()
		local locPlayerRooms = getPlayerRoomsInFirstTurnOrder()
		
		local locRooms = {}
		local locCorridors = {}
		local locFires = {}
		local locMalfunctions = {}
		local locDoors = {}
		local locDoorsDestroyed = {}
		local locIntruders = {}
		local locXyrians = {}
		local locNoises = {}
		local locWait = 0
		
		for _, obj in pairs (getAllObjects()) do
			if obj.hasTag('room') then
				table.insert(locRooms, obj)
			elseif obj.hasTag('Corridors') then
				table.insert(locCorridors, obj)
				
			elseif obj.hasTag('intruder') then
				table.insert(locIntruders, obj)
			elseif obj.getGMNotes() == 'fire' then
				table.insert(locFires, obj)
			elseif obj.getGMNotes() == 'malfunction' then
				table.insert(locMalfunctions, obj)
			elseif obj.getDescription() == 'door' then
				table.insert(locDoors, obj)
			elseif obj.getDescription() == 'destroyedDoor' then
				table.insert(locDoorsDestroyed, obj)
			elseif obj.getGMNotes() == 'xyrian' then
				table.insert(locXyrians, obj)
			elseif obj.getName() == 'Noise' then
				table.insert(locNoises, obj)
			end
		end
		
		
		if insiderTagType == 0 then
			for _, t in pairs (locInsiderStory.getTags()) do
				if t == 'insiderInstantAdd1Adult' then
					if adultFBag.getQuantity() > 0 then
						adultFBag.takeObject({
							position = adultFBag.getPosition() + Vector(0,10,0),
							rotation = {0,0,0},
							callback_function = function(o)
								o.setLock(true)
								o.setPositionSmooth(findSpaceOnTile(locInputRoomTile, nil, true,o), false, true)
								
								if o.hasTag('rot180') then
									o.setRotation({0,180,0})
								else
									o.setRotation({0,0,0})
								end

								checkSecureRoom(locInputRoomTile, o, locPCol)
							end,
						})
					end
				
				elseif t == 'insiderInstantAdd3AmmoToInsider' then
					
					for i = 1, 3 do
						if ammoBag.getQuantity() > 0 then
							ammoBag.takeObject({
								position = insiderCard.getPosition() + Vector(0,i*0.5,0),
								rotation = {0,180,0},
							})
						end
					end
				
				elseif t == 'insiderInstantAdd1Drone' then
					local locFBag = breederFBag
					
					if lifeforms == 'Neoflesh' then
						locFBag = adultFBag
					end
					
					if locFBag.getQuantity() > 0 then
						locFBag.takeObject({
							position = locFBag.getPosition() + Vector(0,10,0),
							rotation = {0,0,0},
							callback_function = function(o)
								o.setLock(true)
								o.setPositionSmooth(findSpaceOnTile(locInputRoomTile, nil, true,o), false, true)
								
								if o.hasTag('rot180') then
									o.setRotation({0,180,0})
								else
									o.setRotation({0,0,0})
								end
								
								checkSecureRoom(locInputRoomTile, o, locPCol)
							end,
						})
					end
				
				elseif t == 'insiderInstantAskPlaceInsider' then
					
					createClickableSign(locInputRoomTile.getPosition(), '플레이어 ' .. locPCol .. ' must place the Insider figure\nin a neighboring Room.')
					
				elseif t == 'insiderInstantAutoDestrOnStory' then
					if autoDestructionToken != nil then
						autoDestructionToken.setPositionSmooth(locInsiderStory.getPosition()+Vector(0,1,0),false, false)
					end
					
					if insiderFig != nil then
						insiderFig.setPosition(insiderCard.getPosition() + Vector(0,1,0))
					end
				
				elseif t == 'insiderInstantBreak' then
					
					for _, obj in pairs (locMalfunctions) do
						if distanceMath(obj.getPosition(), locInputRoomPos) < tileImportedSize.x then
							malfunctionBag.putObject(obj)
							break
						end
					end
					
					malfunctionBag.takeObject({
						position = locInputRoomPos + Vector(0,0.5,-1.05),
						rotation = {0,0,0},
						smooth = false,
						callback_function = function(o)
							if locInsiderStory.hasTag('insiderEffectArmoryNoRepair') then
								o.setLock(true)
								o.setPosition(locInputRoomPos + Vector(0,0.5,-1.05))
								o.setColorTint(Color(0.663,0.306,1))
								o.setName('Malfunction cannot be removed.')
							end
						end,
					})
					

				elseif t == 'insiderInstantBreakComputers' then
				
					for _, roomTile in pairs (locRooms) do
						if roomTile.hasTag('computer') then
							local locMalfFound = false
							local locRoomTilePos = roomTile.getPosition()
							
							for _, malfunctionToken in pairs (locMalfunctions) do
								if distanceMath(malfunctionToken.getPosition(), locRoomTilePos) < tileImportedSize.x then
									locMalfFound = true
									break
								end
							end
							
							if not locMalfFound then
								placeMalfunction(locRoomTilePos + Vector(0,0.5,-1.05))
							end
						end
					end
				
				elseif t == 'insiderInstantBurn' then
					local locFireFound = false
					
					
					for _, obj in pairs (locFires) do
						if distanceMath(obj.getPosition(), locInputRoomPos) < tileImportedSize.x then
							locFireFound = true
							break
						end
					end
					
					if not locFireFound then
						placeFire(locInputRoomPos + Vector(0.35,0,-1.3), false)
					end
				
				elseif t == 'insiderInstantCharBack' then
				
					if locChar != nil then
						locChar.setPositionSmooth(previousRoomPos, false, true)
						locChar.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantCloseAllDoors' then
				
					for _, corridor2GUID in pairs (RoomsMap[locInputRoomTile.getGUID()][2]) do
						local locCor2 = gO(corridor2GUID)
						local locPotentialDoorPos = 0.5 * (locCor2.getPosition() + locInputRoomTile.getPosition())
						local locFreeSpot = true
						
						for _, obj in pairs (locDoors) do
							if distanceMath(obj.getPosition(), locPotentialDoorPos) < corridorImportedSize.x *0.3 then
								locFreeSpot = false
								break
							end
						end
						
						if locFreeSpot then
							for _, obj in pairs (locDoorsDestroyed) do
								if distanceMath(obj.getPosition(), locPotentialDoorPos) < corridorImportedSize.x *0.3 then
									locFreeSpot = false
									break
								end
							end
						
							if locFreeSpot then
								if doorBag.getQuantity() > 0 then
									doorBag.takeObject({
										position = locPotentialDoorPos + Vector(0,1,0),
										rotation = {0,locCor2.getRotation().y+90,0},
										callback_function = function(o)
											o.setLock(true)
											o.setPositionSmooth(locPotentialDoorPos, false, false)
										end,
										smooth = false,
									})
								end
							end
						end	
					end
				
				elseif t == 'insiderInstantDiscardNoises' then
					for _, obj in pairs (locNoises) do
						obj.destruct()
					end
					
				elseif t == 'insiderInstantDraw1RobotCard' then
					robotDeck.shuffle()
					robotDeck.takeObject({
						position = {-8.7,1.79,21.32},
						rotation = {0,180,0},
						callback_function = function(o)
							o.setLock(true)
							if o.getName() == 'Exploration Robot' then
								robot.addTag('characterFig')
								robot.addTag('noEntrance')
							end
							
							broadcastToAll(o.getName() .. '도 공개되었습니다.', insiderColor)
						end,
					})
				
				elseif t == 'insiderInstantDrug' then
					
					locInsiderStory.setPositionSmooth(locBoard.getPosition() + Vector(0,2,0), false,true)
					
					if lifeforms == 'Sangrevores' or lifeforms == 'Carnomorph' then
						local locDeck = taintedDeck
						
						if lifeforms == 'Carnomorph' then
							locDeck = mutationDeck
						end
						
						if locDeck.getQuantity() > 0 then
							locDeck.takeObject({
								position = locBoard.getPosition() + Vector(6.48,1,-4.5),
							})
						end
					else
						if larvaeFBag.getQuantity() > 0 then
							larvaeFBag.takeObject({
								position = locBoard.getPosition() + Vector(0,1,0),
							})
						end
					end
					
					addContamination(locPCol)
					broadcastToAll('플레이어 ' .. locPCol .. '가 약을 먹었으며, 플레이어 보드에 배치되었습니다.', insiderColor)
					
				elseif t == 'insiderInstantFriendly' then
					insiderCard.setGMNotes('active')
					insiderHealth.setPosition(insiderCard.getPosition() + Vector(-1.73,0.3,-0.79))
					insiderHealth.setLock(false)
					
					if locInsiderStory.hasTag('insiderInstantInsiderLose3Health') then
						for i = 1 , 3 do
							loseHealth('insider')
						end
					end
				
				elseif t == 'insiderInstantHostile' then
					insiderCard.setRotation({0,180,180})
					insiderCard.setGMNotes('active')
					insiderHealth.setLock(true)
					insiderHealth.setPosition({0,0,0})
					
					
					if insiderFig != nil then
						if not insiderFig.hasTag('healthCount') then
							insiderFig.addTag('healthCount')
						end
						
						if insiderFig.hasTag('characterFig') then
							insiderFig.removeTag('characterFig')
						end
						
						Wait.time(function()
							local locHostileLink = 'https://steamusercontent-a.akamaihd.net/ugc/11471611012038595211/E1BE1663F536A43444FE631B229CD76C77B86561/'
							insiderFig.setCustomObject({image = locHostileLink, image_secondary = locHostileLink})
							insiderFig.reload()
							
							broadcastToAll('인사이더가 적대적으로 돌변했습니다!', insiderColor)
							playsounds(math.random(257,260))
							Wait.time(function()
								if locInsiderStory.hasTag('insiderInstantInsiderHostileGet3Hits') then
									insiderRecall()
									insiderFig.setVar("count", 3)
									insiderFig.call("updateDisplay")
								end
							end, 1)
						end, 2)
					end
					
				elseif t == 'insiderInstantInsiderCardDeactive' then	
					insiderCard.setGMNotes('')
					
					if insiderFig.hasTag('healthCount') then
						insiderFig.removeTag('healthCount')
					end
				
				elseif t == 'insiderInstantInsiderInEscapeShuttleSlot' then
				
					if insiderFig != nil then
						local locShuttleAvailable = true
						
						for _, passenger in pairs (shapeCast(locEscapePos)) do
							if passenger.hasTag('characterFig') or passenger.hasTag('healthCount') then
								locShuttleAvailable = false
								break
							end
						end
						
						if locShuttleAvailable then
							insiderFig.setLock(true)
							insiderFig.setPositionSmooth({-16.54, 1.9, 19.89}, false, true)
							insiderFig.setRotation({0,0,0})

							toBox(insiderDeck)
							insiderStoryGUID = ''
							
							insiderEnable = false
						end
						broadcastToAll('인사이더가 탈출 셔틀로 도망쳤습니까?!', insiderColor)
					end
				
				elseif t == 'insiderInstantInsiderInHibernatorium' then
					
					if insiderFig != nil then
						insiderFig.setPositionSmooth(findSpaceOnTile(hiddenRoom), false, true)
						insiderFig.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantInsiderInHibernatoriumBeforeRound6' then
				
					if insiderFig != nil and turnMarker.getPosition().z > 10.4 then
						if distanceMath(insiderFig.getPosition(), landingZone.getPosition()) > tileImportedSize.x then
							insiderFig.setPositionSmooth(findSpaceOnTile(hiddenRoom), false, true)
							insiderFig.setRotation({0,0,0})
						end
					end
					
				elseif t == 'insiderInstantInsiderInLanding' then
					
					if insiderFig != nil then
						insiderFig.setPositionSmooth(findSpaceOnTile(landingZone), false, true)
						insiderFig.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantInsiderInPlayerRoom' then
				
					if insiderFig != nil then
						if locPCol != nil then
							insiderFig.setPositionSmooth(findSpaceOnTile(gO(locPlayerRooms[locPCol])), false, true)
						else
							createClickableSign(locInputRoomPos, 'Place the Insider in the Room of the Player\nwho initiated the current Insider Story.')
						end
					end
					
				elseif t == 'insiderInstantInsiderInRoom' then
					if insiderFig != nil then
						insiderFig.setPositionSmooth(findSpaceOnTile(locInputRoomTile), false, true)
						insiderFig.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantInsiderModelDown' then
					
					if insiderFig != nil then
						insiderFig.setPosition(insiderFig.getPosition() + Vector(0,0.5,0))
						insiderFig.setRotation({90,90,0})
						broadcastToAll('인사이더가 고통 속에 쓰러졌습니다.', insiderColor)
					end
				
				elseif t == 'insiderInstantInsiderToDrone' then
				
					local locFBag = breederFBag
					
					if lifeforms == 'Neoflesh' then
						locFBag = adultFBag
					end
				
					
					local locInsiderPos = insiderFig.getPosition()
				
					if locFBag.getQuantity() > 0 then
						locFBag.takeObject({
							position = locInsiderPos,
							rotation = {0,0,0},
							callback_function = function(o)
								o.setLock(true)
								if o.hasTag('rot180') then
									o.setRotation({0,180,0})
								end
								
								for color, playerRoomGUID in pairs (locPlayerRooms) do
									local locPRoom = gO(playerRoomGUID)
									if distanceMath(locInsiderPos, locPRoom.getPosition()) < tileImportedSize.x then
										checkSecureRoom(locPRoom, o, color)
										break
									end
								end
								
							end,
						})
						broadcastToAll('인사이더가 침입자로 변했습니다!', lifeformColor)
					end
					toBox(insiderFig)
					toBox(insiderDeck)
					insiderStoryGUID = ''
					
					insiderEnable = false
					
				elseif t == 'insiderInstantInsiderToNestOrDie' then
				
					if insiderFig != nil and insiderCard != nil then
					
						local locNestFound = false
						local locNest = nil
						
						for _, roomTile in pairs (locRooms) do
							if roomTile.getName() == 'NEST' then
								locNest = roomTile
								for i = 1, 3 do
									loseHealth('insider')
								end
								
								locNestFound = not (insiderHealth.getPosition().x - insiderCard.getPosition().x > 1.47)
								break
							end
						end
						
						if locNestFound then
							insiderFig.setPositionSmooth(findSpaceOnTile(locNest), false, true)
							insiderFig.setRotation({0,0,0})
							broadcastToAll('인사이더가 가까스로 살아서 둥지로 납치되었습니다.', insiderColor)
						else
							broadcastToAll('인사이더가 사망했습니다.', insiderColor)
							toBox(insiderFig)
							toBox(insiderDeck)
							insiderStoryGUID = ''
							
							insiderEnable = false
						end
					
					end
				
				elseif t == 'insiderInstantMoveHurt' then
					if locPCol != nil then
						local locHits = 3
						
						if locCautiousMove then
							locHits = 1
						end
						
						for i = 1, locHits do
							loseHealth(locPCol)
						end
					end
				
				elseif t == 'insiderInstantOpenAllDoorsShelter' then
				
					for _, roomTile in pairs (locRooms) do
						if roomTile.getName() == 'SHELTER' then
							local locShelterPos = roomTile.getPosition()
							
							for _, door in pairs (locDoors) do
								if distanceMath(locShelterPos, door.getPosition()) < tileImportedSize.x then
									door.setLock(false)
									doorBag.putObject(door)
								end
							end
							break
						end
					end
				
				elseif t == 'insiderInstantOxygenOn' then
					for _, obj in pairs (getAllObjects()) do
						if obj.hasTag('LifeSupportOff') then
							if getSectionFromXPos(obj.getPosition().x) == getSectionFromXPos(locInputRoomPos.x) then 
								obj.setState(1)
								break
							end
						end
					end
					
				elseif t == 'insiderInstantPlaceRobot' then
					if hibUnexplored != nil then
						robot.setPosition(findSpaceOnTile(locInputRoomTile))
						onObjectDrop(locPCol, robot)
					end
				
				elseif t == 'insiderInstantRemoveInsider' then
					
					insiderCard.setGMNotes('')
					if insiderFig != nil then
						toBox(insiderFig)
					end
					
					if insiderDeck != nil then
						toBox(insiderDeck)
					end
					insiderStoryGUID = ''
					
					insiderEnable = false
					
				elseif t == 'insiderInstantRemoveInsiderFig' then
					
					if insiderFig != nil then
						toBox(insiderFig)
					end
				
				elseif t == 'insiderInstantRemoveOxy' then
					
					local locLSCount = 0
					
					for _, obj in pairs (getAllObjects()) do
						if obj.hasTag('LifeSupport') or obj.hasTag('LifeSupportOff') then
							obj.destruct()
							locLSCount = locLSCount + 1
							
							if locLSCount == 3 then
								break
							end
						end
					end
					
				elseif t == 'insiderInstantReturnQueen' then
					
					if queenFBag.getQuantity() == 0 then
						if isQueenAlive then
							for _, intruder in pairs (locIntruders) do
								if intruder.getGMNotes() == 'queen' then
									enemyFigReturn(intruder)
									break
								end
							end
						end
					end
				
				elseif t == 'insiderInstantRoundAutoDestr' then
					
					if autoDestructionToken != nil then
						local locTurnPos = turnMarker.getPosition()
						autoDestructionToken.setLock(true)
						autoDestructionToken.setPosition(Vector(locTurnPos.x, 1.63, math.max(2.57,locTurnPos.z- 4*turnOffset.z)))
						
						onObjectDrop(locPCol, autoDestructionToken)
					end
					
					if insiderFig != nil and insiderCard != nil then
						insiderFig.setPosition(insiderCard.getPosition() + Vector(0,1,0))
					end
				
				elseif t == 'insiderInstantRoundEgg' then
				
					local locEgg = getTaggedObjAtPos('Egg', locBoard.getPosition(), 1, locBoard.getBounds().size)
					
					if locEgg != nil then
						local locTurnPos = turnMarker.getPosition()
						locEgg.setPosition(Vector(locTurnPos.x, 3, math.max(2.57,locTurnPos.z- 3*turnOffset.z)))
						locEgg.setScale({0.3,1,0.35})
					end
				
				elseif t == 'insiderInstantRoundInsider' then
					
					if insiderFig != nil then
						local locTurnPos = turnMarker.getPosition()
						insiderFig.setPosition(Vector(locTurnPos.x, 3, math.max(2.57,locTurnPos.z- 4*turnOffset.z)))
						insiderFig.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantRunawayInRoom' then
				
					if insiderRunaway != nil then
						insiderRunaway.setPositionSmooth(findSpaceOnTile(locInputRoomTile, nil, true), false, true)
						insiderRunaway.setRotation({0,0,0})
					end
				
				elseif t == 'insiderInstantTaskTheEscape' then
					for _, storyCard in pairs (insiderDeck.getObjects()) do
						if storyCard.gm_notes == '14' then
							insiderDeck.takeObject({
								position = {-14.72,1.68,-1.21},
								rotation = {0,180,180},
								guid = storyCard.guid,
								callback_function = function(o) o.setLock(true) o.setScale({1.1,1,1.1}) end,
							})
							break
						end
					end
				
				elseif t == 'insiderInstantRemove' then
					if insiderFig != nil then
						toBox(insiderFig)
					end
					
					if insiderCard != nil then
						toBox(insiderCard)
					end
					
					if insiderDeck != nil then
						toBox(insiderDeck)
					end
					insiderStoryGUID = ''
					
					insiderEnable = false
				end
			end
		
		elseif insiderTagType == 1 then
			for _, t in pairs (locInsiderStory.getTags()) do
				if t == 'insiderExp1AdultWithInsider' then
				
					if insiderFig != nil then
						for _, room in pairs (locRooms) do
							if distanceMath(insiderFig.getPosition(), room.getPosition()) < tileImportedSize.x then
								local locAdult = getTaggedObjAtPos('intruder', room.getPosition(), 0, tileImportedSize*0.5)
								if locAdult == nil then
									if adultFBag.getQuantity() > 0 then
										adultFBag.takeObject({
											position = adultFBag.getPosition() + Vector(0,10,0),
											rotation = {0,0,0},
											callback_function = function(o)
												o.setLock(true)
												o.setPositionSmooth(findSpaceOnTile(room, nil, true,o), false, true)
												
												if o.hasTag('rot180') then
													o.setRotation({0,180,0})
												else
													o.setRotation({0,0,0})
												end
												local locRoomGUID = room.getGUID()
												
												locPlayerRooms['insider'] = locRoomGUID
												
												for color, playerRoomGUID in pairs (locPlayerRooms) do
													if playerRoomGUID == locRoomGUID then
														checkSecureRoom(room, o, color)
														break
													end
												end
											end,
										})
									end
								end
								break
							end
						end
					end
				
				elseif t == 'insiderExpAddAdultWithInsider' then
				
					if insiderFig != nil then
						for _, room in pairs (locRooms) do
							if distanceMath(insiderFig.getPosition(), room.getPosition()) < tileImportedSize.x then
								if adultFBag.getQuantity() > 0 then
									adultFBag.takeObject({
										position = adultFBag.getPosition() + Vector(0,10,0),
										rotation = {0,0,0},
										callback_function = function(o)
											o.setLock(true)
											o.setPositionSmooth(findSpaceOnTile(room, nil, true,o), false, true)
											
											if o.hasTag('rot180') then
												o.setRotation({0,180,0})
											else
												o.setRotation({0,0,0})
											end
											
											local locRoomGUID = room.getGUID()
											
											locPlayerRooms['insider'] = locRoomGUID
											
											for color, playerRoomGUID in pairs (locPlayerRooms) do
												if playerRoomGUID == locRoomGUID then
													checkSecureRoom(room, o, color)
													break
												end
											end
										end,
									})
								end
								break
							end
						end
					end
				
				elseif t == 'insiderExpAddLarvaWithInsider' then
				
					if insiderFig != nil then
						local locFBag = larvaeFBag
						
						if lifeforms == 'Sangrevores' then
							locFBag = adultFBag
						end
						
						for _, room in pairs (locRooms) do
							if distanceMath(insiderFig.getPosition(), room.getPosition()) < tileImportedSize.x then
								if locFBag.getQuantity() > 0 then
									locFBag.takeObject({
										position = locFBag.getPosition() + Vector(0,10,0),
										rotation = {0,0,0},
										callback_function = function(o)
											o.setLock(true)
											o.setPositionSmooth(findSpaceOnTile(room, nil, true,o), false, true)
											
											if o.hasTag('rot180') then
												o.setRotation({0,180,0})
											else
												o.setRotation({0,0,0})
											end
											
											local locRoomGUID = room.getGUID()
											
											for color, playerRoomGUID in pairs (locPlayerRooms) do
												if playerRoomGUID == locRoomGUID then
													checkSecureRoom(room, o, color)
													break
												end
											end
										end,
									})
								end
								break
							end
						end
					end
				
				elseif t == 'insiderExpAddDroneOnEgg' then
					
					for color, playerRoomGUID in pairs (locPlayerRooms) do
						if playerHasTag('Egg', 1, nil, color) then
						
							local locFBag = breederFBag
							
							if lifeforms == 'Neoflesh' then
								locFBag = adultFBag
							end
							
							if locFBag.getQuantity() > 0 then
								
								local roomTile = nil
								
								if color == locPCol then
									roomTile = locInputRoomTile
								else
									roomTile = gO(playerRoomGUID)
								end
								
								locFBag.takeObject({
									position = locFBag.getPosition() + Vector(0,6,0),
									callback_function = function(o)
										local w = locWait
										locWait = locWait + 0.25
										o.setLock(true)
										
										Wait.time(function()
											--o.setLock(false)
											o.setRotation({0,0,0})
											o.setPositionSmooth(findSpaceOnTile(roomTile,nil, true,o), false, true)
											checkSecureRoom(roomTile, o, color)
											
											if o.hasTag('rot180') then
												o.setRotation({0,180,0})
											end
										end, w)
									end,
								})
							end
						end
					end
					
					
				
				
				elseif t == 'insiderExpBurn' then
					local locFireFound = false
					
					for _, obj in pairs (locFires) do					
						if distanceMath(obj.getPosition(), locInputRoomPos) < tileImportedSize.x then
							if locGM == 'fire' then
								locFireFound = true
								break
							end
						end
					end
					
					if not locFireFound then
						placeFire(locInputRoomPos + Vector(0.35,0,-1.3), false)
					end
				
				elseif t == 'insiderExpCallAllEffectRound' then
				
					Wait.time(function()
						local locTags = locInsiderStory.getTags()
						
						for _, tag in pairs (locTags) do
							if string.find(tag, 'insiderEffectRound') != nil then
								autoInsider(2, tag)
							end
						end

					end, 2)					
				
				
				elseif t == 'insiderExpCharWithInsiderNoiseRoll' then
				
					if insiderFig != nil then
						local locInsiderPos = insiderFig.getPosition()
						local w = 0
						
						for color, playerRoomGUID in pairs (locPlayerRooms) do
							local locPlayerRoom = gO(playerRoomGUID)
							if distanceMath(locPlayerRoom.getPosition(), locInsiderPos) < tileImportedSize.x then
								Wait.time(function()
									autoNoise(nil, gO(playerInfoTable[color].figureGUID), false)
								end, w)
							end
						end
					end
				
				
				elseif t == 'insiderExpInsiderInSurgery' then
					
					for _, room in pairs (locRooms) do
						if distanceMath(insiderFig.getPosition(), room.getPosition()) < tileImportedSize.x then
							if room.getName() != 'SURGERY ROOM' then
								for _, room in pairs (locRooms) do
									if room.getName() == 'SURGERY ROOM' then
										insiderFig.setPositionSmooth(findSpaceOnTile(room), false, true)
										walksounds(insiderFig)
										
										local locRoomGUID = room.getGUID()
										for color, playerRoomGUID in pairs (locPlayerRooms) do
											if locRoomGUID == playerRoomGUID then
												for _, storyCard in pairs (insiderDeck.getObjects()) do
													if storyCard.gm_notes == '08' then
														insiderDeck.takeObject({
															position = insiderDeck.getPosition() + Vector(0,4,4),
															guid = storyCard.guid,
															callback_function = function(o)
																	insiderSequel(o, inputRoomTile, locPCol, locCautiousMove, previousRoomPos)
																end,
														})
														break
													end
												end
												break
											end
										end
										break
									end
								end
							else
								local locFBag = breederFBag
								
								if lifeforms == 'Neoflesh' then
									locFBag = adultFBag
								end
								
								if locFBag.getQuantity() > 0 then
									locFBag.takeObject({
										position = insiderFig.getPosition(),
										rotation = {0,0,0},
										callback_function = function(o)
											o.setLock(true)
											if o.hasTag('rot180') then
												o.setRotation({0,180,0})
											end
											
										end,
									})
									broadcastToAll('인사이더가 침입자로 변했습니다!', lifeformColor)
								end
								
								toBox(insiderFig)
								locInsiderStory.removeTag(t)
							end
							break
						end
					end
					
				elseif t == 'insiderExpLSFireSpread' then
					
					local locRoomsAddedFire = {}
					local locWait = 0
					
					for _, roomTile in pairs(locRooms) do
						if roomTile.getName() == 'LIFE SUPPORT CONTROL' then
							local locRoomPos = roomTile.getPosition()
							for _, fireToken in pairs(locFires) do
								if distanceMath(fireToken.getPosition(), locRoomPos) <= tileImportedSize.x then
								
									local corList = nil
									local locRoomTileGUID = roomTile.getGUID()
									corList = getLowestNoiseCorridorsAroundRoom(locRoomTileGUID)
									
									if corList != nil then
										for _, lowestCorridor in pairs (corList) do
											local locOtherRoomGUID = ''
											for _, otherRoomGUID in pairs(RoomsMap[lowestCorridor.getGUID()][2]) do
												if otherRoomGUID != locRoomTileGUID then
													locOtherRoomGUID = otherRoomGUID
													break
												end
											end
											
											
											if locOtherRoomGUID != '' then
												if locRoomsAddedFire[locOtherRoomGUID] == nil then
													local locOtherRoom = gO(locOtherRoomGUID)
													local locOtherRoomPos = locOtherRoom.getPosition()
													local locDoorFound = false
													for _, door in pairs(locDoors) do
														if door != nil then
															local locDoorPos = door.getPosition()
															if distanceMath(lowestCorridor.getPosition(), locDoorPos) < corridorImportedSize.x*0.55
															and dotMath(normalizeMath(locDoorPos-locRoomPos), normalizeMath(locOtherRoomPos-locRoomPos)) > 0.9
															then
																locDoorFound = true
																break
															end
														end
													end
													
													if not locDoorFound then
														local locFireFound = false
														for _, fireToken2 in pairs(locFires) do
															if distanceMath(fireToken2.getPosition(), locOtherRoomPos) <= returnRoomDiameter(locOtherRoom) * 0.7 then
																locFireFound = true
																break
															end
														end
														
														if not locFireFound then
															local w = locWait
															locWait = locWait + 1
															locRoomsAddedFire[locOtherRoomGUID] = 1
															Wait.time(function()
																
																placeFire(locOtherRoomPos +Vector(0.35,0,-1.3), false)
																
															end, w)
														end
													end
												end
											end
										end
									end
									break
								end
							end
						end
					end
					
				elseif t == 'insiderExpMoveHurt' then
					if locPCol != nil then
						local locHits = 3
						
						if locCautiousMove then
							locHits = 1
						end
						
						for i = 1, locHits do
							loseHealth(locPCol)
						end
					end
				
				elseif t == 'insiderExpRoundAutoDestrUp' then
					
					if autoDestructionToken != nil then
						if math.abs(autoDestructionToken.getPosition().z - turnMarker.getPosition().z) > turnOffset.z*1.25 then
							autoDestructionToken.setPosition(autoDestructionToken.getPosition() + turnOffset)
						end
					end
				
				elseif t == 'insiderExpRoundEggUp' then
					
					for _, obj in pairs (getAllObjects()) do
						if obj.getName() == 'Egg' then
							if obj.getPosition().z < 14.58 and obj.getPosition().z > 1.9 then
								
								if math.abs(obj.getPosition().z - turnMarker.getPosition().z) > turnOffset.z*0.5 then
									obj.setPosition(obj.getPosition() + turnOffset)
								end
								
								if math.abs(obj.getPosition().z - turnMarker.getPosition().z) < turnOffset.z*0.5 then
									for _, storyCard in pairs (insiderDeck.getObjects()) do
										if storyCard.gm_notes == '20' then
											insiderDeck.takeObject({
												position = insiderDeck.getPosition() + Vector(0,4,4),
												guid = storyCard.guid,
												callback_function = function(o)
														insiderSequel(o, inputRoomTile, locPCol, locCautiousMove, previousRoomPos)
													end,
											})
											break
										end
									end
								end
								
								break
							end
						end
					end
				
				elseif t == 'insiderExpRoundInsiderUp' then
				
					if insiderFig != nil then
						insiderFig.setLock(true)
						insiderFig.setPosition(insiderFig.getPosition() + turnOffset)
						
						if distanceMath(insiderFig.getPosition(), turnMarker.getPosition()) < turnOffset.z*0.5 then
							for _, storyCard in pairs (insiderDeck.getObjects()) do
								if storyCard.gm_notes == '17' then
									insiderDeck.takeObject({
										position = insiderDeck.getPosition() + Vector(0,4,4),
										guid = storyCard.guid,
										callback_function = function(o)
												insiderSequel(o, inputRoomTile, locPCol, locCautiousMove, previousRoomPos)
											end,
									})
									break
								end
							end
						end
					end
				end
			end
			
			local locEIndex = string.find(locInsiderStoryDesc, 'e') --e for explore
			
			if locEIndex != nil then
				local locSequelPass = true
				
				for _, tag in pairs (locInsiderStory.getTags()) do
					if tag == 'insiderSequelExpInsiderOnCard' then
						if insiderFig != nil then
							if distanceMath(insiderFig.getPosition(), locInsiderStory.getPosition()) > 1 then
								insiderFig.setPositionSmooth(locInsiderStory.getPosition() + Vector(0,1,0), false, true)
								locSequelPass = false
							end
						end
						break
					end
				end
				
				if locSequelPass then
					if string.len(locEIndex) > 1 then
						locEIndex = tonumber(string.sub(locEIndex),1,1)
					end
					
					local locChapter = string.sub(locInsiderStoryDesc, locEIndex+1, locEIndex+2)
					for _, storyCard in pairs (insiderDeck.getObjects()) do
						if storyCard.gm_notes == locChapter then
							insiderDeck.takeObject({
								position = insiderDeck.getPosition() + Vector(0,4,4),
								guid = storyCard.guid,
								callback_function = function(o)
										local locNewDesc = string.gsub(locInsiderStoryDesc, 'e'..locChapter,'')
										locInsiderStory.setDescription(string.sub(locNewDesc,1,string.len(locNewDesc)))
										insiderSequel(o, inputRoomTile, locPCol, locCautiousMove, previousRoomPos)
									end,
								
							})
							break
						end
					end
				end
			end
		
		elseif insiderEffectTag != nil then
			
			local t = insiderEffectTag

			for _, tag in pairs (locInsiderStory.getTags()) do
				--Insider OnGoing Effects
				--if t == 'insiderEffectBurstAdd1' then
				
				if tag == t then

					--if t == 'insiderEffectArmoryNoRepair' then
					
					if t == 'insiderEffectBlankRobotClosestCharExplode' then
						locInsiderStory.removeTag(t) --yolo
						if robot != nil then
							local locRobotRoom = nil
							local locRobotRoomGUID = nil
							local locRobotPos = robot.getPosition()
							
							for _, roomTile in pairs (locRooms) do
								if distanceMath(locRobotPos, roomTile.getPosition()) < tileImportedSize.x then
									locRobotRoom = roomTile
									locRobotRoomGUID = roomTile.getGUID()
									break
								end
							end
							
							local locPlayerFound = false
							
							for color, playerRoomGUID in pairs (locPlayerRooms) do
								if playerRoomGUID == locRobotRoomGUID then
									locPlayerFound = true
									break
								end
							end

							
							if not locPlayerFound then
								autoMoveToGoal({locRobotRoom}, {{robot}}, {}, locDoors, {})
								playsounds(163)
								
								Wait.time(function()
									
									locRobotPos = robot.getPosition()
									for _, roomTile in pairs (locRooms) do
										if distanceMath(locRobotPos, roomTile.getPosition()) < tileImportedSize.x then
											locRobotRoom = roomTile
											locRobotRoomGUID = roomTile.getGUID()
											break
										end
									end
									for color, playerRoomGUID in pairs (locPlayerRooms) do
										if playerRoomGUID == locRobotRoomGUID then
											locPlayerFound = true
											break
										end
									end
									
									if not locPlayerFound then
										autoMoveToGoal({locRobotRoom}, {{robot}}, {}, locDoors, {})
										
										Wait.time(function()
											
											locRobotPos = robot.getPosition()
											for _, roomTile in pairs (locRooms) do
												if distanceMath(locRobotPos, roomTile.getPosition()) < tileImportedSize.x then
													locRobotRoom = roomTile
													locRobotRoomGUID = roomTile.getGUID()
													break
												end
											end
											
											for color, playerRoomGUID in pairs (locPlayerRooms) do
												if playerRoomGUID == locRobotRoomGUID then
													locPlayerFound = true
													break
												end
											end
											
											if not locPlayerFound then
												autoMoveToGoal({locRobotRoom}, {{robot}}, {}, locDoors, {})
												
												Wait.time(function()
													
													locRobotPos = robot.getPosition()
													
													
													for color, playerRoomGUID in pairs (locPlayerRooms) do
														local locPlayerRoom = gO(playerRoomGUID)
														if distanceMath(locRobotPos, locPlayerRoom.getPosition()) < tileImportedSize.x then
															locRobotRoom = locPlayerRoom
															locRobotRoomGUID = playerRoomGUID
															locPlayerFound = true
															break
														end
													end

													
												end,0.3)
											end
											
										end,0.3)
									end
									
								end,0.3)
							end
							
							Wait.time(function()
								locRobotPos = robot.getPosition()
								local locRobotRoomPos = nil
								for _, roomTile in pairs (locRooms) do
									if distanceMath(locRobotPos, roomTile.getPosition()) < tileImportedSize.x then
										locRobotRoom = roomTile
										locRobotRoomPos = roomTile.getPosition()
										playsounds(189)
										for _, intruder in pairs (locIntruders) do
											local locDist = distanceMath(intruder.getPosition(), locRobotRoomPos)
											if locDist < tileImportedSize.x*1.5 then
												local locRoomParam = nil
												if locDist < tileImportedSize.x*0.5 then
													locRoomParam = locRobotRoom
												end
												critOnIntruder(intruder, locRoomParam, 'explosion')
											end
										end
										
										for _, xyrian in pairs (locXyrians) do
											if distanceMath(xyrian.getPosition(), locRobotRoomPos) < tileImportedSize.x then
												playsounds(math.random(20,22))
												critOnXyrian(xyrian)
											end
										end
										
										for color, playerRoomGUID in pairs (locPlayerRooms) do
											if playerRoomGUID == locRobotRoomGUID then
												for i = 1, 3 do
													loseHealth(color)
												end
											end
										end
										
										local locMalfFound = false
										local locFireFound = false
										
										for _, malfunctionToken in pairs(locMalfunctions) do
											if distanceMath(malfunctionToken.getPosition(), locRobotRoomPos) < tileImportedSize.x then
												locMalfFound = true
												break
											end
										end
										
										for _, fireToken in pairs(locFires) do
											if distanceMath(fireToken.getPosition(), locRobotRoomPos) < tileImportedSize.x then
												locFireFound = true
												break
											end
										end
										
										if not locMalfFound then
											placeMalfunction(locRobotRoomPos + Vector(0,0,-1.05))
										end
										
										if not locFireFound then
											placeFire(locRobotRoomPos + Vector(0.35,0,-1.3))
										end
										
										toBox(robot)
									end
								end
							end, 2)
						
						end
						
						
					elseif t == 'insiderEffectEndTurnInRedRoomLose1Health' then
					
						if locInputRoomTile != nil then
							if string.find(locInputRoomTile.getDescription(), 'R') != nil then
								loseHealth(locPCol)
								playsounds(math.random(90,91))
							end
						end
					
					elseif t == 'insiderEffectEndTurnBurnChara' then
						local locPlayerRoomPos = gO(locPlayerRooms[locPCol]).getPosition()
						
						for _, fireToken in pairs (locFires) do
							if distanceMath(fireToken.getPosition(), locPlayerRoomPos) < tileImportedSize.x then
								loseHealth(locPCol)
								loseHealth(locPCol)
								break
							end
						end
						
					--elseif t == 'insiderEffectExpInsiderJustRoom' then
					--elseif t == 'insiderEffectExpNoRightCorridor' then
					
					elseif t == 'insiderEffectIntruderEnterWithCharInOxyLand1Hit' then
					
						if intruderFig != nil then
							if intruderFig.hasTag('healthCount') and isInOxygenSection(locInputRoomTile) then
								intruderFig.setVar("count", intruderFig.getVar("count") + 1)
								intruderFig.call("updateDisplay")
								playsounds(179)
							end
						end
					
					--elseif t == 'insiderEffectFireKeep' then
					--elseif t == 'insiderEffectFireKeepOxy' then
					
					elseif t == 'insiderEffectLanderDropWithInsiderRemove' then
						
						if shuttleFigure != nil and insiderCard != nil then
							locInsiderStory.clearButtons()
							local locShuttlePos = shuttleFigure.getPosition()
							
							for _, roomTile in pairs (locRooms) do
								if distanceMath(roomTile.getPosition(), locShuttlePos) < tileImportedSize.x then
									if distanceMath(roomTile.getPosition(), insiderFig.getPosition()) < tileImportedSize.x then
									
										insiderFig.setLock(true)
										shuttleFigure.setLock(true)
										
										shuttleFigure.setPosition(roomTile.getPosition() + Vector(0,1,0))
										insiderFig.setPosition(shuttleFigure.getPosition()+Vector(0,0.5,0))
										insiderFig.setRotation({0,0,0})
										
										shuttleFigure.addAttachment(insiderFig)
										shuttleFigure.setPositionSmooth(insiderCard.getPosition() + Vector(0,6,0.76), false, false)
										onObjectPickUp(pColor, shuttleFigure)
										
										Wait.time(function()
											onObjectDrop(pColor, shuttleFigure)
											shuttleFigure.setLock(false)
										end,7)
										locInsiderStory.removeTag(t)
									end
								end
							end
						end
					
					elseif t == 'insiderEffectMoveFromInsiderFollow' then
					
						if insiderFig != nil then
							
							local locInsiderPos = insiderFig.getPosition()
							local locInsiderRoom = nil
							local locInsiderAlone = true
							
							for color, playerRoomGUID in pairs (locPlayerRooms) do
								if distanceMath(locInsiderPos, gO(playerRoomGUID).getPosition()) < tileImportedSize.x then
									locInsiderAlone = false
									break
								end
							end
							
							if locInsiderAlone and locPCol != nil then
								local locPlayerRoomTile = gO(locPlayerRooms[locPCol])
								
								if locPlayerRoomTile != nil then
									insiderFig.setPositionSmooth(findSpaceOnTile(locPlayerRoomTile, nil, true), false, true)
									insiderFig.setRotation({0,0,0})
									walksounds(insiderFig)
								end
							end
						end
					
					elseif t == 'insiderEffectMoveToInsiderGainContamination' then
						if insiderFig != nil then
							if distanceMath(locChar.getPosition(), insiderFig.getPosition()) < tileImportedSize.x*0.6 then
								addContamination(locPCol)
							end
						end
					
					--elseif t == 'insiderEffectNoData' then
					

					elseif t == 'insiderEffectPassWithInsiderAmmoOrRedItem' then
					
						if insiderFig != nil and insiderCard != nil then
							local locInsiderPos = insiderFig.getPosition()
							
							for _, roomTile in pairs (locRooms) do
								if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
									if roomTile.getGUID() == locPlayerRooms[locPCol] then
										local locAmmos = getTaggedObjAtPos('ammo', insiderCard.getPosition(), 3, insiderCard.getBounds().size + Vector(0,5,0), nil ,true)
										if #locAmmos > 0 then
											choiceToPlayer(locChar.getPosition() + Vector(5,1,-2), 'Yes = 1 Ammo\nNo = Red Item', 80)
											Wait.condition(function()
												
												if choiceState == 1 then
													locAmmos[1].deal(1,locPCol)
												else
													if redItemsDeck != nil then
														if redItemsDeck.getQuantity() > 0 then
															redItemsDeck.deal(1,locPCol)
														end
													end
												end
												choiceState = 2
											
											end, function () return choiceState < 2 end, 999999, function () end)
										else
											if redItemsDeck != nil then
												if redItemsDeck.getQuantity() > 0 then
													redItemsDeck.deal(1,locPCol)
												end
											end
										end
									end
								end
							end	
						end
					
					elseif t == 'insiderEffectPassWithInsiderNoiseRoll' then
					
						if insiderFig != nil then
							
							local locPlayerRoom = gO(locPlayerRooms[locPCol])
							local w = 0
							if distanceMath(locPlayerRoom.getPosition(), insiderFig.getPosition()) < tileImportedSize.x then
								Wait.time(function()
									autoNoise(nil, locChar, false)
								end, w)
								w = w + 0.25
							end
						end
						
						
					elseif t == 'insiderEffectPlayerPhaseInsiderRemoveAllOxy' then
						local locCount = 0
						
						
						if insiderFig != nil then
							for _, lifeSupportObj in pairs (getAllObjects()) do
								if lifeSupportObj.hasTag('LifeSupport') or lifeSupportObj.hasTag('LifeSupportOff') then
									lifeSupportObj.destruct()
									locCount = locCount + 1
									
									if locCount == 3 then
										break
									end
								end
							end
							
							toBox(insiderFig)
							
							broadcastToAll('인사이더가 시설의 모든 생명 유지 장치를 제거한 후 쓰러졌습니다.', insiderColor)
						end

						locInsiderStory.removeTag(t)
						
					elseif t == 'insiderEffectPlayerPhaseLanderTakesOff' then
						
						if shuttleFigure != nil and insiderCard != nil then
							shuttleFigure.setPositionSmooth(insiderCard.getPosition() + Vector(0,6,0.76), false, false)
							onObjectPickUp(pColor, shuttleFigure)
							
							Wait.time(function()
								onObjectDrop(pColor, shuttleFigure)
								shuttleFigure.setLock(false)
							end,7)
							
							locInsiderStory.removeTag(t)
							toBox(insiderDeck)
							insiderStoryGUID = ''
							insiderEnable = false
						end
						
					elseif t == 'insiderEffectRoundInOxyBreakHeavyItems' then
						
						for color, playerRoomGUID in pairs (locPlayerRooms) do
							local locFig = gO(playerInfoTable[color].figureGUID)
							if isInOxygenSection(locFig) then
								local locBoardInOxy = gO(playerInfoTable[color].boardGUID)
								local locHeavies = getTaggedObjAtPos('StartItem', locBoardInOxy.getPosition(), 0, locBoardInOxy.getBounds().size, nil, true)
								
								for _, obj in pairs (locHeavies) do
									local locMalfFound = false
									for _, malfunctionToken in pairs (locMalfunctions) do
										if distanceMath(obj.getPosition(), malfunctionToken.getPosition()) < 1 then
											locMalfFound = true
											break
										end
									end
									
									if not locMalfFound then
										placeMalfunction(obj.getPosition() + Vector(0,1,0))
										broadcastToAll('플레이어 ' .. color .. '의 무거운 아이템이 파손되었습니다.', insiderColor) 
									end
								end
							end
						end
						
					elseif t == 'insiderEffectRoundInsiderAloneIntruder' then
					
						if insiderFig != nil then
							
							local locIntruderFound = false
							local locPlayerFound = false
							
							for _, roomTile in pairs (locRooms) do
								local locRoomPos2 = roomTile.getPosition()
								if distanceMath(locRoomPos2, insiderFig.getPosition()) < tileImportedSize.x then
									for _, intruder in pairs (locIntruders) do
										if distanceMath(locRoomPos2, intruder.getPosition()) < tileImportedSize.x*0.5 then
											locIntruderFound = true
											break
										end
									end
									
									for _, xyrian in pairs (locXyrians) do
										if distanceMath(locRoomPos2, xyrian.getPosition()) < tileImportedSize.x*0.5 then
											locIntruderFound = true
											break
										end									
									end
									
									if locIntruderFound then
										for color, playerRoomGUID in pairs (locPlayerRooms) do
											if playerRoomGUID == roomTile.getGUID() then
												locPlayerFound = true
												break
											end
										end
									end
									break
								end
							end
							
							if locIntruderFound and not locPlayerFound then
								local locTmp = insiderFig
								toBox(locTmp) --???
								insiderFig = nil
								toBox(insiderDeck)
								insiderStoryGUID = ''
								insiderEnable = false
								
								for _, obj in pairs (getAllObjects()) do
									if obj.getName() == 'Egg' then
										if obj.getPosition().z > 1.9 and obj.getPosition().z < 14.58 then
											obj.destruct()
											break
										end
									end
								end
								broadcastToAll('야수와 단둘이 남겨진 인사이더가 잔인하게 찢겨 사망했습니다.', insiderColor)
							end
						end
					
					elseif t == 'insiderEffectRoundInsiderAttackIntruders' then
					
						if insiderFig != nil then
							local locInsiderPos = insiderFig.getPosition()
							local locInsiderRoom = nil
							local locAttacked = false
							local locInsiderRoomPos = nil
							local locDelay = 1
							
							for _, roomTile in pairs (locRooms) do
								if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
									locInsiderRoom = roomTile
									locInsiderRoomPos = roomTile.getPosition()
									break
								end
							end
							
							
							
							for _, intruder in pairs (locIntruders) do
								local locDist = distanceMath(intruder.getPosition(), locInsiderRoomPos)
								local locRoomParam = nil
								if locDist < tileImportedSize.x *1.5 then
									locAttacked = true
									local w = locWait
									locWait = locWait + locDelay
									locDelay = math.max(0.08,locDelay*0.7)
									
									if locDist < tileImportedSize.x * 0.5 then
										locRoomParam = locInsiderRoom
									end
									
									Wait.time(function()
										playsounds(-1)
										critOnIntruder(intruder, locRoomParam, 'insider')
									end, w)
								end
							end
							
							for _, xyrian in pairs (locXyrians) do
								if distanceMath(xyrian.getPosition(), locInsiderRoomPos) < tileImportedSize.x *0.5 then
									locAttacked = true
									local w = locWait
									locWait = locWait + locDelay
									locDelay = math.max(0.08,locDelay*0.7)
									Wait.time(function()
										playsounds(-1)
										playsounds(math.random(90,91))
										critOnXyrian(xyrian)
									end, w)
								end
							end
							
							if not locAttacked and (#locIntruders > 0 or #locXyrians > 0) then
								local locIntruderRooms = {}
								
								for _, intruder in pairs (locIntruders) do
									if intruder != nil then
										for _, roomTile in pairs (locRooms) do
											if distanceMath(intruder.getPosition(), roomTile.getPosition()) < tileImportedSize.x*1.5 then
												table.insert(locIntruderRooms, roomTile.getGUID())
												break
											end
										end
									end
								end
								
								for _, xyrian in pairs (locXyrians) do
									if xyrian != nil then
										for _, roomTile in pairs (locRooms) do
											if distanceMath(xyrian.getPosition(), roomTile.getPosition()) < tileImportedSize.x*0.5 then
												table.insert(locIntruderRooms, roomTile.getGUID())
												break
											end
										end
									end
								end
								
								autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {}, locIntruderRooms)
								
								Wait.time(function()
									local locWait2 = 0
									local locDelay2 = 1
									locInsiderPos = insiderFig.getPosition()
									
									for _, roomTile in pairs (locRooms) do
										if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
											locInsiderRoom = roomTile
											locInsiderRoomPos = roomTile.getPosition()
											break
										end
									end
									
									
									
									for _, intruder in pairs (locIntruders) do
										if intruder != nil then
											local locDist = distanceMath(intruder.getPosition(), locInsiderRoomPos)
											local locRoomParam = nil
											if locDist < tileImportedSize.x *1.5 then
												locAttacked = true
												local w2 = locWait2
												locWait2 = locWait2 + locDelay2
												locDelay2 = math.max(0.08,locDelay2*0.7)
												
												if locDist < tileImportedSize.x * 0.5 then
													locRoomParam = locInsiderRoom
												end
												
												Wait.time(function()
													playsounds(-1)
													critOnIntruder(intruder, locRoomParam, 'insider')
												end, w2)
											end
										end
									end

									for _, xyrian in pairs (locXyrians) do
										if xyrian != nil then
											if distanceMath(xyrian.getPosition(), locInsiderRoomPos) < tileImportedSize.x *0.5 then
												local w = locWait2
												locWait2 = locWait2 + locDelay2
												locDelay2 = math.max(0.08,locDelay2*0.7)
												Wait.time(function()
													playsounds(-1)
													playsounds(math.random(90,91))
													critOnXyrian(xyrian)
												end, w)
											end
										end
									end
								end, 0.4+locWait)
							end
						end
					
					elseif t == 'insiderEffectRoundInsiderHostileAttackClosestChar' then
						
						if insiderFig != nil then
							
							------------Copy paste from slasher robot neoflesh event
							local locInsiderRoom = nil
							local locInsiderRoomGUID = ''
							local locInsiderPos = insiderFig.getPosition()
							local locInsiderWithPlayer = false
							rolldice('purple', math.random(1,6))
							
							broadcastToAll('인사이더가 가장 가까운 캐릭터를 추격하고 있습니다!', lifeformColor)
							
							local locHealthMsg = '내부자가 체력을 ' .. purpleOneroll .. ' 만큼 깎습니다. 대상: 플레이어 '
							
							for _, roomTile in pairs (locRooms) do
								if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
									locInsiderRoom = roomTile
									locInsiderRoomGUID = roomTile.getGUID()
									break
								end
							end

							for color, playerRoomGUID in pairs (locPlayerRooms) do
								if playerRoomGUID == locInsiderRoomGUID then
									locInsiderWithPlayer = true
									for i = 1, purpleOneroll do
										loseHealth(color)
									end
									broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
									local w = locWait
									locWait = locWait + 0.4
									Wait.time(function()
										playsounds(math.random(90,91))
									end, w)
								end
							end
							
							
							
							if not locInsiderWithPlayer then
								autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {})
								
								Wait.time(function()
									locInsiderPos = insiderFig.getPosition()
									for _, roomTile in pairs (locRooms) do
										if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
											locInsiderRoom = roomTile
											locInsiderRoomGUID = roomTile.getGUID()
											break
										end
									end
									
									for color, playerRoomGUID in pairs (locPlayerRooms) do
										if playerRoomGUID == locInsiderRoomGUID then
											locInsiderWithPlayer = true
											for i = 1, purpleOneroll do
												loseHealth(color)
											end
											broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
											local w = locWait
											locWait = locWait + 0.4
											Wait.time(function()
												playsounds(math.random(90,91))
											end, w)
										end
									end
									
									if not locInsiderWithPlayer then
										autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {})
										
										Wait.time(function()
											locInsiderPos = insiderFig.getPosition()
											for _, roomTile in pairs (locRooms) do
												if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
													locInsiderRoom = roomTile
													locInsiderRoomGUID = roomTile.getGUID()
													break
												end
											end
											
											for color, playerRoomGUID in pairs (locPlayerRooms) do
												if playerRoomGUID == locInsiderRoomGUID then
													locInsiderWithPlayer = true
													for i = 1, purpleOneroll do
														loseHealth(color)
													end
													broadcastToAll(locHealthMsg .. color .. '.', lifeformColor)
													local w = locWait
													locWait = locWait + 0.4
													Wait.time(function()
														playsounds(math.random(90,91))
													end, w)
												end
											end
										end, 1) 
									end
								end, 1) 
							end
							--------------
						end
						
					elseif t == 'insiderEffectRoundInsiderHostileHeal' then
					
						if insiderFig != nil then
							insiderFig.setVar("count", 0)
							insiderFig.call("updateDisplay")
							
							broadcastToAll("인사이더가 스스로 치유했습니다.", insiderColor)
						end
						
					elseif t == 'insiderEffectRoundInsiderNotAloneMoveHibernatorium' then
						if insiderFig != nil then
							local locInsiderAlone = true
							local locInsiderRoom = nil
							local locInsiderPos = insiderFig.getPosition()
							
							for _, roomTile in pairs (locRooms) do
								local locRoomTilePos = roomTile.getPosition()
							
								if distanceMath(locRoomTilePos, locInsiderPos) < tileImportedSize.x then
									locInsiderRoom = roomTile
									for _, intruder in pairs (locIntruders) do
										if distanceMath(locRoomTilePos, intruder.getPosition()) < tileImportedSize.x * 0.5 then
											locInsiderAlone = false
											break
										end
									end
									
									if locInsiderAlone and locInsiderRoom != nil then
										local locRoomTileGUID = locInsiderRoom.getGUID()
										for color, playerRoomGUID in pairs (locPlayerRooms) do
											if playerRoomGUID == locRoomTileGUID then
												locInsiderAlone = false
												break
											end
										end
										
										if locInsiderAlone then
											for _, xyrian in pairs (locXyrians) do
												if distanceMath(locRoomTilePos, xyrian.getPosition()) < tileImportedSize.x then
													locInsiderAlone = false
													break
												end
											end
										end
									end
									break
								end
							end
							
							
							if not locInsiderAlone then
								autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {}, {hiddenRoom.getGUID()})
							end
						end
						
					elseif t == 'insiderEffectRoundInsiderRunToLander' then
						if insiderFig != nil and shuttleFigure != nil then
							
							local locLanderRoom = landingZone
							local locInsiderRoom = nil
							local locLanderPos = shuttleFigure.getPosition()
							local locInsiderPos = insiderFig.getPosition()
							
							for _, roomTile in pairs (locRooms) do
							
								if locLanderRoom == landingZone then
									if distanceMath(roomTile.getPosition(), locLanderPos) < tileImportedSize.x then
										locLanderRoom = roomTile
									end
								end
								if locInsiderRoom == nil then
									if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
										locInsiderRoom = roomTile
									end
								end
								if locLanderRoom != landingZone and locInsiderRoom != nil then
									break
								end
							end
							
							autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {}, {locLanderRoom.getGUID()}, locDoorsDestroyed)
							
							local locLanderReached = false
							Wait.time(function()
								locInsiderPos = insiderFig.getPosition()
								
								if distanceMath(locInsiderPos, locLanderRoom.getPosition()) < tileImportedSize.x then
									locLanderReached = true
								else
									for _, roomTile in pairs (locRooms) do
										if distanceMath(roomTile.getPosition(), locInsiderPos) < tileImportedSize.x then
											locInsiderRoom = roomTile
											break
										end
									end
									
									autoMoveToGoal({locInsiderRoom}, {{insiderFig}}, {}, locDoors, {}, {locLanderRoom.getGUID()}, locDoorsDestroyed)
									
									Wait.time(function()
										if distanceMath(insiderFig.getPosition(), locLanderRoom.getPosition()) < tileImportedSize.x then
											locLanderReached = true
										end
									end, 0.3)
								end
							end, 0.3)
							
							Wait.time(function()
								if locLanderReached then
									insiderFig.setLock(true)
									shuttleFigure.setLock(true)
									
									insiderFig.setPositionSmooth(shuttleFigure.getPosition() + Vector(0,0.07,0), false, true)
									insiderFig.setRotation({0,0,0})
									
									Wait.time(function() shuttleFigure.addAttachment(insiderFig) end, 1)
									locInsiderStory.removeTag(t)
									locInsiderStory.addTag('insiderEffectPlayerPhaseLanderTakesOff')
								end
							end,1)
						
						end
					
					elseif t == 'insiderEffectRoundInsiderShootBurst' then
					
						if insiderFig != nil then
							if isInsiderFriendlyAlive then
								local locInsiderRoom = nil
								local locInsiderRoomPos = nil
								local locInsiderPos = insiderFig.getPosition()
								local locShootTargets = {}
								local locBurstTargets = {}
								local locBurstExpected = false
								local locInsiderRoomDiameter = 1
								
								for _, roomTile in pairs (locRooms) do
									locInsiderRoomDiameter = returnRoomDiameter(roomTile)
									
									if distanceMath(roomTile.getPosition(), locInsiderPos) < locInsiderRoomDiameter then
										locInsiderRoom = roomTile
										locInsiderRoomPos = roomTile.getPosition()
										
										break
									end
								end
								
								if locInsiderRoom != nil then
									for _, xyrian in pairs (locXyrians) do
										if distanceMath(xyrian.getPosition(), locInsiderRoomPos) < locInsiderRoomDiameter then
											table.insert(locShootTargets, xyrian)
										end
									end
									
									for _, intruder in pairs (locIntruders) do
										if distanceMath(intruder.getPosition(), locInsiderRoomPos) < locInsiderRoomDiameter*0.506 then
											table.insert(locShootTargets, intruder)
										end
									end
									
									for _, corridorGUID in pairs (RoomsMap[locInsiderRoom.getGUID()][2]) do
										local corridorTile = gO(corridorGUID)
										
										local locCorPos = corridorTile.getPosition()
										local locCorZVector = rotateVectorAboutY({0,0,corridorImportedSize.z*0.5}, corridorTile.getRotation().y)
										
										for _, intruder in pairs (locIntruders) do
											local locIntrPos = intruder.getPosition()
											if distanceMath(locIntrPos, locCorPos) <= corridorImportedSize.x * 0.5 
											and math.abs(dotMath(locIntrPos-locCorPos, locCorZVector)) <= corridorImportedSize.z *0.6 then

												if locBurstTargets[corridorGUID] == nil then
													locBurstTargets[corridorGUID] = {{}, corridorTile.getGMNotes()}
												end
												table.insert(locBurstTargets[corridorGUID][1], intruder)
												locBurstExpected = true
											end
										end
									end
									
									
									-----shootStart
									local locTwitchlingBuff = false
									if lifeforms == 'Neoflesh' then
										locTwitchlingBuff = getTaggedObjAtPos('twitchlingBuff', {20,1.7,15.71}, 3, {0.5,9,18})
										
										if locTwitchlingBuff != nil then
											local locRotZ = locTwitchlingBuff.getRotation().z
											locTwitchlingBuff = not (locRotZ > 170 and locRotZ < 190)
										else
											locTwitchlingBuff = false
										end
									end
									
									
									for _, shootTarget in pairs (locShootTargets) do
										shootingState = 1
										if shootTarget.hasTag('healthCount') then
											local locEnGM = shootTarget.getGMNotes()
											
											local screamSound = math.random(35,40)
											
											if lifeforms == 'Neoflesh' and locEnGM != 'xyrian' and locEnGM != 'breeder' then
												local locSoundTable = {}
												if locEnGM == 'queen' then
													for i = 1, 7 do
														table.insert(locSoundTable, 199 + i)
													end
												
												elseif locEnGM == 'slasher' then
													for i = 1, 2 do
														table.insert(locSoundTable, 235 + i)
													end
														
												elseif locEnGM == 'larvae' then
													for i = 1, 3 do
														table.insert(locSoundTable, 215 + i)
													end
														
												elseif math.random() > 0.4 then
													newSeed()
													for i = 1, 5 do
														table.insert(locSoundTable, 221 + i)
													end
													
												else
													if locEnGM == 'crawlmine' then
														for i = 1, 2 do
															table.insert(locSoundTable, 208 + i)
														end
														
													elseif locEnGM == 'ironclad' then
														table.insert(locSoundTable, 213)
													else
														for i = 1, 5 do
															table.insert(locSoundTable, 221 + i)
														end
													end
												end
												
												screamSound = locSoundTable[math.random(1, #locSoundTable)]
											end
											
											local locCount = shootTarget.getVar("count") + 1
											local w = locWait
											locWait = locWait + 0.25
											Wait.time(function()

												rolldice('red', math.random(1,8))
												local locRedResult = redOneroll
												broadcastToAll('인사이더가 사격하여 ' .. redOne .. '.', {1,0,0})
												
												if ((locCount >= locRedResult or (shootTarget.getGMNotes() == 'larvae' and not locTwitchlingBuff) or (locEnGM == 'creeper' and lifeforms == 'Carnomorph')) and locRedResult != 7 )
												or locRedResult == 8 then
													
													playsounds(-1)
													if shootTarget.getGMNotes() == 'xyrian' then
														playsounds(-1)
														playsounds(math.random(90,91))
														critOnXyrian(shootTarget)
													else
														critOnIntruder(shootTarget, locInsiderRoom, 'insider')
													end
												else
													shootTarget.setVar("count", locCount)
													shootTarget.call("updateDisplay")
													playsounds(-1)
													playsounds(screamSound)
													playsounds(math.random(80,83))
												end
											end, w)
										end
									end
									
									---------Burst start (only if autoBurst; it is inspired from the player burst script but simplified for insider)
									if autoBurst and locBurstExpected then
										shootingState = 2
										local locIroncladBuff = false
										if lifeforms == 'Neoflesh' then									
											locIroncladBuff = ironcladBuffCheck()
										end
										
										local locLastCorGUID = ''
										local locQueens = {}
										local locBreeders = {}
										local locAdults = {}
										local locIronclads = {}
										local locFirespitters = {}
										local locSlashers = {}
										local locCrawlmines = {}
										local locCreepers = {}
										local locLarvaes = {}
										local locAllTables = {}
										local locEnTargets = {}
										
										for corridorGUID, element in pairs (locBurstTargets) do
											
											local burstTargetList = element[1]
											
											locLastCorGUID = corridorGUID
											
											locQueens = {}
											locBreeders = {}
											locAdults = {}
											locIronclads = {}
											locFirespitters = {}
											locSlashers = {}
											locCrawlmines = {}
											locCreepers = {}
											locLarvaes = {}
											locAllTables = {}
											locEnTargets = {}
											
											for _, burstTarget in pairs (burstTargetList) do

												
												local locIGM = burstTarget.getGMNotes()
												local locT = nil
												if locIGM == 'queen' then
													locT = locQueens
												elseif locIGM == 'breeder' then
													locT = locBreeders
												elseif locIGM == 'adult' then
													locT = locAdults
												elseif locIGM == 'ironclad' then
													locT = locIronclads
													
												elseif locIGM == 'firespitter' then
													locT = locFirespitters											
												elseif locIGM == 'slasher' then
													locT = locSlashers
												elseif locIGM == 'crawlmine' then
													locT = locCrawlmines
												elseif locIGM == 'creeper' then
													locT = locCreepers
												elseif locIGM == 'larvae' then
													locT = locLarvaes
												end
												
												if locT != nil then
													table.insert(locT, burstTarget)
													if locIGM != 'queen' then
														burstTarget.setVar("count", 0)
														burstTarget.call("updateDisplay")
													end
												end
											end
											
											if autoBurstBig then
												locAllTables[1] = locQueens
												locAllTables[2] = locBreeders
												locAllTables[3] = locAdults
												locAllTables[4] = locSlashers
												locAllTables[5] = locCrawlmines
												locAllTables[6] = locIronclads
												locAllTables[7] = locFirespitters
												locAllTables[8] = locCreepers
												locAllTables[9] = locLarvaes
												
											else
												locAllTables[1] = locLarvaes
												locAllTables[2] = locCreepers
												locAllTables[3] = locFirespitters
												locAllTables[4] = locIronclads
												locAllTables[5] = locCrawlmines
												locAllTables[6] = locSlashers
												locAllTables[7] = locAdults
												locAllTables[8] = locBreeders
												locAllTables[9] = locQueens
											end
											if lifeforms == 'Neoflesh' and locIroncladBuff then
												if autoBurstBig then
													table.remove(locAllTables,6)
												else
													table.remove(locAllTables,3)
												end
												table.insert(locAllTables,1, locIronclads)
											end
											
											for _, intrTbl in pairs (locAllTables) do
												for _, intruder in pairs(intrTbl) do
													table.insert(locEnTargets, intruder)
												end
											end
											
											local locSize = #locBurstTargets[locLastCorGUID][1]
											
											for i = 1, locSize do
												locBurstTargets[locLastCorGUID][1][i] = locEnTargets[i]
											end	
											

											
										end --sort End
														
										local locQueenMaxHits = 5
										
										if lifeforms == 'Neoflesh' then
											locQueenMaxHits = 11 - (queenBag.getQuantity()*2)
										end
										
										local numberAttacks = 0
										
										for corridorGUID, element in pairs (locBurstTargets) do
										
											local burstTargetList = element[1]
											
											rolldice('purple', math.random(1,6))
											numberAttacks = purpleOneroll
											broadcastToAll('인사이더가 집중사격하여 ' .. purpleOneroll .. '복도 ' .. element[2] .. '.', burstColor)
											
											
											for _, intruder in pairs (burstTargetList) do
												local locEnGM = intruder.getGMNotes()
												
												if numberAttacks > 0 then
													local locScream = math.random(20,22)
													
													if locEnGM == 'queen' then
														local locQueenHitsAvailable = locQueenMaxHits-intruder.getVar("count")
														for i = 1, math.min(numberAttacks, locQueenHitsAvailable) do

															
															locScream = math.random(20,22)
															if lifeforms == 'Neoflesh' then
																locScream = math.random(200,206)
															end

															local w = locWait
															locWait = locWait + 0.25
															Wait.time(function()
																intruder.call("onClick")
																playsounds(-1)
																playsounds(math.random(90,91))
																playsounds(locScream)
																
																Wait.time(function()
																	if intruder.getVar("count") == locQueenMaxHits then
																		Wait.time(function()
																			intruder.setVar("count", 0)
																			intruder.call("updateDisplay")
																		end,1)
																	end
																end, 0.5)
															end,w)
															numberAttacks = numberAttacks - 1
														end

													else
														intruder.setVar("count", 0)
														intruder.call("updateDisplay")
														if locEnGM == 'breeder' or (locEnGM == 'ironclad' and locIroncladBuff) then
															for i = 1, math.min(numberAttacks, 2) do
			
																
																locScream = math.random(20,22)
																if lifeforms == 'Neoflesh' then
																	locScream = 213
																end

																local w = locWait
																locWait = locWait + 0.25
																Wait.time(function()
																	playsounds(-1)
																	if i == 2 then
																		critOnIntruder(intruder, nil, 'insider')
																	else
																		playsounds(math.random(90,91))
																		playsounds(locScream)
																	end
																	intruder.call("onClick")
																end,w)
																
																numberAttacks = numberAttacks - 1
															end
															
														else
															if lifeforms == 'Neoflesh' then
																if locEnGM == 'slasher' then
																	locScream = math.random(238,239)
																else
																	locScream = math.random(227,233)
																end
															end
															
															local w = locWait
															locWait = locWait + 0.25
															Wait.time(function()
																playsounds(-1)
																playsounds(math.random(90,91))
																playsounds(locScream)
																intruder.call("onClick")
															end, w)
															numberAttacks = numberAttacks - 1
														end
													end
												else
													break
												end
											end
										end
									end
									
									Wait.time(function() shootingState = 0 end, locWait + 1)
								end
							end
						end
									
					
					elseif t == 'insiderEffectRoundOnlyInsiderSectionOxy' then
					
						if insiderFig != nil then
							
							local locSection = getSectionFromXPos(insiderFig.getPosition().x)
							
							for _, obj in pairs (getAllObjects()) do
								if obj.hasTag('LifeSupport') then
									if getSectionFromXPos(obj.getPosition().x) != locSection then
										obj.setState(2)
										broadcastToAll('생명 유지 장치가 비활성화되었습니다.', insiderColor)
									end
								end
							end
							
						end
						
					elseif t == 'insiderEffectRoundShootAllRedRoom' then
							
						
						for _, roomTile in pairs (locRooms) do
							if string.find(roomTile.getDescription(), 'R') != nil then
								local locRoomTileGUID = roomTile.getGUID()
								local locRoomPos = roomTile.getPosition()
								local locRoomDiameter = returnRoomDiameter(roomTile)
								
								for color, playerRoomGUID in pairs (locPlayerRooms) do
									if playerRoomGUID == locRoomTileGUID then
										loseHealth(color)
										loseHealth(color)
										local w = locWait
										locWait = locWait + 0.5
										
										Wait.time(function()
											playsounds(math.random(90,91))
										end, w)
									end
								end
								
								for _, intruder in pairs (locIntruders) do
									if intruder.hasTag("healthCount") then
										if distanceMath(intruder.getPosition(), locRoomPos) < locRoomDiameter * 0.5 then
											local w = locWait
											locWait = locWait + 0.5
											
											if intruder.getVar("count") == 0 then
												intruder.setVar("count", intruder.getVar("count") +2)
												intruder.call("updateDisplay")
												Wait.time(function()
													playsounds(-1)
													playsounds(math.random(90,91))
													
													if lifeforms == 'Neoflesh' then
													
														if locEnGM == 'queen' then
															playsounds(math.random(200,206))
														elseif locEnGM == 'slasher' then
															playsounds(math.random(238,239))
														else
															playsounds(math.random(227,233))
														end
													else
														playsounds(math.random(20,22))
													end
													
												end, w)
											else												
												Wait.Time(function()
													critOnIntruder(intruder, roomTile, 'insider')
												end, w)
											end
										end
									end
								end
								
								for _, xyrian in pairs (locXyrians) do
									if distanceMath(xyrian.getPosition(), locRoomPos) < tileImportedSize.x then
										local w = locWait
										locWait = locWait + 0.5
										
										Wait.time(function()
											playsounds(-1)
											playsounds(math.random(90,91))
										end, w)
										
										if xyrian.getVar("count") == 0 then
											xyrian.setVar("count", xyrian.getVar("count") +2)
											xyrian.call("updateDisplay")
										else												
											Wait.Time(function()
												critOnXyrian(xyrian)
											end, w)
										end
									end
								end

							end
						end
						
						if locWait > 0 then
							broadcastToAll('빨간색 아이템 방의 모든 개체가 사격을 받고 있습니다!', insiderColor)
						end
						
					--elseif t == 'insiderEffectShootSub1' then
						
					end
				end
			end
		end
	end
end

function insiderSequel(sequelCard, inputRoomTile, pColor, cautiousMove, previousRoomPos)
	if not scriptEnabled then
		return true
	end
	
	sequelCard.setLock(true)
	Wait.time(function()
		sequelCard.setLock(false)
		local locPreviousStory = gO(insiderStoryGUID)
		broadcastToAll('새로운 인사이더 스토리 카드가 뽑혔습니다.', insiderColor)
		insiderStoryGUID = sequelCard.getGUID()
		
		if sequelCard.hasTag('insiderMerge') then
			
			locPreviousStory.setRotation({0,180,180})
			
			locPreviousStory.setDescription(locPreviousStory.getDescription()..sequelCard.getDescription())
		
			for _, tag in pairs (sequelCard.getTags()) do
				if string.find(tag, 'insiderExp') != nil or string.find(tag, 'insiderEffect') != nil or string.find(tag, 'insiderSequel') != nil then
					if not locPreviousStory.hasTag(tag) then
						locPreviousStory.addTag(tag)
					end
				end
			end
			
			if #locPreviousStory.getSnapPoints() > 0 then
				sequelCard.setPosition(locPreviousStory.getPosition() - locPreviousStory.getSnapPoints()[1].position + Vector(0,3,0))
			else
				sequelCard.setPosition(sequelCard.getPosition() + Vector(0,0,4))
			end
			
			autoInsider(0, nil, inputRoomTile, pColor, cautiousMove, previousRoomPos)
			insiderStoryGUID = locPreviousStory.getGUID()
		else
			if locPreviousStory != nil then
				locPreviousStory.setPosition(locPreviousStory.getPosition() + Vector(0,4,4))
			end
			
			autoInsider(0, nil, inputRoomTile, pColor, cautiousMove, previousRoomPos)
		end
	end, 1.25) --just to make sure we have encounter in the room if moving there.
end

function autoExplore(exploreCard)
	if not scriptEnabled then
		return true
	end
	
	local locCor = nil
	local locCharacter = nil
	local locPCol = nil
	local locCautiousMove = false
	
	if insiderEnable then
		insiderRecall()
	end
	
	local locInsiderStory = gO(insiderStoryGUID)
	
	local locExploreCharList = {}
	
	local locExploreCorList = {}
	
	for _, obj in pairs(getAllObjects()) do
		if obj.hasTag('characterFig') then
			table.insert(locExploreCharList, obj)
		elseif obj.hasTag('Corridors') then
			table.insert(locExploreCorList, obj)
		end
	end
	
	for _, chara in pairs (locExploreCharList) do
		locCharacter = chara
		
		for _, cor in pairs (locExploreCorList) do
			
			if distanceMath(cor.getPosition(), locCharacter.getPosition()) < corridorImportedSize.x * 0.4 then
				locCor = cor
				local locCharacterGUID = locCharacter.getGUID()
				
				for color, entry in pairs(playerInfoTable) do
					if entry.figureGUID == locCharacterGUID then
						locPCol = color
						local locCharRotZ = locCharacter.getRotation().z
						if locCharRotZ > 150 and locCharRotZ < 210 then
							locCautiousMove = true
						end
						break
					end
				end
				
				if insiderEnable then
					if locCharacter == insiderFig then
						locPCol = 'insider'
					end
				end
				break
			end
		end
		if locCor != nil then
			break
		end
	end
	
	if locCor != nil then
		playerMoveStartRoomGUID = nil
		local locWait = 2
		local locDeg = locCor.getRotation().y
		local locLengthToRoom = (corridorImportedSize.x + tileImportedSize.x) *0.5
		local locPass = false
		for i = 1, 2 do
			if locPass then
				break
			end
			
			local sign = 1 --je me rappel plus pourquoi j'ai fait ça... peut être pour les couloirs inversés ??
			if i == 2 then
				sign = -1
			end
			
			local locHibernOffset = Vector(0,0,0)
			local locCorGUID = locCor.getGUID()
			
			for j = 1, #RoomsMap[hiddenRoom.getGUID()][2] do
				local corridorGUID = RoomsMap[hiddenRoom.getGUID()][2][j]
				if corridorGUID == locCorGUID then
					if j == 1 or j == 4 then
						locHibernOffset = Vector(-0.39,0,0)
					elseif j == 2 then
						locHibernOffset = Vector(-0.30,0,0.08)
					elseif j == 3 then
						locHibernOffset = Vector(-0.30,0,-0.08)
					end
					break
					
				end
			end
			
			local locRoomRotZ = 0
			local locOffY = -0.02
			
			if insiderEnable then
				if locInsiderStory != nil then
					if locInsiderStory.getGMNotes() == '06' then --06 being the last drilling story
						if insiderFig != nil then
							if locCharacter == insiderFig then
								locRoomRotZ = 180
								locOffY = 0.14
							end
						end
					end
				end
			end
			
			local locNextRoomPos = rotateVectorAboutY(Vector(sign,1,sign)*(Vector(locLengthToRoom,0,0)+locHibernOffset),locDeg) + locCor.getPosition() + Vector(0,locOffY,0)
			
			local locPreviousRoomPos = 2*locCor.getPosition() - locNextRoomPos + Vector(0,1,0)
			local locNextRoom = nil
			
			for _, entry2 in pairs(shapeCast(locNextRoomPos, {1,15,1},  locCor.getRotation())) do
				if not entry2.hasTag('room') and entry2.getPosition() == Vector(0,-9,0) then
					local locRoomBag = nil
					locPass = true
					
					if exploreCard.hasTag('ExploreRoomI') then
					
						local locSection = getSectionFromXPos(locNextRoomPos.x)
						
						if locSection == 'A' then
							locRoomBag = roomIABag
						
						elseif locSection == 'B' then
							locRoomBag = roomIBBag
							
						elseif locSection == 'C' then
							locRoomBag = roomICBag
						
						end
						
						if locRoomBag.getQuantity() == 0 then
							locRoomBag = roomIIBag
						end
					else
						locRoomBag = roomIIBag
					end
					
					local locExploreInsider = exploreCard.hasTag('ExploreInsider')

					
					
					locRoomBag.takeObject({
						position = locNextRoomPos+Vector(0,0.05,0),
						rotation = {0,180,locRoomRotZ},
						callback_function = function(o)
							locNextRoom = o 
							o.setLock(true)
							o.setRotation({0,180,locRoomRotZ})
							Wait.time(function() o.setPositionSmooth(locNextRoomPos,true,false) end, 2)
							
							RoomsMap[o.getGUID()] = {'room', {locCor.getGUID()}}
							
							if RoomsMap[locCor.getGUID()] != nil then
								table.insert(RoomsMap[locCor.getGUID()][2], o.getGUID())
							else
								RoomsMap[locCor.getGUID()] = {'corridor', {o.getGUID()}}
							end
							
							locCharacter.setPositionSmooth(findSpaceOnTile(locNextRoom),false,true)
							
							
							locCharacter.setRotation({0,locCharacter.getRotation().y,0})
							locCharacter.setLock(false)
							if o.hasTag('computer') and exploreCard.hasTag('ExploreCultist') then
								if breederFBag.getQuantity() > 0 then
									breederFBag.takeObject({
										position = findSpaceOnTile(locNextRoom, nil,true),
										rotation = {0,0,0},
										smooth = false,
										callback_function = function(o2) o2.setLock(true) end,
									})
								end
							end
							
							if locCautiousMove and not o.hasTag('noSecurity') and not o.hasTag('security') then
							
								local locSecPass = true
								
								if useXyrian then
									locSecPass = getTaggedObjAtPos('xyrian', locNextRoomPos, 3, tileImportedSize) == nil
								end
								
								if secureBag.getQuantity() > 0 and locSecPass then
									secureBag.takeObject({
										position = locNextRoomPos+Vector(tileImportedSize.x*0.4, 1, tileImportedSize.z*0.25),
										smooth = false,
									})
								else
									broadcastToAll('보안 토큰이 부족합니다.', {0.5,0.5,0.5})
								end
							end
							
							if xyrianAllegianceToken != nil then
								if xyrianAllegianceToken.getGMNotes() == 'x' then
									xyrianAllegianceToken.setGMNotes('')
									local locXyrPos = findSpaceOnTile(locNextRoom, nil, true)
									xyrianAllegianceToken.setPosition(locNextRoom.getPosition() + Vector(0,0.25,0))
									
									broadcastToAll('자이리안 충성심 토큰이 있는 방에서 자이리안 충성심을 이용할 수 있습니다.', xyrianColor)
									if xyrianFBag.getQuantity() > 0 then
										xyrianFBag.takeObject({
											position = locXyrPos,
											rotation = {0,0,0},
											callback_function = function(o) o.setLock(true) end,
										})
									end
								end
							end
							
							if locCharacter.getName() == 'Exploring Drone' then
								locCharacter.setPositionSmooth({20,1.6,-2.89}, false, false)
								locCharacter.setRotation({0,0,0})
							end
							

							Wait.time(function() --to avoid overlapping doors closing effects and exploration.
								if insiderEnable then
									local locSequelPass = false
									local locSequel = false
									
									if locRoomRotZ != 0 then
										locCharacter.setPositionSmooth(locPreviousRoomPos,false,false)
										locCharacter.setRotation({0,0,0})
									end
									
									if locInsiderStory != nil then
										local locInsiderStoryDesc = locInsiderStory.getDescription()
										local locChapter = string.find(locInsiderStoryDesc, 'd')  --d for discover
										
										if string.find(locInsiderStory.getName(), '/') != nil then --there's only one like that... right ?
											local locStoryRoomCount = 0
											for _, storyRoomObj in pairs (getAllObjects()) do
												local locRName = storyRoomObj.getName()
												if locRName == 'COOLING SYSTEM' or locRName == 'REACTOR' then
													locStoryRoomCount = locStoryRoomCount + 1
													if locStoryRoomCount == 2 then
														locSequelPass = true
														break
													end
												end
											end
										else
											
											if locNextRoom.getName() == locInsiderStory.getName() then
												locSequelPass = true
											end
										end
										
										if locChapter != nil and locSequelPass then
											
											if string.len(locChapter) > 1 then
												locChapter = tonumber(string.sub(locChapter,1,1))
											end
											
											locChapter = string.sub(locInsiderStoryDesc, locChapter+1, locChapter+2)
											
											for _, storyCard in pairs (insiderDeck.getObjects()) do
												if storyCard.gm_notes == locChapter then
													locSequel = true
													
													insiderDeck.takeObject({
														position = insiderDeck.getPosition() + Vector(0,4,4),
														guid = storyCard.guid,
														callback_function = function(o2)
																local locNewDesc = string.gsub(locInsiderStoryDesc, 'd'.. locChapter,'')
																locInsiderStory.setDescription(string.sub(locNewDesc,1,string.len(locNewDesc)))
																insiderSequel(o2, locNextRoom, locPCol, locCautiousMove, locPreviousRoomPos)
															end,
														
													})
													break
												end
											end
										else
											local locTag2 = 'insiderEffectMoveFromInsiderFollow'
											if locInsiderStory.hasTag(locTag2) then
												autoInsider(2, locTag2, nil, locPCol)
											end
										end
									end
									
									
									if locExploreInsider and not locSequel then
										broadcastToAll('인사이더 탐험 카드가 뽑혔습니다.', insiderColor)
										
										local locType = 0
										
										if insiderStoryGUID != '' then
											locType = 1
										end
									
										autoInsider(locType, nil, o, locPCol, locCautiousMove, locPreviousRoomPos)
									end
								end
							end, 2) 
						end,
						smooth = false,
					})
					
					local locExploreCor = {}
					
					local locExploreCorPass = true
					
					if insiderEnable and locInsiderStory != nil then
						locExploreCorPass = not (locInsiderStory.hasTag('insiderEffectExpInsiderJustRoom') and locExploreInsider)
					end
					
					if locExploreCorPass then
						if exploreCard.hasTag('ExploreCorR') then --could be optimised but eeeh. It's only one corridor at a time.
							local N = 0
							if exploreCard.hasTag('ExploreCorRNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorRNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorRNoise3') then
								N = 3
							end
							
							local locCorRPass = true
							
							if insiderEnable and locInsiderStory != nil then
								locCorRPass = not locInsiderStory.hasTag('insiderEffectExpNoRightCorridor')
							end
							
							if locCorRPass then
								if locRoomRotZ != 0 then
									N = 0
								end
								table.insert(locExploreCor, {noise = N, deg = 0})
							end
						end
						
						if exploreCard.hasTag('ExploreCorRD') then
							local N = 0
							if exploreCard.hasTag('ExploreCorRDNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorRDNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorRDNoise3') then
								N = 3
							end
							
							if locRoomRotZ != 0 then
								N = 0
							end
							table.insert(locExploreCor, {noise = N, deg = 60})
						end
						
						
						if exploreCard.hasTag('ExploreCorLD') then
							local N = 0
							if exploreCard.hasTag('ExploreCorLDNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorLDNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorLDNoise3') then
								N = 3
							end
							
							if locRoomRotZ != 0 then
								N = 0
							end

							table.insert(locExploreCor, {noise = N, deg = 120})
						end
						
						
						if exploreCard.hasTag('ExploreCorL') then
							local N = 0
							if exploreCard.hasTag('ExploreCorLNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorLNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorLNoise3') then
								N = 3
							end
							
							if locRoomRotZ != 0 then
								N = 0
							end

							table.insert(locExploreCor, {noise = N, deg = 180})
						end
						
						if exploreCard.hasTag('ExploreCorLU') then
							local N = 0
							if exploreCard.hasTag('ExploreCorLUNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorLUNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorLUNoise3') then
								N = 3
							end
							
							if locRoomRotZ != 0 then
								N = 0
							end

							table.insert(locExploreCor, {noise = N, deg = 240})
						end
						
						if exploreCard.hasTag('ExploreCorRU') then
							local N = 0
							if exploreCard.hasTag('ExploreCorRUNoise') then
								N = 1
							elseif exploreCard.hasTag('ExploreCorRUNoise2') then
								N = 2
							elseif exploreCard.hasTag('ExploreCorRUNoise3') then
								N = 3
							end
							
							if locRoomRotZ != 0 then
								N = 0
							end

							table.insert(locExploreCor, {noise = N, deg = 300})
						end
					end
					
					for _, exploreCorridors in pairs(locExploreCor) do
					
				
						local locExploreCorPos = rotateVectorAboutY(Vector(locLengthToRoom,0,0),exploreCorridors.deg) + locNextRoomPos + Vector(0,0.02,0)
						local locOldCor = (getTaggedObjAtPos('Corridors', locExploreCorPos, 0) != nil)
						
						
						
						
						if not locOldCor then
							local locExploreCorPos2 = rotateVectorAboutY(Vector(locLengthToRoom*2,0,0),exploreCorridors.deg) + locNextRoomPos
							locOldCor = (getTaggedObjAtPos('room', locExploreCorPos2, 0) != nil)
						end
						
						
						local boarderPos = boarderTile.getPosition()
						local boarderBounds = boarderTile.getBounds().size
						
						if not locOldCor
						and (locExploreCorPos.x > (boarderPos.x - boarderBounds.x*0.5*0.77) and locExploreCorPos.x < (boarderPos.x + boarderBounds.x*0.5*0.83))
						and (locExploreCorPos.z > (boarderPos.z - boarderBounds.z*0.5*0.9) and locExploreCorPos.z < (boarderPos.z + boarderBounds.z*0.5*0.73))
						then
							
							corridorBag.takeObject({
								position = locExploreCorPos+Vector(0,0.05,0),
								rotation = {0,exploreCorridors.deg,0},
								callback_function = function(o)
									o.setLock(true)
									o.setRotation({0, o.getRotation().y, 0})
									
									RoomsMap[o.getGUID()] = {'corridor', {locNextRoom.getGUID()}}
									table.insert(RoomsMap[locNextRoom.getGUID()][2], o.getGUID())
									
									Wait.time(function()
										o.setPositionSmooth(locExploreCorPos, true, false)
									end,2) 
									
									if exploreCorridors.noise > 0 then
										Wait.time(function()
											if exploreCorridors.noise == 1 and lifeforms != 'Sangrevores' then
												noiseBag.takeObject({
													position = locExploreCorPos + Vector(0,1,0),
													smooth = false,
												})
											else
												for i = 1, exploreCorridors.noise do
													Wait.time(function()
														noiseBag.takeObject({
															position = findSpaceOnTile(o, nil, true),
															smooth = false,
														})
													end, i*0.25)
												end
											end
										end, 1)
									end
								end,
								smooth = false,
							})
							

						end
						
					end
					
					if exploreCard.hasTag('ExploreFire') and locExploreCorPass and locRoomRotZ == 0 then
						Wait.time(function()
							placeFire(locNextRoomPos + Vector(0.35,0,-1.3))
						end, 1)
					end
					
					if exploreCard.hasTag('ExploreMalfunction') and locExploreCorPass and locRoomRotZ == 0 then
						
						Wait.time(function ()
							if not locNextRoom.hasTag('nest') then
								placeMalfunction(locNextRoomPos + Vector(0,0.5,-1.05))
							end
						end, 1)
					end
					
					if exploreCard.hasTag('ExploreMeat') and locExploreCorPass and locRoomRotZ == 0 then
						Wait.time(function()
							carcassBag.takeObject({
								position = locNextRoomPos + Vector(0,1, 1.05),
							})
						end, 1)
					end
					
					if not locCharacter.hasTag('noEntrance') and locExploreCorPass and locRoomRotZ == 0 then
						if exploreCard.hasTag('ExploreEnc') then
							if playerHasTag('NoExploreEncounter', 0, locCharacter.getGUID(), nil) then
								broadcastToAll('탐험 중 이 캐릭터에게 위험 효과가 무시됩니다.', {1,1,1})
							else
								Wait.time(function()
									encounter(locNextRoom, locPCol)
									if insiderEnable and insiderStoryGUID != '' and locNextRoom != nil then
										insiderSequelMoveCheck(locNextRoom, locPCol, locCautiousMove)
									end
								end, 2)
							end
						end
						
						local locFBagTable = {}
						
						
						
						local locCorCast = getTaggedObjAtPos('healthCount', locCor.getPosition(), 0, locCor.getBounds().size *Vector(0.99,1,0.57) + Vector(0,9,0), locCor.getRotation(), true)
						local locSpaceAvailable = 6
						
						for _, intruder in pairs (locCorCast) do
							if distanceMath(intruder.getPosition(), locCor.getPosition()) < corridorImportedSize.x *0.5 then
								if intruder.getGMNotes() == 'queen' then
									locSpaceAvailable = locSpaceAvailable - 4
								else
									locSpaceAvailable = locSpaceAvailable - 1
								end
							end
						end
						
						local locMaxEnc = math.min(4, math.max(0,locSpaceAvailable))
						
						for _, tag in pairs (exploreCard.getTags()) do
							if tag == 'ExploreEnc2' then
								for i = 1, math.min(2,locMaxEnc) do
									if lifeforms == 'Carnomorph' then
										locFBagTable[i] = creeperFBag
									else
										locFBagTable[i] = adultFBag
									end
								end
							elseif tag == 'ExploreEnc3' then
								for i = 1, math.min(3,locMaxEnc) do
									if lifeforms == 'Carnomorph' then
										locFBagTable[i] = creeperFBag
									else
										locFBagTable[i] = adultFBag
									end
								end
							elseif tag == 'ExploreEnc4' then
								
								for i = 1, math.min(4,locMaxEnc) do
									if lifeforms == 'Carnomorph' then
										locFBagTable[i] = creeperFBag
									else
										locFBagTable[i] = adultFBag
									end
								end
							elseif tag == 'ExploreEnc2Firespitter' then
								for i = 1, math.min(2,locMaxEnc) do
									locFBagTable[i] = firespitterFBag
								end
								if locMaxEnc-2 > 0 then
									locFBagTable[3] = larvaeFBag
								end
							elseif tag == 'ExploreEnc2Ironclad' then
								for i = 1, math.min(2,locMaxEnc) do
									locFBagTable[i] = ironcladFBag
								end
								if locMaxEnc-2 > 0 then
									locFBagTable[3] = larvaeFBag
								end
							elseif tag == 'ExploreEnc2Slasher' then
								for i = 1, math.min(2,locMaxEnc) do
									locFBagTable[i] = adultFBag
								end
								if locMaxEnc-2 > 0 then
									locFBagTable[3] = larvaeFBag
								end
							end
						end
						
						
						if #locFBagTable != 0 then
							
							if lifeforms != 'Sangrevores' then
								for _, noiseEntry in pairs(shapeCast(locCor.getPosition(), corridorImportedSize + Vector(0,5,0), locCor.getRotation())) do
									if noiseEntry.getName() == 'Noise' then
										noiseEntry.destruct()
										break
									end

								end
							end
							
							locWait = locWait + #locFBagTable
							
							local locDirToTile = locNextRoomPos-locPreviousRoomPos
							
							local locDegreeToTile = 90+180+180*math.atan2(locDirToTile[3],locDirToTile[1]*(-1))/3.1415926352
							
							
							for i = 1, #locFBagTable do
								if locFBagTable[i].getQuantity() > 0 then
									locFBagTable[i].takeObject({
										position = locFBagTable[i].getPosition() + Vector(0,6,0),
										rotation = {0,0,0},
										callback_function = function (o)
											o.setLock(true)
											Wait.time(function()
												o.setPositionSmooth(findSpaceOnTile(locCor,nil, true), false, true)
												
												
												if o.hasTag('rot180') then
													o.setRotation({0,locDegreeToTile,0})
												else
													o.setRotation({0,0,0})
												end
											end, (i-1)*0.25+1)
										end,
									})
								end
							end
						end
						
						
						if exploreCard.hasTag('ExploreCloseDoor') or exploreCard.hasTag('ExplorePlaceDoor') then
							
							Wait.time(function()
								if doorBag.getQuantity() > 0 then
									for _, locCorDoor in pairs(shapeCast(locNextRoomPos, tileImportedSize* 1.25 + Vector(0,5,0))) do
										if locCorDoor.hasTag('Corridors') then

											for _, SnapP in pairs(locCorDoor.getSnapPoints()) do
												if SnapP.tags[1] == 'doorSlot' or exploreCard.hasTag('ExplorePlaceDoor') then
													local SnapPos = SnapP.position
													local locScale = locCorDoor.getScale()
													
													local SnapPosWorld = rotateVectorAboutY(SnapPos*locScale, locCorDoor.getRotation().y) + locCorDoor.getPosition()
													local roomDoorDistance = distanceMath(locNextRoom.getPosition(), SnapPosWorld)

													if roomDoorDistance < (tileImportedSize.x) then

														
														doorBag.takeObject({
															position = SnapPosWorld + Vector(0,1,0),
															rotation = {0, locCorDoor.getRotation().y + 90, 0},
															callback_function = function(o)
																o.setLock(true)
																o.setPositionSmooth(SnapPosWorld, false, false)
															end,
															smooth = false,
														})
														break
													end
												end
											end
										end
									end
								end
							end,2)
						
						end
						
						if exploreCard.hasTag('ExploreNoiseRoll') and exploreNoiseEnable then
							Wait.time(function() autoNoise(locCharacter.getPosition(), locCharacter, true) end, #locFBagTable*0.25+2.25)--+1.25
						end
						
					end
					
					if exploreCard.hasTag('ExploreDelete') then
						broadcastToAll(removeWarning,lifeformColor)
						exploreCard.drop()
						exploreCard.setPosition({-27,3,-0.41})
						exploreCard.setRotation({0,180,0})
					end
					
				break	
				end			
			
			end
			
			if hibUnexplored != nil then
				if distanceMath(hibUnexplored.getPosition(), locNextRoomPos) < corridorImportedSize.x * 2.235294 then
					hibExplore(hibUnexplored)
				end
			end
			
			if not locCautiousMove and lifeforms == 'Sangrevores' and not locCharacter.hasTag('noEntrance') then
				Wait.time(function()
					local locShadows = {}
					locShadows = getTaggedObjAtPos('noise', locCor.getPosition(), 3, locCor.getBounds().size *Vector(0.99,1,0.57) + Vector(0,9,0), locCor.getRotation(), true)
					
					if locShadows[1] != nil then
						local locShadowAmount = #locShadows
						for _, noiseToken in pairs(locShadows) do
							noiseToken.setPosition({50,0,0})
							noiseToken.destruct()
						end
						Wait.time(function()
							local locNextRoomTmp = locNextRoom
							shadowBag.takeObject({
								position = shadowBag.getPosition() + Vector(0,3,4),
								rotation = {0,180,0},
								smooth = false,
								callback_function = function(o) o.setLock(true) autoShadow(o, locShadowAmount, locCor, locNextRoomTmp, locPCol, true) end,
							})
						end, 0.5)
					end
				end, locWait)
				
			end
		end
	end
end

function getSectionFromXPos(XPos)
	if not scriptEnabled then
		return true
	end
	
	local locSectionDistance = boarderTile.getBounds().size.x/5.965474
	
	if XPos < (locSectionDistance *(-1)) then
		return 'A'
	elseif XPos > locSectionDistance then
		return 'C'
	else
		return 'B'
	end
						
end

function distanceMath(pos1, pos2)
	if not scriptEnabled then
		return true
	end
	
	local p1 = pos1 * Vector(1,0,1)
	local p2 = pos2 * Vector(1,0,1)
	return math.sqrt(dotMath(p1-p2, p1-p2))
end

function playerHasTag(customTag, stringType, characterFigureGUID, pColor)
	if not scriptEnabled then
		return true
	end
	
	local locBoard = nil
	local locStringType = 0
	
	if stringType != nil then
		locStringType = stringType
	end
	
	if characterFigureGUID != nil then
		for color, entry in pairs(playerInfoTable) do
			if characterFigureGUID == entry.figureGUID then
				locBoard = gO(entry.boardGUID)
				break
			end
		end
		
		if insiderEnable and locBoard == nil then
			insiderRecall()
			if insiderCard != nil then
				if insiderCard.getGMNotes() == 'active' and insiderFig != nil then
					if characterFigureGUID == insiderFig.getGUID() and insiderFig.hasTag('characterFig') then
						locBoard = insiderCard
					end
				end
			end
		end
	else
		if pColor != 'insider' and pColor != nil then
			locBoard = gO(playerInfoTable[pColor].boardGUID)
		else
			locBoard = insiderCard
		end
	end
	
	
	if locBoard != nil then
		return (getTaggedObjAtPos(customTag, locBoard.getPosition(), locStringType, locBoard.getBounds().size) != nil)
	else
		return false
	end

end

function insiderRecall()
	if not scriptEnabled then
		return true
	end
	
	insiderDeck = gO('1c3be3')
	insiderFig = gO('b8323a')
	insiderCard = gO('04e7a0')
	insiderHealth = gO('03446d')
	insiderRunaway = gO('1b11a3')
end

function placeFire(pos, check)
	if not scriptEnabled then
		return true
	end
	
	local locNoFire = true
	
	if check != nil then
		if check then
			locNoFire = getTaggedObjAtPos('fire', pos, 3, tileImportedSize) == nil
		end
	end
	
	if locNoFire then
		if fireBag.getQuantity() > 0 then
			fireBag.takeObject({position = pos + Vector(0,1,0), smooth = false})
		else
			broadcastToAll(fireWarning, {0.90, 0.39, 0.11})	
		end
	end
end

function placeMalfunction(pos)
	if not scriptEnabled then
		return true
	end
	
	if malfunctionBag.getQuantity() > 0 then
		malfunctionBag.takeObject({position = {pos[1], pos[2] + 1, pos[3]}, smooth = false})
	else
		broadcastToAll(malfunctionWarning, {0.50, 0.50, 0.50})
		placeFire(pos)
	end
end

function playbombticks (ticknumbers)
	if not scriptEnabled then
		return true
	end
	if not sound3Used then
		for i=1, ticknumbers do
			Wait.time(function() playsounds(182) end, soundDuration[183]*1.5*(i-1))
		end
	end
end



--shuffles the table
function shuffleTable(tbl)
	if not scriptEnabled then
		return true
	end
	
    for i = #tbl, 2, -1 do
      local j = math.random(i)
      tbl[i], tbl[j] = tbl[j], tbl[i]
    end
    return tbl
end

function newSeed(offset)
	
	local locOff = 0
	
	if offset != nil then
		locOff = offset
	end
	
	math.randomseed(os.time({year = 2005+8-seedYearOffset, month=os.date("%m"),day=os.date("%d"), hour=os.date("%H"), min=os.date("%M"), sec=os.date("%S")}) + locOff)
	
end

function none() end
function none2(obj) obj.clearButtons() end
