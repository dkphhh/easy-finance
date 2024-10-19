from datetime import datetime

from .bank_slip import parse_date, parse_none


def get_invoice_data(invoice_info: dict[str, str]) -> list[str]:
    """将 api 回传的发票信息整理成前端使用的标准格式

    Args:
        invoice_info (dict[str, str]): api 回传的发票信息

    Returns:
        list[str]: 包含已经识别信息的列表，顺序如下：
        开票日期
        发票类型
        发票号码
        购买方名称
        购买方税号
        销售方名称
        销售方税号
        税额
        金额（不含税价格）
        价税合计（小写）
    """
    invoice_type = invoice_info["Title"]
    invoice_code = invoice_info["Number"]
    invoice_date = (
        datetime.strptime(parse_date(invoice_info["Date"])[:8], "%Y%m%d")
        .date()
        .strftime("%Y-%m-%d")
    )
    buyer_name = invoice_info["Buyer"]
    seller_name = invoice_info["Seller"]
    buyer_code = invoice_info["BuyerTaxID"]
    seller_code = invoice_info["SellerTaxID"]
    tax_amount = invoice_info["Tax"]
    price_excluded_tax = invoice_info["PretaxAmount"]
    price_included_tax = invoice_info["Total"]

    invoice_data = list(
        map(
            parse_none,
            [
                invoice_date,
                invoice_type,
                invoice_code,
                buyer_name,
                buyer_code,
                seller_name,
                seller_code,
                tax_amount,
                price_excluded_tax,
                price_included_tax,
            ],
        )
    )

    return invoice_data
