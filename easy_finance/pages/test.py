import reflex as rx
from ..utils.request_api import request_api


class RecordState(rx.State):
    res: list[str] = []
    file_names: list[str] = []

    async def handle_upload(self, files: list[rx.UploadFile]):
        res = []
        file_names = []

        for f in files:
            file_names.append(f.filename)
            resp = await request_api(file=f, mode="bank_slip")

        self.res = res
        self.file_names = file_names


def upload_zone() -> rx.Component:
    return rx.upload(
        rx.vstack(
            rx.button(
                "Select File",
                bg="white",
                border="1px solid",
            ),
            rx.text("Drag and drop files here or click to select files"),
        ),
        id="upload1",
        border=f"1px dotted",
        padding="5em",
        on_drop=RecordState.handle_upload(
            rx.upload_files(upload_id="upload1")
        ),  # type:ignore
    )


@rx.page(route="/test", title="测试页面")
def test_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            upload_zone(),
            rx.foreach(
                RecordState.file_names,
                lambda file_name: rx.hstack(
                    rx.image(src=rx.get_upload_url(file_name)), rx.divider()
                ),
            ),
        ),
        size="4",
    )
