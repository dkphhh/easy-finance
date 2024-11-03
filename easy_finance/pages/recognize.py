import asyncio
import io
import time
from base64 import b64encode
from datetime import datetime
from typing import Generator

import polars as pl
import reflex as rx


from ..utils.log import logger
from ..utils.request_api import request_api

# 银行回单的表头
BANK_SLIP_COLUMNS: list[dict[str, str]] = [
    {
        "title": "文件名",
        "id": "file_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "转账日期",
        "id": "trans_date",
        "type": "str",
        "width": 100,
    },
    {
        "title": "付款人名称",
        "id": "buyer_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "付款人账号",
        "id": "buyer_account",
        "type": "str",
        "width": 250,
    },
    {
        "title": "付款人开户行",
        "id": "buyer_bank",
        "type": "str",
        "width": 200,
    },
    {
        "title": "收款人名称",
        "id": "seller_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "收款人账号",
        "id": "seller_account",
        "type": "str",
        "width": 250,
    },
    {
        "title": "收款人开户银行",
        "id": "seller_bank",
        "type": "str",
        "width": 200,
    },
    {
        "title": "转账金额",
        "id": "trans_amount",
        "type": "str",
        "width": 100,
    },
]


# 发票的表头
INVOICE_COLUMNS: list[dict[str, str]] = [
    {
        "title": "文件名",
        "id": "file_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "开票日期",
        "id": "invoice_date",
        "type": "str",
        "width": 100,
    },
    {
        "title": "发票类型",
        "id": "invoice_type",
        "type": "str",
        "width": 200,
    },
    {
        "title": "发票号码",
        "id": "invoice_code",
        "type": "str",
        "width": 200,
    },
    {
        "title": "购买方名称",
        "id": "buyer_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "购买方统一社会信用代码",
        "id": "buyer_code",
        "type": "str",
        "width": 200,
    },
    {
        "title": "销售方名称",
        "id": "seller_name",
        "type": "str",
        "width": 200,
    },
    {
        "title": "销售方统一社会信用代码",
        "id": "seller_code",
        "type": "str",
        "width": 200,
    },
    {
        "title": "税额",
        "id": "tax_amount",
        "type": "str",
        "width": 50,
    },
    {
        "title": "不含税价格",
        "id": "price_excluded_tax",
        "type": "str",
        "width": 100,
    },
    {
        "title": "价税合计",
        "id": "price_included_tax",
        "type": "str",
        "width": 100,
    },
]


test_invoice = [
    [
        "¥27.25.pdf",
        "2024-04-20",
        "电子发票(普通发票)",
        "24137123456735267188",
        "北京有一家科技有限公司",
        "91110108MABCDEF101",
        "上海另一家科技有限公司",
        "91131022ABCD07LN99",
        "3.13",
        "24.12",
        "27.25",
    ],
    [
        "¥29.60.pdf",
        "2024-05-25",
        "电子发票(普通发票)",
        "24111234562222945473",
        "北京有一家科技有限公司",
        "91110108MABCDEF101",
        "上海另一家科技有限公司",
        "91131022ABCD07LN99",
        "3.41",
        "26.19",
        "29.60",
    ],
]

test_bank_slip = [
    [
        "北京银行.jpeg",
        "2024-09-03",
        "银联商务股份有限公司",
        "未识别",
        "中国银联股份有限公司",
        "北京碧园文化发展有限公司",
        "未识别",
        "北京银行密云支行",
        "6229.00",
    ],
    [
        "91491726191886_.pic.jpg",
        "2024-09-13",
        "北京有一家科技有限公司",
        "10242123456466214",
        "华夏银行北京学院路支行",
        "上海另一家科技有限公司",
        "866182028512344123121",
        "招商银行股份有限公司上海浦东支行",
        "10000.00",
    ],
]

bank_slip_data_now = [[]]

invoice_data_now = [[]]


