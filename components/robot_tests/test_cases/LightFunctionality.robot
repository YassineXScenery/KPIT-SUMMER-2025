*** Settings ***
Resource    ../resources/CommonKeywords.robot
Resource    ../resources/LightFunctionalityKeywords.robot

Suite Setup       Connect To Database And Initialize Test
Suite Teardown    CommonKeywords.Disconnect From Database

*** Keywords ***
Connect To Database And Initialize Test
    CommonKeywords.Connect To Database
    Initialize Light Test

*** Test Cases ***
Test Light Functionality In Different Modes
    [Documentation]    Test that light only works in W and F modes
    
    # Test in P mode
    Test Light In Mode    P    ${FALSE}
    
    # Test in S mode
    Test Light In Mode    S    ${FALSE}
    
    # Test in W mode
    Test Light In Mode    W    ${TRUE}
    
    # Test in F mode
    Test Light In Mode    F    ${TRUE}