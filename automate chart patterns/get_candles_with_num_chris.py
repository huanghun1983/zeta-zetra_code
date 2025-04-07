import requests
import time
import pandas as pd
from datetime import datetime
import os
import pytz

def get_okx_history_index_candles(instId="BTC-USDT", bar="1H", total_limit=1000, save_txt=True, save_csv=True):
    """
    获取 OKX history-index-candles 指数 K 线数据，支持自定义获取数量，并保存到 TXT 和 CSV 文件
    :param instId: 交易对，例如 "BTC-USDT"
    :param bar: K 线周期，例如 "1m", "15m", "1H", "1D"
    :param total_limit: 需要获取的 K 线数量，例如 1000
    :param save_txt: 是否保存为 TXT 文件
    :param save_csv: 是否保存为 CSV 文件
    :return: 返回拼接后的 K 线数据（DataFrame）
    """
    # base_url = "https://www.okx.com/api/v5/market/history-index-candles"
    base_url = "https://www.okx.com/api/v5/market/index-candles"
    max_limit = 300  # OKX 限制每次最多获取 300 条
    df = pd.DataFrame()  # 初始化空的 DataFrame
    last_timestamp = None  # 记录最后一条数据的时间戳

    while len(df) < total_limit:
        # 计算本次请求数量
        fetch_limit = min(max_limit, total_limit - len(df))

        # 构造请求参数
        params = {
            "instId": instId,
            "bar": bar,
            "limit": fetch_limit,
        }
        if last_timestamp:
            # params["before"] = last_timestamp  # 获取更早的 K 线数据
            params["after"] = last_timestamp  # 获取更早的 K 线数据

        # 尝试请求，最多重试 5 次
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(base_url, params=params, timeout=10)
                response.raise_for_status()  # 检查 HTTP 错误码
                data = response.json()

                # 如果请求成功且有数据，则跳出重试循环
                if "data" in data and data["data"]:
                    break
                else:
                    print(f"⚠️ [警告] 第 {attempt + 1} 次尝试：数据为空，等待 0.5 秒重试...")
                    time.sleep(0.5)

            except requests.exceptions.RequestException as e:
                print(f"❌ [错误] 第 {attempt + 1} 次尝试失败：{e}，等待 0.5 秒重试...")
                time.sleep(0.5)
        else:
            print("🚨 [严重错误] 5 次请求均失败，跳过本次数据获取")
            break  # 彻底放弃本次请求，继续后续流程

        # 获取新的 K 线数据并转换为 DataFrame
        new_candles = data["data"]
        new_df = pd.DataFrame(new_candles, columns=["Date", "Open", "High", "Low", "Close", "volume"])

        # # 使用 datetime 处理时间戳（避免大整数转换问题）
        # new_df["timestamp"] = pd.to_datetime(new_df["timestamp"], unit="ms")  # 转换时间戳
        # 使用 datetime 处理时间戳，避免大整数转换问题
        new_df["Date"] = pd.to_datetime(new_df["Date"], unit="ms")

        # 将时间戳转换为北京时间
        tz = pytz.timezone('Asia/Shanghai')  # 设置时区为北京时间
        new_df["Date"] = new_df["Date"].dt.tz_localize('UTC').dt.tz_convert(tz)

        # 如果数据是从大到小排列，则反转数据顺序
        new_df = new_df[::-1]

        # 合并数据并去重
        df = pd.concat([df, new_df]).drop_duplicates(subset=["Date"], keep="first").reset_index(drop=True)

        # 获取最后一条数据的时间戳（用于下一次分页请求）
        last_timestamp = new_candles[-1][0]  # 第 0 列是时间戳

        # 避免 API 访问频率过高，稍微休息 0.5 秒
        time.sleep(0.5)

    # 如果获取到的数据超过需要的数量，截取所需部分
    df = df.head(total_limit)

    # 按时间戳升序排序
    df = df.sort_values(by="Date", ascending=True).reset_index(drop=True)

    # 生成时间戳文件名（年月日时分秒）
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"{timestamp_str}_{instId}_{bar}_{total_limit}"

    # 获取当前脚本文件所在的目录
    script_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # 拼接文件路径
    txt_filename = os.path.join(script_dir, "data", f"{filename_base}.txt")
    csv_filename = os.path.join(script_dir, "data", f"{filename_base}.csv")

    # 保存为 TXT 文件
    if save_txt:
        df.to_csv(txt_filename, sep="\t", index=False)
        print(f"📄 K 线数据已保存为 TXT 文件: {txt_filename}")

    # 保存为 CSV 文件
    if save_csv:
        df.to_csv(csv_filename, index=False)
        print(f"📄 K 线数据已保存为 CSV 文件: {csv_filename}")

    return df

# 例子：获取 1000 条 BTC-USDT 的 1H K 线数据，并保存为 TXT 和 CSV
# df_candles = get_okx_history_index_candles(instId="BTC-USDT", bar="1H", total_limit=1000)
df_candles = get_okx_history_index_candles(instId="TURBO-USDT", bar="5m", total_limit=2000)
# df_candles = get_okx_history_index_candles(instId="BTC-USDT", bar="15m", total_limit=1000)
