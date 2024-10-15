import reflex as rx
from reflex.style import color_mode, toggle_color_mode

from .pages.recognize import (
    recognize_page,
    recognize_title,
    test_mode_for_recognize,
)

"""
TODO:

2. 增加一个将结果回传到飞书表格的功能
3. 美化table,给未识别内容标黄突出显示
4. 增加一个删除内容的警告


"""


# class IndexState(rx.State):
    









def dark_mode_toggle() -> rx.Component:
    """全局切换亮/暗模式"""
    return rx.button(
        rx.cond(
            color_mode == "light",
            rx.icon("sun", size=18),
            rx.icon("moon", size=18),
        ),
        on_click=toggle_color_mode,
        size="1",
        color_scheme="violet",
        variant="soft",
        radius="large",
        width="30px",
        height="30px",
        padding="0px",
        position="fixed",
        left="10px",
        bottom="10px",
    )


def header() -> rx.Component:
    """标题栏"""
    return rx.vstack(
        rx.heading(  # 大标题
            "Easy Finance",
            as_="h1",
            color_scheme="violet",
            size=rx.breakpoints(initial="8", xs="9"),
        ),
        recognize_title(),
        margin_bottom="10px",
        align="center",
    )


# --------------------------- 页面构建 -------------------


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
            header(),  # 标题
            recognize_page(),  # 发票与回单识别页面
            align="center",
            justify="center",
            width="100vw",
            height=rx.breakpoints(initial="100%", xs="100vh"),
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
