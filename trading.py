import requests
import json
import datetime
import time
import keyring
import pandas as pd
import os

APP_KEY = keyring.get_password('real_app_key', 'occam123')
APP_SECRET = keyring.get_password('real_app_secret', 'occam123')
URL_BASE = "https://openapi.koreainvestment.com:9443"  # 실전 투자
CANO = keyring.get_password('CANO', 'occam123')
ACNT_PRDT_CD = '01'


def get_access_token():
    """토큰 발급"""
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET}
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"
    res = requests.post(URL, headers=headers, data=json.dumps(body))
    ACCESS_TOKEN = res.json()["access_token"]
    return ACCESS_TOKEN


def hashkey(datas):
    """암호화"""
    PATH = "uapi/hashkey"
    URL = f"{URL_BASE}/{PATH}"
    headers = {
        'content-Type': 'application/json',
        'appKey': APP_KEY,
        'appSecret': APP_SECRET,
    }
    res = requests.post(URL, headers=headers, data=json.dumps(datas))
    hashkey = res.json()["HASH"]
    return hashkey


def get_current_price(code="005930"):  # 주식 현재가 시세
    """현재가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010100"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
    }
    res = requests.get(URL, headers=headers, params=params)
    return int(res.json()['output']['stck_prpr']), float(res.json()['output']['prdy_vrss_vol_rate'])  # 전일 대비 거래량 비율
    # Return: 주식 현재가, 전일 대비 거래량 비율


def get_target_price(code="005930"):
    """전날 종가 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-daily-price"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010400"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,
        "fid_org_adj_prc": "1",
        "fid_period_div_code": "D"
    }
    res = requests.get(URL, headers=headers, params=params)
    stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
    target_price = stck_clpr
    return target_price


def get_stock_5d_before():
    def get_stock_before(date):
        PATH = "uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        URL = f"{URL_BASE}/{PATH}"
        headers = {"Content-Type": "application/json",
                   "authorization": f"Bearer {ACCESS_TOKEN}",
                   "appKey": APP_KEY,
                   "appSecret": APP_SECRET,
                   "tr_id": "TTTC8001R",  # 실전 투자 "TTTC8001R", 모의투자 "VTTC8001R"
                   "custtype": "P",
                   }
        params = {
            "CANO": CANO,
            "ACNT_PRDT_CD": ACNT_PRDT_CD,
            "INQR_STRT_DT": date,
            "INQR_END_DT": date,
            "SLL_BUY_DVSN_CD": "02",  # 00:전체, 01:매도, 02:매수
            "INQR_DVSN": "01",  # 00: 역순
            "PDNO": "",
            "CCLD_DVSN": "01",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "01",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        res = requests.get(URL, headers=headers, params=params)
        stock_dict = res.json()['output1']
        return stock_dict

    prev = 7
    while prev < 15:
        t_previous_5d = datetime.datetime.now().date() - datetime.timedelta(days=prev)
        t_previous_5d = t_previous_5d.strftime("%Y%m%d")
        bought_previous_5d_dict = get_stock_before(t_previous_5d)
        if len(bought_previous_5d_dict) > 0:
            break
        else:
            prev += 1
    sell_list_5d_over = []
    for stock in bought_previous_5d_dict:
        sell_list_5d_over.append(stock['pdno'])
    sell_list_5d_over = list(set(sell_list_5d_over))
    return sell_list_5d_over


def get_stock_balance():
    """주식 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-balance"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8434R",  # 실전 투자 "TTTC8434R" 모의투자 "VTTC8434R"
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    res = requests.get(URL, headers=headers, params=params)
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    print(f"====주식 보유잔고====")
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = [stock['hldg_qty'], stock['ord_psbl_qty'],
                                         stock['evlu_pfls_rt']]  # 0: 보유 수량, 1: 평가수익율
            print(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
            time.sleep(0.1)
    print(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    time.sleep(0.1)
    print(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    time.sleep(0.1)
    print(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    time.sleep(0.1)
    print(f"=================")
    return stock_dict


def get_balance():
    """현금 잔고조회"""
    PATH = "uapi/domestic-stock/v1/trading/inquire-psbl-order"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC8908R",  # 실전 투자 : "TTTC8908R" 모의투자 "VTTC8908R"
               "custtype": "P",
               }
    params = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": "005930",
        "ORD_UNPR": "65500",
        "ORD_DVSN": "01",
        "CMA_EVLU_AMT_ICLD_YN": "Y",
        "OVRS_ICLD_YN": "Y"
    }
    res = requests.get(URL, headers=headers, params=params)
    cash = res.json()['output']['ord_psbl_cash']
    print(f"주문 가능 현금 잔고: {cash}원")
    return int(cash)


def get_transactions(code="005930"):
    """현재 체결 조회"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-ccnl"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010300"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,

    }
    res = requests.get(URL, headers=headers, params=params)

    stck_cntg_hour = datetime.datetime.strptime(res.json()['output'][1]['stck_cntg_hour'], '%H%M%S').time()
    stck_prpr = int(res.json()['output'][1]['stck_prpr'])  # 현재가
    prdy_vrss = int(res.json()['output'][1]['prdy_vrss'])  # 전일대비
    prdy_vrss_sign = int(res.json()['output'][1]['prdy_vrss_sign'])  # 전일대비
    cntg_vol = int(res.json()['output'][1]['cntg_vol'])  # 체결 거래량
    tday_rltv = float(res.json()['output'][1]['tday_rltv'])  # 당일 체결 강도

    return stck_cntg_hour, stck_prpr, prdy_vrss, prdy_vrss_sign, cntg_vol, tday_rltv