class UploadFile(rx.State):
    bank_slips_data: rx.Field[list[list[str]]] = rx.field([])  # 存储银行回单数据
    invoice_data: rx.Field[list[list[str]]] = rx.field([])  # 存储发票数据
    upload_loading: rx.Field[bool] = rx.field(False)  # 判断 dropzone 是否等待的状态判断
    download_loading: rx.Field[bool] = rx.field(
        False
    )  # 判断 download button 是否是等待状态
    mode: rx.Field[str] = rx.field("invoice")  # 前端展示的选单,默认值是发票识别
    bank_slips_notification: rx.Field[bool] = rx.field(False)
    invoice_notification: rx.Field[bool] = rx.field(False)
    test_mode: rx.Field[bool] = rx.field(False)  # 测试模式，默认为 False
    original_bank_slips_data: list[list[str]] = []  # 用于测试摸下保存原有数据
    original_invoice_data: list[list[str]] = []  # 用于测试摸下保存原有数据
    # TODO 目前 Literal 类型存在 bug，等修复后将 mode 改为 Literal 类型

    # 将 state 需要经常用到的方法和属性抽象出一个配置列表，通过固定的方法获取当前 state 的识别，并执行相应的操作
    MODE_CONFIG = {
        "bank_slip": {
            "data_attr": "bank_slips_data",
            "columns": BANK_SLIP_COLUMNS,
            "notification_attr": "bank_slips_notification",
            "filename_tag": "银行回单",
        },
        "invoice": {
            "data_attr": "invoice_data",
            "columns": INVOICE_COLUMNS,
            "notification_attr": "invoice_notification",
            "filename_tag": "增值税发票",
        },
    }

    @rx.var
    def get_current_data(self) -> list[list[str]]:
        """获取当前 mode 选单下对应的数据"""
        return getattr(self, self.MODE_CONFIG[self.mode]["data_attr"])

    @rx.var
    def get_current_columns(self) -> list[list[str]]:
        """获取当前 mode 选单对应的表格标题栏"""
        return self.MODE_CONFIG[self.mode]["columns"]

    @rx.var
    def data_is_exists(self) -> bool:
        """这是一个 computed var，用于检查当前mode 选单下对应的 state var 是否存在数据，如果存在数据，则返回 True，否则返回 False。"""
        return bool(self.invoice_data or self.bank_slips_data)

    @rx.event
    def go_test(self, test_mode: bool):
        if test_mode:
            # 进入测试模式
            if not self.test_mode:  # 只在首次进入测试模式时保存原始数据
                self.original_bank_slips_data = self.bank_slips_data.copy()
                self.original_invoice_data = self.invoice_data.copy()
            self.bank_slips_data = test_bank_slip
            self.invoice_data = test_invoice
        else:
            # 退出测试模式
            self.bank_slips_data = self.original_bank_slips_data
            self.invoice_data = self.original_invoice_data

        self.test_mode = test_mode

    async def uni_request(self, file: rx.UploadFile) -> None:
        """处理单个银行回单识别和发票识别的请求：
        1. 将上传文件的文件名插入到识别结果的第一位
        2. 识别新增数据的类型，并将数据插入到对应数据集
        Args:
            file (rx.UploadFile): 上传的文件

        Returns:
            list[str]: 插入文件名后的识别结果
        """
        try:
            filename = file.filename  # 提取文件名
            file_content = await file.read()
            if not file_content:
                raise ValueError(f"文件 {filename} 是空的")  # 检查文件内容是否正常上传
            file_base64 = b64encode(file_content).decode(
                "utf-8"
            )  # 将接收的文件批量转化为base64编码
            resp = await request_api(file_base64)
            if not resp or "result_type" not in resp or "result_data" not in resp:
                raise ValueError(
                    f"API 返回了无效的响应: {resp}"
                )  # 检查 API 是否正常返回内容
            logger.info(f"正在处理文件：{filename}")
            result_type: str = resp["result_type"]  # 获取文件类型
            result_data: list[str] = resp["result_data"]  # 获取文件数据
            result_data.insert(0, filename)  # 在文件数据中插入文件名
            logger.info(
                f"""文件「{filename}」处理结果\n
                result_type：{result_type}\n
                result_data:{result_data}"""
            )
            current_data: list[list[str]] = getattr(
                self, self.MODE_CONFIG[result_type]["data_attr"]
            )  # 获取当前文件类型对应的数据集

            current_data.append(result_data)
            setattr(
                self, self.MODE_CONFIG[result_type]["data_attr"], current_data
            )  # 将新增数据加入到数据集中

            setattr(self, self.MODE_CONFIG[result_type]["notification_attr"], True)
        except Exception as e:
            logger.error(f"解析文件「{filename}」过程中遇到错误：{e}。")
            raise ValueError(f"解析文件「{filename}」过程中遇到错误：{e}。")

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        """用户上传文件后的处理函数，将文件转换为base64编码，将编码后的文件传递给相应的上游 api 处理，返回格式化后的处理结果

        Args:
            files (list[rx.UploadFile]): 文件列表，可以是一个文件也可以是多个文件

        Returns:
            AsyncGenerator[None, Any]: 没有输出，只会通过 yield 更新两次页面状态，第一次是将 loading 设置为 True，第二次是将 loading 设置为 False。
        """

        # 批量调用 api 接口
        try:
            self.upload_loading = True  # 接收到文件后，更新 loading状态
            self.test_mode = False
            yield
            start_time = time.time()
            tasks = [self.uni_request(file) for file in files]
            await asyncio.gather(*tasks)
            end_time = time.time()
            elapsed_time = end_time - start_time
            logger.info(
                f"函数 handle_upload 处理{len(files)}个文件,用时：{elapsed_time:.5f}s"
            )  # 计算函数运行时间
        except Exception as e:  # 检查异常
            yield rx.window_alert(f"{e}\n其他文件将正常解析。")
        finally:
            self.upload_loading = False  # 文件上传结束，更新 loading 状态

    @rx.event
    def get_edited_data(self, pos: tuple[int, int], val):
        """处理页面表格更新的函数，将更新的数据存储在对应选单的数据集中，这样用户编辑后页面的数据也能同步更新。

        Args:
            pos (tuple[int, int]): 表格的位置信息，是一个二维元组
            val (_type_): 用户输入位置的单元格对象，应该是 reflex 自定义的一个类，类似字典，val["data"] 是用户输入的值
        """
        current_data = self.get_current_data
        col, row = pos
        current_data[row][col] = val["data"]
        setattr(self, self.MODE_CONFIG[self.mode]["data_attr"], current_data)

    @rx.event
    def download_to_excel(self) -> Generator:
        """将 bank_slips_date 或 invoice_data 内的信息下载为 excel 表

        Yields:
            Generator: yield 一个 rx.download 事件，将数据下载为 excel 表
        """
        self.download_loading = True  # 将下载按钮的状态切换为 loading
        yield

        data = [
            item for item in self.get_current_data
        ]  # 获取当前选单的数据,要注意， 作为 state 的属性，他们并不是真正的列表，而是一个 reflex 定义的特殊对象（reflex.vars.sequence.ToArrayOperation），所以需要通过 item 的方式提取出来。

        df = pl.DataFrame(
            data,
            schema=[
                column["title"] for column in self.MODE_CONFIG[self.mode]["columns"]
            ],
            orient="row",
        )

        file_name = f"{self.MODE_CONFIG[self.mode]["filename_tag"]}-{datetime.now().strftime("%Y%m%d%H%M%S") }"  # 文件名格式：增值税发票/银行回单-时间字符串

        buffer = io.BytesIO()  # 生成一个 BytesIO 对象，用于存储 excel 文件
        df.write_excel(buffer)  # 将 excel 文件写入 BytesIO 对象

        self.download_loading = False  # 文件准备结束，结束下载按钮的 loading 状态

        yield rx.download(data=buffer.getvalue(), filename=f"{file_name}.xlsx")

    @rx.event
    def set_notification_false(self):
        """将 notification 的状态切换为 False，这样 notification 就会消失"""
        setattr(self, self.MODE_CONFIG[self.mode]["notification_attr"], False)


