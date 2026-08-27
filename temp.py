
# def nhap_tai_khoan():
#     check_shells_created()

#     def _nhap_input(lan):
#         while True:
#             value = input(f"Nhập lần {lan} (Q để thoát): ").strip()

#             if value.lower() == "q":
#                 return None

#             arr = value.split("-")

#             if len(arr) != 3 or not arr[0].isdigit() or not arr[2].isdigit() or not arr[1]:
#                 print("❌ Sai định dạng! Phải có dạng: 1-huy-1")
#                 continue

#             return arr

#     arr1 = _nhap_input(1)

#     if arr1 is None:
#         return

#     arr2 = _nhap_input(2)

#     if arr2 is None:
#         return

#     # Kiểm tra tên
#     if arr1[1] != arr2[1]:
#         print("❌ Tên 2 input phải giống nhau!")
#         return

#     start = int(arr1[0])
#     name = arr1[1]
#     end = int(arr2[0])

#     start_number = int(arr1[2])
#     end_number = int(arr2[2])

#     accounts = []
#     for i in range(start, end + 1):
#         temp = []
#         for j in range(start_number, end_number + 1):
#             temp.append(f"{i}{name}{j}")
#         accounts.append(temp)

#     input_text_list(accounts[0])





# def menu_nhap_theo_danh_sach():
#     check_shells_created()

#     try:
#         with open(r"C:\Users\huy\Desktop\accounts.txt", "r", encoding="utf-8") as f:
#             danh_sach = [line.strip() for line in f if line.strip()]
#     except FileNotFoundError:
#         print("❌ Không tìm thấy file 1.txt")
#         input("Nhấn Enter để tiếp tục...")
#         return

#     if not danh_sach:
#         print("❌ File 1.txt không có dữ liệu.")
#         input("Nhấn Enter để tiếp tục...")
#         return

#     while True:
#         print("\n========== NHẬP THEO DANH SÁCH ==========")

#         for i, item in enumerate(danh_sach, 1):
#             print(f"{i}. {item}")

#         print("Q. Thoát")
#         print("==========================================")

#         choice = input("Chọn: ").strip().lower()

#         if choice == "q":
#             break

#         if not choice.isdigit():
#             print("❌ Lựa chọn không hợp lệ.")
#             continue

#         index = int(choice) - 1

#         if index < 0 or index >= len(danh_sach):
#             print("❌ Lựa chọn không hợp lệ.")
#             continue

#         data = danh_sach[index]

#         print(f"▶ Đã chọn: {data}")

#         parts = data.split()

#         arr1 = parts[0].split("-")
#         arr2 = parts[1].split("-")

#         start = int(arr1[0])
#         name = arr1[1]
#         end = int(arr2[0])

#         start_number = int(arr1[2])
#         end_number = int(arr2[2])

#         accounts = []
#         for i in range(start, end + 1):
#             temp = []
#             for j in range(start_number, end_number + 1):
#                 temp.append(f"{i}{name}{j}")
#             accounts.append(temp)

#         input_text_list(accounts[0])

#         input("\nNhấn Enter để tiếp tục...")
