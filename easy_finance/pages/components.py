import reflex as rx
from reflex.style import color_mode, toggle_color_mode


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
