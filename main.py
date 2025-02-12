import os
import Rdata
import Ghtml


def main():
    print("正在执行 Rdata.py ...")
    # 调用 Rdata.py 中的主更新函数
    Rdata.main_update()

    print("正在执行 Ghtml.py ...")
    # 调用 Ghtml.py 中的 main 函数生成 HTML 文件
    Ghtml.main()

    print("所有脚本执行完成！")
    os.system("pause")

if __name__ == '__main__':
    main()
