import reflex as rx
from sqlmodel import Field, select
from datetime import datetime, date
from typing import Annotated


class User(rx.Model, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    username: str
    email: str
    password: str


def create_users(users: list[User]):
    with rx.session() as session:
        for user in users:
            session.add(user)
        session.commit()

        # 手动刷新
        for user in users:
            session.refresh(user)

    userid_list = [user.id for user in users]

    return userid_list


class JournalAccount(rx.Model, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    trade_date: Annotated[date, Field(index=True)]  # 交易发生的时间
    description: Annotated[str, Field(index=True)] = ""  # 关于这笔流水的说明
    additional_info: Annotated[str, Field(index=True)] = ""  # 备注
    amount: str  # 金额
    category: Annotated[str, Field(index=True)] = ""  # 分类
    payer: Annotated[str, Field(index=True)]  # 付款方
    receiver: Annotated[str, Field(index=True)]  # 收款方
    bank_slip_url: str = ""  # 银行回单文件链接
    tax_invoice_url: str = ""  # 发票文件链接
    created_datetime: datetime = datetime.now()  # 记录生成时间

    @classmethod
    def create_records(cls, records: list[dict]):
        with rx.session() as session:

            new_records = []

            for record in records:
                new_record = JournalAccount(**record)
                new_records.append(new_record)
                session.add(new_record)

            session.commit()

            for record in new_records:
                session.refresh(record)

            return new_records

    @classmethod
    def get_all_records(cls) -> list[dict]:
        with rx.session() as session:
            records = session.exec(select(JournalAccount)).all()
            result = [record.model_dump() for record in records]
            return result


if __name__ == "__main__":
    print(JournalAccount.get_all_records())
