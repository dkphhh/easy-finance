import re
from datetime import date, datetime

from .log import logger

BUYER_KEYWORD = "付款"
SELLER_KEYWORD = "收款"
NAME_KEYWORDS = {"称", "名", "人"}
ACCOUNT_KEYWORD = "账号"
BANK_KEYWORD = "行"
DATE_KEYWORDS = {"时间", "日期"}
DATE_TO_REMOVE = "-/\\.:：年月日时秒分 "
AMOUNT_KEYWORDS = {"金额", "小写"}
AMOUNT_EX_KEYWORD = "大写"
AMOUNT_PATTERN = re.compile(r"[^\d.]")


def parse_date(date_string: str) -> str:
    """将银行回单内的日期时间字符串转化为纯数字格式
    简单来说，就是把 DATE_TO_REMOVE 里的所有字符全部删除

    Args:
        date_string (str): 日期格式的字符串

    Returns:
        str: 纯数字的日期字符串
    """
    trans_table = str.maketrans("", "", DATE_TO_REMOVE)
    return date_string.translate(trans_table)


def extract_datetime(bank_slip_info: list[dict]) -> str | None:
    """遍历 bank_slip_info 内的所有值，找到日期相关值，将日期字符串转化为 date ，并返回其中最小（早）的 date

    Args:
        bank_slip_info (list[dict]): request_api 返回的值

    Returns:
        str: 整个回单里最早的日期的字符串，格式为 "%Y-%m-%d"
    """
    if not bank_slip_info:
        logger.warning("当前处理的 bank_slip_info 为 None")
        return None

    date_values: list[date] = []
    for info in bank_slip_info:
        if any(keyword in info["Name"] for keyword in DATE_KEYWORDS):
            parsed_date = datetime.strptime(
                parse_date(info["Value"])[:8], "%Y%m%d"
            ).date()
            date_values.append(parsed_date)
    if not date_values:
        logger.warning("没有在当前处理的 bank_slip_info 找到时间值")
        return None

    return min(date_values).strftime("%Y-%m-%d")


def extract_amount(amount_str: str) -> str:
    """将提取到的金额字符串转化为只包含数字和小数点的字符串

    Args:
        amount_str (str): 取到的金额字符串转

    Returns:
        str: 只包含数字和小数点的字符串
    """
    return AMOUNT_PATTERN.sub("", amount_str)


def parse_none(value: str | None) -> str:
    """将所有 None 和空字符串转化为 "未识别" """
    if value is None or value == "":
        return "未识别"
    else:
        return value


def get_bank_slip_data(bank_slip_info: list[dict]) -> list[str]:
    """提取 API 接口返回的银行回单信息，整理成列表输出，
    主要目用于 easy finance 前端使用，
    由于腾讯云的通用票据识别接口将银行回单归类为”其他发票“，
    所以这个 function 还兼具识别用户上传其他无法图片的功能。

    Args:
        bank_slip_info  list[dict]: api 回传的银行回单信息

    Returns:
         list[str | None]: 转化后的立标格式，包含以下内容：

        付款人名称
        付款人账号
        付款人开户银行
        收款人名称
        收款人账号
        收款人开户银行
        转账金额
        转账日期


    """

    # 初始化所有字段，所有字段值都是 None
    (
        buyer_name,
        buyer_account,
        buyer_bank,
        seller_name,
        seller_account,
        seller_bank,
        trans_amount,
        trans_date,
    ) = [None] * 8

    # 提取发票内的时间信息
    trans_date = extract_datetime(bank_slip_info)

    for info in bank_slip_info:  # type:ignore
        # 提取付款方信息
        if BUYER_KEYWORD in info["Name"]:
            # 付款人名称
            if (
                not buyer_name
                and any(keyword in info["Name"] for keyword in NAME_KEYWORDS)
                and all(
                    keyword not in info["Name"]
                    for keyword in {ACCOUNT_KEYWORD, BANK_KEYWORD}
                )
            ):
                buyer_name = info["Value"]
            # 付款人账号
            if not buyer_account and ACCOUNT_KEYWORD in info["Name"]:
                buyer_account = info["Value"]
            # 付款人银行
            if not buyer_bank and BANK_KEYWORD in info["Name"]:
                buyer_bank = info["Value"]

        # 提取收款方信息
        if SELLER_KEYWORD in info["Name"]:
            # 收款人名称
            if (
                not seller_name
                and any(keyword in info["Name"] for keyword in NAME_KEYWORDS)
                and all(
                    keyword not in info["Name"]
                    for keyword in {ACCOUNT_KEYWORD, BANK_KEYWORD}
                )
            ):
                seller_name = info["Value"]
            # 收款人账号
            if not seller_account and ACCOUNT_KEYWORD in info["Name"]:
                seller_account = info["Value"]
            # 收款人银行
            if not seller_bank and BANK_KEYWORD in info["Name"]:
                seller_bank = info["Value"]

        # 提取回单金额
        if (
            not trans_amount
            and any(keyword in info["Name"] for keyword in AMOUNT_KEYWORDS)
            and AMOUNT_EX_KEYWORD not in info["Name"]
        ):
            extracted = extract_amount(info["Value"])
            if extracted:  # 只有当提取出非空字符串时才赋值
                trans_amount = extracted

        if all(
            {
                buyer_name,
                buyer_account,
                buyer_bank,
                seller_name,
                seller_account,
                seller_bank,
                trans_amount,
                trans_date,
            }
        ):
            break

    # 通过统计 None 的数量来判断
    none_count = sum(
        [
            1
            for item in [
                buyer_name,
                buyer_account,
                buyer_bank,
                seller_name,
                seller_account,
                seller_bank,
                trans_amount,
                trans_date,
            ]
            if item is None
        ]
    )

    if none_count >= 5:
        raise TypeError("文件可能不是发票或银行回单")

    # 整理信息
    bank_slip_data = list(
        map(
            parse_none,
            [
                trans_date,
                buyer_name,
                buyer_account,
                buyer_bank,
                seller_name,
                seller_account,
                seller_bank,
                trans_amount,
            ],
        )
    )

    return bank_slip_data
