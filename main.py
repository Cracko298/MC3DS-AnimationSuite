from tkinter import messagebox, filedialog, Listbox, Scrollbar, Button, Frame, HORIZONTAL, Scale, colorchooser
import os, sys, winsound, time, zipfile, io, urllib, re
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk

current_animation_label = None
current_animation_id = None
getCurrentFrame12 = None
VERSION = 0.3

try:
    import py3dst
except ImportError:
    try:
        import requests
    except ImportError:
        answer0 = messagebox.askyesno(
            "Animation Suite - Module Installation",
            "We need to install a Module named: 'requests'.\nThis allows the application to Update if the User wants.\nInstead of needing to constantly redownload new(er) versions."
        )
        if answer0:
            os.system('pip install requests')
            time.sleep(0.5)
            import requests
    answer1 = messagebox.askyesno(
        "Animation Suite - Module Installation",
        "We need to install a Module named: 'py3dst'.\nThis is required to view and convert animations/textures."
    )
    if answer1:
        os.system('pip install py3dst')
        time.sleep(0.5)
        import py3dst
    else:
        messagebox.showerror(
            "Animation Suite - Notice",
            "The Animation Suite cannot function without the 'py3dst' python Module.\nThe Application will now Close without Saving any work that could be opened."
        )
        sys.exit(1)

def cutAnimationTexture(image_path, chunk_height, output_dir):
    img = Image.open(image_path)
    img_width, img_height = img.size
    num_chunks = int(img_height / chunk_height)
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    for i in range(num_chunks):
        box = (0, i * chunk_height, img_width, (i + 1) * chunk_height)
        chunk = img.crop(box)
        new_file_name = f"{base_name}_keyFrame{i}.png"
        new_file_path = os.path.join(output_dir, new_file_name)
        chunk.save(new_file_path)

def getConvertedFrames(selectedFile: str):
    global listbox
    actualFilename = os.path.basename(str(selectedFile)).replace(".3dst", ".png")
    configurationFilename = str(actualFilename).replace('.png', '.config')
    newAnimationPath = f".\\animations\\{configurationFilename.replace('.config', '')}"
    texture = py3dst.Texture3dst().open(selectedFile)
    sizeX, sizeY = int(texture.size[0]), int(texture.size[1])
    if sizeY < 92 or sizeY == sizeX or sizeX > 64:
        messagebox.showerror('Animation Suite - Notice', "The provided Texture File is NOT a *.3dst Animation Texture.")
        return
    image = texture.copy(0, 0, sizeX, sizeY)
    os.makedirs(f"{newAnimationPath}", exist_ok=True)
    with open(f"{newAnimationPath}\\{configurationFilename}", 'w') as conFile:
        conFile.write(
            f"File={actualFilename}\nFolder={newAnimationPath}\nSizeX={sizeX}\nSizeY={sizeY}\nFormat=rgba8\nKeyFrames={int(sizeY/sizeX)}\nKeyFrameFolder={newAnimationPath}\\KeyFrames"
        )
        image.save(f"{newAnimationPath}\\{actualFilename}")
    os.makedirs(f"{newAnimationPath}\\KeyFrames", exist_ok=True)
    cutAnimationTexture(f"{newAnimationPath}\\{actualFilename}", sizeX, f"{newAnimationPath}\\KeyFrames")
    getStoredAnimationList()
    updateAnimationList(listbox)

def openFile():
    filePath = filedialog.askopenfilename(filetypes=[("3DST Animation", "*.3dst")], title="Select 3DST Animation Texture")
    if not filePath: return
    getConvertedFrames(selectedFile=filePath)

def getSelectedAnimationConfig(selectedAnimation: str):
    listOfPureAwesomeness = []
    configPath = f".\\animations\\{selectedAnimation}\\{selectedAnimation}.config"
    with open(configPath, 'r') as f:
        linesOfData = f.readlines()
    for line in linesOfData:
        if "=" in line:
            splitLine = line.split('=')
            listOfPureAwesomeness.append(splitLine[1])
    return listOfPureAwesomeness

