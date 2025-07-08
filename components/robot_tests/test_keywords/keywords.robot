* Settings *
Library    DatabaseLibrary
Library    Collections
Library    String

Resource    ../test_cases/variables.robot

* Keywords *

Connect To HMI Database
    [Documentation]    Connexion à la base de données iot_system
    Connect To Database    pymysql    ${DB_NAME}    ${DB_USER}    ${DB_PASS}    ${DB_HOST}

Disconnect From HMI Database
    [Documentation]    Déconnexion de la base de données
    Disconnect From Database

Query LED State From DB
    [Documentation]    Récupère le dernier état de la LED depuis la base
    ${result}=    Query    SELECT value FROM signals_log WHERE signal_name='led' ORDER BY timestamp DESC LIMIT 1
    ${led_state}=    Set Variable    ${result[0][0]}
    [Return]    ${led_state}

Allumer LED
    [Documentation]    Insère l'état ON pour la LED dans la base
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('led', 'on', 'test')
    Sleep    3s

Eteindre LED
    [Documentation]    Insère l'état OFF pour la LED dans la base
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('led', 'off', 'test')
    Sleep    3s

Simuler Appui Bouton
    [Documentation]    Simule l'appui sur le bouton poussoir et allume la LED
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('button', 'pressed', 'test')
    Sleep    3s
    Allumer LED

Simuler Relachement Bouton
    [Documentation]    Simule le relâchement du bouton poussoir et éteint la LED
    Execute SQL String    INSERT INTO signals_log (signal_name, value, source) VALUES ('button', 'not pressed', 'test')
    Sleep    3s
    Eteindre LED