def get_orderbook(code="005930"):
    """현재 호가 예상 체결"""
    PATH = "uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    URL = f"{URL_BASE}/{PATH}"
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "FHKST01010200"}
    params = {
        "fid_cond_mrkt_div_code": "J",
        "fid_input_iscd": code,

    }
    res = requests.get(URL, headers=headers, params=params)

    aspr_acpt_hour = datetime.datetime.strptime(res.json()['output1']['aspr_acpt_hour'],'%H%M%S').time()

    askp_rsqn1 = int(res.json()['output1']['askp_rsqn1'])  # 매도호가 잔량1
    askp_rsqn2 = int(res.json()['output1']['askp_rsqn2'])  # 매도호가 잔량2
    askp_rsqn3 = int(res.json()['output1']['askp_rsqn3'])  # 매도호가 잔량3
    askp_rsqn4 = int(res.json()['output1']['askp_rsqn4'])  # 매도호가 잔량4
    askp_rsqn5 = int(res.json()['output1']['askp_rsqn5'])  # 매도호가 잔량5
    askp_rsqn6 = int(res.json()['output1']['askp_rsqn6'])  # 매도호가 잔량6
    askp_rsqn7 = int(res.json()['output1']['askp_rsqn7'])  # 매도호가 잔량7
    askp_rsqn8 = int(res.json()['output1']['askp_rsqn8'])  # 매도호가 잔량8
    askp_rsqn9 = int(res.json()['output1']['askp_rsqn9'])  # 매도호가 잔량9
    askp_rsqn10 = int(res.json()['output1']['askp_rsqn10'])  # 매도호가 잔량10

    bidp_rsqn1 = int(res.json()['output1']['bidp_rsqn1'])  # 매수호가 잔량1
    bidp_rsqn2 = int(res.json()['output1']['bidp_rsqn2'])  # 매수호가 잔량2
    bidp_rsqn3 = int(res.json()['output1']['bidp_rsqn3'])  # 매수호가 잔량3
    bidp_rsqn4 = int(res.json()['output1']['bidp_rsqn4'])  # 매수호가 잔량4
    bidp_rsqn5 = int(res.json()['output1']['bidp_rsqn5'])  # 매수호가 잔량5
    bidp_rsqn6 = int(res.json()['output1']['bidp_rsqn6'])  # 매수호가 잔량6
    bidp_rsqn7 = int(res.json()['output1']['bidp_rsqn7'])  # 매수호가 잔량7
    bidp_rsqn8 = int(res.json()['output1']['bidp_rsqn8'])  # 매수호가 잔량8
    bidp_rsqn9 = int(res.json()['output1']['bidp_rsqn9'])  # 매수호가 잔량9
    bidp_rsqn10 = int(res.json()['output1']['bidp_rsqn10'])  # 매수호가 잔량10

    antc_cnpr = int(res.json()['output2']['antc_cnpr'])  # 예상체결가
    antc_vol = int(res.json()['output2']['antc_vol'])  # 예상 거래량

    return aspr_acpt_hour, askp_rsqn1, askp_rsqn2, askp_rsqn3, askp_rsqn4, askp_rsqn5, askp_rsqn6, askp_rsqn7, askp_rsqn8, askp_rsqn9, askp_rsqn10, \
           bidp_rsqn1, bidp_rsqn2, bidp_rsqn3, bidp_rsqn4, bidp_rsqn5, bidp_rsqn6, bidp_rsqn7, bidp_rsqn8, bidp_rsqn9, bidp_rsqn10, antc_cnpr, antc_vol


def buy(code="005930", qty="1", buy_price="0"):
    """주식 시장가 매수"""
    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": "00",
        "ORD_QTY": qty,
        "ORD_UNPR": buy_price,
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0802U",  # 실전 투자 : "TTTC0802U" 모의투자 'VTTC0802U'
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        print(f"[매수 성공]{str(res.json())}")
        return True
    else:
        print(f"[매수 실패]{str(res.json())}")
        return False


