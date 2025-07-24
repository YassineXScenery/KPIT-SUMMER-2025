*** Settings ***
Library    ../resources/python_libs/hazard_system.py
Library    ../resources/python_libs/can_lin_checker.py
Library    Collections

*** Keywords ***
Initialize Hazard System
    Reset System
    System Should Be In Mode    ${MODE_P}

Reset System
    Hazard System.Reset

System Should Be In Mode
    [Arguments]    ${expected_mode}
    ${current_mode}=    Get Current Mode
    Should Be Equal    ${current_mode}    ${expected_mode}

Request Mode Change
    [Arguments]    ${new_mode}
    ${result}=    Hazard System.Change Mode    ${new_mode}
    [Return]    ${result}

Get Current Mode
    ${status}=    Hazard System.Get System Status
    [Return]    ${status['mode']}

Verify LED State
    [Arguments]    ${expected_state}
    ${status}=    Hazard System.Get System Status
    Should Be Equal    ${status['led_state']}    ${expected_state}

Verify Error Occurred
    [Arguments]    ${expected_error}=${None}
    ${status}=    Hazard System.Get System Status
    Run Keyword If    $expected_error is not None
    ...    Should Contain    ${status['error']}    ${expected_error}
    ...    ELSE
    ...    Should Not Be None    ${status['error']}

Verify No Error
    ${status}=    Hazard System.Get System Status
    Should Be None    ${status['error']}

Verify CAN Message
    [Arguments]    ${message_name}
    ${expected}=    CAN LIN Checker.Get Expected CAN Message    ${message_name}
    ${actual}=    CAN LIN Checker.Receive CAN Message    ${expected['id']}
    Dictionaries Should Match    ${actual}    ${expected}

Verify LIN Message
    [Arguments]    ${message_name}
    ${expected}=    CAN LIN Checker.Get Expected LIN Message    ${message_name}
    ${actual}=    CAN LIN Checker.Receive LIN Message    ${expected['id']}
    Dictionaries Should Match    ${actual}    ${expected}

Verify Valid Transition Path
    [Arguments]    @{mode_sequence}
    FOR    ${mode}    IN    @{mode_sequence}
        ${result}=    Request Mode Change    ${mode}
        Should Be True    ${result}    Transition to ${mode} failed
        System Should Be In Mode    ${mode}
        Verify No Error
    END

Verify Invalid Transition In Path
    [Arguments]    @{mode_sequence}    ${invalid_transition_index}
    FOR    ${index}    ${mode}    IN ENUMERATE    @{mode_sequence}
        ${result}=    Request Mode Change    ${mode}
        IF    ${index} == ${invalid_transition_index}
            Should Not Be True    ${result}    Invalid transition should fail
            Verify Error Occurred
            Exit For Loop
        ELSE
            Should Be True    ${result}    Valid transition failed
            System Should Be In Mode    ${mode}
            Verify No Error
        END
    END