*** Settings ***
Library         DatabaseLibrary
Library         OperatingSystem
Library         Collections

Resource        ../test_keywords/keywords.robot   # Path to 'keywords.robot'
Resource        variables.robot                 # Path to 'variables.robot' (same directory)

Suite Setup         Connect To HMI Database
Suite Teardown      Disconnect From HMI Database

*** Test Cases ***

Verify LED Initial State Is Off
    [Documentation]    Vérifie l'état initial de la LED
    ${led_state}=      Query LED State From DB
    Should Be Equal As Strings    ${led_state}    off


Test LED Toggle With Button Press
    [Documentation]    Simule l'appui et le relâchement du bouton poussoir et vérifie l'effet sur la LED

    # Appui sur le bouton
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('button', 'pressed', 'test')
    Sleep                 2s
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('led', 'on', 'test')
    ${led_state}=         Query LED State From DB
    Should Be Equal As Strings    ${led_state}    on
    Log                   LED allumée après appui sur le bouton

    # Relâchement du bouton
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('button', 'not pressed', 'test')
    Sleep                 2s
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('led', 'off', 'test')
    ${led_state}=         Query LED State From DB
    Should Be Equal As Strings    ${led_state}    off
    Log                   LED éteinte après relâchement du bouton