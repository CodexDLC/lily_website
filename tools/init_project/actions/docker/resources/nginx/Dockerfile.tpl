FROM nginx:alpine

# Copy configurations
COPY deploy/nginx/nginx-main.conf /etc/nginx/nginx.conf
COPY deploy/nginx/site.conf /etc/nginx/conf.d/default.conf

# Create Certbot directory
RUN mkdir -p /var/www/certbot

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
