"""
Date: 20230102

This program implements the Head and Shoulders pattern

Source: https://www.youtube.com/watch?v=Mxk8PP3vbuA
"""

import mplfinance as mpf 
import glob
import matplotlib.dates as mpdates
import matplotlib.pyplot as plt 
import numpy as np
import os
import pandas as pd
from scipy.stats import linregress
from progress.bar import Bar
from typing import List, Union
import time
import mplfinance as mpf


plt.style.use('seaborn-v0_8-darkgrid')

def pivot_id(ohlc: pd.DataFrame, l:int , n1:int , n2:int ):
    """
    Get the pivot id 

    :params ohlc is a dataframe

    :params l is the l'th row

    :params n1 is the number of candles to the left

    :params n2 is the number of candles to the right

    如果 ohlc["Low"] 在 n1 根左边 和 n2 根右边都是最小值，则是 局部低点（Pivot Low）。
    如果 ohlc["High"] 在 n1 根左边 和 n2 根右边都是最大值，则是 局部高点（Pivot High）。

    :return boolean  
    """
    
    # Check if the length conditions met
    if l-n1 < 0 or l+n2 >= len(ohlc):
        return 0
    
    pivot_low  = 1
    pivot_high = 1

    bar = Bar(f'Processing pivot for n1:{n1} and n2:{n2}', max=len(range(l-n1, l+n2+1)))

    # 如果遇到
    for i in range(l-n1, l+n2+1):
        # if ohlc.loc[l,"Low"] == ohlc.loc[i, "Low"] and i < l:
        #     pivot_low = 0
        if(ohlc.loc[l,"Low"] > ohlc.loc[i, "Low"]):
            pivot_low = 0

        # if ohlc.loc[l,"High"] == ohlc.loc[i, "High"] and i < l:
        #     pivot_high = 0
        if(ohlc.loc[l, "High"] < ohlc.loc[i, "High"]):
            pivot_high = 0

        bar.next()

    bar.finish()
    if pivot_low and pivot_high:
        return 3 # will never happened

    elif pivot_low:
        return 1

    elif pivot_high:
        return 2
    else:
        return 0


def pivot_point_position(row):
    """
    Get the Pivot Point position

    :params row of the ohlc dataframe
    """
   
    if row['Pivot']==1:
        return row['Low']-1e-3
    elif row['Pivot']==2:
        return row['Low']+1e-3
    else:
        return np.nan


def _find_points(df, candle_id, back_candles):
    """
    Find points provides all the necessary arrays and data of interest

    :params df        -> DataFrame with OHLC data
    :params candle_id -> current candle
    :params back_candles -> lookback period
    :return maxim, minim, xxmax, xxmin, maxacount, minacount, maxbcount, minbcount
    """

    maxim = np.array([])
    minim = np.array([])
    xxmin = np.array([])
    xxmax = np.array([])
    minbcount=0 #minimas before head
    maxbcount=0 #maximas before head
    minacount=0 #minimas after head
    maxacount=0 #maximas after head
    
    for i in range(candle_id-back_candles, candle_id+back_candles):
        # 这里是找到局部低点
        if df.loc[i,"ShortPivot"] == 1:
            minim = np.append(minim, df.loc[i, "Low"]) #低点的值
            xxmin = np.append(xxmin, i) #低点的索引  
            if i < candle_id:
                minbcount=+1 #头部前的低点数
            elif i>candle_id:
                minacount+=1 #头部后的低点数
        # 这里是找到局部高点
        if df.loc[i, "ShortPivot"] == 2:
            maxim = np.append(maxim, df.loc[i, "High"]) #高点的值
            xxmax = np.append(xxmax, i) #高点的索引
            if i < candle_id:
                maxbcount+=1 #头部前的高点数
            elif i>candle_id:
                maxacount+=1 #头部后的高点数
    
    print(f"_find_points return maxbcount:{maxbcount}, maxacount:{maxacount}")
    return maxim, minim, xxmax, xxmin, maxacount, minacount, maxbcount, minbcount

