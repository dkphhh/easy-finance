import asyncio
import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv

from .bank_slip import get_bank_slip_data
from .invoice import get_invoice_data
from .log import logger

load_dotenv()


# 从环境变量中获取密钥参数
secret_id = os.getenv("SECRETID")
secret_key = os.getenv("SECRETKEY")


rate_limit = AsyncLimiter(
    3, 1
)  # 腾讯云api限制，最高 QPS 为 5，所以创建一个 limiter ，限制每秒最多并发3个请求


def request_depends(
    file_base64: str, Action="RecognizeGeneralInvoice"
) -> tuple[str, str, dict[str, Any]]:
    """根据腾讯云的 API 调用规范，拼接请求时需要的签名，返回 API 请求时需要用到的 endpoint（请求地址）、payload（上传的数据）和headers（请求头）

    Args:
        file_base64 (str): 文件的base64字符串，可以是常用图片格式，也可以是pdf
        Action(Literal): 调用的API名称，在本项目中只会用到 RecognizeGeneralInvoice(通用识别接口)
    Returns:
        tuple[str, str, dict[str, Any]]: 返回 API 请求时需要用到的 endpoint（请求地址）、payload（上传的数据）和headers（请求头）
    """

    service = "ocr"
    host = "ocr.tencentcloudapi.com"
    endpoint = "https://" + host
    action = Action
    version = "2018-11-19"
    region = "ap-beijing"
    algorithm = "TC3-HMAC-SHA256"
    timestamp = int(time.time())
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
    params = {"ImageBase64": file_base64, "EnableMultiplePage": False}

    # ************* 步骤 1：拼接规范请求串 *************
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    ct = "application/json; charset=utf-8"
    payload = json.dumps(params)
    canonical_headers = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (
        ct,
        host,
        action.lower(),
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (
        http_request_method
        + "\n"
        + canonical_uri
        + "\n"
        + canonical_querystring
        + "\n"
        + canonical_headers
        + "\n"
        + signed_headers
        + "\n"
        + hashed_request_payload
    )

    # ************* 步骤 2：拼接待签名字符串 *************
    credential_scope = date + "/" + service + "/" + "tc3_request"
    hashed_canonical_request = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()
    string_to_sign = (
        algorithm
        + "\n"
        + str(timestamp)
        + "\n"
        + credential_scope
        + "\n"
        + hashed_canonical_request
    )

    # ************* 步骤 3：计算签名 *************
    # 计算签名摘要函数
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date = sign(("TC3" + secret_key).encode("utf-8"), date)  # type:ignore
    secret_service = sign(secret_date, service)
    secret_signing = sign(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # ************* 步骤 4：拼接 Authorization *************
    authorization = (
        algorithm
        + " "
        + "Credential="
        + secret_id  # type:ignore
        + "/"
        + credential_scope
        + ", "
        + "SignedHeaders="
        + signed_headers
        + ", "
        + "Signature="
        + signature
    )

    headers = {
        "Authorization": authorization,
        "content-type": "application/json; charset=utf-8",
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(int(time.time())),
        "X-TC-Version": version,
        "X-TC-Region": region,
    }

    return (endpoint, payload, headers)


async def request_api(
    file_base64: str,
    action="RecognizeGeneralInvoice",
) -> dict[str, str | list[str]]:
    """将文件base64字符串提交到腾讯云的银行回单 OCR 识别 API 接口

    Args:
        file_base64 (str): 文件的base64字符串
        Action(Literal): 调用的API名称，在本项目中只会用到RecognizeGeneralInvoice（通用识别接口）

    Returns:
       dict[str, str | dict[str, Any] | list[dict[str, str]]]: API 接口识别结果，包含识别出的文件类型和识别出的数据

    """
    async with rate_limit:  # 腾讯云api限制，最高 QPS 为 5，这里限制为3
        endpoint, payload, headers = request_depends(
            file_base64, action
        )  # 生成api请求需要的各种参数

        async with httpx.AsyncClient() as client:
            resp = await client.post(endpoint, data=payload, headers=headers)
            json_data = resp.json()

            try:
                resp = json_data["Response"]
                resp_type = resp["MixedInvoiceItems"][0]["SubType"]
            except KeyError as err:
                logger.error(f"request_api 遇到异常{err},此时resp为：{resp}")
                raise KeyError(err)
            else:
                match resp_type:
                    case (
                        "VatSpecialInvoice"
                        | "VatCommonInvoice"
                        | "VatElectronicCommonInvoice"
                        | "VatElectronicSpecialInvoice"
                        | "VatElectronicInvoiceBlockchain"
                        | "VatElectronicInvoiceToll"
                        | "VatElectronicSpecialInvoiceFull"
                        | "VatElectronicInvoiceFull"
                        | "VatInvoiceRoll"
                        | "MachinePrintedInvoice"
                    ):
                        result_data = resp["MixedInvoiceItems"][0][
                            "SingleInvoiceInfos"
                        ][resp_type]
                        result_type = "invoice"
                        result_data = get_invoice_data(result_data)
                    case "OtherInvoice":
                        result_data = resp["MixedInvoiceItems"][0][
                            "SingleInvoiceInfos"
                        ][resp_type]["OtherInvoiceListItems"]
                        result_type = "bank_slip"
                        result_data = get_bank_slip_data(result_data)

                    case _:
                        raise TypeError("暂时无法解析该类票据")

                return {
                    "result_type": result_type,
                    "result_data": result_data,
                }


if __name__ == "__main__":

    async def main():
        dir_path = Path("/Users/dkphhh/dev/easy-finance/测试文件")
        file_path_list = (
            list(dir_path.glob("*.pdf"))
            + list(dir_path.glob("*.jpeg"))
            + list(dir_path.glob("*.jpg"))
            + list(dir_path.glob("*.png"))
        )

        tasks = [
            request_api(
                file_base64=base64.b64encode(file_path.read_bytes()).decode("utf-8")
            )
            for file_path in file_path_list
        ]

        await asyncio.gather(*tasks)

    asyncio.run(main())
