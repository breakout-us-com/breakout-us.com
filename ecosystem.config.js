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
      // 로그 설정
      out_file: './logs/backend-out.log',
      error_file: './logs/backend-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
    },
    {
      name: 'breakout-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'start',
      interpreter: 'none',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
      },
      watch: false,
      instances: 1,
      autorestart: true,
      max_memory_restart: '500M',
      // 로그 설정
      out_file: './logs/frontend-out.log',
      error_file: './logs/frontend-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
    },
  ],
};
