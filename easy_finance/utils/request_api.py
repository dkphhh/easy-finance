import os
from typing import Literal

import httpx
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
import reflex as rx
import base64
import re
from .log import logger
import string
import random
from datetime import date, datetime

load_dotenv()


# 从环境变量中获取密钥参数
api_key = os.getenv("APIKEY")
secret_key = os.getenv("SECRETKEY")

rate_limit = AsyncLimiter(
    3, 1
)  # 腾讯云api限制，最高 QPS 为 5，所以创建一个 limiter ，限制每秒最多并发3个请求


DATE_TO_REMOVE = "-/\\.:：年月日时秒分 "
AMOUNT_PATTERN = re.compile(r"[^\d.]")


def recognize_filetype(file: rx.UploadFile) -> tuple[str, str]:
    """
    检查用户上传的文件是图片还是pdf
    Args:
        file:用户上传的文件
    Returns: 是图片就返回img，是pdf，就返回pdf，都不是就报错

    """
    filename = file.filename.lower()
    image_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    file_extension = (
        "." + filename.split(".")[-1] if "." in filename else ""
    )  # 获取文件扩展名

    # 判断文件类型
    if file_extension in image_extensions:
        return "img", file_extension
    elif file_extension == ".pdf":
        return "pdf", file_extension
    else:
        raise TypeError("未知文件类型")


def generate_random_string(length=6) -> str:
    """生成随机6位字符串
    Args:
        length: 字符串长度
    """
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def parse_date(date_string: str) -> date:
    """将银行回单内的日期时间字符串转化为 datetime 格式
    简单来说，就是把 DATE_TO_REMOVE 里的所有字符全部删除
    然后转化为 date 格式

    Args:
        date_string (str): 日期格式的字符串

    Returns:
        str: 纯数字的日期字符串
    """
    trans_table = str.maketrans("", "", DATE_TO_REMOVE)
    date_num = date_string.translate(trans_table)
    result = date.fromisoformat(date_num)
    return result


def extract_amount(amount_str: str) -> str:
    """将提取到的金额字符串转化为只包含数字和小数点的字符串

    Args:
        amount_str (str): 取到的金额字符串转

    Returns:
        str: 只包含数字和小数点的字符串
    """
    return AMOUNT_PATTERN.sub("", amount_str)


def parse_none(value: str | None) -> str:
    """将所有 None 串转化为 空字符串 "" """

    return "" if value is None else value


def process_bank_slip(words_result: dict) -> dict:
    trade_date = parse_date(words_result["交易日期"][0]["word"])
    amount = extract_amount(words_result["小写金额"][0]["word"])
    payer = words_result["付款人户名"][0]["word"]
    receiver = words_result["收款人户名"][0]["word"]

    return {
        "trade_date": trade_date,
        "amount": amount,
        "payer": payer,
        "receiver": receiver,
    }


async def request_api(file: rx.UploadFile, mode: Literal["bank_slip", "vat_invoice"]):

    async with httpx.AsyncClient() as client:

        # ---------获取token-----------

        token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"

        token_payload = ""
        token_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        token_res = await client.post(
            token_url, json=token_payload, headers=token_headers
        )

        token = token_res.json()["access_token"]

        # ----处理文件-----

        filetype, file_extension = recognize_filetype(
            file
        )  # 获取文件类型 和 文件扩展名

        # 用时间和随机字符串给文件重新命名
        new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{generate_random_string()}{file_extension}"
        upload_file = rx.get_upload_dir() / new_filename  # 创建一个保存上传文件的地址，

        # 默认保存文件的目录时 upload_files

        upload_data = await file.read()

        with upload_file.open("wb") as file_object:
            file_object.write(upload_data)  # 把文件保存到指定目录

        # 输出文件的 base64 字符串
        file_b64 = base64.b64encode(upload_data).decode("utf-8")

        # 请求api的参数
        request_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        request_payload = (
            {"image": file_b64} if filetype == "img" else {"pdf_file": file_b64}
        )

        match mode:

            case "bank_slip":

                # ----------银行回单请求-------

                bank_slip_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/bank_receipt_new?access_token={token}"

                bank_slip_res = await client.post(
                    url=bank_slip_url, headers=request_headers, data=request_payload
                )

                bank_slip_result = bank_slip_res.json()

                words_result = bank_slip_result["words_result"]

                result = process_bank_slip(words_result)

                result["bank_slip_url"] = f"/_upload/{new_filename}"

                logger.info(result)

                return result

            case "vat_invoice":

                # ------------发票请求-----------

                vat_invoice_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={token}"

                vat_invoice_res = await client.post(
                    url=vat_invoice_url, headers=request_headers, data=request_payload
                )

                vat_invoice_result = vat_invoice_res.json()

                words_result = vat_invoice_result["words_result"]

            case _:
                raise AttributeError("识别模式错误！")


if __name__ == "__main__":
    pass
