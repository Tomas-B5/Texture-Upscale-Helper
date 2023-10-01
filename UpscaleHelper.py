import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import shutil

MAX_THREADS = 6

def flatten_folder_structure(main_folder):
    for root, _, files in os.walk(main_folder):
        for file in files:
            if file.endswith('.png'):
                # Construct the new filename using the folder structure
                relative_path = os.path.relpath(root, main_folder)
                new_filename = relative_path.replace(os.sep, '__') + '__' + file
                # Move the file to the main folder
                shutil.move(os.path.join(root, file), os.path.join(main_folder, new_filename))

def restore_folder_structure(main_folder):
    for file in os.listdir(main_folder):
        if file.endswith('.png'):
            # Split the filename into its original folder structure
            parts = file.split('__')
            original_folder = os.path.join(main_folder, *parts[:-1])
            original_filename = parts[-1]
            # Recreate the original folder structure
            os.makedirs(original_folder, exist_ok=True)
            # Move the file back to its original location
            shutil.move(os.path.join(main_folder, file), os.path.join(original_folder, original_filename))

def get_dds_compression_type(dds_path):
    try:
        # Use imagemagick's identify command to get DDS info
        result = subprocess.run(
            ["magick", "identify", "-verbose", dds_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the output to find the compression type
        for line in result.stdout.splitlines():
            if "Compression:" in line:
                compression = line.split(":")[-1].strip().lower()
                if "dxt1" in compression:
                    return "dxt1"
                elif "dxt3" in compression:
                    return "dxt3"
                elif "dxt5" in compression:
                    return "dxt5"
                else:
                    # Return a default compression type if unknown
                    return "dxt5"
    except Exception as e:
        print(f"Error reading DDS compression type: {e}")
        return "dxt5"  # Default fallback

def compression_output(input_type):
    mapping = {
        "dxt1": "dxt1",
        "dxt3": "dxt5",
        "dxt5": "dxt5"
    }
    return mapping.get(input_type, "dxt5")

def convert_dds_to_png(dds_path):
    compression_type = get_dds_compression_type(dds_path)
    png_path = os.path.splitext(dds_path)[0] + f"_{compression_output(compression_type)}_compression.png"
    cmd = ["magick", "convert", dds_path, png_path]
    subprocess.run(cmd, check=True)

def convert_png_to_dds(png_path):
    compression_type = png_path.split("_")[-2]
    dds_path = os.path.splitext(png_path.replace(f"_{compression_type}_compression", ""))[0] + ".dds"
    cmd = ["magick", "convert", png_path, f"-define", f"dds:compression={compression_type}", dds_path]
    subprocess.run(cmd, check=True)

def process_folder(folder_path, conversion_func, file_extension, progress_var):
    all_files = [os.path.join(root, file) for root, _, files in os.walk(folder_path) for file in files if file.endswith(file_extension)]
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [executor.submit(conversion_func, file_path) for file_path in all_files]
        
        for future in tqdm(futures, desc="Processing", unit="file", bar_format='{l_bar}{bar:20}{r_bar}{bar:-10b}'):
            try:
                future.result()  # Wait for the future to complete and get its result (or exception).
                progress_var.set(progress_var.get() + 1)
                root.update()  # Update the GUI
            except Exception as e:
                print(f"Error during conversion: {e}")

    for file_path in all_files:
        os.remove(file_path)

def select_directory():
    return filedialog.askdirectory()

def on_convert_to_png_clicked(progress_var):
    folder = select_directory()
    if folder:
        progress_var.set(0)
        process_folder(folder, convert_dds_to_png, ".dds", progress_var)
        messagebox.showinfo("Info", "Conversion to PNG completed!")

def on_convert_to_dds_clicked(progress_var):
    folder = select_directory()
    if folder:
        progress_var.set(0)
        process_folder(folder, convert_png_to_dds, ".png", progress_var)
        messagebox.showinfo("Info", "Conversion to DDS completed!")
        
def on_flatten_clicked():
    folder = select_directory()
    if folder:
        flatten_folder_structure(folder)
        messagebox.showinfo("Info", "Flatten operation completed!")

def on_restore_clicked():
    folder = select_directory()
    if folder:
        restore_folder_structure(folder)
        messagebox.showinfo("Info", "Restore operation completed!")

root = tk.Tk()
root.title("DDS & PNG Converter")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(padx=10, pady=10)

btn_convert_to_png = tk.Button(frame, text="[1]Convert Folder to PNG", command=lambda: on_convert_to_png_clicked(progress_var), width=20, height=2)
btn_convert_to_png.grid(row=0, column=0, pady=10)

btn_flatten = tk.Button(frame, text="[2]Flatten Folder Structure", command=on_flatten_clicked, width=25, height=2)
btn_flatten.grid(row=1, column=0, pady=10)

btn_restore = tk.Button(frame, text="[3]Restore Folder Structure", command=on_restore_clicked, width=25, height=2)
btn_restore.grid(row=2, column=0, pady=10)

btn_convert_to_dds = tk.Button(frame, text="[4]Convert Folder to DDS", command=lambda: on_convert_to_dds_clicked(progress_var), width=20, height=2)
btn_convert_to_dds.grid(row=3, column=0, pady=10)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, orient="horizontal", length=200, mode="determinate")
progress_bar.grid(row=4, column=0, pady=20)

root.mainloop()
