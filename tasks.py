import os
import shutil
import time
from getpass import getpass
from pathlib import Path

import paramiko
import requests
import yaml
from dotenv import load_dotenv
from git import Repo
from invoke import task

load_dotenv()

TEMPLATE_ROOT = Path(__file__).parent.resolve()
ESSENTIALS = ("git", "python3", "dotenv", "docker-compose")
OCA_URL = "https://github.com/OCA/%s.git"
VERSION = os.getenv("WEB_IMAGE_TAG")
WEB_HOST = os.getenv("WEB_HOST")
WEB_PORT = os.getenv("WEB_PORT")


@task
def check_dependencies(c):
    """Check essential development dependencies are present."""
    failures = []
    for dependency in ESSENTIALS:
        try:
            c.run(f"{dependency} --version", hide=True)
        except Exception:
            failures.append(dependency)
    if failures:
        print(f"Missing essential dependencies: {failures}")


@task(check_dependencies)
def upgrade_pip(ctx):
    """Actualizar pip en el contenedor"""
    command = (
        "docker exec -it --user root {}-odoo sh -c 'pip3 install --upgrade pip'".format(
            WEB_HOST
        )
    )
    os.system(command)


@task(check_dependencies)
def install_dependencies(ctx):
    """Instalar dependencias definidas en apt.txt y pip.txt en el contenedor"""
    command = "docker exec -it --user root {}-odoo sh -c 'pip3 install -r /opt/dependencies/pip.txt'".format(
        WEB_HOST
    )
    os.system(command)
    command = "docker exec -it --user root {}-odoo sh -c 'apt-get install < /opt/dependencies/apt.txt'".format(
        WEB_HOST
    )
    os.system(command)


@task(check_dependencies)
def pip_install(ctx):
    """Combo install dependencies y actualizar pip"""
    upgrade_pip(ctx)
    install_dependencies(ctx)


@task(check_dependencies)
def upload_oca(ctx):
    """Descargar en local los repos de OCA definidos en oca_addons.yaml"""
    with open("%s/oca_addons.yaml" % TEMPLATE_ROOT) as f:
        repos = yaml.load(f, Loader=yaml.loader.SafeLoader)
        if not repos:
            raise Exception("No hay módulos OCA definidos.")
        path = "~/oca"
        if not os.path.exists(os.path.expanduser(path)):
            os.system("mkdir ~/oca")

        if os.path.exists("{}/oca".format(TEMPLATE_ROOT)):
            # para sobresscribir simpre
            os.system("rm -r {}/oca/*".format(TEMPLATE_ROOT))

            # Antes de empezar a copiar modulos nos aseguramos de que el directorio oca este vacio
            oca_dir = os.listdir("{}/oca".format(TEMPLATE_ROOT))
            while oca_dir:
                time.sleep(1)
                oca_dir = os.listdir("{}/oca".format(TEMPLATE_ROOT))

        for repo in repos:
            if not os.path.exists("{}/{}".format(os.path.expanduser(path), repo)):
                # El repo no existe, lo clonamos y nos situamos en la revision
                command = "git clone -b %s.0 %s" % (VERSION, OCA_URL % repo)
                os.chdir(os.path.expanduser(path))
                os.system(command)
                os.chdir("{}/{}".format(os.path.expanduser(path), repo))
                if not repos.get(repo).get("revision") == "last":
                    os.system("git checkout {}".format(repos.get(repo).get("revision")))
            else:
                # Cambiamos de rama el repo
                os.chdir("{}/{}".format(os.path.expanduser(path), repo))
                os.system("git checkout .")
                os.system("git checkout {}.0 -f".format(VERSION))
                os.system("git pull origin {}.0".format(VERSION))
                if not repos.get(repo).get("revision") == "last":
                    os.system("git checkout {}".format(repos.get(repo).get("revision")))

            if repos.get(repo).get("modules"):
                for module in repos.get(repo).get("modules"):
                    # Para copiar todos los modulos del repo
                    if module == "*":
                        dir_iterator = os.scandir(
                            "{}/{}".format(os.path.expanduser(path), repo)
                        )
                        for directory in dir_iterator:
                            if directory.is_dir() and directory.name not in [
                                "setup",
                                ".git",
                                ".github",
                            ]:
                                os.system(
                                    "cp -r {} {}/oca".format(
                                        directory.path,
                                        TEMPLATE_ROOT,
                                    )
                                )
                        continue

                    try:
                        # Copiamos los modulos del repo en el proyecto/oca
                        src = "{}/{}/{}".format(os.path.expanduser(path), repo, module)
                        dst = "{}/oca/{}".format(TEMPLATE_ROOT, module)
                        shutil.copytree(src=src, dst=dst)
                    except Exception as error:
                        print("El módulo: %s no se copió error: %s" % (module, error))


