from tkinter import messagebox, filedialog, Listbox, Scrollbar, Button, Frame
import os, sys, winsound, time, zipfile, io, urllib, re
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk

VERSION = 0.1

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
        print(f"Saved: {new_file_path}")


def getConvertedFrames(selectedFile: str):
    global listbox
    actualFilename = os.path.basename(str(selectedFile)).replace(".3dst", ".png")
    configurationFilename = str(actualFilename).replace('.png', '.config')
    newAnimationPath = f".\\animations\\{configurationFilename.replace('.config', '')}"
    texture = py3dst.Texture3dst().open(selectedFile)
    sizeX, sizeY = int(texture.size[0]), int(texture.size[1])
    if int(texture.size[1]) < 96:
        messagebox.showerror('Animation Suite - Notice', "The provided Texture File is NOT a *.3dst Animation Texture.")
        return
    image = texture.copy(0, 0, texture.size[0], texture.size[1])
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
    print(fileList)
    sortedAnimationList = []
    for entry in fileList:
        if os.path.isdir(f".\\animations\\{entry}"):
            sortedAnimationList.append(entry)
    return sortedAnimationList


current_animation_label = None
current_animation_id = None


def openAnimation(selectedAnimation: str):
    global current_animation_label, current_animation_id

    # Stop the current animation if it exists
    if current_animation_label is not None:
        current_animation_label.destroy()  # Remove the current label
        current_animation_label = None  # Reset the label reference

    if current_animation_id is not None:
        root.after_cancel(current_animation_id)  # Cancel the scheduled animation update
        current_animation_id = None  # Reset the animation ID

    # Get the new animation configuration
    filename, animationFolder, x, y, textFormat, frameCount, frameFolder = getSelectedAnimationConfig(selectedAnimation)

    # Start playing the new animation
    playAnimation(frameFolder)


def playAnimation(frameFolder: str):
    global current_animation_label, current_animation_id

    # Stop any previous animation properly
    if current_animation_label is not None or current_animation_id is not None:
        print("Stopping previous animation...")
        return  # Exit if an animation is already playing

    # Get a list of keyframe files
    keyframe_files = sorted(os.listdir(frameFolder))

    # Pre-load images into memory
    frames = []
    for frame_file in keyframe_files:
        frame_path = os.path.join(frameFolder, frame_file)
        img = Image.open(frame_path)
        img = img.resize((img.size[0] * 5, img.size[1] * 5), Image.Resampling.NEAREST)  # Resize to fit the label
        frames.append(ImageTk.PhotoImage(img))

    # Create a label to display the keyframes
    current_animation_label = tk.Label(root)
    current_animation_label.pack()

    def show_frame(frame_index):
        global current_animation_id

        # Update the label with the new image
        current_animation_label.config(image=frames[frame_index])
        current_animation_label.image = frames[frame_index]  # Keep a reference to avoid garbage collection

        # Schedule the next frame
        next_frame_index = (frame_index + 1) % len(frames)  # Loop back to the first frame
        current_animation_id = root.after(200, show_frame, next_frame_index)  # Adjust the delay as needed

    # Start showing the first frame
    show_frame(0)


def updateAnimationList(listbox):
    # Clear the current items in the listbox
    listbox.delete(0, tk.END)

    # Get the updated animation list
    animationList = getStoredAnimationList()

    # Insert the updated items into the listbox
    for animation in animationList:
        listbox.insert(tk.END, animation)


def mainApp():
    global listbox, label, root
    root = tk.Tk()
    root.geometry("750x500")
    root.title("MC3DS Animation Suite")
    root.resizable(False, False)
    root.configure(bg='darkgray')  # Set background color to dark gray

    fileMenuBar = tk.Menu(root)
    file_menu = tk.Menu(fileMenuBar, tearoff=0)
    file_menu.add_command(label="Open", command=openFile)
    file_menu.add_command(label="Save", command=openFile)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    fileMenuBar.add_cascade(label="File", menu=file_menu)
    root.config(menu=fileMenuBar)

    if not os.path.exists(".\\animations"):
        messagebox.showinfo(
            "Animation Suite - Welcome",
            "Looks like this is your First time in MC3DS Animation Suite.\nHere you can modify Animations and KeyFrame data on Textures for MC3DS.\n\nDeveloped by: Cracko298."
        )
        openFile()

    # Create a frame for the listbox and scrollbar
    frame = Frame(root, bg='darkgray')
    frame.pack(pady=10)

    # Create a scrollbar
    scrollbar = Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a listbox
    listbox = Listbox(
        frame, width=50, height=15, yscrollcommand=scrollbar.set,
        bg='lightgray', selectbackground='lightblue', selectforeground='white'
    )
    listbox.pack(side=tk.LEFT)

    # Configure the scrollbar
    scrollbar.config(command=listbox.yview)

    # Update the animation list initially
    updateAnimationList(listbox)

    # Create the "Open Animation" button
    open_button = Button(root, text="Open Animation", command=lambda: openAnimation(listbox.get(tk.ACTIVE)), bg='lightblue')
    open_button.pack(pady=20)

    root.mainloop()


if __name__ == "__main__":
    mainApp()
