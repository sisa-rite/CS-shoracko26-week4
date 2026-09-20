# syntax=docker/dockerfile:1
FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/index.html /usr/share/nginx/html/index.html

RUN chgrp -R 0 /usr/share/nginx/html /etc/nginx /var/cache/nginx \
    && chmod -R g=u /usr/share/nginx/html /etc/nginx /var/cache/nginx

USER 1001
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
