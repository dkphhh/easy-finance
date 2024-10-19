import reflex as rx

from .components import dark_mode_toggle
from .pages.recognize import (
    recognize_page,
    test_mode_for_recognize,
)

"""
TODO:

1.新增功能模块：批量票据文件名改名
2.新增功能模块：数字大小写转换
3.美化table,给未识别内容标黄突出显示
4.增加一个删除内容的警告
5.增加一个将结果回传到飞书表格的功能


"""


meta = [{"name": "keywords", "content": "发票,银行回单,图片,PDF,识别,转Excel"}]


@rx.page(
    route="/",
    title="Easy Finance-发票识别，银行回单识别",
    description="批量识别发票与银行回单，发票、银行回单图片、PDF转Excel表格",
    meta=meta,
)
def index():
    """主页面"""
    return rx.fragment(
        dark_mode_toggle(),  # 明暗模式调整按钮
        test_mode_for_recognize(),  # 测试模式按钮
        rx.vstack(
            recognize_page(),  # 发票与回单识别页面
            width="100vw",
            height=rx.breakpoints(initial="100%", md="100vh"),
            spacing="1",
        ),
    )


app = rx.App(
    theme=rx.theme(
        appearance="inherit",
        has_background=True,
        radius="large",
        accent_color="violet",
        gray_color="auto",
        panel_background="solid",
    ),
)
