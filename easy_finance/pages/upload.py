import reflex as rx
from ..utils.request_api import request_api
from reflex_ag_grid import ag_grid
from ..models import JournalAccount
from datetime import datetime, timedelta


class UploadState(rx.State):

    upload_data: list[dict] = []

    @rx.var
    def data(self) -> list[dict]:
        """
        Ag Grid 组件最好用 computed var 传输数据，用 state var 数据更新会有延迟
        Returns: 用户上传的数据

        """
        return self.upload_data

    async def handle_upload(self, files: list[rx.UploadFile]) -> None:
        """
        调用百度云的api，上传用户传入的文件，将返回的数据赋值给 self.upload_data
        Args:
            files: 用户上传的文件

        """
        resp_list = [await request_api(file=f, mode="bank_slip") for f in files]
        self.upload_data.extend(resp_list)

    def cell_value_changed(self, row, col_field, new_value) -> None:
        """
        同步更新表格
        Args:
            row: 更新表格的行数
            col_field:  更新表格的字段
            new_value: 用户输入的新值

        """

        if col_field == "trade_date":

            try:
                # 将 ISO 格式转换为 YYYY-MM-DD 格式
                utc_date = datetime.fromisoformat(new_value.replace("Z", "+00:00"))
                local_date = utc_date + timedelta(hours=8)
                formatted_date = local_date.strftime("%Y-%m-%d")
                self.upload_data[row][col_field] = formatted_date

            except (ValueError, AttributeError):
                formatted_date = ""
                self.upload_data[row][col_field] = formatted_date

        else:
            self.upload_data[row][col_field] = new_value

    def send_to_database(self) -> None:
        """
        将数据上传到数据库,刷新 upload_data，清空前端表格
        如果用户上传空数据会警告
        """

        if self.upload_data:

            JournalAccount.create_records(records=self.upload_data)
            self.upload_data = []

        else:
            yield rx.toast.error("数据为空！", duration=2000)


bank_slip_column_defs = [
    ag_grid.column_def(
        field="trade_date",
        header_name="交易日期",
        cell_data_type="date",
        editable=True,
        filter=ag_grid.filters.date,
        cell_editor=ag_grid.editors.date,
    ),
    ag_grid.column_def(
        field="description",
        header_name="项目描述",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
    ag_grid.column_def(
        field="additional_info",
        header_name="备注",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
    ag_grid.column_def(
        field="amount",
        header_name="金额",
        cell_data_type="number",
        editable=True,
        filter=ag_grid.filters.number,
        cell_editor=ag_grid.editors.number,
    ),
    ag_grid.column_def(
        field="category",
        header_name="分类",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
        header_tooltip="""
                搜索广告:
                营销推广:
                外包劳务:
                技术服务:
                物业支出:
                财务分红:
                其他支出:
        """,
        cell_editor_params={
            "values": [
                "搜索广告",
                "营销推广",
                "外包劳务",
                "技术服务",
                "物业支出",
                "财务分红",
                "其他支出",
            ]
        },
    ),
    ag_grid.column_def(
        field="payer",
        header_name="付款方",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
    ag_grid.column_def(
        field="receiver",
        header_name="收款方",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
    ag_grid.column_def(
        field="bank_slip_url",
        header_name="银行回单",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
    ag_grid.column_def(
        field="tax_invoice_url",
        header_name="发票",
        cell_data_type="text",
        editable=True,
        filter=ag_grid.filters.text,
        cell_editor=ag_grid.editors.text,
    ),
]


def ag_grid_zone() -> rx.Component:
    return rx.vstack(
        ag_grid(
            id="ag_grid_basic_editing",
            row_data=UploadState.data,
            column_defs=bank_slip_column_defs,
            on_cell_value_changed=UploadState.cell_value_changed,
            width="90vw",
            height="50vh",
            pagination=True,
            pagination_page_size=10,
            pagination_page_size_selector=[10, 50, 100],
        ),
    )


def upload_zone() -> rx.Component:
    return rx.upload(
        rx.text("Drag and drop files here or click to select files"),
        id="upload1",
        border=f"1px dotted",
        padding="5em",
        width="40vw",
        height="30vh",
        on_drop=UploadState.handle_upload(
            rx.upload_files(upload_id="upload1")
        ),  # type:ignore
        accept={
            "image/png": [".png"],
            "image/jpeg": [".jpg", ".jpeg"],
            "image/bmp": [".bmp"],
            "application/pdf": [".pdf"],
        },
    )


def upload_and_send() -> rx.Component:
    return rx.vstack(
        upload_zone(),
        ag_grid_zone(),
        rx.button("上传数据", on_click=UploadState.send_to_database),
        width="100%",
        align="center",
        justify="center",
        padding="2em",
    )
