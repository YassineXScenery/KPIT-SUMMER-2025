*** Settings ***
Resource    CommonKeywords.robot

*** Keywords ***
Test Light In Mode
    [Arguments]    ${mode}    ${should_work}
    # Set the mode
    Change PWF State    ${mode}
    ${current_mode} =    Get Current PWF State
    Should Be Equal    ${current_mode}    ${mode}    Failed to set mode to ${mode}
    
    # Try to turn on the light
    Set LED State    on
    ${led_state} =    Get Current LED State
    
    Run Keyword If    ${should_work}
    ...    Should Be Equal    ${led_state}    on    Light should be on in ${mode} mode but is off
    ...    ELSE
    ...    Should Be Equal    ${led_state}    off    Light should be off in ${mode} mode but is on
    
    # Log appropriate message
    ${message} =    Set Variable If    ${should_work}
    ...    Light correctly works in ${mode} mode
    ...    Light correctly doesn't work in ${mode} mode
    Log    ${message}

Initialize Light Test
    Set LED State    off
    Log    Light test initialized with lights off