import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk


def create_app(presets, subs_positions, start_processing):
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Video Subtitler")
    root.geometry("730x640")

    def log(message):
        # Логи пишем в UI через after (так безопасно даже из потока)
        def _write():
            log_box.insert("end", message + "\n")
            log_box.see("end")
            root.update_idletasks()

        root.after(0, _write)

    def choose_input():
        # Выбор входного видео
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi")])
        if path:
            entry_input.delete(0, "end")
            entry_input.insert(0, path)

    def choose_output_folder():
        # Выбор папки, куда сохраняем результат
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            entry_output.delete(0, "end")
            entry_output.insert(0, folder)

    def toggle_split():
        # Если галочка выключена — блокируем и затемняем поле
        if split_var.get():
            video_count.configure(state="normal")
            video_count.configure(fg_color = "#000000")
        else:
            video_count.configure(state="disabled")
            video_count.configure(fg_color="#535353")

    def on_start_click():
        # Собираем значения из UI
        input_video = entry_input.get().strip()
        output_folder = entry_output.get().strip()
        preset_name = combo_presets.get().strip()
        subs_position = combo_subs_pos.get().strip()

        if not input_video or not output_folder:
            messagebox.showerror("Ошибка", "Выберите вход и выход!")
            return

        split_enabled = bool(split_var.get())
        split_parts = None
        if split_enabled:
            raw = video_count.get().strip()
            if not raw:
                messagebox.showerror("Ошибка", "Укажи количество частей.")
                return
            try:
                split_parts = int(raw)
            except ValueError:
                messagebox.showerror("Ошибка", "Количество частей должно быть числом.")
                return
            if split_parts < 2:
                messagebox.showerror("Ошибка", "Количество частей минимум 2.")
                return

        state = {
            "input_video": input_video,
            "output_folder": output_folder,
            "preset_name": preset_name,
            "subs_position": subs_position,
            "split_enabled": split_enabled,
            "split_parts": split_parts,
        }

        btn_start.configure(state="disabled")

        def worker():
            try:
                # Основная обработка в отдельном потоке, чтобы окно не зависало
                start_processing(state, log)
            except Exception as e:
                log(f"Ошибка: {e}")
                messagebox.showerror("Ошибка", str(e))
            finally:
                root.after(0, lambda: btn_start.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    # --- Настройки окна --- #

    # Поле входного видео
    ctk.CTkLabel(root, text="Входное видео:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    entry_input = ctk.CTkEntry(root, width=400)
    entry_input.grid(row=0, column=1, padx=5)
    ctk.CTkButton(root, text="Обзор", command=choose_input).grid(row=0, column=2, padx=10)

    # Поле выхода
    ctk.CTkLabel(root, text="Выходная папка:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    entry_output = ctk.CTkEntry(root, width=400)
    entry_output.grid(row=1, column=1, padx=5)
    ctk.CTkButton(root, text="Сохранить как...", command=choose_output_folder).grid(row=1, column=2, padx=10)

    # Поле выбора субтитров
    ctk.CTkLabel(root, text="Стиль субтитров:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    combo_presets = ctk.CTkComboBox(root, values=presets, width=400)
    if presets:
        combo_presets.set(presets[0])
    combo_presets.grid(row=2, column=1, padx=5)

    # Где на кадре рисовать субтитры
    ctk.CTkLabel(root, text="Положение субтитров:").grid(
        row=3, column=0, padx=10, pady=10, sticky="w"
    )
    combo_subs_pos = ctk.CTkComboBox(root, values=subs_positions, width=400)
    if subs_positions:
        combo_subs_pos.set("Снизу" if "Снизу" in subs_positions else subs_positions[0])
    combo_subs_pos.grid(row=3, column=1, padx=5, sticky="w")

    # Проверка на галочку, по умолчанию False
    split_var = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(root, text="Нарезать видео на части", variable=split_var, command=toggle_split).grid(
        row=4, column=1, padx=5, pady=10, sticky="w"
    )

    # Поле выбора количества частей. Работает при включенной галочке
    ctk.CTkLabel(root, text="Количество частей:").grid(row=5, column=0, padx=10, pady=10, sticky="w")
    video_count = ctk.CTkEntry(root, width=100)
    video_count.insert(0, "2")
    video_count.grid(row=5, column=1, padx=5, sticky="w")
    video_count.configure(state="disabled")
    video_count.configure(fg_color="#2a2a2a")

    # Поле кнопки запуска
    btn_start = ctk.CTkButton(root, text="ЗАПУСТИТЬ", command=on_start_click, height=40, fg_color="green")
    btn_start.grid(row=7, column=1, pady=25)

    # Поле настройки окна с логами
    log_box = ctk.CTkTextbox(root, width=680, height=150)
    log_box.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

    return root