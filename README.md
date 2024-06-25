# glpi-tools
use the python glpi api to extract data and provide additional functionality


## Environment

we expect to find in the environment:

 - export GLPI_URL="<the apprest.php url for your glpi instance, use https please>"
 - export GLPI_APPTOKEN="<a glpi app token>"
 - export GLPI_USERTOKEN="<a glpi user token with sufficient read all privilegies>"
 - export MAILHOST="<your mail server ip or dns name>"
 - export MAILHOST_PORT="25"
 - export MY_EMAIL_FROM="<your from mail noreply most likely>"

The makefile uses:

  - ~/.glpi_api.env

but you can naturally add them to .bashrc (fedora) or .profile (ubuntu)
