import json
import re

import requests
from utils.logger_manager import logger_manager


class eptrade:

    def __init__(self, username, password, logger=None):
        self.username = username
        self.password = password
        self.is_login = False
        self.logger = logger or logger_manager.logger
        self.s = requests.Session()

        self.s.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            }
        )

        self.aes_key = "www.easipass.com"

        self.bill_info = {}

        self.ctnType_list = [
            {"ctnType": "20BULK"},
            {"ctnType": "20BULK(high)"},
            {"ctnType": "20DRY"},
            {"ctnType": "20FLAT"},
            {"ctnType": "20HIGH"},
            {"ctnType": "20HIVE"},
            {"ctnType": "20OPEN"},
            {"ctnType": "20OPEN(high)"},
            {"ctnType": "20OSOT"},
            {"ctnType": "20PLWD"},
            {"ctnType": "20PORT"},
            {"ctnType": "20REEF"},
            {"ctnType": "20RH"},
            {"ctnType": "20TANK"},
            {"ctnType": "20TANK(8)"},
            {"ctnType": "40DRY"},
            {"ctnType": "40FLAT"},
            {"ctnType": "40FLAT(high)"},
            {"ctnType": "40HCRF"},
            {"ctnType": "40HIGH"},
            {"ctnType": "40OPEN"},
            {"ctnType": "40OPEN(high)"},
            {"ctnType": "40PLWD"},
            {"ctnType": "40PLWD(high)"},
            {"ctnType": "40REEF"},
            {"ctnType": "40TANK"},
            {"ctnType": "40TANK(high)"},
            {"ctnType": "40TK"},
            {"ctnType": "40TWDK"},
            {"ctnType": "45HCRF"},
            {"ctnType": "45HIGH"},
            {"ctnType": "45PLWD(high)"},
        ]
        self.handTypes = [
            {
                "location": "SGH",
                "code": "HCRF",
                "id": 1054,
                "codeName": "REEF,HCRF",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "冷代干",
            },
            {
                "location": "SGH",
                "code": "REEF",
                "id": 1053,
                "codeName": "REEF,HCRF",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "冷箱",
            },
            {
                "location": "SGH",
                "code": "OPEN",
                "id": 1055,
                "codeName": "OPEN,OPEN(high)",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "开顶箱",
            },
            {
                "location": "SGH",
                "code": "GOH",
                "id": 1051,
                "codeName": "*",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "挂衣箱",
            },
            {
                "location": "SGH",
                "code": "FLAT",
                "id": 1056,
                "codeName": "FLAT,FLAT(high)",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "框架箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1999943,
                "codeName": "TWDK",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1999939,
                "codeName": "REEF,HCRF",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1999940,
                "codeName": "OPEN,OPEN(high)",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1999941,
                "codeName": "FLAT,FLAT(high)",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1999942,
                "codeName": "TANK,TANK(high),TANK(8)",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
            {
                "location": "SGH",
                "code": "SOC",
                "id": 1052,
                "codeName": "*",
                "dataType": "MSKEIR_HANDTYPE",
                "relCode": "货主自备箱",
            },
        ]

    # def _aes_password(self, password):
    #     key = self.aes_key.encode("utf-8")
    #     data = password.encode("utf-8")
    #     cipher = AES.new(key, AES.MODE_ECB)
    #     encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    #     return base64.b64encode(encrypted_data).decode("utf-8")

    def _get(self, url, data):
        url = "https://www.eptrade.cn" + url

        r = self.s.get(url, params=data, timeout=3)
        # 打印请求头
        self.logger.debug(r.request.headers)
        #
        self.logger.debug("响应码： {}".format(r.status_code))
        if r.status_code == 200:
            # 判断r.text 是否为json
            try:
                rjson = r.json()
                return rjson
            except:
                return r.text
        else:
            # 访问出错, 打印响应头
            self.logger.error(r.headers)
            raise Exception("访问出错")

    def _post(self, url, data, params=None):
        url = "https://www.eptrade.cn" + url
        r = self.s.post(url, data=data, params=params, allow_redirects=False, timeout=3)
        # 打印请求头
        self.logger.debug(r.request.url)
        self.logger.debug(r.request.headers)
        #
        self.logger.debug(r.request.body)
        #
        self.logger.debug("响应码： {}".format(r.status_code))
        self.logger.debug("响应体： {}".format(r.text))
        if r.status_code == 200:
            # 判断r.text 是否为json
            try:
                rjson = r.json()
                return rjson
            except:
                return r.text
        else:
            # 访问出错, 打印响应头
            self.logger.error(r.headers)
            raise Exception("访问出错")

    # def login(self):
    #     self.s.get(url="https://www.chinasailing.com.cn/login")
    #     yzm = self._ocr_pic()
    #     url = "https://www.chinasailing.com.cn/getWbUser"
    #     data = {"username": self.username, "password": self.password, "captan": yzm}
    #     r = self.s.post(url, data=data)
    #     self.logger.info(r.text)
    #     self.logger.debug(r.status_code)
    #     self.logger.debug(r.request.headers)
    #     # 打印响应头
    #     self.logger.debug(r.headers)

    def init_cookie(self, cookie_str):
        cookies = {
            cookie.split("=")[0]: cookie.split("=")[1]
            for cookie in cookie_str.split("; ")
        }
        self.logger.debug(f"set cookie: {cookies}")
        self.s.cookies.update(cookies)

    def _get_rcmd_yard(self, billId, ctnType, ctnNum):
        """
        获取推荐堆场
        Args:
            billId (int): 订舱号
            ctnType (str): 箱子类型
            ctnNum (str): 箱子数量
        """
        url = "/mskeir2/mskCarrierApplyCtnr.do/getMatchedRcmdYards.do?shipCode=SGH"
        data = {
            "billId": billId,
            "ctnType": ctnType,
            "ctnNum": ctnNum,
            "handType": "",
        }
        r = self._post(url, data)
        self.logger.debug(r)
        return r

    def _operate(self, bookingno):
        """
        访问提单号页面

        Args:
            bookingno (_type_): 提单号

        Raises:
            Exception: 没有找到model

        Returns:
            _type_: 返回bill_info
        """
        url = "/mskeir2/mskCarrierApplyCtnr.do/operate.do"
        data = {"bookingno": bookingno, "shipCode": "SGH"}
        r = self._get(url, data)
        # 使用正则匹配出 model
        model_match = re.search(r"var model = (\{.*?\});", r, re.DOTALL)
        self.logger.debug(model_match)
        if model_match:
            model_json_str = model_match.group(1)
            self.logger.debug(model_json_str)
            model_data = json.loads(model_json_str)
            self.logger.debug(model_data)
            return model_data
        raise Exception("提单号不存在")

    def validateBeforeOperate(self, bookingno):
        """
        检查单号是否有效

        Args:
            bookingno (提单号): 提单号
        """
        url = "/mskeir2/mskCarrierApplyCtnr.do/validateBeforeOperate.do?shipCode=SGH&bookingno={}".format(bookingno)
        r = self._post(url, {})
        self.logger.debug("验证提单号是否有效: {}".format(r))
        if r["isValid"]:
            # 提取billid
            return True
        raise Exception("提单号不存在")

    def smlCarrierApplyCtnr(
        self,
        billId: int,
        ctnQuantity: str,
        ctnType: str,
        handId: int = 0,
        areaCode: str = "不选区域",
    ):
        """
        申请箱型

        Args:
            billId (int): 订舱号
            ctnQuantity (str): 箱数
            ctnType (str): 箱子名称
        """
        if areaCode not in ["不选区域", "芦潮港区域", "外高桥区域"]:
            raise Exception("区域不存在")

        if ctnType not in {item["ctnType"] for item in self.ctnType_list}:
            raise Exception("箱子类型不存在")
        handTypeName = ""
        handType = ""
        if handId != 0:
            for item in self.handTypes:
                if item["id"] == handId:
                    handTypeName = item["relCode"]
                    handType = item["code"]
                    break
            else:
                raise Exception("特种箱子类型不存在")
        url = "/mskeir2/mskCarrierApplyCtnr.do/apply.do?shipCode=SGH"

        postjson = {
            "billId": billId,
            "items": [
                {
                    "ctnQuantity": ctnQuantity,
                    "ctnType": ctnType,
                    "handType": handType,
                    "handTypeName": handTypeName,
                    "rcmdYard": "",
                    "editing": False,
                    "isReceiveSealNo": "",
                }
            ],
            "areaCode": areaCode,
        }
        data = {"data": json.dumps(postjson)}
        r = self._post(url, data)
        self.logger.debug(r)
        if r["success"]:
            self.logger.info("箱子申请成功")
            return True, "申请成功"
        else:
            self.logger.info(r["message"])
            return False, "申请失败 {}".format(r.get("message", ""))

    def findSuccessfulAppliedCtnrs(self, billId):
        """
        打印通知单记录
        1、如果 data['total'] == 0 表示未申请箱子
        2、如果有表示有箱子信息 data['rows']   如果申请多个箱子，会有多条记录
        遍历箱子记录，如果status='6' 表示已经成功打印，其他状态则触发打印

        Args:
            billId (_type_): _description_
        """
        url = (
            "/mskeir2/mskCarrierApplyCtnr.do/findSuccessfulAppliedCtnrs.do?shipCode=SGH"
        )
        data = {"billId": billId}
        r = self._post(url, data)
        if r["total"] == 0:
            return "打印结果：未申请箱子"
        for i in r["rows"]:
            self.logger.info(f"申请箱子记录: {billId}  id:{i['id']} status:{i['status']}")
            if i["status"] == "6":
                return "打印结果：已打印"
        # 请求打印接口
        return r

    def testfindSuccessfulAppliedCtnrs(self, billId):
        url = (
            "/mskeir2/mskCarrierApplyCtnr.do/findSuccessfulAppliedCtnrs.do?shipCode=SGH"
        )
        data = {"billId": billId}
        r = self._post(url, data)
        if r["total"] == 0:
            return "打印结果：未申请箱子"
        for i in r["rows"]:
            self.logger.info(f"申请箱子记录: {billId}  id:{i['id']} status:{i['status']}")
            if i["status"] == "6":
                return "打印结果：已打印"
        # 请求打印接口
        return "打印结果：可打印"

    def smlCarrierApplyCtnr_print(self, billId: int, cthrs, areaCode: str = "不选区域"):
        """
        数字小票打印
        """
        url = "/mskeir2/mskCarrierApplyCtnr.do/print.do?shipCode=SGH"
        printType = "pdf"
        sendType = "DIAODU"
        orgId = "000"
        # 请求参数
        postjson = {
            "location": "SGH",
            "areaCode": areaCode,
            "billId": billId,
            "ctnrs": [],
            "printType": printType,
            "sendType": sendType,
            "orgId": orgId,
            "driver": "",
            "isShowApplicant": False,
        }
        # 组合箱子数据
        postjson["ctnrs"] = []
        for row in cthrs:
            if row.status != "6" or (row.enabledEeir and row.status == "6" and row.handType == "SOC"):
                postjson["ctnrs"].append(row)
        if len(postjson["ctnrs"]) == 0:
            return "打印结果：没有符合打印条件的箱子"
        # 发起请求
        data = {"data": json.dumps(postjson)}
        r = self._post(url, data)
        self.logger.info(f"{billId} 打印结果: {r.get('message', '')}  pdfuuid: {r.get('pdfuuid', '')}")
        if r["success"] and r["ctnrs"]:
            return "打印成功"
        return "打印失败 {}".format(r.get("message", ""))

    def login_by_token(self, token):
        r = self.s.get(
            "https://www.eptrade.cn/eir2/main.do?service=http://www.eptrade.cn/eir2&servfrom=ols&ticket={}&refresh_token={}&redirectEirAuth=true".format(
                token, token
            )
        )
        with open("test.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        r = self.s.get(
            "https://www.eptrade.cn/mskeir2/mskCarrierApplyCtnr.do?forward=msk/carrier/mskCarrierApplyCtnr/mskCarrierApplyCtnr&shipCode=SGH&servfrom=ols&service=eir.html&ticket={}".format(
                token
            )
        )
        with open("test2.html", "w", encoding="utf-8") as f:
            f.write(r.text)
        if "用箱申请查询" in r.text:
            # 登录成功
            self.logger.info("初始化成功")
            self.is_login = True
            return True
        self.logger.info("初始化失败")
        return False


if __name__ == "__main__":
    username = "xxxx"
    password = "xxxx"
    eptradeobj = eptrade(username, password)
    token = "JSESSIONID={}".format(
        "v4wMFMRb5aUU1oAaITxvTgjQuJAAORsbhgi1ir6PBm7v5p877puR!1767103804"
    )
    eptradeobj.init_cookie(token)