@task
def odoo_modules_update(ctx, db, module=None):
    """Actualizar modulo/s por linea de comandos. Obligatorio pasa nombre de la DB con [-d db_name]"""
    pre_command = "/usr/bin/python3 /usr/bin/odoo --dev xml --db_host db --db_port 5432 --db_user odoo --db_password odoo "
    if not module:
        module = "all"

    odoo_cli_params = "-d {} -u {} --stop-after-init".format(db, module)
    command = "docker exec -it --user root {}-odoo sh -c '{}{}'".format(
        WEB_HOST, pre_command, odoo_cli_params
    )
    os.system(command)


@task
def update_all_db(ctx, module=None):
    """Actualizar los modulos especificados en todas las bases de datos, si no se pasan modulos se actualizan todos"""
    pre_command = "/usr/bin/python3 /usr/bin/odoo --dev xml --db_host db --db_port 5432 --db_user odoo --db_password odoo "
    if not module:
        module = "all"
    odoo_cli_params = "-u {} --stop-after-init".format(module)
    dbs = []
    try:
        dbs = (
            requests.get(
                "http://localhost:{}/web/database/list".format(WEB_PORT),
                headers={
                    "Content-type": "application/json",
                },
                json={},  # No necesitamos enviar nada
            )
            .json()
            .get("result")
        )

    except Exception as e:
        print("Error al obtener las bases de datos: %s" % e)
        return
    if not dbs:
        print("No hay bases de datos para actualizar")
        return

    for db in dbs:
        odoo_cli_params += " -d {}".format(db)
        command = "docker exec -it --user root {}-odoo sh -c '{}{}'".format(
            WEB_HOST, pre_command, odoo_cli_params
        )
        os.system(command=command)


@task
def join_odoo_container(ctx):
    """Conectarse al contenedor de odoo"""
    container_name = "{}-odoo".format(WEB_HOST)
    os.system("docker exec -it --user root {} /bin/bash".format(container_name))


@task
def logs(ctx, odoo=False, db=False):
    """Ver los logs del stack, si pasamos el parametro -o veremos solo los logs de odoo,
    si pasamos -d veremos los logs de postgres,
    si no pasamos nada veremos los logs de todo el stack"""

    command = "docker-compose logs -f --tail 200"
    if odoo:
        command += " web"
    if db:
        command += " db"
    os.system(command=command)


@task
def build_develop(ctx):
    """Construir entorno de desarrollo"""
    # Primero cargamos los modulos de oca para el proyecto
    os.system("invoke upload-oca")
    # Creamos la carpeta extra-addons si no existe, para que no de problemas al estar como volumen
    if not os.path.exists("{}/extra-addons".format(TEMPLATE_ROOT)):
        os.system("mkdir {}/extra-addons".format(TEMPLATE_ROOT))

    # Luego construimos el entorno de desarrollo
    os.system("docker-compose up -d")


@task
def rebuild_develop(ctx, volume=False):
    """Reconstruir entorno de desarrollo, (-v para borrar volumenes)"""
    # Primero destruimos el stack ya existente, si pasamos el parametro de volumenes, tambien borramos los volumenes
    command = "docker-compose down"
    if volume:
        command += " -v"
    os.system(command=command)

    # Luego construimos el entorno de desarrollo
    os.system("docker-compose up -d")


@task
def build_demo(ctx):
    # TODO docker-compose -H "ssh://username@servername" up -d
    raise NotImplementedError


@task(check_dependencies)
def upload_prod_oca(ctx):
    """Copiar en un servidor remoto los modulos de ./oca"""
    oca = os.getenv("PROD_OCA_PATH")
    if not oca:
        print("No hay ruta definida para oca en el servidor de producción")
        return

    host, user, port, password = get_prod_credentials()
    ssh_client = ssh_connect(host, user, port, password)
    remove_dir(ssh_client, oca)
    # El borrado en servidores de produccion puede ser lento, entonces nos aseguramos de que la carpeta ha sido borrada antes de copiar
    exist = directory_exists(ssh_client, oca)
    while exist:
        time.sleep(1)
        exist = directory_exists(ssh_client, oca)

    os.system(
        "sshpass -p {} scp -r {}/oca {}@{}:{}".format(
            password, TEMPLATE_ROOT, user, host, oca
        )
    )