def sell(code="005930", qty="1", sell_price="0", sell_type="00"):
    """주식 시장가 매도"""

    PATH = "uapi/domestic-stock/v1/trading/order-cash"
    URL = f"{URL_BASE}/{PATH}"
    data = {
        "CANO": CANO,
        "ACNT_PRDT_CD": ACNT_PRDT_CD,
        "PDNO": code,
        "ORD_DVSN": sell_type,
        "ORD_QTY": qty,
        "ORD_UNPR": sell_price,
    }
    headers = {"Content-Type": "application/json",
               "authorization": f"Bearer {ACCESS_TOKEN}",
               "appKey": APP_KEY,
               "appSecret": APP_SECRET,
               "tr_id": "TTTC0801U",  # 실전 투자 : TTTC0801U "VTTC0801U"
               "custtype": "P",
               "hashkey": hashkey(data)
               }
    res = requests.post(URL, headers=headers, data=json.dumps(data))
    if res.json()['rt_cd'] == '0':
        print(f"[매도 성공]{str(res.json())}")
        return True
    else:
        print(f"[매도 실패]{str(res.json())}")
        return False


ACCESS_TOKEN = get_access_token()


def ho(x):
    if x >= 500000:
        return 1000
    elif x >= 100000:
        return 500
    elif x >= 50000:
        return 100
    elif x >= 10000:
        return 50
    elif x >= 5000:
        return 10
    elif x > 1000:
        return 5
    else:
        return 1


