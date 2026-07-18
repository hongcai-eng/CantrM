-- 为 tenant_customer 表添加 system_name 字段
-- 实现租户独立的系统名称配置
-- 执行日期: 2026-07-01

ALTER TABLE tenant_customer ADD COLUMN system_name VARCHAR(200);

-- 说明：
-- 1. 每个租户可以独立配置 system_name、company_name、logo_file
-- 2. superadmin 使用全局 SysConfig 表配置
-- 3. 租户超管在系统配置页面修改的配置只影响自己租户
