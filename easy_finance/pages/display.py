import reflex as rx
from reflex_ag_grid import ag_grid
from ..models import JournalAccount
from .upload import bank_slip_column_defs
from sqlmodel import select

"""
TODO:
1. 加一个发票上传的功能，上传完以后自动将发票文件的链接拷贝到剪贴板，提示用户可以粘贴
2. 


"""


class DisplayState(rx.State):
    """
    向用户展示数据的 State
    """

    display_data: list[dict] = []  # 展示的数据

    @rx.var
    def data(self) -> list[dict]:
        """
        Ag Grid 组件需要用 computed var 向前端传输数据，用 state var 数据更新会有延迟

        Returns: 展示的数据

        """
        return self.display_data

    def load_data(self) -> None:
        """
        用于在页面加载时从数据库中获取数据
        """
        self.display_data = JournalAccount.get_all_records()

    def cell_value_changed(self, row, col_field, new_value) -> None:
        """
        实时处理用户对表格内容的修改，并更新到数据库
        Args:
            row: 修改单元格的行
            col_field: 修改单元格的列
            new_value: 单元格的更新值
        """
        self.display_data[row][col_field] = new_value  # 获取更新数据
        with rx.session() as session:
            record = session.get(
                JournalAccount, self.display_data[row]["id"]
            )  # 通过id获取更新条目对应的数据库实例
            if record:
                setattr(record, col_field, new_value)  # 修改数据库内的值
                session.commit()

        yield rx.toast(
            f"数据更新, 行: {row}, 列: {col_field}, 更新值: {new_value}"
        )  # 向用户发出提示


def ag_grid_zone() -> rx.Component:
    return ag_grid(
        id="ag_grid_basic_editing",
        row_data=DisplayState.data,
        column_defs=bank_slip_column_defs,
        on_cell_value_changed=DisplayState.cell_value_changed,
        width="90vw",
        height="90vh",
        pagination=True,
        pagination_page_size=10,
        pagination_page_size_selector=[10, 50, 100],
    )


@rx.page(
    route="/display", title="财务数据展示-EasyFinance", on_load=DisplayState.load_data
)
def display() -> rx.Component:
    return rx.flex(ag_grid_zone(), justify="center", padding_top="2rem")
