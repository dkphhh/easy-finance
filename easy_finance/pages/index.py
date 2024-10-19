import os

import reflex as rx

from .components import dark_mode_toggle
from .recognize import recognize_page

PASSWORD = os.getenv("PASSWORD")


class PassState(rx.State):
    """进入网站后的密码验证"""

    check: rx.Field[bool] = rx.field(False)

    def check_input(self, value: dict[str, str]) -> None | rx.Component:
        """用于验证用户输入的值是否等于环境变量里的 PASSWORD

        Args:
            value (dict[str, str]): 前端提交的表单值

        Returns:
            None | rx.Component: 如果密码正确不返回值，如果密码错误,在前端显示一个小提示
        """
        if value["password"] == PASSWORD:
            self.check = True
        else:
            self.check = False
            return rx.toast.warning("密码错误!", close_button=True, duration=3000)


meta = [{"name": "keywords", "content": "发票,银行回单,图片,PDF,识别,转Excel"}]


@rx.page(
    route="/",
    title="Easy Finance-发票识别，银行回单识别",
    description="批量识别发票与银行回单，发票、银行回单图片、PDF转Excel表格",
    meta=meta,
)
def index() -> rx.Component:
    """主页面"""
    return rx.fragment(
        dark_mode_toggle(),  # 明暗模式调整按钮
        rx.cond(  # type:ignore
            PassState.check,
            rx.vstack(
                recognize_page(),  # 发票与回单识别页面
                width="100vw",
                height=rx.breakpoints(initial="100%", md="100vh"),
                spacing="1",
            ),
            rx.form(  # 输入密码的表单
                rx.hstack(
                    rx.input(
                        name="password",
                        placeholder="请输入密码",
                        type="password",
                        required=True,
                    ),
                    rx.button("确定", type="submit"),
                    spacing="1",
                    height="100vh",
                    width="100vw",
                    justify="center",
                    align="center",
                ),
                on_submit=PassState.check_input,
            ),
        ),
    )