def getStoredAnimationList():
    global sortedAnimationList
    fileList = os.listdir(".\\animations")
    sortedAnimationList = []
    for entry in fileList:
        if os.path.isdir(f".\\animations\\{entry}"):
            sortedAnimationList.append(entry)
    return sortedAnimationList

def openAnimation(selectedAnimation:str, version:int):
    global current_animation_label, current_animation_id
    if current_animation_label is not None:
        current_animation_label.destroy()
        current_animation_label = None

    if current_animation_id is not None:
        root.after_cancel(current_animation_id)
        current_animation_id = None 

    filename, animationFolder, x, y, textFormat, frameCount, frameFolder = getSelectedAnimationConfig(selectedAnimation)
    if version == 1:
        playAnimationWithProgressBar(frameFolder, int(frameCount))
    if version == 2:
        saveAnimation(animationFolder, frameFolder, filename, int(x), int(y), int(frameCount))

def playAnimationWithProgressBar(frameFolder:str, keyFrameCount:int):
    global current_animation_label, current_animation_id, progress_bar, is_playing, controls_frame, modify_frame
    if current_animation_label is not None or current_animation_id is not None:
        root.after_cancel(current_animation_id)
        current_animation_label.destroy()
        current_animation_label = None
        current_animation_id = None

    if 'controls_frame' in globals() and controls_frame.winfo_exists():
        controls_frame.destroy()

    controls_frame = Frame(root, background='black')
    controls_frame.pack(pady=10)
    keyframe_files = sorted(os.listdir(frameFolder), key=extract_keyframe_number)
    frames = []

    for frame_file in keyframe_files:
        frame_path = os.path.join(frameFolder, frame_file)
        img = Image.open(frame_path).convert("RGBA")
        if img.size != (128, 128):
            print(f"Frame {frame_file} resized from {img.size} to 128x128")
        img = img.resize((128, 128), Image.Resampling.NEAREST)
        frames.append(ImageTk.PhotoImage(img))

    frame_count = len(frames)
    is_playing = True
    current_animation_label = tk.Label(root, background='black')
    current_animation_label.pack()
    progress_bar = Scale(
        controls_frame, from_=0, to=frame_count - 1, orient=HORIZONTAL,
        length=750, sliderlength=int(keyFrameCount), tickinterval=1, background="black", foreground="cyan", font=("Helvetica")
    )
    progress_bar.pack(pady=10)

    def show_frame(frame_index):
        global current_animation_id, is_playing
        if not is_playing:
            return

        current_animation_label.config(image=frames[frame_index])
        current_animation_label.image = frames[frame_index]
        progress_bar.set(frame_index)
        next_frame_index = (frame_index + 1) % frame_count
        current_animation_id = root.after(200, show_frame, next_frame_index)

    def toggle_play_pause():
        global is_playing, current_animation_id
        is_playing = not is_playing
        if is_playing:
            play_button.config(text="Pause")
            show_frame(progress_bar.get())
        else:
            play_button.config(text="Play")
            if current_animation_id:
                root.after_cancel(current_animation_id)

    def jump_to_frame(event):
        global is_playing
        if not is_playing:
            frame_index = progress_bar.get()
            current_animation_label.config(image=frames[frame_index])
            current_animation_label.image = frames[frame_index]

    def modify_frame():
        global save_frame, current_color, is_erasing, text0, draw_window
        frame_index = progress_bar.get()  # Get the current frame index from the progress bar
        frame_path = os.path.join(frameFolder, keyframe_files[frame_index])
        original_frame = Image.open(frame_path)
        original_width, original_height = original_frame.size
        scaled_frame = original_frame.resize((256, 256), Image.Resampling.NEAREST)

        draw_window = tk.Toplevel(root, background="black", bd=0)
        draw_window.title(f"Modify Keyframe - {frame_index}")
        draw_window.geometry(f"{700}x{650}")
        draw_window.resizable(False, False)
        text0 = tk.Label(draw_window, text=f"KeyFrame: {frame_index}\nMode: Drawing", font=("Helvetica", 16, "bold"), background="black", foreground="cyan")
        text0.pack()
        canvas = tk.Canvas(draw_window, width=256, height=256, bg="black")
        canvas.pack(expand=True, fill=None)

        tk_image = ImageTk.PhotoImage(scaled_frame)
        canvas.image = tk_image
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

        grid_color = "gray"
        grid_size = int(256/original_height)
        for i in range(0, 256, grid_size):
            canvas.create_line(i, 0, i, 256, fill=grid_color)
            canvas.create_line(0, i, 256, i, fill=grid_color)

        draw = ImageDraw.Draw(scaled_frame)
        pen_size = grid_size
        last_x, last_y = None, None
        current_color = "red"
        is_erasing = False

        def start_draw(event):
            nonlocal last_x, last_y
            last_x, last_y = event.x, event.y

        def draw_line(event):
            nonlocal last_x, last_y
            if last_x is not None and last_y is not None:
                x, y = event.x, event.y
                if is_erasing:
                    draw.line([(last_x, last_y), (x, y)], fill=(0, 0, 0, 0), width=pen_size)
                else:
                    draw.line([(last_x, last_y), (x, y)], fill=current_color, width=pen_size)
                canvas.create_line(last_x, last_y, x, y, fill=current_color if not is_erasing else "white", width=pen_size)
                last_x, last_y = x, y

        def choose_color():
            global current_color
            color_code = colorchooser.askcolor(title="Choose color")
            if color_code[1]:
                current_color = color_code[1]

        def toggle_erase():
            global is_erasing, text0
            is_erasing = not is_erasing
            erase_button.config(text="Draw" if is_erasing else "Erase")
            if is_erasing:
                text0.config(text=f"KeyFrame: {frame_index}\nMode: Erasing")
            else:
                text0.config(text=f"KeyFrame: {frame_index}\nMode: Drawing")

        def save_frame():
            modified_frame = scaled_frame.resize((original_width, original_height), Image.Resampling.NEAREST)
            modified_frame.save(frame_path)
            messagebox.showinfo("Modify Keyframe", f"Modified keyframe saved: {frame_path}")
            openAnimation(listbox.get(tk.ACTIVE), 1)  # This will now open the correct frame
            draw_window.destroy()
            
        def replace_with_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")], title="Select an Image")
            if not file_path:
                return
        
            try:
                new_image = Image.open(file_path)
                if new_image.size != (original_width, original_height):
                    messagebox.showerror("Error", "Selected image dimensions do not match the original keyframe dimensions.")
                    return

                new_image.save(frame_path)
                messagebox.showinfo("Success", f"Keyframe replaced successfully with {os.path.basename(file_path)}!")
                original_frame.paste(new_image)
                canvas.image = ImageTk.PhotoImage(original_frame.resize((256, 256), Image.Resampling.NEAREST))
                canvas.create_image(0, 0, anchor=tk.NW, image=canvas.image)
                draw_window.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while replacing the keyframe: {e}")

        replace_button = Button(draw_window, text="Replace with Image", command=replace_with_image, background="black", foreground="cyan", bd=0, font=("Helvetica", 14, "bold"))
        replace_button.pack(pady=5)
        color_button = Button(draw_window, text="Choose Color", command=choose_color, background="black", foreground="cyan", bd=0, font=("Helvetica", 14, "bold"))
        color_button.pack(pady=5)

        canvas.bind("<Button-1>", start_draw)
        canvas.bind("<B1-Motion>", draw_line)

        erase_button = Button(draw_window, text="Erase", command=toggle_erase, background="black", foreground="cyan", bd=0, font=("Helvetica", 14, "bold"))
        erase_button.pack(pady=5)

        save_button = Button(draw_window, text="Save", command=save_frame, background="black", foreground="cyan", bd= 0, font=("Helvetica", 14, "bold"))
        save_button.pack(pady=5)

    play_button = Button(controls_frame, text="Play", command=toggle_play_pause, background="black", foreground="cyan", width=8, bd=0, highlightbackground="cyan", highlightcolor="cyan", font=("Helvetica", 12, "bold"))
    play_button.pack(side=tk.LEFT, padx=10)
    modify_button = Button(controls_frame, text="Modify Keyframe", command=modify_frame, background="black", foreground="cyan", width=16, bd=0, highlightbackground="cyan", highlightcolor="cyan", font=("Helvetica", 12, "bold"))
    modify_button.pack(side=tk.LEFT, padx=10)
    progress_bar.bind("<ButtonRelease-1>", jump_to_frame)
    is_playing = True
    toggle_play_pause()

