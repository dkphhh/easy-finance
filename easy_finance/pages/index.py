import os

import reflex as rx

from .components import nav_bar
from .upload import upload_and_send

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
    title="快捷记账-EasyOffice",
    description="自动识别银行回单，并导入到数据库",
    meta=meta,
)
def index() -> rx.Component:
    """主页面"""
    return rx.fragment(
        rx.cond(  # type:ignore
            PassState.check,
            rx.vstack(
                nav_bar(),
                upload_and_send(),  # 上传银行回单、识别、将结果上传到数据库
                width="100vw",
                spacing="1",
                align="center",
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
