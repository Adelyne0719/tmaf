monsterImageList = {}
monsterGUID = "d3d7fe"
myexp = ""

-- [최적화] 하드코딩된 이미지 데이터 (로딩 속도 0초)
monsterImageData = {
    ["Vyraxen"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2493386495702049481/87AA8EDE7D1A00DCE6B425FCE9D63ACA8C5458D5/", mColor="rgba(0.799457967281342,0.0374504327774048,0.0374504327774048,1)", order=1},
    ["Kharja"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719242985/217BFC3CFBA2F7B9E34DE9E7D0089C55B0413572/", mColor="rgba(0.799457967281342,0.0374504327774048,0.0374504327774048,1)", order=2},
    ["Toramat"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2514782313678839863/8E69403E0E1B085D4C889E14DDB4F324C4C7985E/", mColor="rgba(0.480836153030396,0.350900828838348,0.104710198938847,1)", order=3},
    ["Dygorax"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2499015458373590704/47D7C91715BD68B4AF016D9B1D278B7565F1A059/", mColor="rgba(0.615686297416687,0.482352912425995,0.329411715269089,1)", order=4},
    ["Korowon"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2499015458373598155/A9B844BB26DAD85ED8DE6C86376125E1CBC67231/", mColor="rgba(0.0472396016120911,0.75709742307663,0.83575314283371,1)", order=5},
    ["Orouxen"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719266083/4A1148EEBB262528C7367862775028404399381A/", mColor="rgba(0.0472396686673164,0.75709742307663,0.83575314283371,1)", order=6},
    ["Morkraas"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719259322/F249ECA1A9CF56FB07E3AC8ECE9771B0FF81EF20/", mColor="rgba(0.352007567882538,0.101960547268391,0.478431284427643,1)", order=7},
    ["Felaxir"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2499015458373595127/61A241142529BEAB8F9656955CC2815F5E6E5B52/", mColor="rgba(0.328682124614716,0.101960428059101,0.478431284427643,1)", order=8},
    ["Ozew"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2514782313678840067/F8F5A7F42A215F16274DF005D48D1845F2742BAD/", mColor="rgba(0.862452983856201,1,0,1)", order=9},
    ["Jekoros"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719274333/D880ADEC6957650A846C883FE5463D81ACDCFE4D/", mColor="rgba(0.862452983856201,1,0,1)", order=10},
    ["Hurom"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719278214/6108FA7400B7E15804EDFB44349162FD803A5A23/", mColor="rgba(0.818815410137177,0.818815410137177,0.818815410137177,1)", order=11},
    ["Tarragua"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719279685/F9FA5CE581B59347570FDA6AD9B5940B727710BA/", mColor="rgba(0.818815410137177,0.818815410137177,0.818815410137177,1)", order=12},
    ["Hydar"] = {img="https://steamusercontent-a.akamaihd.net/ugc/10802865489012418478/0F001C8CE630EB9229AFC47797F8F8384A470B6A/", mColor="rgba(0.276862680912018,0.751064836978912,0,1)", order=13},
    ["Reikal"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719294528/A6DCFE9FF381687B7A7BF58A5B162EF8AA5F262A/", mColor="rgba(0.276862740516663,0.751064836978912,0,1)", order=14},
    ["Pazis"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719287145/922C926BDDC8A012D3C08D6D041B2BED0487C928/", mColor="rgba(1,0.838290512561798,0,1)", order=15},
    ["Nagarjas"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2499015458373603150/480362FB85780C4451316D6F28942D0CE033F94C/", mColor="rgba(1,0.838290512561798,0,1)", order=16},
    ["Sirkaaj"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719301689/306C61845CA107FD60A9C498BE6E0951DBAC374A/", mColor="rgba(1,1,1,1)", order=17},
    ["Mamuraak"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719300585/D244A36D7905F803CEB0AAB89C6C2CF3F1AED903/", mColor="rgba(1,1,1,1)", order=18},
    ["Zekath"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719317394/9CB80A89613E990067B1229AA58CAC3267FE5FDA/", mColor="rgba(0.11869765073061,0.0739774778485298,0.141308188438416,1)", order=19},
    ["Zekalith"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719320465/AC7D55B1DCC155BADA1D740F201C4690D38FF2DA/", mColor="rgba(0.118697680532932,0.0739775076508522,0.141308218240738,1)", order=20},
    ["Taraska"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719311270/F8CA8EDFE4DDBC1129C31F4022E7C6067752201E/", mColor="rgba(0.11869765073061,0.0739774778485298,0.141308188438416,1)", order=21},
    ["Xitheros"] = {img="https://steamusercontent-a.akamaihd.net/ugc/2513648804719314365/9ADB9E5D9644BCB244912A93291D22A03DB606F8/", mColor="rgba(0.118697680532932,0.0739775076508522,0.141308218240738,1)", order=22},
    ["Awakened"] = {img="https://steamusercontent-a.akamaihd.net/ugc/14049218675992794331/9261F74124B6A9D5556EB63039425EC25E85C0C1/", mColor="rgba(1,0,0,1)", order=23},
}

function summon(a,b,c)
    local mName = self.UI.getAttribute(c.."name","text")
	self.UI.setAttribute("banner", "image",self.UI.getAttribute(c,"image") )
	self.UI.setAttribute("banner", "tooltip", "Start the Fight")
	self.UI.setAttribute("monsterselector", "active", "false")
	self.UI.setAttribute("title", "text", mName)
	self.UI.setAttribute("+", "image","x")
	self.UI.setAttribute("+", "onclick","reset")
	self.UI.setAttribute("title","color", self.UI.getAttribute(c.."name","color"))

	if mName == "Awakened" then
	    self.UI.setAttribute("LevelInput", "text", "3")
	end
end

function setexpedition(a,b,c)
    self.UI.setAttribute("Expedition1Setup","image", "")
    self.UI.setAttribute("Expedition2Setup","image", "")
    self.UI.setAttribute("Expedition1Setup","color", "")
    self.UI.setAttribute("Expedition2Setup","color", "")
    self.UI.setAttribute("Expedition1Setup","textColor", "white")
    self.UI.setAttribute("Expedition2Setup","textColor", "white")
    self.UI.setAttribute(c,"image", "https://steamusercontent-a.akamaihd.net/ugc/2493386495702200472/672A5FD0825986A6FDC42412A871337EBA298735/")
    self.UI.setAttribute(c,"color", "red")
    self.UI.setAttribute(c,"textColor", "white")
    myexp = c
end

function reset()
    self.UI.setAttribute("+", "onclick","reset")
    self.UI.setAttribute("banner", "image","Primal" )
    self.UI.setAttribute("banner", "tooltip", "")
    self.UI.setAttribute("title", "text","Choose a monster")
    self.UI.setAttribute("+", "image","Rightb")
    self.UI.setAttribute("+", "onclick","plus")
    self.UI.setAttribute("title","color", "yellow")
    self.UI.setAttribute("Expedition1Setup","image", "")
    self.UI.setAttribute("Expedition2Setup","image", "")
    self.UI.setAttribute("Expedition1Setup","color", "")
    self.UI.setAttribute("Expedition2Setup","color", "")
    self.UI.setAttribute("Expedition1Setup","textColor", "white")
    self.UI.setAttribute("Expedition2Setup","textColor", "white")
    myexp = ""
end

function setImages()
    monsterImageList = {}
    for name, data in pairs(monsterImageData) do
        table.insert(monsterImageList, {name = name, img = data.img, mColor = data.mColor, order = data.order})
    end
    
    -- 숫자(order) 순으로 자연스럽게 정렬
    table.sort(monsterImageList, function(a, b) return a.order < b.order end)
    
    updateUI()
end

function updateUI()
    for i, data in ipairs(monsterImageList) do
        self.UI.setAttribute("monster"..i, "image", data.img)
        self.UI.setAttribute("monster"..i.."name", "text", data.name)
        self.UI.setAttribute("monster"..i.."name", "color", data.mColor)
    end
end

function SetupMonster()
    local selectedMonster = self.UI.getAttribute("title","text")
    local selectedLevel = self.UI.getAttribute("LevelInput", "text")

    if selectedMonster == "Awakened" then
        selectedLevel = "3"
    end

    if myexp == "" then
        broadcastToAll("Pick an expedition number", Color.Orange)
    else
        Global.call("CleanMonster")
        Global.call("SetupMonster", {selectedMonster, selectedLevel, myexp})
    end
end

function onload()
    setImages()
end

function handleLevel(a,b,c)
    if b == "" then
        self.UI.SetAttribute(c, "text", "0")
    else
        self.UI.SetAttribute(c, "text", b)
    end
end

function setAttr(attrID, attrTag, attrVal)
    if attrVal == "" then
        self.UI.setAttribute(attrID, "active", "false")
        self.UI.setAttribute(attrID, attrTag, attrVal)
    else
        if attrID == 'title' and attrVal == "Primal" then
            attrVal = "Choose a monster"
        end
        self.UI.setAttribute(attrID, "active", "true")
        self.UI.setAttribute(attrID, attrTag, attrVal)
    end
end

function plus()
   self.UI.setAttribute("monsterselector", "active", "true")
end