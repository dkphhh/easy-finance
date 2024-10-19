import reflex as rx


class UserState(rx.State):
    form_data: dict = {}

    def handle_submit(self, form_data: dict):
        """Handle the form submit."""
        self.form_data = form_data


@rx.page(route="/test", title="测试页面")
def test_page() -> rx.Component:
    return rx.vstack(
        rx.form(
            rx.vstack(
                rx.input(
                    name="username",
                    placeholder="Enter your user name",
                ),
                rx.input(
                    name="email",
                    placeholder="Enter your email",
                ),
                rx.input(name="password", type_="password"),
                rx.button("Submit", type="submit"),
                align="center",
            ),
            on_submit=UserState.handle_submit,
            reset_on_submit=True,
        ),
        rx.divider(),
        rx.heading("Results"),
        rx.text(UserState.form_data.to_string()),  # type:ignore
        height="100vh",
        width="100vw",
        justify="center",
        align="center",
        spacing="2",
    )