def find_inverse_head_and_shoulders(df, back_candles=14):
    """
    Find all the inverse head and shoulders chart patterns

    :params df -> an ohlc dataframe that has "ShortPivot" and "Pivot" as columns
    :params back_candles -> Look-back and look-forward period
    :returns all_points
    """
    all_points = []
    for candle_id in range(back_candles+20, len(df)-back_candles):
        
        if df.loc[candle_id, "Pivot"] != 1 or df.loc[candle_id,"ShortPivot"] != 1:
            continue
        

        maxim, minim, xxmax, xxmin, maxacount, minacount, maxbcount, minbcount = _find_points(df, candle_id, back_candles)
        if minbcount<1 or minacount<1 or maxbcount<1 or maxacount<1:
            continue

        slmax, intercmax, rmax, pmax, semax = linregress(xxmax, maxim)
        
        headidx = np.argmin(minim, axis=0)

        try:
            # if minim[headidx-1]-minim[headidx]>1.5e-3 and minim[headidx+1]-minim[headidx]>1.5e-3 and abs(slmax)<=1e-4:
            # 不管斜率看看 
            if minim[headidx-1]-minim[headidx]>1.5e-3 and minim[headidx+1]-minim[headidx]>1.5e-3: 
                all_points.append(candle_id)
        except:
            pass
            

    return all_points



def find_head_and_shoulders(df: pd.DataFrame, back_candles: int = 14) -> List[int]:
    """
    Find all head and shoulder chart patterns

    :params df -> an ohlc dataframe that has "ShortPivot" and "Pivot" as columns
    :type :pd.DataFrame

    :params back_candles -> Look-back and look-forward period
    :type :int
    
    :returns all_points
    """
    all_points = []
    for candle_id in range(back_candles+20, len(df)-back_candles):
        
        if df.loc[candle_id, "Pivot"] != 2 or df.loc[candle_id,"ShortPivot"] != 2:
            continue
         
        maxim, minim, xxmax, xxmin, maxacount, minacount, maxbcount, minbcount = _find_points(df, candle_id, back_candles)
        if minbcount<1 or minacount<1 or maxbcount<1 or maxacount<1:
            continue

        slmin, intercmin, rmin, pmin, semin = linregress(xxmin, minim)
        headidx = np.argmax(maxim, axis=0)

        all_points.append(candle_id)
        # if maxim[headidx]-maxim[headidx-1]>1.5e-3 and maxim[headidx]-maxim[headidx+1]>1.5e-3 and abs(slmin)<=1e-4: 
        # if maxim[headidx]-maxim[headidx-1]>1.5e-3 and maxim[headidx]-maxim[headidx+1]>1.5e-3: 
        #     all_points.append(candle_id)
            
    return all_points

def delete_continuous_pivot(x, y):
    """
    minim和maxim的连续点去掉

    """
    # 初始化一个布尔掩码，用于标记保留的元素
    mask = np.ones(len(x), dtype=bool)

    # 从前往后检查：如果后一个比前一个大1，就把前一个设为False（不保留）
    for i in range(len(x) - 1):
        if x[i + 1] - x[i] == 1:
            mask[i] = False

    # 应用掩码，生成新的数组
    return x[mask], y[mask]

