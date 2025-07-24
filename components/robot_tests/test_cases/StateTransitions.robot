*** Settings ***
Resource    ../resources/CommonKeywords.robot
Resource    ../resources/StateTransitionKeywords.robot

Suite Setup       CommonKeywords.Connect To Database
Suite Teardown    CommonKeywords.Disconnect From Database

*** Test Cases ***
Test Invalid Transitions From P Mode
    [Documentation]    Test that invalid transitions from P mode are blocked
    Initialize Test For State Transitions    P
    
    # Test invalid transitions
    Verify State Transition    P    W    ${FALSE}
    Log    Transition from P to W correctly blocked
    
    Verify State Transition    P    F    ${FALSE}
    Log    Transition from P to F correctly blocked
    
    # Test valid transition
    Verify State Transition    P    S    ${TRUE}
    Log    Transition from P to S correctly allowed

Test Valid Transitions From S Mode
    [Documentation]    Test all transitions from S mode
    Initialize Test For State Transitions    S
    
    # Test transitions
    Verify State Transition    S    W    ${TRUE}
    Log    Transition from S to W correctly allowed
    
    Change PWF State    S    # Reset to S
    
    Verify State Transition    S    F    ${TRUE}
    Log    Transition from S to F correctly allowed
    
    Change PWF State    S    # Reset to S
    
    Verify State Transition    S    P    ${TRUE}
    Log    Transition from S to P correctly allowed

Test Valid Transitions From W Mode
    [Documentation]    Test all transitions from W mode
    Initialize Test For State Transitions    W
    
    # Test transitions
    Verify State Transition    W    F    ${TRUE}
    Log    Transition from W to F correctly allowed
    
    Change PWF State    W    # Reset to W
    
    Verify State Transition    W    P    ${FALSE}
    Log    Transition from W to P correctly blocked
    
    Change PWF State    W    # Reset to W
    
    Verify State Transition    W    S    ${TRUE}
    Log    Transition from W to S correctly allowed

Test Valid Transitions From F Mode
    [Documentation]    Test all transitions from F mode
    Initialize Test For State Transitions    F
    
    # Test transitions
    Verify State Transition    F    P    ${FALSE}
    Log    Transition from F to P correctly blocked
    
    Change PWF State    F    # Reset to F
    
    Verify State Transition    F    S    ${TRUE}
    Log    Transition from F to S correctly allowed
    
    Change PWF State    F    # Reset to F
    
    Verify State Transition    F    W    ${TRUE}
    Log    Transition from F to W correctly allowed