def test_mode_for_recognize() -> rx.Component:
    return rx.hstack(
        rx.text("演示模式", size="1"),
        rx.switch(
            checked=UploadFile.test_mode,
            on_change=UploadFile.go_test,
            color_scheme="violet",
            variant="surface",
            radius="full",
        ),
        position="fixed",
        top="10px",
        right="10px",
        align="center",
    )


def notification_badge() -> rx.Component:
    """在切换按钮上显示信息更新的红点"""
    return rx.box(
        background_color="#DC3B5D",
        border_radius="100%",
        height="7px",
        width="7px",
    )


def render_hint_text(hint_text: str) -> rx.Component:
    """渲染上传区的提示词文本"""
    return rx.text(
        hint_text,
        size="1",
        align="center",
    )


def upload_zone(
    is_loading: bool,
    color: str,
    hint_text: list[str],
    upload_id: str = "upload1",
) -> rx.Component:
    """文件上传区组件

    Args:
        is_loading (bool): 确认是否处于 loading 状态（是否有文件正在上传）
        color (str): 主题色
        hint_text (list[str]): 提示词
        upload_id (str, optional): html 中的 id. 默认值是 "upload1".

    Returns:
        rx.Component: _description_
    """
    return rx.upload(
        rx.vstack(
            rx.button(  # 上传文件的按钮
                "上传文件",
                loading=is_loading,
                color=color,
                bg="white",
                border=f"1px solid {color}",
                width="82px",
                height="32px",
            ),
            rx.foreach(hint_text, render_hint_text),
            align="center",
            justify="center",
            width="100%",
            height="100%",
            spacing="1",
        ),
        id=upload_id,
        border=f"1px dotted {color}",
        multiple=True,
        accept={
            "image/png": [".png"],
            "image/jpeg": [".jpg", ".jpeg"],
            "image/webp": [".webp"],
            "application/pdf": [".pdf"],
        },
        max_files=10,
        disabled=is_loading,
        no_keyboard=True,
        on_drop=UploadFile.handle_upload(
            rx.upload_files(upload_id=upload_id)
        ),  # type:ignore
        align="center",
        justify="center",
        border_radius="2%",
        width=rx.breakpoints(initial="80vw", md="30vw"),
        height="35vh",
        padding="20px",
        margin_x="3px",
    )


