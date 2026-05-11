from __future__ import annotations

import queue
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk


class AppWindow:
    def __init__(self, *, presets, on_start, title="Video Subtitler"):
        self._presets = presets
        self._on_start = on_start
        self._log_queue = queue.Queue()
        self._busy = False

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(title)
        self.root.geometry("760x600")

        self._build()

    def log(self, message: str) -> None:
        # можно вызывать из любого потока
        self._log_queue.put(message)

    def _drain_logs(self):
        try:
            while True:
                msg = self._log_queue.get_nowait()
                self.log_box.insert("end", msg + "\n")
        except queue.Empty:
            pass
        self.log_box.see("end")
        self.root.update_idletasks()
        self.root.after(100, self._drain_logs)

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi")])
        if path:
            self.entry_input.delete(0, "end")
            self.entry_input.insert(0, path)

    def _choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.entry_output.delete(0, "end")
            self.entry_output.insert(0, folder)

    def _toggle_split(self) -> None:
        if self.split_var.get():
            self.video_count.configure(state="normal")
        else:
            self.video_count.configure(state="disabled")

    def _read_state(self):
        split_enabled = bool(self.split_var.get())
        split_parts = None
        if split_enabled:
            raw = self.video_count.get().strip()
            if not raw:
                raise ValueError("Укажи количество частей для нарезки.")
            split_parts = int(raw)
            if split_parts < 2:
                raise ValueError("Количество частей должно быть минимум 2.")

        return {
            "input_video": self.entry_input.get().strip(),
            "output_folder": self.entry_output.get().strip(),
            "preset_name": self.combo_presets.get().strip(),
            "split_enabled": split_enabled,
            "split_parts": split_parts,
        }

    def _start_processing(self) -> None:
        try:
            if self._busy:
                return

            state = self._read_state()
            if not state["input_video"] or not state["output_folder"]:
                messagebox.showerror("Ошибка", "Выберите вход и выход!")
                return

            self._busy = True
            self.btn_start.configure(state="disabled")

            def worker():
                try:
                    self._on_start(state)
                finally:
                    self._busy = False
                    self.root.after(0, lambda: self.btn_start.configure(state="normal"))

            threading.Thread(target=worker, daemon=True).start()
        except Exception as e:
            self.log(f"Произошла ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))

    def _build(self) -> None:
        ctk.CTkLabel(self.root, text="Входное видео:").grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )

        self.entry_input = ctk.CTkEntry(self.root, width=400)
        self.entry_input.grid(row=0, column=1, padx=5)

        ctk.CTkButton(self.root, text="Обзор", command=self._choose_input).grid(
            row=0, column=2, padx=10
        )

        ctk.CTkLabel(self.root, text="Выходная папка:").grid(
            row=1, column=0, padx=10, pady=10, sticky="w"
        )

        self.entry_output = ctk.CTkEntry(self.root, width=400)
        self.entry_output.grid(row=1, column=1, padx=5)

        ctk.CTkButton(
            self.root, text="Сохранить как...", command=self._choose_output_folder
        ).grid(row=1, column=2, padx=10)

        ctk.CTkLabel(self.root, text="Стиль субтитров:").grid(
            row=2, column=0, padx=10, pady=10, sticky="w"
        )

        self.combo_presets = ctk.CTkComboBox(
            self.root,
            values=self._presets,
            width=400,
        )
        if self._presets:
            self.combo_presets.set(self._presets[0])
        self.combo_presets.grid(row=2, column=1, padx=5)

        self.split_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.root,
            text="Нарезать видео на части",
            variable=self.split_var,
            command=self._toggle_split,
        ).grid(row=3, column=1, padx=5, pady=10, sticky="w")

        ctk.CTkLabel(self.root, text="Количество частей:").grid(
            row=4, column=0, padx=10, pady=10, sticky="w"
        )

        self.video_count = ctk.CTkEntry(self.root, width=100)
        self.video_count.insert(0, "2")
        self.video_count.grid(row=4, column=1, padx=5, sticky="w")
        self.video_count.configure(state="disabled")

        self.btn_start = ctk.CTkButton(
            self.root,
            text="ЗАПУСТИТЬ",
            command=self._start_processing,
            height=40,
            fg_color="green",
        )
        self.btn_start.grid(row=6, column=1, pady=25)

        self.log_box = ctk.CTkTextbox(self.root, width=680, height=150)
        self.log_box.grid(
            row=7,
            column=0,
            columnspan=3,
            padx=10,
            pady=10,
        )

    def run(self) -> None:
        self.root.after(100, self._drain_logs)
        self.root.mainloop()