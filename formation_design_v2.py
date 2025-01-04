import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab

class FormationApp:
    def __init__(self, root, performers, stage_n, stage_m, audience_dir):
        """
        performers: { '1':{'name':'Alice','label':..., 'row':None,'col':None}, ... }
        stage_n, stage_m: 舞台格子 (n 行, m 列)
        audience_dir: 'top' or 'bottom'
        """
        self.root = root
        self.performers = performers
        self.stage_n = stage_n
        self.stage_m = stage_m
        self.audience_dir = audience_dir

        # 每格大小
        self.cell_size = 60
        # Canvas 大小
        self.canvas_width = self.stage_m * self.cell_size
        self.canvas_height = self.stage_n * self.cell_size

        self.root.title("舞台隊形排位")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        #------------------ 整體 grid 排版 ------------------#
        self.stage_frame = tk.Frame(self.root, bg="#ddd")
        self.stage_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # stage_frame -> 2 行 1 列
        #  row=0 -> 觀眾標籤 (若 audience_dir==top 就顯示在上)
        #  row=1 -> Canvas (真正的舞台格子)
        #  如果 audience_dir == bottom 就把標籤放在下方
        self.stage_frame.rowconfigure(0, weight=0)
        self.stage_frame.rowconfigure(1, weight=1)  # Canvas 可擴張
        self.stage_frame.columnconfigure(0, weight=1)

        #------------------ 舞台 Canvas ------------------#
        # 放在左上 (x=10, y=10)
        self.stage_canvas = tk.Canvas(self.stage_frame,
            width=self.canvas_width, height=self.canvas_height, bg="white")
        # 如果觀眾在上方, Canvas 就放在 row=1; 在下方, Canvas 也放在 row=1 (中間)
        self.stage_canvas.grid(row=1, column=0, sticky="nsew")

        # 畫網格線
        for r in range(self.stage_n + 1):
            y = r * self.cell_size
            self.stage_canvas.create_line(0, y, self.canvas_width, y, fill="gray")
        for c in range(self.stage_m + 1):
            x = c * self.cell_size
            self.stage_canvas.create_line(x, 0, x, self.canvas_height, fill="gray")

        # 中心線
        cx = self.canvas_width / 2
        self.stage_canvas.create_line(cx, 0, cx, self.canvas_height,
                                      fill="red", dash=(5,3), width=2)

        #------------------ 建立「觀眾標籤」------------------#
        self.audience_label_top = None
        self.audience_label_bottom = None
        if self.audience_dir == "top":
            self.audience_label_top = tk.Label(self.stage_frame, text="（觀眾在這邊）",
                                               font=("微軟正黑體", 12, "bold"), bg="#ddd")
            self.audience_label_top.grid(row=0, column=0, sticky="n", pady=5)
        elif self.audience_dir == "bottom":
            self.audience_label_bottom = tk.Label(self.stage_frame, text="（觀眾在這邊）",
                                                  font=("微軟正黑體", 12, "bold"), bg="#ddd")
            # 放在最下方（row=2），我們先加一個 row
            self.stage_frame.rowconfigure(2, weight=0)
            self.audience_label_bottom.grid(row=2, column=0, sticky="s", pady=5)
        
        #------------------ 右側：表演者列表 ------------------#
        self.list_title = tk.Label(self.root, text="表演者列表",
                                   font=("微軟正黑體", 12, "underline"), bg=self.root["bg"])
        # 放在舞台右邊 + 一些空間
        self.list_title.place(x=10 + self.canvas_width + 40, y=10)

        # 依序放每位表演者
        self.start_list_x = 10 + self.canvas_width + 40
        self.start_list_y = 40
        self.label_spacing = 40  # 垂直距
        sorted_pids = sorted(performers.keys(), key=lambda x: int(x))
        for i, pid in enumerate(sorted_pids):
            info = performers[pid]
            lbl = tk.Label(self.root,
                text=f"{pid}. {info['name']}",
                bg="#D7EBFA", fg="#000",
                bd=1, relief="solid",
                font=("微軟正黑體", 10)
            )
            # 直接 place
            lbl.place(x=self.start_list_x, y=self.start_list_y + i*self.label_spacing)
            # 綁定拖曳事件
            lbl.bind("<Button-1>", self.on_mouse_down)
            lbl.bind("<B1-Motion>", self.on_mouse_move)
            lbl.bind("<ButtonRelease-1>", self.on_mouse_up)
            info["label"] = lbl
            info["row"] = None
            info["col"] = None

        #------------------ 下方按鈕 ------------------#
        self.btn_save = tk.Button(self.root, text="儲存圖像", font=("微軟正黑體", 10),
                                  command=self.on_save_image)
        self.btn_save.place(x=200, y=700)

        self.btn_reset = tk.Button(self.root, text="重置", font=("微軟正黑體", 10),
                                   command=self.on_reset)
        self.btn_reset.place(x=320, y=700)

        # 拖曳狀態
        self.dragging_label = None
        self.drag_start_x = 0
        self.drag_start_y = 0

    #---------------- 拖曳事件 ----------------#
    def on_mouse_down(self, event):
        self.dragging_label = event.widget
        self.dragging_label.lift()  # 在最上層顯示
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_mouse_move(self, event):
        if self.dragging_label:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            cur_x = self.dragging_label.winfo_x()
            cur_y = self.dragging_label.winfo_y()
            new_x = max(cur_x + dx, 0)
            new_y = max(cur_y + dy, 0)
            self.dragging_label.place(x=new_x, y=new_y)

    def on_mouse_up(self, event):
        if not self.dragging_label:
            return

        # 找出是哪個表演者
        the_pid = None
        for pid, info in self.performers.items():
            if info["label"] == self.dragging_label:
                the_pid = pid
                break
        if not the_pid:
            self.dragging_label = None
            return

        # 檢查是否落在舞台
        #   先取得舞台 Canvas 在螢幕上的絕對座標
        canvas_x1 = self.stage_canvas.winfo_rootx()
        canvas_y1 = self.stage_canvas.winfo_rooty()
        canvas_x2 = canvas_x1 + self.canvas_width
        canvas_y2 = canvas_y1 + self.canvas_height

        # 取得 label 左上角在螢幕的絕對座標
        label_gx = self.dragging_label.winfo_rootx()
        label_gy = self.dragging_label.winfo_rooty()

        if (canvas_x1 <= label_gx < canvas_x2) and (canvas_y1 <= label_gy < canvas_y2):
            # 在舞台
            offset_x = label_gx - canvas_x1
            offset_y = label_gy - canvas_y1
            col_index = int(offset_x // self.cell_size)
            row_index = int(offset_y // self.cell_size)

            self.performers[the_pid]["row"] = row_index
            self.performers[the_pid]["col"] = col_index
            print(f"{the_pid} → row={row_index}, col={col_index}")
        else:
            # 不在舞台
            self.performers[the_pid]["row"] = None
            self.performers[the_pid]["col"] = None
            print(f"{the_pid} 不在舞台上")

        self.dragging_label = None

    #---------------- 功能 ----------------#
    def on_reset(self):
        # 全部回到右側
        i = 0
        for pid in sorted(self.performers.keys(), key=lambda x:int(x)):
            self.performers[pid]["row"] = None
            self.performers[pid]["col"] = None
            lbl = self.performers[pid]["label"]
            lbl.place_forget()
            lbl.place(x=self.start_list_x, y=self.start_list_y + i*self.label_spacing)
            i += 1
        print("已重置表演者位置")

    def on_save_image(self):
        # 讓使用者指定要存檔的路徑
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files","*.png"),("All Files","*.*")]
        )
        if not filename:
            return

        # 截圖：整個視窗
        x1 = self.root.winfo_rootx()
        y1 = self.root.winfo_rooty()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x2 = x1 + w
        y2 = y1 + h

        img = ImageGrab.grab(bbox=(x1,y1,x2,y2))
        img.save(filename)
        print(f"已儲存圖像：{filename}")

def main():
    num_performers = int(input("輸入表演者人數: "))
    names_str = input("輸入各表演者名稱 (逗號分隔) (可忽略): ")
    stage_n = int(input("輸入舞台列數 n: "))
    stage_m = int(input("輸入舞台欄數 m: "))
    audience_dir = input("觀眾方向 (top 或 bottom): ")

    name_list = [nm.strip() for nm in names_str.split(",") if nm.strip()]
    if len(name_list) < num_performers:
        for i in range(len(name_list), num_performers):
            name_list.append(f"Person{i+1}")
    else:
        name_list = name_list[:num_performers]

    performers = {}
    for i,nm in enumerate(name_list):
        pid = str(i+1)
        performers[pid] = {"name": nm, "label": None, "row": None, "col": None}

    root = tk.Tk()
    app = FormationApp(root, performers, stage_n, stage_m, audience_dir)
    root.mainloop()

if __name__ == "__main__":
    main()
