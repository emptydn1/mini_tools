"""
Hệ thống menu console: định nghĩa menu chính + menu con,
và vòng lặp chạy menu dùng chung.
"""

from mumu_tool.tool_game.mumu.control import openAllmumuplayer, nhap_tai_khoan, hoangdnvn, menu_nhap_theo_danh_sach
from mumu_tool.tool_game.kiemhieptinh1.hoa_dang import posHoaDang, turnOffAuto, vut_do_hoa_dang, screenshot_mode, logOut_temp
from mumu_tool.tool_game.kiemhieptinh1.cay_van import cay_van
from mumu_tool.tool_game.kiemhieptinh1.to_doi_bst_tay import to_doi_bst_tay, loop_to_doi_bst
from mumu_tool.tool_game.kiemhieptinh1.giao_dich_van import giao_dich_van_Hoang, giao_dich_van_Huy
from mumu_tool.tool_game.kiemhieptinh1.tool_vut_exp import tool_vut_exp
from mumu_tool.tool_game.kiemhieptinh1.da_tau import lam_da_tau, vut_do_da_tau
from mumu_tool.tool_game.utils import auto_click, auto_luom, sync_mouse_keyboard, test_click


def run_menu(title, menu_dict):
    while True:
        print(f"\n========== {title} ==========")
        for key, (text, _) in menu_dict.items():
            print(f"{key}. {text}")
        print("Q. Thoát")
        print("============================")

        choice = input("Chọn: ").strip().lower()

        if choice in ("q"):
            break

        if choice not in menu_dict:
            print("❌ Lựa chọn không hợp lệ.")
            continue

        text, func = menu_dict[choice]
        print(f"▶ Đang chạy: {text}")

        try:
            func()
        except Exception as e:
            print(f"Lỗi: {e}")

        print("\n✅ Hoàn thành!")
        input("Nhấn Enter để tiếp tục...")


def menu_kiemhieptinh1():
    def menu_hoa_dang():
        def menu_vi_tri_hoa_dang():
            menu = {
                "1": ("Huy", lambda: posHoaDang("huy")),
                "2": ("Hoang", lambda: posHoaDang("hoang")),
                "3": ("Hao", lambda: posHoaDang("hao")),
                "4": ("may4", lambda: posHoaDang("may4")),
                "5": ("may5", lambda: posHoaDang("may5")),
                "6": ("may6", lambda: posHoaDang("may6")),
                "7": ("tắt nhặt đồ, tự động đánh", turnOffAuto),
                "8": ("logout", logOut_temp),
            }
            run_menu("sắp vị trí acc Hoa Đăng", menu)

        menu = {
            "1": ("sắp vị trí acc Hoa Đăng", menu_vi_tri_hoa_dang),
            "2": ("chụp hình lấy câu trả lời Hoa Đăng", screenshot_mode),
            "3": ("vứt đồ Hoa Đăng", vut_do_hoa_dang),
        }
        run_menu("Hoa Đăng", menu)

    def menu_giao_dich_van():
        menu = {
            "1": ("Hoang", giao_dich_van_Hoang),
            "2": ("Huy", giao_dich_van_Huy),
        }
        run_menu("giao dịch vạn", menu)

    def menu_lam_nv_da_tau():
        menu = {
            "1": ("lam da tau - Hoang", lam_da_tau),
            "2": ("lam da tau - Huy", vut_do_da_tau),
        }
        run_menu("làm nhiệm vụ dã tẩu", menu)

    menu = {
        "1": ("hoa đăng", menu_hoa_dang),
        "2": ("cày vạn", cay_van),
        "3": ("giao dịch vạn", menu_giao_dich_van),
        "4": ("tổ đội bằng tay", to_doi_bst_tay),
        "5": ("loop tổ đội BST", loop_to_doi_bst),
        "6": ("tool vứt exp", tool_vut_exp),
        "7": ("làm dã tẩu", menu_lam_nv_da_tau),
    }
    run_menu("KIẾM HIỆP TÌNH 1", menu)


def menu_mumuplayer():
    menu = {
        "1": ("mở giả lập mumuplayer", openAllmumuplayer),
        "2": ("nhập tài khoản theo yêu cầu", nhap_tai_khoan),
        "3": ("nhập tài khoản theo danh sách", menu_nhap_theo_danh_sach),
        "4": ("điền thứ tự tài khoản hoangdnvn", hoangdnvn),
    }
    run_menu("TOOLS MUMUPLAYER", menu)


def menu_sync_mouse_keyboard():
    menu = {
        "1": ("MASTER", lambda: sync_mouse_keyboard("MASTER")),
        "2": ("SLAVE", lambda: sync_mouse_keyboard("SLAVE")),
    }
    run_menu("Sync Mouse Keyboard", menu)


main_menu = {
    "1": ("tools mumuplayer", menu_mumuplayer),
    "2": ("kiem hiep tinh 1", menu_kiemhieptinh1),
    "3": ("auto click", auto_click),
    "4": ("auto luom", auto_luom),
    "5": ("đồng bộ chuột bàn phím", menu_sync_mouse_keyboard),
    "6": ("test click", test_click),
}
