module.exports = {
  apps: [
    {
      name: 'sleepbot',
      script: 'main.py',
      interpreter: 'python3',
      cwd: '/opt/sleepbot',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        ENVIRONMENT: 'production',
        LOG_LEVEL: 'INFO',
        PYTHONUNBUFFERED: '1',
      },
      error_file: '/opt/sleepbot/logs/pm2-error.log',
      out_file: '/opt/sleepbot/logs/pm2-out.log',
      log_file: '/opt/sleepbot/logs/pm2-combined.log',
      time: true,
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      // Restart strategies
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000,
      // Graceful shutdown
      kill_timeout: 5000,
      listen_timeout: 3000,
      // Health monitoring
      wait_ready: false,
    },
  ],
};
