import reflex as rx
from reflex.style import color_mode, toggle_color_mode


def dark_mode_toggle() -> rx.Component:
    """全局切换亮/暗模式"""
    return rx.flex(
        rx.button(
            rx.cond(
                color_mode == "light",
                rx.icon("sun", size=25, color=rx.color("slate", 12)),
                rx.icon("moon", size=25, color=rx.color("slate", 12)),
            ),
            on_click=toggle_color_mode,
            padding=0,
            variant="ghost",
            width="40px",
            height="40px",
        ),
        width="160px",
        justify="end",
    )


class NavItem(rx.Base):
    name: str = ""
    path: str = ""


class NavBarState(rx.State):
    items: list[NavItem] = [
        NavItem(name="快捷记账", path="/"),
        NavItem(name="账目一览", path="/display"),
    ]


def render_nav_item(item: NavItem) -> rx.Component:
    return rx.heading(
        rx.link(
            item.name,
            href=item.path,
            color=rx.cond(
                rx.State.router.page.path == item.path,
                rx.color("slate", 12),
                rx.color("slate", 10),
            ),
        ),
        as_="h2",
        size="6",
    )


def nav_bar() -> rx.Component:
    return rx.el.nav(
        rx.flex(
            rx.box(
                rx.heading(
                    rx.link("EasyOffice", href="/", color=rx.color("slate", 2)),
                    as_="h1",
                    size="6",
                ),
                bg=rx.color("slate", 12),
                class_name="rounded-full py-1 px-4 w-40",
            ),
            rx.hstack(
                rx.foreach(NavBarState.items, render_nav_item),
                spacing="5",
                align="center",
                justify="center",
            ),
            dark_mode_toggle(),
            direction="row",
            justify="between",
            align="center",
            width="80%",
            height="48px",
        ),
        bg=rx.color("slate", 2),
        class_name="flex flex-row justify-center items-center w-8/12 h-16 mt-2 rounded-full",
    )
