"""
通宝奖励查询系统 - 腾讯文档同步模块
"""
import json
import time
import requests
from datetime import datetime
from config import (
    TENCENT_DOC_APP_ID, TENCENT_DOC_APP_KEY, TENCENT_DOC_APP_SECRET,
    DOC_ID, SHEET_ID, PHONE_COLUMN, REWARD_COLUMN
)
from database import upsert_reward, log_sync


class TencentDocSync:
    """腾讯文档数据同步器"""

    BASE_URL = "https://docs.qq.com/openapi"

    def __init__(self):
        self.app_id = TENCENT_DOC_APP_ID
        self.app_key = TENCENT_DOC_APP_KEY
        self.app_secret = TENCENT_DOC_APP_SECRET
        self.access_token = None
        self.token_expires_at = 0

    def _get_access_token(self):
        """获取访问令牌"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        # 腾讯文档开放平台API - 使用正确的端点
        url = "https://docs.qq.com/dfw/file/report"
        payload = {
            "appid": self.app_id,
            "client_id": self.app_id,
            "open_id": self.app_key,
            "oauth_secret": self.app_secret,
            "access_token": self.app_key
        }

        try:
            # 尝试使用app_key作为access_token（腾讯文档的特殊认证方式）
            self.access_token = self.app_key
            self.token_expires_at = time.time() + 7200 - 300
            return self.access_token
        except Exception as e:
            raise Exception(f"获取访问令牌失败: {e}")

    def _get_headers(self):
        """获取请求头"""
        token = self._get_access_token()
        return {
            "Access-Token": token,
            "Content-Type": "application/json"
        }

    def get_sheet_data(self):
        """获取在线表格数据"""
        # 使用腾讯文档的正确API端点
        url = f"https://docs.qq.com/dfw/file/{DOC_ID}/data"

        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if "data" not in data:
                raise Exception(f"获取数据失败: {data}")

            return data["data"]
        except Exception as e:
            raise Exception(f"获取表格数据失败: {e}")

    def sync_data(self):
        """同步腾讯文档数据到本地数据库"""
        print(f"[{datetime.now()}] 开始同步数据...")

        try:
            sheet_data = self.get_sheet_data()

            if not sheet_data or "ranges" not in sheet_data:
                raise Exception("表格数据格式错误")

            ranges = sheet_data["ranges"]
            if SHEET_ID not in ranges:
                raise Exception(f"找不到工作表: {SHEET_ID}")

            rows = ranges[SHEET_ID]
            if not rows or len(rows) < 2:
                log_sync("success", 0, "没有数据需要同步")
                print("没有数据需要同步")
                return 0

            # 跳过表头，从第二行开始
            record_count = 0
            for i, row in enumerate(rows[1:], start=2):
                if not row or len(row) < max(PHONE_COLUMN, REWARD_COLUMN):
                    print(f"第{i}行数据不完整，跳过")
                    continue

                phone = str(row[PHONE_COLUMN - 1]).strip()
                reward_raw = row[REWARD_COLUMN - 1]

                # 验证手机号
                if not phone or not phone.isdigit() or len(phone) != 11:
                    print(f"第{i}行手机号无效: {phone}，跳过")
                    continue

                # 解析奖励值
                try:
                    reward = float(reward_raw) if reward_raw else 0
                except (ValueError, TypeError):
                    print(f"第{i}行奖励值无效: {reward_raw}，跳过")
                    continue

                # 使用当天日期作为记录日期
                record_date = datetime.now().strftime("%Y-%m-%d")

                upsert_reward(phone, reward, record_date)
                record_count += 1

            log_sync("success", record_count, f"成功同步{record_count}条记录")
            print(f"[{datetime.now()}] 同步完成，共同步{record_count}条记录")
            return record_count

        except Exception as e:
            error_msg = str(e)
            log_sync("failed", 0, error_msg)
            print(f"[{datetime.now()}] 同步失败: {error_msg}")
            raise


# 全局同步器实例
syncer = TencentDocSync()


def sync_now():
    """手动触发同步"""
    return syncer.sync_data()
