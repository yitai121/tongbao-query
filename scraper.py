"""
通宝奖励查询系统 - 浏览器自动抓取模块
"""
import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright
from database import upsert_reward, log_sync


async def fetch_tencent_doc_data():
    """使用Playwright抓取腾讯文档数据"""
    print(f"[{datetime.now()}] 开始抓取腾讯文档...")

    doc_url = "https://docs.qq.com/sheet/DT2VMQU1PbkhXWWpJ"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # 捕获网络请求，获取表格数据
        sheet_data = []

        async def handle_response(response):
            url = response.url
            # 腾讯文档的数据API
            if 'dop-api' in url or 'sheet' in url.lower():
                try:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if 'json' in content_type or 'text' in content_type:
                            data = await response.text()
                            # 尝试解析JSON
                            try:
                                json_data = json.loads(data)
                                sheet_data.append(json_data)
                            except:
                                pass
                except:
                    pass

        page.on('response', handle_response)

        try:
            # 访问文档 - 使用更宽松的等待条件
            await page.goto(doc_url, wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(8000)  # 等待数据加载

            # 尝试从页面提取表格数据
            table_data = await page.evaluate('''() => {
                // 尝试从DOM提取表格
                const rows = [];
                const tableRows = document.querySelectorAll('tr, .row, [data-row]');
                tableRows.forEach(row => {
                    const cells = [];
                    const cellElements = row.querySelectorAll('td, .cell, [data-cell]');
                    cellElements.forEach(cell => {
                        cells.push(cell.textContent.trim());
                    });
                    if (cells.length > 0) {
                        rows.push(cells);
                    }
                });
                return rows;
            }''')

            await browser.close()

            # 处理抓取到的数据
            if table_data and len(table_data) > 1:
                return process_sheet_data(table_data)
            elif sheet_data:
                return process_api_data(sheet_data)
            else:
                raise Exception("未能抓取到表格数据")

        except Exception as e:
            await browser.close()
            raise Exception(f"抓取失败: {e}")


def process_sheet_data(table_data):
    """处理从DOM提取的表格数据"""
    record_count = 0
    today = datetime.now().strftime("%Y-%m-%d")

    # 跳过表头
    for i, row in enumerate(table_data[1:], start=2):
        if len(row) < 2:
            continue

        phone = str(row[0]).strip()
        reward_raw = str(row[1]).strip()

        # 验证手机号
        if not phone or not phone.isdigit() or len(phone) != 11:
            continue

        # 解析奖励值
        try:
            reward = float(reward_raw) if reward_raw else 0
        except (ValueError, TypeError):
            continue

        upsert_reward(phone, reward, today)
        record_count += 1

    log_sync("success", record_count, f"浏览器抓取成功，共同步{record_count}条记录")
    print(f"[{datetime.now()}] 抓取完成，共同步{record_count}条记录")
    return record_count


def process_api_data(api_data):
    """处理从API捕获的数据"""
    # 这里需要根据实际的API响应格式来解析
    # 暂时返回0，后续可以根据实际数据格式完善
    print(f"[{datetime.now()}] 捕获到API数据，但需要进一步解析")
    return 0


def fetch_now():
    """手动触发抓取"""
    return asyncio.run(fetch_tencent_doc_data())


if __name__ == "__main__":
    # 测试抓取
    count = fetch_now()
    print(f"共同步 {count} 条记录")