def updateAnimationList(listbox):
    listbox.delete(0, tk.END)
    animationList = getStoredAnimationList()
    for animation in animationList:
        listbox.insert(tk.END, animation)

def extract_keyframe_number(filename):
    match = re.search(r'keyFrame(\d+)', filename)
    if match:
        return int(match.group(1))
    return float('inf')

def saveAnimation(animationFolder:str, keyframeFolder:str, filename:str, width:int, height:int, num_images:int):
    filename = filename.replace('\n', '')
    animationFolder = animationFolder.replace('\n', '')
    outputFilename = filename.replace('.png', '.3dst')
    modifiedFrameList = []
    tempKeyframeName = filename.replace('.png', "")
    keyframeName = f"{tempKeyframeName}_keyFrame"
    for entry in sorted(os.listdir(keyframeFolder)):
        if os.path.isfile(f"{keyframeFolder}\\{entry}"):
            modifiedFrameList.append(f"{keyframeFolder}\\{entry}")
    
    sortedList = sorted(modifiedFrameList, key=extract_keyframe_number)
    result_image = Image.new('RGBA', (int(width), int(height)))

    for index, image_path in enumerate(sortedList):
        img = Image.open(image_path)
        result_image.paste(img, (0, index * int(width)))
    
    result_image.save(f"{animationFolder}\\{filename.replace('.png', '_modified.png')}")
    outImage = Image.open(f"{animationFolder}\\{filename.replace('.png', '_modified.png')}")
    texture = py3dst.Texture3dst().fromImage(outImage)
    texture.export(f".\\{outputFilename}")
    messagebox.showinfo("Animation Suite - Notice", f"Successfully saved your Animation to:\n{os.path.dirname(__file__)}\\{outputFilename}")

