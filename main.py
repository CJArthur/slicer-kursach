import customtkinter as ctk
import os
from tkinter import filedialog, messagebox  # messagebox берем из tkinter
from video_slicer import extract_audio_from_video, transcribe_with_whisperx, burn_subtitles_into_video

def log(message):
    log_box.insert("end", message + "\n")
    log_box.see("end")  # автоскролл
    root.update_idletasks()

# Настройки вида
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Список пресетов
PRESETS = ["classic", "neon_yellow", "electric_blue", "story_telling", "deep_purple", "water_melon"]

def choose_input():
    path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi")])
    if path:
        entry_input.delete(0, "end")
        entry_input.insert(0, path)

def choose_output():
    path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Video", "*.mp4")])
    if path:
        entry_output.delete(0, "end")
        entry_output.insert(0, path)

def choose_output_folder():
    # Выбираем только папку
    folder = filedialog.askdirectory(title="Выберите папку для сохранения")
    if folder:
        entry_output.delete(0, "end")
        entry_output.insert(0, folder)

def start_processing():
    input_video = entry_input.get()
    output_folder = entry_output.get()
    preset_name = combo_presets.get()  # Получаем выбранный пресет
    
    if not input_video or not output_folder:
        messagebox.showerror("Ошибка", "Выберите вход и выход!")
        return
    
    base_name = os.path.splitext(os.path.basename(input_video))[0]
    output_video = os.path.join(output_folder, f"{base_name}_subtitled.mp4")
    audio_path = os.path.join("temp_files", f"{base_name}_extr_audio.wav")


    try:
        log("Загружается видео")
        audio_file = extract_audio_from_video(input_video, audio_path)

        log("Переходим к транскрибации")
        segments = transcribe_with_whisperx(audio_file,
                                            language="ru",
                                            model_name="large-v3",
                                            device="cpu",
                                            compute_type="int8",
                                            batch_size=4)
        
        log("Накладываем субы")
        burn_subtitles_into_video(input_video, segments, output_video, preset_name)
        log("Готово!")
        messagebox.showinfo("Готово", "Видео обработано!")
    except Exception as e:
        log(f"Произошла ошибка {e}")
        messagebox.showerror("Ошибка", str(e))

# Окно
root = ctk.CTk()
root.title("Video Subtitler")
root.geometry("720x450") # Чуть выше для нового элемента

# Вход
ctk.CTkLabel(root, text="Входное видео:").grid(row=0, column=0, padx=10, pady=10)
entry_input = ctk.CTkEntry(root, width=400)
entry_input.grid(row=0, column=1, padx=5)
ctk.CTkButton(root, text="Обзор", command=choose_input).grid(row=0, column=2, padx=10)

# Выход
ctk.CTkLabel(root, text="Выходное видео:").grid(row=1, column=0, padx=10, pady=10)
entry_output = ctk.CTkEntry(root, width=400)
entry_output.grid(row=1, column=1, padx=5)
ctk.CTkButton(root, text="Сохранить как...", command=choose_output_folder).grid(row=1, column=2, padx=10)

# Выбор пресета (НОВОЕ)
ctk.CTkLabel(root, text="Стиль субтитров:").grid(row=2, column=0, padx=10, pady=10)
combo_presets = ctk.CTkComboBox(root, values=PRESETS, width=400)
combo_presets.set("electric_blue") # Значение по умолчанию
combo_presets.grid(row=2, column=1, padx=5)

# Старт (сдвинули на ряд ниже)
ctk.CTkButton(root, text="ЗАПУСТИТЬ", command=start_processing, height=40, fg_color="green").grid(row=3, column=1, pady=30)

log_box = ctk.CTkTextbox(root, width=680, height=150)
log_box.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()