def render_data() -> rx.Component:
    """生成展示识别结果的表格

    Returns:
        rx.Component: 将识别结果渲染为表格
    """
    return rx.vstack(
        rx.data_editor(
            columns=UploadFile.get_current_columns,
            data=UploadFile.get_current_data,
            align="center",
            justify="center",
            on_cell_edited=UploadFile.get_edited_data,  # 表格可以编辑
            freeze_columns=1,
            get_cell_for_selection=True,
            column_select="multi",
            draw_focus_ring=True,
            on_paste=True,
            fixed_shadow_x=True,
            fixed_shadow_y=True,
            smooth_scroll_x=True,
            smooth_scroll_y=True,
            min_column_width=100,
            max_column_width=300,
            max_column_auto_width=300,
            width=rx.breakpoints(initial="90vw", md="60vw"),
            height=rx.breakpoints(md="30vh"),
            border_radius="2%",
        ),
        rx.cond(  # 一个是否在准备下载文件的条件判断，如果有文件正在准备下载则显示加载按钮
            UploadFile.download_loading,
            rx.button(
                loading=True,
                color=color,
                bg="white",
                border=f"1px solid {color}",
                width="82px",
                height="32px",
            ),
            rx.button(
                "下载结果",
                on_click=UploadFile.download_to_excel,
                color=color,
                bg="white",
                border=f"1px solid {color}",
            ),
        ),
        rx.text("下载为 Excel 表", size="1"),
        rx.callout(
            "如识别结果有误，可双击单元格修改。",
            icon="info",
            color_scheme="violet",
        ),
        margin_top="5px",
        align="center",
        justify="center",
        margin="3px",
        spacing="3",
    )


