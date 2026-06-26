CREATE DATABASE IF NOT EXISTS evidence_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE evidence_db;

CREATE TABLE IF NOT EXISTS tasktest (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appname VARCHAR(64) DEFAULT NULL COMMENT '平台名称',
    task_args TEXT COMMENT '直播/取证 URL',
    title VARCHAR(512) DEFAULT NULL COMMENT '标题',
    roomid VARCHAR(128) DEFAULT NULL COMMENT '房间号',
    casenum VARCHAR(128) DEFAULT NULL COMMENT '案件编号',
    taskid VARCHAR(128) NOT NULL COMMENT '取证任务 ID',
    forensic_type VARCHAR(64) DEFAULT NULL COMMENT '取证类型',
    domain VARCHAR(64) NOT NULL DEFAULT 'southnotary' COMMENT '域名标识',
    videopath VARCHAR(1024) DEFAULT NULL COMMENT '本地视频路径',
    complete TINYINT(1) NOT NULL DEFAULT 0 COMMENT '录制是否完成',
    upload TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已上传',
    start_time DATETIME DEFAULT NULL COMMENT '录屏开始时间',
    end_time DATETIME DEFAULT NULL COMMENT '录屏结束时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_taskid_domain (taskid, domain),
    KEY idx_complete_upload (complete, upload, domain)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='取证任务表';
