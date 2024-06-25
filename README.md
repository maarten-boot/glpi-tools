# glpi-tools
use the python glpi api to extract data and provide additional functionality

## SoftwareLicences

 - The tool reads from the Glpi Licences and looks for expire date happening in the near future (30 days)
 - it then collects the tech_user and tech_group emails and combined them to send a mail
 - if the resulting email list is empty its send to the glpi admin.

## Environment

we expect to find in the environment:

 - export GLPI_URL="the apprest.php url for your glpi instance, use https please"
 - export GLPI_APPTOKEN="a glpi app token"
 - export GLPI_USERTOKEN="a glpi user token with sufficient read all privilegies"
 - export MAILHOST="your mail server ip or dns name"
 - export MAILHOST_PORT="25"
 - export MY_EMAIL_FROM="your from mail noreply most likely"

The makefile uses:

  - ~/.glpi_api.env

but you can naturally add them to .bashrc (fedora) or .profile (ubuntu)

## requirements

pip install glpi-api python-dateutil requests urllib3

the make file builds its own venv
youcan run the executable with make run via cron

e.g. on Fedora/Centos/Rocky/...
on monday 08:08 Am

    08 08 * * 1 ( source $HOME/.bashrc; $HOME/glpi-tools; make run )
