FROM nginx:alpine

# Удаляем все стандартные конфиги
RUN rm /etc/nginx/conf.d/*

# Копируем наш основной конфиг
COPY deploy/nginx/nginx-main.conf /etc/nginx/nginx.conf

# Копируем шаблон конфига сайта
COPY deploy/nginx/site.conf.template /etc/templates/site.conf.template

# Создаем папку для certbot
RUN mkdir -p /var/www/certbot

EXPOSE 80 443

# При запуске подставляем переменные окружения в конфиг и запускаем nginx
CMD ["/bin/sh", "-c", "envsubst '${DOMAIN_NAME}' < /etc/templates/site.conf.template > /etc/nginx/conf.d/site.conf && exec nginx -g 'daemon off;'"]
