-- Southnotary evidence task table
-- Used by southnotary_uploader to store forensic tasks and upload status.

CREATE TABLE IF NOT EXISTS `tasktest` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `appname` VARCHAR(64) DEFAULT NULL COMMENT 'Platform display name, e.g. Douyin, Xiuse',
  `task_args` TEXT COMMENT 'Live room URL or task arguments',
  `title` VARCHAR(512) DEFAULT NULL COMMENT 'Live room title',
  `roomid` VARCHAR(128) DEFAULT NULL COMMENT 'Live room ID',
  `casenum` VARCHAR(128) DEFAULT NULL COMMENT 'Case number from evidence API',
  `taskid` VARCHAR(128) NOT NULL COMMENT 'Forensic task ID from evidence API',
  `forensic_type` VARCHAR(64) DEFAULT NULL COMMENT 'Forensic type from evidence API',
  `domain` VARCHAR(64) NOT NULL DEFAULT 'southnotary' COMMENT 'Tenant/domain identifier',
  `complete` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 when local recording is finished',
  `upload` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '1 when video uploaded and callback succeeded',
  `videopath` VARCHAR(1024) DEFAULT NULL COMMENT 'Absolute path to recorded video file',
  `start_time` DATETIME DEFAULT NULL COMMENT 'Screen recording start time',
  `end_time` DATETIME DEFAULT NULL COMMENT 'Screen recording end time',
  `record_duration` INT DEFAULT NULL COMMENT 'Optional per-task recording duration override in seconds',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Row creation time',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Row update time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_taskid_domain` (`taskid`, `domain`),
  KEY `idx_domain_complete_upload` (`domain`, `complete`, `upload`),
  KEY `idx_domain_taskid` (`domain`, `taskid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Southnotary forensic task queue';