def mainApp():
    global listbox, label, root, open_button, modify_frame, save_frame
    root = tk.Tk()
    root.geometry("950x750")
    root.title("MC3DS Animation Suite")
    root.resizable(False, False)
    root.configure(bg='black')
    fileMenuBar = tk.Menu(root)
    file_menu = tk.Menu(fileMenuBar, tearoff=0)
    file_menu.add_command(label="Open", command=openFile)
    file_menu.add_command(label="Save", command=lambda: openAnimation(listbox.get(tk.ACTIVE), 2))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    fileMenuBar.add_cascade(label="File", menu=file_menu)
    root.config(menu=fileMenuBar)
    frame = Frame(root, bg='cyan')
    frame.pack(pady=10)
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = Listbox(
        frame, width=50, height=15, yscrollcommand=scrollbar.set,
        bg='black', selectbackground='black', selectforeground='cyan', foreground="lightgray", justify="center", font=("Helvetica", 10, "bold"), bd=0, highlightbackground="cyan"
    )
    if not os.path.exists(".\\animations"):
        messagebox.showinfo(
            "Animation Suite - Welcome",
            "Looks like this is your First time in MC3DS Animation Suite.\nHere you can modify Animations and KeyFrame data on Textures for MC3DS.\n\nDeveloped by: Cracko298."
        )
        openFile()
    listbox.pack(side=tk.TOP, pady=2, padx=2)
    scrollbar.pack_forget()
    updateAnimationList(listbox)
    open_button = Button(root, text="Open Animation", command=lambda: openAnimation(listbox.get(tk.ACTIVE), 1), bg='black', fg="cyan", bd="0", font=("Helvetica", 14, "bold"))
    open_button.pack(pady=20)
    root.mainloop()


if __name__ == "__main__":
    mainApp()
