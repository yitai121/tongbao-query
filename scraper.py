"""
通宝奖励查询系统 - 腾讯文档 API 同步模块
使用腾讯文档 Open API V3 读取在线表格数据

数据结构：
- "账号" sheet：姓名→手机号映射（按分组：商学院、服务团队、CMO）
- "商学院总数据" sheet：列头为姓名，每行为奖励数据
- "服务团队总数据" sheet：同上，服务团队的奖励数据
"""
import requests
from datetime import datetime
from config import (
    DOC_ID, SHEET_ID,
    TENCENT_DOC_ACCESS_TOKEN, TENCENT_DOC_OPEN_ID, TENCENT_DOC_APP_ID
)
from database import upsert_reward, log_sync


# 腾讯文档 API 基础 URL
API_BASE = "https://docs.qq.com/openapi/spreadsheet/v3"


def _build_headers():
    """构造 API 请求头"""
    return {
        "Access-Token": TENCENT_DOC_ACCESS_TOKEN,
        "Open-Id": TENCENT_DOC_OPEN_ID,
        "Client-Id": TENCENT_DOC_APP_ID,
        "Accept": "application/json",
    }


def _get_cell_text(cell):
    """从单元格提取文本值"""
    cv = cell.get("cellValue") or {}
    text = cv.get("text", "")
    if not text:
        for v in cv.values():
            if isinstance(v, str):
                text = v
                break
            elif isinstance(v, (int, float)):
                text = str(v)
                break
    return text


def _fetch_sheet_range(sheet_id, range_str):
    """获取指定 sheet 的指定范围数据"""
    url = f"{API_BASE}/files/{DOC_ID}/{sheet_id}/{range_str}"
    headers = _build_headers()
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # 错误检查（API 可能返回 code 或 ret 字段）
    if data.get("code", 0) != 0 and data.get("ret", 0) != 0:
        msg = data.get("message", data.get("msg", "未知错误"))
        raise Exception(f"API返回错误: {msg}")

    grid = data.get("gridData", data.get("data", {}).get("gridData", {}))
    return grid.get("rows", [])


def _parse_rows(rows):
    """将 API 返回的 rows 解析为二维文本数组"""
    result = []
    for row in rows:
        vals = [_get_cell_text(c) for c in row.get("values", [])]
        result.append(vals)
    return result


def get_sheet_metadata():
    """获取所有工作表的元数据（sheetId、标题、大小等）"""
    url = f"{API_BASE}/files/{DOC_ID}?concise=1"
    headers = _build_headers()
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("properties", [])


def build_name_phone_map():
    """
    从"账号" sheet 构建 姓名→手机号 映射

    账号 sheet 结构：
    - 分组标题行（商学院/服务团队/CMO）
    - 姓名列
    - 手机号行
    - 重复...
    """
    rows = _fetch_sheet_range("ttk1x4", "A1:Z50")
    table = _parse_rows(rows)

    name_phone = {}
    i = 0
    while i < len(table):
        row = table[i]
        first = row[0].strip() if row else ""

        # 检测分组标题（只有一个单元格有内容，且不是手机号）
        if first and not first.isdigit():
            # 下一行是姓名，再下一行是手机号
            if i + 2 < len(table):
                names = table[i + 1]
                phones = table[i + 2]
                for j in range(min(len(names), len(phones))):
                    name = names[j].strip()
                    phone = phones[j].strip()
                    if name and phone and phone.isdigit() and len(phone) == 11:
                        name_phone[name] = phone
                i += 3
            else:
                i += 1
        else:
            i += 1

    print(f"[{datetime.now()}] 构建姓名→手机号映射: {len(name_phone)} 人")
    return name_phone


def fetch_reward_data(sheet_id, name_phone_map):
    """
    从数据 sheet 读取奖励数据，按手机号写入数据库

    数据 sheet 结构：
    - 第0行：列头，A1="姓名时间"，B1=姓名1，C1=姓名2，...
    - 第1行起：每行是奖励数据，B列=姓名1的奖励，C列=姓名2的奖励，...
    - 每个手机号存储所有行的奖励总和
    """
    rows = _fetch_sheet_range(sheet_id, "A1:Z200")
    table = _parse_rows(rows)

    if not table:
        return 0

    # 第0行是列头，提取姓名→列索引
    header = table[0]
    col_names = {}
    for col_idx, name in enumerate(header):
        name = name.strip()
        if name and name in name_phone_map:
            col_names[col_idx] = name

    if not col_names:
        print(f"[{datetime.now()}] Sheet {sheet_id}: 未找到匹配的姓名列")
        return 0

    # 先汇总每个手机号的总奖励
    phone_rewards = {}
    for row in table[1:]:
        for col_idx, name in col_names.items():
            if col_idx >= len(row):
                continue

            reward_raw = row[col_idx].strip()
            try:
                reward = float(reward_raw) if reward_raw else 0
            except (ValueError, TypeError):
                continue

            phone = name_phone_map[name]
            phone_rewards[phone] = phone_rewards.get(phone, 0) + reward

    # 写入数据库
    today = datetime.now().strftime("%Y-%m-%d")
    record_count = 0
    for phone, total_reward in phone_rewards.items():
        upsert_reward(phone, total_reward, today)
        record_count += 1

    print(f"[{datetime.now()}] Sheet {sheet_id}: 处理 {record_count} 人，总奖励 {sum(phone_rewards.values()):.2f}")
    return record_count


def fetch_now():
    """手动触发同步"""
    try:
        # 1. 构建姓名→手机号映射
        name_phone_map = build_name_phone_map()
        if not name_phone_map:
            log_sync("failed", 0, "未能构建姓名→手机号映射")
            return 0

        # 2. 获取所有 sheet 元数据
        sheets = get_sheet_metadata()
        sheet_titles = {s["sheetId"]: s.get("title", "") for s in sheets}

        # 3. 从数据 sheet 读取奖励数据
        # 已知数据 sheet：商学院总数据(BB08J2)、服务团队总数据(9xae30)
        data_sheets = []
        for sid, title in sheet_titles.items():
            if "总数据" in title:
                data_sheets.append((sid, title))

        total_count = 0
        for sid, title in data_sheets:
            try:
                count = fetch_reward_data(sid, name_phone_map)
                total_count += count
            except Exception as e:
                print(f"[{datetime.now()}] 处理 {title} 失败: {e}")

        log_sync("success", total_count, f"API同步成功，共同步{total_count}条记录")
        print(f"[{datetime.now()}] 同步完成，共同步{total_count}条记录")
        return total_count

    except Exception as e:
        print(f"[{datetime.now()}] 同步失败: {e}")
        log_sync("failed", 0, f"同步失败: {e}")
        raise


if __name__ == "__main__":
    # 测试同步
    count = fetch_now()
    print(f"共同步 {count} 条记录")
