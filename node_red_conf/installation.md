Notes for installing NodeRed on Hassbian
===

from here : https://nodered.org/docs/hardware/raspberrypi

Steps
===

```
sudo apt-get install npm && sudo npm i -g npm
bash <(curl -sL https://raw.githubusercontent.com/node-red/raspbian-deb-package/master/resources/update-nodejs-and-nodered)
sudo systemctl enable nodered.service
```

should be installed, fire it up

`sudo systemctl start nodered.service`

Enable projects:
===

(from https://nodered.org/docs/user-guide/projects/)

To enable the projects feature, edit your settings.js file and add the following option within the module.exports block and restart Node-RED.

Note : The settings.js file exports a JavaScript object. To configure Node-RED you should understand how to modify a JavaScript object by adding new or modifying existing key/value pairs like the editorTheme below.

   editorTheme: {
       projects: {
           enabled: true
       }
   },

The feature relies on having the git and ssh-keygen command line tools available. Node-RED will check for them on start-up and let you know if they are missing.

add the twohunnid project
===

open a project from here : https://github.com/snicker/twohunnid_ha_nodered.git

will probably have to update git credentials for this to work
