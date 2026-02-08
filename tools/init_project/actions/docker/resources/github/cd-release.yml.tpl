name: CD Release (Deploy)

on:
  push:
    branches: [ release ]

jobs:
  deploy:
    name: Build & Deploy to VPS
    runs-on: ubuntu-latest

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Lowercase repo name
        run: |
          echo "REPO_LOWER=${GITHUB_REPOSITORY,,}" >> $GITHUB_ENV

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

{{BUILD_PUSH_STEPS}}

      - name: Copy docker-compose to VPS
        uses: appleboy/scp-action@master
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          source: "deploy/docker-compose.prod.yml,deploy/nginx/"
          target: "/opt/{{PROJECT_NAME}}/"

      - name: SSH Deploy
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          envs: REPO_LOWER
          script: |
            cd /opt/{{PROJECT_NAME}}

            cat << 'EOF' > .env
            ${{ secrets.ENV_FILE }}
            EOF

            echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin

{{EXPORT_IMAGES}}

            docker compose -f deploy/docker-compose.prod.yml pull
{{MIGRATE_STEP}}
            docker compose -f deploy/docker-compose.prod.yml up -d --remove-orphans --wait

            docker image prune -f
