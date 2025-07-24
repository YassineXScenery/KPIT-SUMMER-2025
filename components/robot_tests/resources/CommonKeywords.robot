*** Settings ***
Library    DatabaseLibrary
Library    OperatingSystem
Library    String
Library    Collections

*** Variables ***
${DB_HOST}        10.20.0.104
${DB_USER}        user
${DB_PASSWORD}    1234
${DB_NAME}        iot_system
${DB_PORT}        3306

*** Keywords ***
Connect To Database
    Connect To Database Using Custom Params    pymysql    database='${DB_NAME}', user='${DB_USER}', password='${DB_PASSWORD}', host='${DB_HOST}', port=${DB_PORT}

Disconnect From Database
    Disconnect From Database

Get Current PWF State
    ${result} =    Query    SELECT state FROM pwf_state WHERE is_active = 1 LIMIT 1
    [Return]    ${result[0][0]}

Change PWF State
    [Arguments]    ${new_state}
    Execute SQL String    UPDATE pwf_state SET is_active = 0
    Execute SQL String    UPDATE pwf_state SET is_active = 1, timestamp = CURRENT_TIMESTAMP WHERE state = '${new_state}'
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source, timestamp, protocol) VALUES ('pwf_state_change', '${new_state}', 'ROBOT', CURRENT_TIMESTAMP, 'CAN')

Get Current LED State
    ${result} =    Query    SELECT value FROM signals_log WHERE signal_name = 'led' ORDER BY timestamp DESC LIMIT 1
    [Return]    ${result[0][0]}

Set LED State
    [Arguments]    ${state}
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source, timestamp, protocol) VALUES ('led', '${state}', 'ROBOT', CURRENT_TIMESTAMP, 'CAN')