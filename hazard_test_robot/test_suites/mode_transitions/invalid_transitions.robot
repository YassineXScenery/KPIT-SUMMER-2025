*** Settings ***
Resource    ../../resources/keywords.robot
Resource    ../../resources/variables.robot
Test Setup    Initialize Hazard System
Test Teardown    Reset System

*** Test Cases ***
Invalid Transition From P To F
    [Documentation]    Verify system rejects transition from P to F
    When Request Mode Change    ${MODE_F}
    Then System Should Be In Mode    ${MODE_P}
    And Verify LED State    ${LED_OFF}
    And Verify Error Occurred    Cannot transition from P to F

Invalid Transition From P To W
    [Documentation]    Verify system rejects transition from P to W
    When Request Mode Change    ${MODE_W}
    Then System Should Be In Mode    ${MODE_P}
    And Verify LED State    ${LED_OFF}
    And Verify Error Occurred    Cannot transition from P to W

Invalid Transition From F To P
    [Documentation]    Verify system rejects transition from F to P
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    And Request Mode Change    ${MODE_F}
    When Request Mode Change    ${MODE_P}
    Then System Should Be In Mode    ${MODE_F}
    And Verify LED State    ${LED_BLINK_FAST}
    And Verify Error Occurred    Cannot transition from F to P

Invalid Transition From W To P
    [Documentation]    Verify system rejects transition from W to P
    Given Request Mode Change    ${MODE_S}
    And Request Mode Change    ${MODE_W}
    When Request Mode Change    ${MODE_P}
    Then System Should Be In Mode    ${MODE_W}
    And Verify LED State    ${LED_BLINK_SLOW}
    And Verify Error Occurred    Cannot transition from W to P

Invalid Transition In Complex Path
    [Documentation]    Verify invalid transition during path
    When Verify Invalid Transition In Path    ${MODE_S}    ${MODE_W}    ${MODE_P}    2
    Then System Should Be In Mode    ${MODE_W}
    And Verify LED State    ${LED_BLINK_SLOW}