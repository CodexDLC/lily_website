events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # --- Logging ---
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # --- Performance ---
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;

    # --- Gzip ---
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;

    # --- Upstream (Backend) ---
    upstream backend {
        server backend:8000;
    }

    # --- Rate Limiting ---
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=30r/s;

    # --- Site Configs ---
    include /etc/nginx/conf.d/*.conf;
}
