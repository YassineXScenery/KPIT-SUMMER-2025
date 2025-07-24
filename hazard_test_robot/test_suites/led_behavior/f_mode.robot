*** Settings ***
Resource    ../../resources/keywords.robot
Resource    ../../resources/variables.robot
Test Setup    Initialize Hazard System
Test Teardown    Reset System

*** Test Cases ***
Verify F Mode LED Pattern
    [Documentation]    Verify LEDs show correct pattern in F mode
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    And Request Mode Change    ${MODE_F}
    Then Verify LED State    ${LED_BLINK_FAST}
    And Verify CAN Message    LED_Status

Verify F Mode Persistence
    [Documentation]    Verify LED pattern continues consistently
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    And Request Mode Change    ${MODE_F}
    When Wait    5s
    Then Verify LED State    ${LED_BLINK_FAST}