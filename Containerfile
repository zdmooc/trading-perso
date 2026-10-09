# Image du rapport horaire pour CRC (OpenShift). Lecture seule : aucun ordre de bourse.
FROM registry.access.redhat.com/ubi9/python-312:latest
WORKDIR /opt/app-root/src
COPY --chown=1001:0 pyproject.toml README.md ./
COPY --chown=1001:0 src ./src
COPY --chown=1001:0 reports/ig/epics.json ./reports/ig/epics.json
RUN pip install --no-cache-dir . && rm -rf src
# OpenShift lance le conteneur avec un utilisateur au hasard : tout ce qui s'écrit va dans /tmp.
ENV HOME=/tmp XDG_CACHE_HOME=/tmp/.cache PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["tradeperso", "serveur", "--out", "/tmp/reports", "--port", "8080", "--minutes", "15"]
