import reflex as rx

"""
TODO:

1.新增功能模块：批量票据文件名改名
2.新增功能模块：数字大小写转换
3.美化table,给未识别内容标黄突出显示
4.增加一个删除内容的警告
5.增加一个将结果回传到飞书表格的功能


"""


app = rx.App(
    theme=rx.theme(
        appearance="inherit",
        accent_color="gray",
        gray_color="slate",
        radius="full",
        panel_background="translucent",
        scaling="100%",
    )
)
