import os
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

def get_desktop_path():
    return "C:\\Users\\Huawei\\OneDrive\\Masaüstü"

def lzw_compress(text):
    dictionary = {chr(i): i for i in range(256)}
    w = ""
    compressed = []
    dict_size = 256
    
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            compressed.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    
    if w:
        compressed.append(dictionary[w])
    
    return compressed

def lzw_decompress(compressed):
    dictionary = {i: chr(i) for i in range(256)}
    w = chr(compressed.pop(0))
    decompressed = [w]
    dict_size = 256
    
    for k in compressed:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0]
        else:
            raise ValueError("Invalid compressed data.")
        
        decompressed.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        w = entry
    
    return "".join(decompressed)

def detect_file_type(file_path):
    try:
        with open(file_path, 'r') as f:
            f.read()
        return 'text'
    except:
        try:
            img = Image.open(file_path)
            return 'grayscale' if img.mode == 'L' else 'color'
        except:
            return 'unknown'

def process_file(file_path, level, action):
    file_type = detect_file_type(file_path)
    original_size = os.path.getsize(file_path) / 1024
    desktop_path = get_desktop_path()
    
    if action == 'compress':
        output_path = os.path.join(desktop_path, os.path.basename(file_path) + f"_level{level}_compressed.bmp")
        
        try:
            if level == 1 and file_type == 'text':
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                compressed_data = lzw_compress(text)
                
                with open(output_path, 'wb') as file:
                    np.save(file, np.array(compressed_data, dtype=np.uint32))
            
            elif level in [2, 3, 4, 5] and file_type in ['grayscale', 'color']:
                img = Image.open(file_path)
                img = img.convert('L') if level in [2, 3] else img.convert('RGB')
                img_array = np.array(img, dtype=np.int16)
                
                if level in [3, 5]:  
                    img_array[1:] -= img_array[:-1]  
                
                img_array = np.clip(img_array, 0, 255).astype(np.uint8)  

                shape_info = np.array(img_array.shape, dtype=np.uint16)
                compressed_data = lzw_compress("".join(map(chr, img_array.flatten())))
                
                with open(output_path, 'wb') as file:
                    np.save(file, np.array(compressed_data, dtype=np.uint32))
                    np.save(file, shape_info)
            
            compressed_size = os.path.getsize(output_path) / 1024
            compression_ratio = (compressed_size / original_size) * 100
            compression_info.set(f"Original: {original_size:.2f} KB | Compressed: {compressed_size:.2f} KB | Ratio: {compression_ratio:.2f}%")
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                messagebox.showinfo("Success", f"Compressed\n{file_path}\nSaved as\n{output_path}")
            else:
                raise Exception("File was not saved correctly.")
        except Exception as e:
            messagebox.showerror("Error", f"Compression failed: {e}")
    
    elif action == 'decompress':
        decompressed_path = os.path.join(desktop_path, os.path.basename(file_path).replace("_compressed.bmp", "_decompressed.bmp"))
        try:
            with open(file_path, 'rb') as file:
                compressed_data = np.load(file).tolist()
                shape_info = tuple(np.load(file))
            
            decompressed_text = lzw_decompress(compressed_data)
            decompressed_array = np.array([ord(c) for c in decompressed_text], dtype=np.uint8).reshape(shape_info)
            
            if level in [3, 5]:  
                decompressed_array[1:] += decompressed_array[:-1]  
            
            new_img = Image.fromarray(decompressed_array)
            new_img.save(decompressed_path)
            display_image(decompressed_path)
            
            decompressed_size = os.path.getsize(decompressed_path) / 1024
            compression_info.set(f"Decompressed Size: {decompressed_size:.2f} KB")
            
            if os.path.exists(decompressed_path) and os.path.getsize(decompressed_path) > 0:
                messagebox.showinfo("Success", f"Decompressed\n{file_path}\nSaved as\n{decompressed_path}")
            else:
                raise Exception("File was not saved correctly.")
        except Exception as e:
            messagebox.showerror("Error", f"Decompression failed: {e}")

def display_image(image_path):
    img = Image.open(image_path)
    img.thumbnail((200, 200))
    img = ImageTk.PhotoImage(img)
    image_label.config(image=img)
    image_label.image = img

def browse_file():
    global file_path
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.config(text=f"Selected: {file_path}", fg="green")

def run_level(level, action):
    if not file_path:
        messagebox.showerror("Error", "Please select a file first.")
        return
    process_file(file_path, level, action)

def gui():
    global file_label, image_label, file_path, compression_info
    file_path = ""
    
    root = tk.Tk()
    root.title("LZW Compression & Decompression Tool")
    root.geometry("500x750")
    
    tk.Label(root, text="Upload a text or image file:").pack(pady=5)
    tk.Button(root, text="Browse", command=browse_file).pack(pady=5)
    
    file_label = tk.Label(root, text="No file selected", fg="red")
    file_label.pack(pady=5)
    
    tk.Label(root, text="Select Level to Apply:").pack(pady=5)
    
    for level in range(1, 6):
        tk.Button(root, text=f"Level {level} - Compress", width=25, command=lambda l=level: run_level(l, 'compress')).pack(pady=2)
        tk.Button(root, text=f"Level {level} - Decompress", width=25, command=lambda l=level: run_level(l, 'decompress')).pack(pady=2)
    
    compression_info = tk.StringVar()
    compression_label = tk.Label(root, textvariable=compression_info, font=("Arial", 10, "bold"), fg="purple")
    compression_label.pack(pady=10)
    
    image_label = tk.Label(root)
    image_label.pack()
    
    tk.Button(root, text="Exit", command=root.quit, bg="red", fg="white").pack(pady=10)
    
    root.mainloop()

gui()