def get_hs_xy(xxmax, maxim, xxmin, minim, hs=True):
    """
    识别以(xxmax, maxim)为头肩，
    以xxmin, minim为颈线的点，并返回对应的hsx和hsy

    如果想识别倒头肩底，则只要将传入的xxmax,maxim和xxmin,minim位置互换即可
    
    其中针对不完全满足头肩底的情况，也返回假头肩底的结果供参考
    """
    hsx = []        
    hsy = []

    # 是否是真头肩的标记
    is_true_hs = True

    # 2. hs，找到最高的点
    try:
        # 2. 初始化头肩底的下标，因为当前数据不一定够，如果没有头肩底，则找到一头一肩作为M头也可以
        # 这里的_indx指的是numpy里面的索引，而_val才是ohlc.loc里面的行号
        left_shoulder_indx = None
        neckline_left_indx = None
        head_indx = None
        neckline_right_indx = None
        right_shoulder_indx = None

        # 这里的_val指的是ohlc.loc里面的行号
        left_shoulder_val = None
        neckline_left_val = None
        head_val = None
        neckline_right_val = None
        right_shoulder_val = None

        # 如果hs为True，则head找最大值，否则head找最小值
        if hs:
            head_indx = np.argmax(maxim, axis=0)
        else:
            head_indx = np.argmin(maxim, axis=0)
        # 如果headidx前后都有值，则取前后两个点作为hs的起始点
        #        __
        #     __/  \__ 
        #    /        \
        #    LS   H   RS
        if head_indx > 0 and head_indx < len(maxim) - 1:
            left_shoulder_indx = head_indx - 1
            left_shoulder_val = xxmax[head_indx - 1]
            head_val = xxmax[head_indx]
            right_shoulder_indx = head_indx + 1
            right_shoulder_val = xxmax[head_indx + 1]

        # 如果headidx后面没有值，但是maxim里面的元素有3个，则也算一种假头肩，只是头部在最后
        elif head_indx > 0 and len(maxim) >=3:
            head_indx = head_indx - 1 # head前移一位，返回头部在最后的假头肩
            left_shoulder_indx = head_indx - 1
            left_shoulder_val = xxmax[head_indx - 1]
            head_val = xxmax[head_indx]
            right_shoulder_indx = head_indx + 1
            right_shoulder_val = xxmax[head_indx + 1]
            is_true_hs = False

        # 如果headidx后面没有值并且不到3个元素，则只有一个头一个肩
        #        __
        #     __/  |
        #    /        
        #    LS   H   
        elif head_indx > 0:
            left_shoulder_indx = head_indx - 1
            left_shoulder_val = xxmax[head_indx - 1]
            head_val = xxmax[head_indx] 

        # 如果headidx前面没有值，但是maxim里面的元素有3个，则也算一种假头肩，只是头部在前面
        elif head_indx < len(maxim) - 1 and len(maxim) >=3:
            head_indx = head_indx + 1 # head后移一位，返回头部在最前的假头肩
            left_shoulder_indx = head_indx - 1
            left_shoulder_val = xxmax[head_indx - 1]
            head_val = xxmax[head_indx]
            right_shoulder_indx = head_indx + 1
            right_shoulder_val = xxmax[head_indx + 1]
            is_true_hs = False

        # 如果headidx前面没有值并且不到3个元素，则只有一个头一个肩
        #     __
        #    |  \__ 
        #          \
        #      H   RS
        elif head_indx < len(maxim) - 1:
            head_val = xxmax[head_indx]
            right_shoulder_indx = head_indx + 1
            right_shoulder_val = xxmax[head_indx + 1]
        # 如果headidx前后都没有值，则说明只有一个头部，继续
        else:
            print("there is only one head, continue")
            return None, None, is_true_hs

        for idx, val in enumerate(xxmin):
            # 如果左肩存在，则找到左肩和头部中的点作为neckline_left
            if left_shoulder_val is not None and left_shoulder_val < val < head_val:
                neckline_left_indx = idx
                neckline_left_val = val
            # 如果右肩存在，则找到头部和右肩中的点作为neckline_right
            elif right_shoulder_val is not None and head_val < val < right_shoulder_val:
                neckline_right_indx = idx
                neckline_right_val = val
            # 如果左肩不存在，则找到头部前面的点作为neckline_left
            if left_shoulder_val is None and val < head_val:
                neckline_left_indx = idx
                neckline_left_val = val
            # 如果右肩不存在，则找到头部后面的点作为neckline_right
            if right_shoulder_val is None and val > head_val:
                neckline_right_indx = idx
                neckline_right_val = val

            # 如果两个都找到了就跳出
            if neckline_left_val is not None and neckline_right_val is not None:
                break

        # 只将有的赋值
        # 左肩
        if left_shoulder_val is not None:
            # hsx = hsx.append(ohlc.loc[left_shoulder_val, "Date"])
            hsx.append(ohlc.loc[left_shoulder_val, "Date"])
            hsy.append(maxim[left_shoulder_indx])
        # 左颈
        if neckline_left_val is not None:
            # hsx = hsx.append(ohlc.loc[neckline_left_val, "Date"])
            hsx.append(ohlc.loc[neckline_left_val, "Date"])
            hsy.append(minim[neckline_left_indx])
        # 头部
        # hsx = hsx.append(ohlc.loc[head_val, "Date"])
        hsx.append(ohlc.loc[head_val, "Date"])
        hsy.append(maxim[head_indx])
        # 右颈
        if neckline_right_val is not None:
            # hsx = hsx.append(ohlc.loc[neckline_right_val, "Date"])
            hsx.append(ohlc.loc[neckline_right_val, "Date"])
            hsy.append(minim[neckline_right_indx])
        # 右肩
        if right_shoulder_val is not None:
            # hsx = hsx.append(ohlc.loc[right_shoulder_val, "Date"])
            hsx.append(ohlc.loc[right_shoulder_val, "Date"])
            hsy.append(maxim[right_shoulder_indx])
        
        return hsx, hsy, is_true_hs
    except:
            print("data not enough, continue")
            return None, None, is_true_hs