def process_mode_tabs() -> rx.Component:
    """
    处理tab切换按钮，也就是 UploadFile.mode 的值
    只有在有数据时才会显示，如果没有数据就不会显示
    这个 tab 已经包含了需要渲染的数据表格
    """
    return rx.tabs.root(
        rx.tabs.list(
            rx.tabs.trigger(
                rx.hstack(
                    rx.icon("ticket", size=15),
                    rx.text("增值税发票", size="2"),
                    rx.cond(
                        UploadFile.invoice_notification,
                        notification_badge(),
                    ),
                    justify="center",
                    align="center",
                    width="120px",
                    spacing="2",
                ),
                value="invoice",
                on_click=UploadFile.set_notification_false,
            ),
            rx.tabs.trigger(
                rx.hstack(
                    rx.icon("landmark", size=15),
                    rx.text("银行回单", size="2"),
                    rx.cond(
                        UploadFile.bank_slips_notification,
                        notification_badge(),
                    ),
                    width="120px",
                    justify="center",
                    align="center",
                    spacing="2",
                ),
                value="bank_slip",
                on_click=UploadFile.set_notification_false,
            ),
        ),
        rx.tabs.content(
            render_data(),
            value="invoice",
        ),
        rx.tabs.content(
            render_data(),
            value="bank_slip",
        ),
        on_change=UploadFile.set_mode,  # type:ignore
        variant="classic",
        radius="large",
        value=UploadFile.mode,
    )


def recognize_title() -> rx.Component:
    """票据识别模块的单页小标题"""
    return rx.vstack(
        rx.heading(  # 大标题
            "发票转Excel",
            as_="h2",
            color_scheme="violet",
            size=rx.breakpoints(initial="8", xs="9"),
            margin_top=rx.breakpoints(initial="30px", md="0px"),
        ),
        rx.hstack(  # 小标题
            rx.text(
                "批量识别增值税发票与银行回单,导出为Excel",
                size=rx.breakpoints(initial="3", xs="6"),
            ),
            rx.badge(
                rx.text("New", size="1"),
                size="1",
                color_scheme="violet",
                variant="soft",
                padding="1px",
            ),
            spacing="1",
            justify="start",
        ),
        margin_bottom="15px",
        align="center",
    )


def recognize_page() -> rx.Component:
    return rx.vstack(
        test_mode_for_recognize(),
        recognize_title(),
        # ------------------ 桌面端显示----------------------
        rx.desktop_only(
            rx.hstack(
                rx.cond(
                    # 文件上传区
                    # 用于检查是否正在上传的条件判断，如果有文件在上传，显示加载状态
                    UploadFile.upload_loading,
                    upload_zone(
                        is_loading=True,
                        color=color,
                        hint_text=["文件上传中……"],
                    ),
                    upload_zone(
                        is_loading=False,
                        color=color,
                        hint_text=[
                            "将发票或银行回单文件拖入框内",
                            "支持文件格式：.jpg、.jpeg、.png、.pdf",
                            "一次最多上传10个文件，可分批多次上传",
                        ],
                    ),
                ),
                rx.cond(
                    # 表格显示区
                    # 检查 bank_slips_date内是否有数据，如果有显示表格和下载按钮
                    UploadFile.data_is_exists,
                    process_mode_tabs(),
                ),
                align="start",
                justify="center",
                width="100%",
                height="100%",
            ),
        ),
        # ------------------ 移动端显示-----------------
        rx.mobile_and_tablet(
            rx.vstack(
                rx.cond(
                    # 文件上传区
                    # 用于检查是否正在上传的条件判断，如果有文件在上传，显示加载状态
                    UploadFile.upload_loading,
                    upload_zone(
                        is_loading=True,
                        color=color,
                        hint_text=["文件上传中……"],
                    ),
                    upload_zone(
                        is_loading=False,
                        color=color,
                        hint_text=[
                            "将发票或银行回单文件拖入框内",
                            "支持文件格式：.jpg、.jpeg、.png、.pdf",
                            "一次最多上传10个文件，可分批多次上传",
                        ],
                    ),
                ),
                rx.cond(
                    # 表格显示区
                    # 检查 bank_slips_date内是否有数据，如果有显示表格和下载按钮
                    UploadFile.data_is_exists,
                    process_mode_tabs(),
                ),
                align="center",
                justify="center",
                width="100%",
                height="100%",
            ),
        ),
        align="center",
        justify="center",
        width="100%",
        height="100%",
    )
