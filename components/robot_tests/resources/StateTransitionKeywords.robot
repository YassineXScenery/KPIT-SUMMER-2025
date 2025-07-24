*** Settings ***
Resource    CommonKeywords.robot

*** Keywords ***
Verify State Transition
    [Arguments]    ${from_state}    ${to_state}    ${should_succeed}
    ${initial_state} =    Get Current PWF State
    Should Be Equal    ${initial_state}    ${from_state}    Initial state should be ${from_state} but was ${initial_state}
    
    Change PWF State    ${to_state}
    ${new_state} =    Get Current PWF State
    
    Run Keyword If    ${should_succeed}
    ...    Should Be Equal    ${new_state}    ${to_state}    Transition from ${from_state} to ${to_state} should have succeeded but didn't
    ...    ELSE
    ...    Should Be Equal    ${new_state}    ${from_state}    Transition from ${from_state} to ${to_state} should have failed but succeeded

Initialize Test For State Transitions
    [Arguments]    ${initial_state}
    Change PWF State    ${initial_state}
    ${current_state} =    Get Current PWF State
    Should Be Equal    ${current_state}    ${initial_state}    Failed to initialize test with ${initial_state} state
    Log    Test initialized with ${initial_state} mode