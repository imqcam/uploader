" A GUI to run the single file uploader "

# imports
import pathlib
import tkinter as tk
from tkinter import filedialog
from ..uploaders.file_uploader import IMQCAMFileUploader


class FileUploaderGUI(tk.Tk):
    """A GUI interface to run the IMQCAMFileUploader"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("IMQCAM File Uploader")
        self.create_widgets()

    def create_widgets(self):
        """Create all the widgets in the GUI"""
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
        self.arg_entries = {}
        for iarg, (arg_name, arg_def) in enumerate(def_args.items()):
            if arg_name == "api_key" and arg_def is not None:
                arg_def = "$IMQCAM_API_KEY"
            label = tk.Label(self, text=f"{arg_name}: ")
            label.grid(column=0, row=iarg)
            entry = tk.Entry(self, width=entry_width)
            entry.grid(column=1, row=iarg)
            if arg_def is not None:
                entry.insert(0, str(arg_def))
            self.arg_entries[arg_name] = entry
        # Set up Entry boxes and buttons for the filepath and relative_to arguments
        label = tk.Label(self, text="Path to upload file: ")
        label.grid(column=0, row=len(def_args) + 1)
        self.filepath_entry = tk.Entry(self, width=entry_width)
        self.filepath_entry.grid(column=1, row=len(def_args) + 1)
        label = tk.Label(self, text="Upload file relative to: ")
        label.grid(column=0, row=len(def_args) + 2)
        self.relative_to_entry = tk.Entry(self, width=entry_width)
        self.relative_to_entry.grid(column=1, row=len(def_args) + 2)
        self.run_upload_button = tk.Button(
            self, text="RUN UPLOAD", state="disabled", command=self.run_upload
        )
        self.run_upload_button.grid(column=1, row=len(def_args) + 3)
        filepath_button = tk.Button(self, text="Select File", command=self.set_filepath)
        filepath_button.grid(column=2, row=len(def_args) + 1)
        relative_to_button = tk.Button(
            self, text="Select Folder", command=self.set_relative_to
        )
        relative_to_button.grid(column=2, row=len(def_args) + 2)

    def set_filepath(self):
        """Ask the user for a file to open and replace the path in the filepath entry.
        Also set the "relative_to" entry to the parent of the file, and enable the
        "run upload" button
        """
        file_path = filedialog.askopenfilename()
        if file_path is not None and file_path not in ("", "."):
            self.filepath_entry.delete(0, tk.END)
            self.filepath_entry.insert(0, file_path)
            self.relative_to_entry.delete(0, tk.END)
            self.relative_to_entry.insert(0, str(pathlib.Path(file_path).parent))
            self.run_upload_button.config(state="normal")

    def set_relative_to(self):
        """Ask the user for a folder to use as the "relative_to" argument and set the
        entry's value
        """
        relative_to_path = filedialog.askdirectory()
        if relative_to_path is not None and relative_to_path not in ("", "."):
            self.relative_to_entry.delete(0, tk.END)
            self.relative_to_entry.insert(0, relative_to_path)

    def run_upload(self):
        """Collect the set of arguments from the different entry fields and call the
        uploader
        """
        args = [
            self.filepath_entry.get(),
            "--relative_to",
            self.relative_to_entry.get(),
        ]
        for argname, argentry in self.arg_entries.items():
            argval = argentry.get()
            if argval is not None and argval not in ("", "$IMQCAM_API_KEY"):
                args.append(f"--{argname}")
                args.append(str(argval))
        IMQCAMFileUploader.run_from_command_line(args)


def main():
    """Run the loop for the GUI"""
    uploader_gui = FileUploaderGUI()
    uploader_gui.mainloop()


if __name__ == "__main__":
    main()