def auto_trading():  # 매수 희망 종목 리스트
    print("===국내 주식 자동매매 프로그램을 시작합니다===")

    data_all = pd.DataFrame()
    symbol_list = ['090410']

    # 자동매매 시작
    try:

        while True:

            t_now = datetime.datetime.now()
            t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
            t_start = t_now.replace(hour=9, minute=1, second=0, microsecond=0)
            t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
            t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
            today = datetime.datetime.today().weekday()

            if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
                print("주말이므로 프로그램을 종료합니다.")
                break


            if t_start < t_now <= t_sell:  # AM 09:00 ~ PM 15:15

                total_cash = get_balance()  # 보유 현금 조회

                if len(symbol_list) > 0:
                    buy_percent = 1 / len(symbol_list)  # 종목당 매수 금액 비율
                else:
                    buy_percent = 0  # 종목당 매수 금액 비율

                buy_amount = total_cash * 0.2 * buy_percent  # 종목별 주문 금액 계산

                # 매수 코드
                for sym in symbol_list:

                    target_price = get_target_price(sym)  # 전날 종가, Get from Input dictionary
                    current_price, volume_rate = get_current_price(sym)

                    t_progress = ((t_now - t_9) / (t_exit - t_9)) * 100
                    volume_rate = float(volume_rate)

                    volume_check = int((volume_rate / t_progress) > 1.6)

                    print(f'전일 대비 거래량 비율: {volume_rate:4.1f}')
                    print(f'종목: {sym}, 현재가: {current_price}, 거래량지표: {float(volume_rate / t_progress):5.1f}')

                    time.sleep(1)

                    aspr_acpt_hour, askp_rsqn1, askp_rsqn2, askp_rsqn3, askp_rsqn4, askp_rsqn5, askp_rsqn6, askp_rsqn7, askp_rsqn8, askp_rsqn9, askp_rsqn10,\
                    bidp_rsqn1, bidp_rsqn2, bidp_rsqn3, bidp_rsqn4, bidp_rsqn5, bidp_rsqn6, bidp_rsqn7, bidp_rsqn8, bidp_rsqn9, bidp_rsqn10, antc_cnpr, antc_vol = get_orderbook(sym)

                    stck_cntg_hour, stck_prpr, prdy_vrss, prdy_vrss_sign, cntg_vol, tday_rltv = get_transactions(sym)

                    data = pd.DataFrame(
                        [askp_rsqn1, askp_rsqn2, askp_rsqn3, askp_rsqn4, askp_rsqn5, askp_rsqn6, askp_rsqn7, askp_rsqn8,
                         askp_rsqn9, askp_rsqn10,\
                         bidp_rsqn1, bidp_rsqn2, bidp_rsqn3, bidp_rsqn4, bidp_rsqn5, bidp_rsqn6, bidp_rsqn7, bidp_rsqn8,
                         bidp_rsqn9, bidp_rsqn10,\
                         antc_cnpr, antc_vol, stck_prpr, prdy_vrss, prdy_vrss_sign, cntg_vol, tday_rltv]).T

                    data.columns = ['askp_rsqn1', 'askp_rsqn2', 'askp_rsqn3', 'askp_rsqn4', 'askp_rsqn5', 'askp_rsqn6',
                                    'askp_rsqn7', 'askp_rsqn8', 'askp_rsqn9', 'askp_rsqn10',\
                                    'bidp_rsqn1', 'bidp_rsqn2', 'bidp_rsqn3', 'bidp_rsqn4', 'bidp_rsqn5', 'bidp_rsqn6',
                                    'bidp_rsqn7', 'bidp_rsqn8', 'bidp_rsqn9', 'bidp_rsqn10',\
                                    'antc_cnpr', 'antc_vol', 'stck_prpr', 'prdy_vrss', 'prdy_vrss_sign', 'cntg_vol',
                                    'tday_rltv']

                    data['time'] = datetime.datetime.now()
                    data.set_index('time', inplace=True)

                    data_all = pd.concat([data_all, data], axis=0).tail(18)

                    if len(data_all) >= 18:
                        df = data_all.resample('3s').mean()  # Noise reduction

                        askp = [c for c in df.columns if 'askp' in c]
                        bidp = [c for c in df.columns if 'bidp' in c]

                        df['tot_askp'] = df[askp].sum(axis=1)
                        df['tot_bidp'] = df[bidp].sum(axis=1)

                        df['c1'] = (df['stck_prpr'] >= df['stck_prpr'].shift(1)) * (df['stck_prpr'].shift(1) >= df['stck_prpr'].shift(2)).astype('int')
                        df['c2'] = (df['tot_askp'] > df['tot_bidp'] * 2.0) * (df['tot_askp'].shift(1) > df['tot_bidp'].shift(1) * 2.0) * (df['tot_askp'].shift(2) > df['tot_bidp'].shift(2) * 2.0).astype('int')
                        df['c3'] = (df['tday_rltv'] > df['tday_rltv'].shift(1)) * (df['tday_rltv'].shift(1) >= df['tday_rltv'].shift(2)) * (df['tday_rltv'].shift(2) >= df['tday_rltv'].shift(3)).astype('int')
                        df['c4'] = (df['tday_rltv'] > 110).astype('int')

                        decision = df.tail(1)[['c1', 'c2', 'c3', 'c4']].product(axis=1)[0]
                        print(df.tail(1)['c1'].values[0], df.tail(1)['c2'].values[0], df.tail(1)['c3'].values[0], df.tail(1)['c4'].values[0])
                        print(decision, volume_check)

                        if decision == 1 & volume_check == 1:  # Max: 5% 상승 가격, Min: 전날 종가

                            buy_qty = int(buy_amount // current_price)
                            if (buy_qty > 0):

                                print(f"{sym} 매수를 시도합니다.")
                                # buy_price = float(current_price) - ho(float(current_price))
                                buy_price = float(current_price)
                                print(sym, str(int(buy_qty)), str(int(buy_price)))

                                result = buy(sym, str(int(buy_qty)), str(int(buy_price)))
                                # result = buy(sym, str(int(buy_qty)), "0", "01")
                                if result:
                                    print(f'{sym} 매수 성공')

                        # 매도 코드 (지정가)
                        balance_dict = get_stock_balance()
                        for sym, qty_rt in balance_dict.items():  # qty_rt / [0]: 보유수량, [1] 주문가능 수량 [2]: rt(평가수익율)

                            print(f'{sym} 현재 수익율: {float(qty_rt[2]): 5.2f}')
                            # current_price, volume_rate = get_current_price(sym)
                            # sell_price = float(current_price) + ho(float(current_price))  # 한 호가 높여 매도 주문

                            if float(qty_rt[2]) > 1.0 or float(qty_rt[2]) < -1.0:  # 익절 라인은 dynamic 하게 바꿀 수 있다 (단위 %)

                                # print(sym, str(qty_rt[1]), str(int(sell_price)))  # 매도 주문 인자 정보
                                if float(qty_rt[1]) != 0:
                                    # sell(sym, str(qty_rt[1]), str(int(sell_price)), "00") # "00 지정가 매도
                                    sell(sym, str(qty_rt[1]), "0", "01")  # "01 시장가 메도

                    if t_now.minute % 30 == 0:  # 매 30분 마다 창 지움
                        os.system('cls')

                    # PM 09:00 ~ PM 09:01: 관찰
                    if t_9 < t_now < t_start:

                        balance_dict = get_stock_balance()
                        for sym, qty_rt in balance_dict.items():
                            sell(sym, str(qty_rt[1]), "0", "01")  # "01 전량 시장가 메도

                        time.sleep(1)

    except Exception as e:
        print(f"[오류 발생]{e}")
        time.sleep(1)

