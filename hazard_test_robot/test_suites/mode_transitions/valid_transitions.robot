*** Settings ***
Resource    ../../resources/keywords.robot
Resource    ../../resources/variables.robot
Test Setup    Initialize Hazard System
Test Teardown    Reset System

*** Test Cases ***
Valid Transition From P To S Mode
    [Documentation]    Verify system can enter S mode from P
    When Request Mode Change    ${MODE_S}
    Then System Should Be In Mode    ${MODE_S}
    And Verify LED State    ${LED_BLINK_URGENT}
    And Verify No Error
    And Verify CAN Message    Mode_Transition

Valid Transition From S To W Mode
    [Documentation]    Verify system can enter W mode from S
    Given Request Mode Change    ${MODE_S}
    When Request Mode Change    ${MODE_W}
    Then System Should Be In Mode    ${MODE_W}
    And Verify LED State    ${LED_BLINK_SLOW}
    And Verify No Error

Valid Transition From W To F Mode
    [Documentation]    Verify system can enter F mode from W
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    When Request Mode Change    ${MODE_F}
    Then System Should Be In Mode    ${MODE_F}
    And Verify LED State    ${LED_BLINK_FAST}
    And Verify No Error

Valid Transition From F To S Mode
    [Documentation]    Verify system can enter S mode from F
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    And Request Mode Change    ${MODE_F}
    When Request Mode Change    ${MODE_S}
    Then System Should Be In Mode    ${MODE_S}
    And Verify LED State    ${LED_BLINK_URGENT}
    And Verify No Error

Valid Complex Transition Path
    [Documentation]    Verify P→S→W→F→S→P path
    When Verify Valid Transition Path    ${MODE_S}    ${MODE_W}    ${MODE_F}    ${MODE_S}    ${MODE_P}
    Then System Should Be In Mode    ${MODE_P}
    And Verify LED State    ${LED_OFF}