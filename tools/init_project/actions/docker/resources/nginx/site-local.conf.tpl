server {
    listen 80;
    server_name localhost;

    client_max_body_size 10M;

    # Deny hidden files
    location ~ /\.(?!well-known) {
        deny all;
    }

    # === API → Backend ===
    location /api/ {
        limit_req zone=api_limit burst=5 nodelay;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # === Swagger ===
    location /docs {
        proxy_pass http://backend;
    }

    location /openapi.json {
        proxy_pass http://backend;
    }

    # === Media ===
    location /media/ {
        alias /app/media/;
    }

    # === Health ===
    location /health {
        proxy_pass http://backend;
    }
}
