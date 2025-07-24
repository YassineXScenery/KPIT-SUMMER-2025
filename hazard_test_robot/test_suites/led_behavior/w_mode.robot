*** Settings ***
Resource    ../../resources/keywords.robot
Resource    ../../resources/variables.robot
Test Setup    Initialize Hazard System
Test Teardown    Reset System

*** Test Cases ***
Verify W Mode LED Pattern
    [Documentation]    Verify LEDs show correct pattern in W mode
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    Then Verify LED State    ${LED_BLINK_SLOW}
    And Verify CAN Message    LED_Status

Verify W Mode Persistence
    [Documentation]    Verify LED pattern continues consistently
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    When Wait    5s
    Then Verify LED State    ${LED_BLINK_SLOW}