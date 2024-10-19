import reflex as rx
from reflex.style import color_mode, toggle_color_mode


def navbar_item(text: str, icon: str, url: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon),
            rx.text(text, size="4", weight="medium"),
        ),
        href=url,
    )


def navbar_menu_item(text: str, icon: str, url: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(icon, size=16),
            rx.text(text, size="3", weight="medium"),
        ),
        href=url,
    )


def navbar() -> rx.Component:
    return rx.box(
        rx.desktop_only(
            rx.hstack(
                rx.heading("Easy Finance", as_="h1", size="6", color_scheme="violet"),
                rx.hstack(
                    navbar_item("Home", "home", "/"),
                    navbar_item("Test", "flask-conical", "/test"),
                    navbar_item("Contact", "mail", "/#"),
                    navbar_item("Services", "layers", "/#"),
                    spacing="6",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        rx.mobile_and_tablet(
            rx.hstack(
                rx.heading("Easy Finance", as_="h1", size="6", color_scheme="violet"),
                rx.menu.root(
                    rx.menu.trigger(rx.icon("menu", size=30)),
                    rx.menu.content(
                        navbar_menu_item("Home", "home", "/#"),
                        navbar_menu_item("Pricing", "coins", "/#"),
                        navbar_menu_item("Contact", "mail", "/#"),
                        navbar_menu_item("Services", "layers", "/#"),
                    ),
                    justify="end",
                ),
                justify="between",
                align_items="center",
            ),
        ),
        bg=rx.color("accent", 3),
        padding="1em",
        # position="fixed",
        # top="0px",
        # z_index="5",
        width="100%",
        margin_bottom="10px"
    )


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
