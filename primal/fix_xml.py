import re
with open('global.xml', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''<TableLayout
    id="TurnOrder"
    active="false"
    rowBackgroundImage="midUI"
    rectAlignment="MiddleLeft"
    offsetXY="75 115"
    columnWidths="200"
    width="200"
    height="200"
    maxHeight="800"
    allowDragging="true"
    returnToOriginalPositionWhenReleased="false"
    cellBackgroundImage="midUI"
>
    <Row
        preferredHeight="145"
        dontUseTableRowBackground="true"
        image="https://steamusercontent-a.akamaihd.net/ugc/11409641284205216910/AE3857677F5C5774CDB6D112C2189DB21B286831/"
    >
        <Button height="32" width="32" rectAlignment="MiddleLeft" id="behave1" image="Question" offsetXY="24 7" tooltip="Behaviour description" tooltipBackgroundColor="black" tooltipPosition="Right" tooltipOffset="152"></Button>
        <Button height="32" width="32" id="behave2" image="Question" offsetXY="0 7" rectAlignment="MiddleCenter" tooltip="Behaviour description" tooltipBackgroundImage="midUI" tooltipPosition="Right" tooltipOffset="92"></Button>
        <Button height="32" width="32" id="behave3" image="Question" offsetXY="-24 7" rectAlignment="MiddleRight" tooltip="Behaviour description" tooltipBackgroundImage="midUI" tooltipPosition="Right" tooltipOffset="30"></Button>
        
        <Button
            id="monsterUpkeepBtn"
            onClick="DoMonsterUpkeep"
            image="https://steamusercontent-a.akamaihd.net/ugc/10107878986189429939/BA2775F9415E1776DE78511B4D2E9FC6E7508353/"
            width="185"
            height="30"
            rectAlignment="LowerCenter"
            offsetXY="0 13"
            preserveAspect="true"
            tooltip="Upkeep Phase"
            tooltipBackgroundColor="black"
        ></Button>
    </Row>

    <Row id="btn1_row" active="true" preferredHeight="40" dontUseTableRowBackground="true" image="midUI">
        <Cell>
            <Panel>
                <Button id="aggro_Blue" onClick="ClickAggroIcon" active="true" image="https://steamusercontent-a.akamaihd.net/ugc/2452852111571389540/CA30F389ADD46B0FE9F0CFABD07C20615EFDE103/" width="30" height="30" rectAlignment="MiddleLeft" offsetXY="20 0" preserveAspect="true" />
                <Button id="btn1" onClick="changecolor" color="white" image="BlueP" width="150" height="40" rectAlignment="MiddleRight" />
            </Panel>
        </Cell>
    </Row>

    <Row id="btn2_row"'''

content = re.sub(r'<TableLayout\s+id="TurnOrder".*?id="btn2_row"', replacement, content, flags=re.DOTALL)
content = content.replace('onClick="Global/DoMonsterUpkeep"', 'onClick="Global/ClickUpkeepPhase"')

with open('global.xml', 'w', encoding='utf-8') as f:
    f.write(content)
