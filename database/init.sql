-- ============================================================================
-- Interactive Data Analysis System — Database Initialization
-- MySQL 8.0+ required.
-- Execute: mysql -u root -p < database/init.sql
-- ============================================================================

CREATE DATABASE IF NOT EXISTS data_analysis_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE data_analysis_db;

-- ----------------------------------------------------------------------------
-- Users table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          INT           NOT NULL AUTO_INCREMENT,
    username    VARCHAR(50)   NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE  KEY uq_users_username (username),
    INDEX        idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Datasets table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS datasets (
    id           INT           NOT NULL AUTO_INCREMENT,
    user_id      INT           NOT NULL,
    filename     VARCHAR(255)  NOT NULL,
    columns_info JSON          DEFAULT NULL,
    row_count    INT           DEFAULT NULL,
    uploaded_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX        idx_datasets_user_id (user_id),
    INDEX        idx_datasets_uploaded_at (uploaded_at),
    CONSTRAINT   fk_datasets_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Analysis records table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_records (
    id             INT           NOT NULL AUTO_INCREMENT,
    user_id        INT           NOT NULL,
    dataset_id     INT           DEFAULT NULL,
    analysis_type  VARCHAR(50)   DEFAULT NULL,
    parameters     JSON          DEFAULT NULL,
    result_summary TEXT          DEFAULT NULL,
    chart_paths    JSON          DEFAULT NULL,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    INDEX          idx_ar_user_id (user_id),
    INDEX          idx_ar_dataset_id (dataset_id),
    INDEX          idx_ar_created_at (created_at),
    CONSTRAINT     fk_ar_user
        FOREIGN KEY (user_id) REFERENCES users (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT     fk_ar_dataset
        FOREIGN KEY (dataset_id) REFERENCES datasets (id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