def save_plot(ohlc, all_points, back_candles, analysis_file, fname="head_and_shoulders", hs=True):
    """
    Save all the graphs

    :params ohlc         -> dataframe that has OHLC data
    :params all_points   -> points
    :params back_candles -> number of periods to lookback
    :params fname -> filename
    :params hs -> Is it head and shoulders or inverse head and shoulders
    :return 
    """

    total = len(all_points)
    bar = Bar(f'Processing {fname} images', max=total)

    for j, point in enumerate(all_points):

        maxim = np.array([])
        minim = np.array([])
        xxmin = np.array([])
        xxmax = np.array([])
        ohlc["HS"] = np.nan

        for i in range(point-back_candles, point+back_candles):
            if ohlc.loc[i,"ShortPivot"] == 1:
                minim = np.append(minim, ohlc.loc[i, "Low"])
                xxmin = np.append(xxmin, i)        

            if ohlc.loc[i, "ShortPivot"] == 2:
                maxim = np.append(maxim, ohlc.loc[i, "High"])
                xxmax = np.append(xxmax, i)              
        
        # 1. 删除连续的点
        xxmin, minim = delete_continuous_pivot(xxmin, minim)
        xxmax, maxim = delete_continuous_pivot(xxmax, maxim)

        # 2. 找到头肩底的下标，因为当前数据不一定够，如果没有头肩底，则找到一头一肩作为M头也可以
        hsx = None
        hsy = None

        # 3. hs为true则找头肩，为false则找倒头肩底
        is_true_hs = True
        if hs:
            hsx, hsy, is_true_hs = get_hs_xy(xxmax, maxim, xxmin, minim, hs)
        else:
            hsx, hsy, is_true_hs = get_hs_xy(xxmin, minim, xxmax, maxim, hs)
        
        if hsx is None or hsy is None:
            print("no hs found, continue")
            bar.next()
            continue

        # if hs:
        #     headidx = np.argmax(maxim, axis=0)  
        #     hsx = ohlc.loc[[xxmax[headidx-1],xxmin[0],xxmax[headidx],xxmin[1],xxmax[headidx+1] ],"Date"]
        #     hsy = [maxim[headidx-1], minim[0], maxim[headidx], minim[1], maxim[headidx+1]]
        # else:

        #     headidx = np.argmin(minim, axis=0)
        #     hsx = ohlc.loc[[xxmin[headidx-1],xxmax[0],xxmin[headidx],xxmax[1],xxmin[headidx+1] ],"Date"]
        #     hsy = [minim[headidx-1], maxim[0], minim[headidx], maxim[1], minim[headidx+1]]

        ohlc_copy = ohlc.copy()
        ohlc_copy.set_index("Date", inplace=True)
        
        levels = [(x,y) for x,y in zip(hsx,hsy)]

        for l in levels:
            ohlc_copy.loc[l[0].strftime("%Y-%m-%dT%H:%M:%S.%f"),"HS"] = l[1]

        ohlc_hs  = ohlc_copy.iloc[point-(back_candles+6):point+back_candles+6, : ]
        hs_l       = mpf.make_addplot(ohlc_hs["HS"], type="scatter", color='r', marker="v", markersize=200)

        # 添加对没有目录的容错处理，避免保存文件时报错，by chris
        # save_   = os.path.join( dir_,'images','analysis',fn)
        # 文件保存路径
        file_name_without_extension = os.path.splitext(os.path.basename(analysis_file))[0]
        save_dir = os.path.join(dir_, 'images', 'analysis', file_name_without_extension)
        
        # 检查目录是否存在，如果不存在则创建
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        fn      = f"{fname}-{'T' if is_true_hs else 'F'}-{point}-{ohlc.loc[point, 'Date'].strftime('%Y%m%d-%H%M')}.png"
        save_   = os.path.join(save_dir, fn)
        mpf.plot(ohlc_hs,
                type='candle',
                style='charles',
                addplot=[hs_l],
                alines=dict(alines=levels,colors=['purple'], alpha=0.5,linewidths=10),
                savefig=f"{save_}"
                )

        bar.next()
    bar.finish()
    return

