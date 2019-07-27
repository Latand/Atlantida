#!/usr/bin/env bash
#"""
#Internalize your bot
#Step 1: extract texts
#     pybabel extract i18n_example.py -o locales/mybot.pot
#Step 2: create *.po files. For e.g. create en, ru, uk locales.
#     echo {en,ru,uk} | xargs -n1 pybabel init -i locales/mybot.pot -d locales -D mybot -l
#Step 3: translate texts
#Step 4: compile translations
#     pybabel compile -d locales -D mybot
#
#
#
#Step 5: When you change the code of your bot you need to update po & mo files.
#    Step 5.1: regenerate pot file:
#        pybabel extract main.py -o locales_old/mybot.pot
#    Step 5.2: update po files
#         pybabel update -d locales_old -D mybot -i locales_old/mybot.pot
#    Step 5.3: update your translations
#    Step 5.4: compile mo files
#        pybabel compile -d locales_old -D mybot
#"""
#pybabel extract handlers -o locales/atlantida.pot
#echo {ru,en,uk} | xargs -n1 pybabel init -i locales/atlantida.pot -d locales -D atlantida -l
#pybabel compile -d locales -D atlantida

pybabel extract handlers -o locales/atlantida.pot
pybabel update -d locales -D atlantida -i locales/atlantida.pot
pybabel compile -d locales -D atlantida
