" A GUI to run the single file uploader "

# imports
import pathlib
import tkinter as tk
from tkinter import filedialog
from ..uploaders.file_uploader import IMQCAMFileUploader


def run_uploader(arg_entries, filepath_entry, relative_to_entry):
    "Actually run the uploader with argument specified by the current entry boxes"
    args = [filepath_entry.get(), "--relative_to", relative_to_entry.get()]
    for argname, argentry in arg_entries.items():
        argval = argentry.get()
        if argval is not None and argval not in ("", "$IMQCAM_API_KEY"):
            args.append(f"--{argname}")
            args.append(str(argval))
    IMQCAMFileUploader.run_from_command_line(args)


def set_filepath(filepath_entry, relative_to_entry, run_upload_button):
    "Button callback to set the filepath field from a system call"
    file_path = filedialog.askopenfilename()
    if file_path is not None and file_path not in ("", "."):
        filepath_entry.insert(0, file_path)
        relative_to_entry.insert(0, str(pathlib.Path(file_path).parent))
        run_upload_button.config(state="normal")


def set_relative_to(relative_to_entry):
    "Button callback to set the 'relative_to' field from a system call"
    relative_to_path = filedialog.askdirectory()
    if relative_to_path != ".":
        relative_to_entry.insert(0, relative_to_path)


def main():
    "Define all of the pieces of the GUI and run the main loop"
    root = tk.Tk()
    root.title("IMQCAM File Uploader")
    # Set up Entry boxes for each of the simple arguments
    parser = IMQCAMFileUploader.get_argument_parser()
    def_args = {
        action.dest: action.default
        for action in parser.actions
        if action.dest
        not in (
            "help",
            "filepath",
            "relative_to",
            "logger_stream_level",
            "logger_file_path",
            "logger_file_level",
        )
    }
    entry_width = max(
        len(str(def_arg)) for def_arg in def_args.values() if def_arg is not None
    )
    arg_entries = {}
    for iarg, (arg_name, arg_def) in enumerate(def_args.items()):
        if arg_name == "api_key" and arg_def is not None:
            arg_def = "$IMQCAM_API_KEY"
        label = tk.Label(root, text=f"{arg_name}: ")
        label.grid(column=0, row=iarg)
        entry = tk.Entry(root, width=entry_width)
        entry.grid(column=1, row=iarg)
        if arg_def is not None:
            entry.insert(0, str(arg_def))
        arg_entries[arg_name] = entry
    # Set up Entry boxes and buttons for the filepath and relative_to arguments
    filepath_label = tk.Label(root, text="Path to upload file: ")
    filepath_label.grid(column=0, row=len(def_args) + 1)
    filepath_entry = tk.Entry(root, width=entry_width)
    filepath_entry.grid(column=1, row=len(def_args) + 1)
    relative_to_label = tk.Label(root, text="Upload file relative to: ")
    relative_to_label.grid(column=0, row=len(def_args) + 2)
    relative_to_entry = tk.Entry(root, width=entry_width)
    relative_to_entry.grid(column=1, row=len(def_args) + 2)
    run_upload_button = tk.Button(
        root,
        text="RUN UPLOAD",
        state="disabled",
        command=lambda: run_uploader(arg_entries, filepath_entry, relative_to_entry),
    )
    run_upload_button.grid(column=1, row=len(def_args) + 3)
    filepath_button = tk.Button(
        root,
        text="Select File",
        command=lambda: set_filepath(
            filepath_entry, relative_to_entry, run_upload_button
        ),
    )
    filepath_button.grid(column=2, row=len(def_args) + 1)
    relative_to_button = tk.Button(
        root,
        text="Select Folder",
        command=lambda: set_relative_to(relative_to_entry),
    )
    relative_to_button.grid(column=2, row=len(def_args) + 2)
    root.mainloop()


if __name__ == "__main__":
    main()