@task(check_dependencies)
def upload_prod_extra(ctx):
    """Copiar en un servidor remoto los modulos de ./extra-addons"""
    extra = os.getenv("PROD_EXTRA_PATH")
    if not extra:
        print("No hay ruta definida para extra-addons en el servidor de producción")
        return

    host, user, port, password = get_prod_credentials()
    ssh_client = ssh_connect(host, user, port, password)
    remove_dir(ssh_client, extra)
    os.system(
        "sshpass -p {} scp -r {}/extra-addons {}@{}:{}".format(
            password, TEMPLATE_ROOT, user, host, extra
        )
    )


@task(check_dependencies)
def upload_prod_third(ctx):
    """Copiar en un servidor remoto los modulos de ./third-party-addons"""
    third = os.getenv("PROD_THIRD_PATH")
    if not third:
        print(
            "No hay ruta definida para third-party-addons en el servidor de producción"
        )
        return

    host, user, port, password = get_prod_credentials()
    ssh_client = ssh_connect(host, user, port, password)
    remove_dir(ssh_client, third)
    os.system(
        "sshpass -p {} scp -r {}/third-party-addons {}@{}:{}".format(
            password, TEMPLATE_ROOT, user, host, third
        )
    )


# ----- SSH Functions -----


def get_prod_host():
    host = input("Introduzca la dirección del servidor ")
    return host


def get_prod_user():
    user = input("Introduzca el usuario del servidor ")
    return user


def get_prod_port():
    port = input("Introduzca el puerto del servidor (22 por defecto) ")
    if not port:
        port = 22
    return port


def get_prod_credentials():
    host = get_prod_host()
    user = get_prod_user()
    port = get_prod_port()
    password = getpass("Introduzca contraseña para el usuario {} ".format(user))
    return host, user, port, password


def remove_dir(ssh_client, path):
    try:
        ssh_client.exec_command("rm -r %s" % path)
    except IOError:
        pass


def ssh_connect(host, user, port, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(host, port, user, password)
    except Exception as e:
        print("Error al conectar con el servidor: %s" % e)
    return ssh_client


def directory_exists(ssh_client, path):
    is_directory_exists = False
    cmd = "ls -d " + path
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    stderror = stderr.read()
    if not bool(stderror):
        is_directory_exists = True
    return is_directory_exists


# ----- Maintain Functions -----


@task(
    check_dependencies,
    help={
        "repo_name": "Nombre del repo",
    },
)
def update_revision_oca(ctx, repo_name=None):
    """Asignar la ultima revision publicada en github de los repositorios definidos en oca_addons.yaml"""
    path = "~/oca/"

    def update_revision(repos, repo_name):
        repo_yaml = repos.get(repo_name)
        os.chdir("{}/{}".format(os.path.expanduser(path), repo_name))
        os.system("git checkout .")
        os.system("git checkout {}.0 -f".format(VERSION))
        os.system("git switch {}.0".format(VERSION))
        os.system("git pull origin {}.0".format(VERSION))
        repo = Repo("{}/{}".format(os.path.expanduser(path), repo_name))
        repo_yaml["revision"] = repo.head.commit.hexsha[:7]

    with open("%s/oca_addons.yaml" % TEMPLATE_ROOT) as f:
        repos = yaml.load(f, Loader=yaml.loader.SafeLoader)
        if not repo_name:
            for repo_name in repos:
                update_revision(repos, repo_name)
        else:
            update_revision(repos, repo_name)

    with open("%s/oca_addons.yaml" % TEMPLATE_ROOT, "w") as f:
        return yaml.safe_dump(repos, f)


@task(
    check_dependencies,
    help={
        "core": "Path CE Addons",
        "enterprise": "Path EE Addons",
    },
)
def extract_enterprise_addons(ctx, core, enterprise):
    """
    Extraer modulos de enterprise en un directorio aparte enterpise-addons.
    Primer parametro core: es la ruta donde donde estan los addons en la version comunity.
    Segundo parametro enterprise: es la ruta donde estan los addons en la version enterprise descargada.
    """

    # Limpiamos siempre el contenido, si no existe arroja un error de que no existe direcotrio pero no pasa nada
    os.system("rm -r {}/eterprise-addons/*".format(TEMPLATE_ROOT))

    # Recorremos los modulos de enterprise, comprobando si estan en core, si no estan los copiamos
    for dir in os.scandir(enterprise):
        if not os.path.exists("{}/{}".format(core, dir.name)):
            print("Copiando modulo: {}".format(dir.name))
            os.system(
                "cp -r {}/{} {}/enterprise-addons".format(
                    enterprise, dir.name, TEMPLATE_ROOT
                )
            )
