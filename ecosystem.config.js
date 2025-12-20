module.exports = {
  apps: [
    {
      name: 'breakout-backend',
      cwd: './backend',
      script: 'venv/bin/uvicorn',
      args: 'main:app --host 0.0.0.0 --port 8800 --ssl-keyfile /var/www/breakout-us.com/ssl/key.pem --ssl-certfile /var/www/breakout-us.com/ssl/fullchain.pem',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production',
      },
      watch: false,
      instances: 1,
      autorestart: true,
      max_memory_restart: '500M',
    },
  ],
};