def print_pivot_values(pivot_series):
    """
    打印 Pivot 值为 1（Low 点）和 2（High 点）的索引和值

    :param pivot_series: 一个 pandas.Series，例如 ohlc["Pivot"]
    """
    print("🔻 Pivot == 1 的行（代表 Low 点）:")
    pivot_1 = pivot_series[pivot_series == 1]
    for idx, val in pivot_1.items():
        print(f"👉 Index: {idx}, Pivot: {val} (Low)")

    print("\n🟢 Pivot == 2 的行（代表 High 点）:")
    pivot_2 = pivot_series[pivot_series == 2]
    for idx, val in pivot_2.items():
        print(f"👉 Index: {idx}, Pivot: {val} (High)")

    print("\n🔻🟢 Pivot == 2 的行（代表极点）:")
    pivot_2 = pivot_series[(pivot_series == 1) | (pivot_series == 2)]
    for idx, val in pivot_2.items():
        print(f"👉 Index: {idx}, Pivot: {val} (High)")



if __name__ == "__main__":
    # 记录开始时间
    start_time = time.time()

    dir_ = os.path.realpath('').split("research")[0]
    # file = os.path.join( dir_,'data','eurusd-4h.csv') 
    file = os.path.join( dir_,'data','20250403_214832_TURBO-USDT_5m_2000.csv') 

    df = pd.read_csv(file)

    ohlc = df.loc[:, ["Date", "Open", "High", "Low", "Close"] ]
    ohlc["Date"] = pd.DatetimeIndex(ohlc["Date"]) 

   
    ohlc["Pivot"] = ohlc.apply(lambda x: pivot_id(ohlc, x.name, 15, 15), axis=1)
    print_pivot_values(ohlc["Pivot"])

    ohlc['ShortPivot'] = ohlc.apply(lambda x: pivot_id(df, x.name,5,5), axis=1)
    print_pivot_values(ohlc["ShortPivot"])

    ohlc['PointPos'] = ohlc.apply(lambda row: pivot_point_position(row), axis=1)
    print_pivot_values(ohlc["PointPos"])
 
    # back_candles =14
    back_candles =20
    all_points         = find_head_and_shoulders(ohlc,back_candles=back_candles)
    # all_points_inverse = find_inverse_head_and_shoulders(ohlc, back_candles=back_candles)
    
    # Save plots
    save_plot(ohlc, all_points, back_candles, file, fname="hs", hs=True)
    save_plot(ohlc, all_points, back_candles, file, fname="ihs", hs=False)
    # save_plot(ohlc, all_points_inverse, back_candles, file, fname="inverse_head_and_shoulders", hs=False)

    # 原始的数据也画个图做对比
    # 文件保存路径
    file_name_without_extension = os.path.splitext(os.path.basename(file))[0]
    save_dir = os.path.join(dir_, 'images', 'analysis', file_name_without_extension)
    
    # 检查目录是否存在，如果不存在则创建
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_png = os.path.join(save_dir, f"{file_name_without_extension}.png")
    # 转换Date列为datetime类型
    df["Date"] = pd.to_datetime(df["Date"])
    # df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y %H:%M:%S.%f", dayfirst=True)

    # 将Date列设置为索引
    df.set_index("Date", inplace=True)

    # 调整涨跌颜色
    mc = mpf.make_marketcolors(up='#00FF00', down='#FF0000', wick={'up': 'green', 'down': 'red'}, edge={'up': 'green', 'down': 'red'})
    # 创建高清风格
    # s = mpf.make_mpf_style(marketcolors=mc, gridcolor='gray', gridstyle='--')
    # # 绘制K线图并保存为PNG文件
    # mpf.plot(df, type='candle', style=s, title="K-Line", ylabel="Price", 
    #          ylabel_lower="Volume", savefig=file_png)
    # 绘制 K 线图
    # mpf.plot(df, type='candle', style=s, title="K-Line", ylabel="Price", ylabel_lower="Volume",
    mpf.plot(df, type='candle', style="charles", title="K-Line", ylabel="Price", ylabel_lower="Volume",
            figsize=(12, 6),  # 调整图像大小
            # line_width=1.2,  # 增加 K 线宽度
            figratio=(3, 2),
            savefig=dict(fname=file_png, dpi=300, bbox_inches="tight"))  # 提高分辨率

    # 记录结束时间
    end_time = time.time()

    # 计算总执行时间
    execution_time = end_time - start_time

    # 打印总执行时间
    print(f"Total execution time: {execution_time:.2f} seconds")