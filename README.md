# odoo-project-template

Deploy Odoo Project Template wtih Docker and full dependencies of
https://github.com/OCA/l10n-spain with some useful modules, see file "oca_addons.yaml".

# Configurar Windows

- Instalar DockerDesktop https://www.docker.com/products/docker-desktop/
- Ejecutar powershell con permisos de administrador y copiar comandos

```javascript
  dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
  wsl --set-default-version 2
```

- Ir a microsoft store instalar Debian.
- Comprobar en DokerDesktop en la configuración que está con wsl2.
- Ejecutar en un terminal wsl y se nos inciara el debian y habrá que configurar nombre y
  contraseña.
- Instalar python en el debian.

```javascript
sudo apt update && upgrade
sudo apt install python3 python3-pip ipython3
```

# Dependencias

```javascript
apt-get install sshpass
pip3 install requests
pip3 install paramiko
pip3 install GitPython
pip3 install python-dotenv
pip3 install PyYAML
pip3 install invoke
pip install pre-commit
pip install docker-compose
```

# Uso

- Para que el pre-commit tome efecto necesitamos instalar el precommit en el mismo, usar
  comando: pre-commit install
- Para levantar proyecto despues de definir configuraciones: docker-compse up |
  docker-compose up -d
- Para destruir contenedores del proyecto: docker-compose down
- Para iniciar contenedores del proyecto: docker-compose start
- Para parar contenedores del proyecto: docker-compose stop
- Para reiniciar contenedores del proyecto docker-compose restart
- Para ver log del contenedor si lo hemos arrancado con start o con up -d: docker logs
  -f --tail 100 container_name
- Para subir módulos de OCA: invoke upload-oca
- Para instalar dependencias en el contenedor: invoke pip-install

# DEBUG

- Ir al fichero .env y poner el valor true a la variable DEBUG
- Asignar puerto para debug en el fichero .env
- En el fichero launch.json asignar el puerto especificado para debug en el .env
- Eliminar contenedores del stack del proyecto y su imagen para volver a reconstruir con
  los nuevos parametros de debug

# VSC Recommended

- code --install-extension abusaidm.html-snippets
- code --install-extension batisteo.vscode-django
- code --install-extension donjayamanne.jquerysnippets
- code --install-extension donjayamanne.python-environment-manager
- code --install-extension donjayamanne.python-extension-pack
- code --install-extension DotJoshJohnson.xml
- code --install-extension eamodio.gitlens
- code --install-extension ecmel.vscode-html-css
- code --install-extension esbenp.prettier-vscode
- code --install-extension GitHub.copilot
- code --install-extension GitHub.copilot-chat
- code --install-extension jeffery9.odoo-snippets
- code --install-extension KevinRose.vsc-python-indent
- code --install-extension mechatroner.rainbow-csv
- code --install-extension ms-azuretools.vscode-docker
- code --install-extension ms-python.black-formatter
- code --install-extension ms-python.flake8
- code --install-extension ms-python.isort
- code --install-extension ms-python.pylint
- code --install-extension ms-python.python
- code --install-extension ms-python.vscode-pylance
- code --install-extension ms-toolsai.jupyter
- code --install-extension ms-toolsai.jupyter-keymap
- code --install-extension ms-toolsai.jupyter-renderers
- code --install-extension ms-toolsai.vscode-jupyter-cell-tags
- code --install-extension ms-toolsai.vscode-jupyter-slideshow
- code --install-extension njpwerner.autodocstring
- code --install-extension redhat.vscode-xml
- code --install-extension redhat.vscode-yaml
- code --install-extension sketchbuch.vsc-workspace-sidebar
- code --install-extension trinhanhngoc.vscode-odoo
- code --install-extension usernamehw.errorlens
- code --install-extension VisualStudioExptTeam.intellicode-api-usage-examples
- code --install-extension VisualStudioExptTeam.vscodeintellicode
- code --install-extension wayou.vscode-todo-highlight
- code --install-extension wholroyd.jinja
- code --install-extension Zignd.html-css-class-completion
- code --install-extension PKief.material-icon-theme

# VSC custom snippets

- snippetspython
  ```javascript
  "oocoding": {
      "prefix": "oocoding",
      "body": [
          "# -*- coding: utf-8 -*-",
      ],
      "description": "python coding"
      },
  "ooimportlogging": {
      "prefix": "ooimportlogging",
      "body": [
          "import logging",
          "_logger = logging.getLogger(__name__)",
      ],
      "description": "python logging"
      }
  ```

# GitHub Actions

- int-deploy
  - Activar en los settings del repo, que las GH Actions puedan hacer PR...
  - para configurar esta action hay que generar una clave en el servidor con: ssh-keygen
    -t rsa -b 4096
  - luego pegar la clave publica en el fichero authorized_keys: cat ~/.ssh/id_rsa.pub >>
    ~/.ssh/authorized_keys
  - Tambien pegar la clave publica en nuestra cuenta de github en settings add ssh key
  - pegar en el secreto GH_TOKEN la clave privada sacandola de: cat ~/.ssh/id_rsa
  - IMPORTANTE: si el proyecto ya esta clonado en el servidor y no lo ha clonado el
    mismo usuario de GH, en el que se esta configurando la clave publica,no funcionará
    ya que el el directorio del proyecto .git esta el usuario que lo clonó,entonces
    elminar el proyecto del server y dejar que la Action lo clone, o borrarlo y clonarlo
    manualmente con el mismo usuario de GH con el que se esta configurando la clave.
- pr-main
- pr-develop
- setup
