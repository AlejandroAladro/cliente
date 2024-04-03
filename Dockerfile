ARG WEB_IMAGE_TAG=16
FROM odoo:$WEB_IMAGE_TAG
USER root
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
RUN apt-get update
RUN pip3 install --upgrade pip
RUN apt-get install -y procps

# Instalamos debugpy para poder debugear
RUN pip3 install debugpy

# Copiamos e instalamos las dependencias de python del proyecto
COPY ./dependencies /opt/dependencies
RUN if  [ -s dependencies/apt.txt]; then apt-get install < /opt/dependencies/apt.txt ; fi;
RUN pip3 install -r /opt/dependencies/pip.txt


COPY wait-for-psql.py /usr/local/bin/wait-for-psql.py
RUN chmod +x /usr/local/bin/wait-for-psql.py

# Set default user when running the container
USER odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]
