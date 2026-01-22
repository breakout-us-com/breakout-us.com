import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import path from 'path';

// Log directory
const LOG_DIR = path.join(process.cwd(), 'logs');

// Custom format for KST timestamp
const kstTimestamp = winston.format((info) => {
  const now = new Date();
  // Convert to KST (UTC+9)
  const kstOffset = 9 * 60 * 60 * 1000;
  const kstTime = new Date(now.getTime() + kstOffset);
  info.timestamp = kstTime.toISOString().replace('T', ' ').substring(0, 19);
  return info;
});

// Log format
const logFormat = winston.format.combine(
  kstTimestamp(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    const metaStr = Object.keys(meta).length ? ` ${JSON.stringify(meta)}` : '';
    return `${timestamp} [${level.toUpperCase()}] ${message}${metaStr}`;
  })
);

// Daily rotate file transport with KST-based rotation
const fileTransport = new DailyRotateFile({
  dirname: LOG_DIR,
  filename: 'frontend-%DATE%.log',
  datePattern: 'YYYY-MM-DD',
  maxFiles: '30d', // Keep 30 days of logs
  utc: false, // Use local time for rotation
});

// Create logger instance
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: logFormat,
  transports: [
    // Console output
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        logFormat
      ),
    }),
    // File output with daily rotation
    fileTransport,
  ],
});

export default logger;
