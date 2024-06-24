import tkinter as tk
from tkinter import ttk, messagebox, filedialog, filedialog, messagebox, Toplevel, StringVar, Canvas
import pandas as pd
from datetime import datetime
from tkcalendar import DateEntry
import os
import shutil
import pickle
import sys
import babel
import babel.numbers
import babel.dates

class JobApplicationTracker:
    def __init__(self, master):
        self.master = master
        self.master.title("Job Application Tracker")
        self.master.geometry("800x600")

        # Use a folder in the user's home directory
        self.app_data_dir = os.path.join(os.path.expanduser("~"), "JobApplicationTracker")
        os.makedirs(self.app_data_dir, exist_ok=True)

        self.data_file = os.path.join(self.app_data_dir, "job_applications.pkl")
        self.resume_folder = os.path.join(self.app_data_dir, "resume")
        self.cover_letter_folder = os.path.join(self.app_data_dir, "cover_letter")

        os.makedirs(self.resume_folder, exist_ok=True)
        os.makedirs(self.cover_letter_folder, exist_ok=True)

        self.load_data()
        self.create_widgets()

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            # Running as executable
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.getcwd(), relative_path)

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'rb') as f:
                self.data = pickle.load(f)
            # Ensure the Index column exists and is correctly populated
            if 'Index' not in self.data.columns:
                self.data.insert(0, 'Index', range(1, len(self.data) + 1))
            else:
                self.data = self.data.sort_values('Index').reset_index(drop=True)
                self.data['Index'] = range(1, len(self.data) + 1)
        else:
            self.data = pd.DataFrame(columns=[
                "Index", "Company Name", "Job Title", "Application Date", "Status",
                "Job URL", "Company Website", "Location", "Salary Range",
                "Contact Person", "Contact Email/Phone", "Application Method",
                "Resume Version", "Cover Letter Version", "Interview Date",
                "Follow-up Date", "Notes", "Next Steps", "Priority"
            ])

    def save_data(self):
        with open(self.data_file, 'wb') as f:
            pickle.dump(self.data, f)

    def on_closing(self):
        self.save_data()
        self.master.destroy()

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=1)

        # Create canvas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # Add scrollbar to the canvas
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Create another frame inside the canvas
        input_frame = ttk.Frame(canvas)

        # Add that new frame to a window in the canvas
        canvas.create_window((0, 0), window=input_frame, anchor="nw")

        # Create input fields
        self.fields = {}
        row = 0
        for field in self.data.columns:
            if field != "Index":  # Skip the Index field
                ttk.Label(input_frame, text=f"{field}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)

                if field == "Application Date":
                    self.fields[field] = DateEntry(input_frame, width=20, background='darkblue', foreground='white', borderwidth=2)
                elif field in ["Interview Date", "Follow-up Date"]:
                    date_frame = ttk.Frame(input_frame)
                    date_frame.grid(row=row, column=1, sticky=tk.W)
                    self.fields[f"{field}_check"] = tk.BooleanVar()
                    check = ttk.Checkbutton(date_frame, text="No date", variable=self.fields[f"{field}_check"], 
                                            command=lambda f=field: self.toggle_date(f))
                    check.pack(side=tk.LEFT)
                    self.fields[field] = DateEntry(date_frame, width=20, background='darkblue', foreground='white', borderwidth=2)
                    self.fields[field].pack(side=tk.LEFT)
                elif field == "Status":
                    self.fields[field] = ttk.Combobox(input_frame, values=["Applied", "Interview Scheduled", "Rejected", "Offer Received"])
                elif field == "Priority":
                    self.fields[field] = ttk.Combobox(input_frame, values=["Low", "Medium", "High"])
                elif field in ["Resume Version", "Cover Letter Version"]:
                    file_frame = ttk.Frame(input_frame)
                    file_frame.grid(row=row, column=1, sticky=tk.W)
                    self.fields[field] = ttk.Combobox(file_frame, width=30)
                    self.fields[field].pack(side=tk.LEFT)
                    ttk.Button(file_frame, text="Upload", command=lambda f=field: self.upload_file(f)).pack(side=tk.LEFT)
                    self.update_file_list(field)
                elif field in ["Notes", "Next Steps"]:
                    self.fields[field] = tk.Text(input_frame, width=40, height=3)
                elif field == "Application Method":
                    self.fields[field] = ttk.Combobox(input_frame, values=["Company's Website", "LinkedIn", "Indeed", "Glassdoor", "Referral", "Email", "Job Board", "Other"])
                else:
                    self.fields[field] = ttk.Entry(input_frame, width=40)
                
                if field not in ["Interview Date", "Follow-up Date", "Resume Version", "Cover Letter Version"]:
                    self.fields[field].grid(row=row, column=1, pady=2, padx=5, sticky=tk.W)
                row += 1

        # Buttons
        button_frame = ttk.Frame(self.master)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Add Entry", command=self.add_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Entries", command=self.view_entries).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save to Excel", command=self.save_to_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save to CSV", command=self.save_to_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import File", command=self.import_file).pack(side=tk.LEFT, padx=5)


    def toggle_date(self, field):
        if self.fields[f"{field}_check"].get():
            self.fields[field].config(state='disabled')
        else:
            self.fields[field].config(state='normal')

    def upload_file(self, field):
        file_path = filedialog.askopenfilename()
        if file_path:
            if "Resume" in field:
                destination = self.resume_folder
            else:
                destination = self.cover_letter_folder
            shutil.copy(file_path, destination)
            self.update_file_list(field)

    def update_file_list(self, field):
        if "Resume" in field:
            folder = self.resume_folder
        else:
            folder = self.cover_letter_folder
        files = [""] + [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        self.fields[field]['values'] = files

    def add_entry(self):
        new_entry = {}
        for field, widget in self.fields.items():
            if field.endswith("_check"):
                continue
            if isinstance(widget, tk.Text):
                new_entry[field] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, DateEntry):
                if field in ["Interview Date", "Follow-up Date"] and self.fields[f"{field}_check"].get():
                    new_entry[field] = ""
                else:
                    new_entry[field] = widget.get_date().strftime("%Y-%m-%d")
            else:
                new_entry[field] = widget.get()

        new_entry["Index"] = len(self.data) + 1
        self.data = self.data._append(new_entry, ignore_index=True)
        self.save_data()
        messagebox.showinfo("Success", "Entry added successfully!")
        self.clear_fields()

    def clear_fields(self):
        for field, widget in self.fields.items():
            if field.endswith("_check"):
                continue
            if isinstance(widget, tk.Text):
                widget.delete("1.0", tk.END)
            elif isinstance(widget, DateEntry):
                widget.set_date(datetime.now())
            elif isinstance(widget, ttk.Combobox):
                widget.set('')
            elif isinstance(widget, ttk.Entry):
                widget.delete(0, tk.END)
            else:
                # For any other widget types, try set() method, otherwise ignore
                try:
                    widget.set('')
                except AttributeError:
                    pass

        # Reset checkboxes
        for field in ["Interview Date", "Follow-up Date"]:
            self.fields[f"{field}_check"].set(False)
            self.fields[field].config(state='normal')
    
    def view_entries(self):
        view_window = tk.Toplevel(self.master)
        view_window.title("View Entries")
        view_window.geometry("1000x600")

        # Add search frame
        search_frame = ttk.Frame(view_window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Search", command=lambda: self.search_entries(tree, search_entry.get())).pack(side=tk.LEFT, padx=5)

        # Create a frame to hold the treeview and scrollbars
        frame = ttk.Frame(view_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create vertical scrollbar
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create a treeview with both scrollbars
        tree = ttk.Treeview(frame, columns=list(self.data.columns), show='headings',
                            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Ensure Index column is first
        columns = ["Index"] + [col for col in self.data.columns if col != "Index"]
        tree = ttk.Treeview(frame, columns=columns, show='headings',
                            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Configure the scrollbars
        v_scrollbar.config(command=tree.yview)
        h_scrollbar.config(command=tree.xview)

        # Set column headings and adjust column widths
        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: self.sort_treeview(tree, _col, False))
            tree.column(col, width=100, minwidth=100)

        # Add data to the treeview
        for i, row in self.data.iterrows():
            tree.insert('', 'end', values=[row['Index']] + [row[col] for col in columns if col != 'Index'])

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add Edit and Delete buttons
        button_frame = ttk.Frame(view_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Edit", command=lambda: self.edit_entry(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete", command=lambda: self.delete_entry(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete All", command=lambda: self.delete_all_entries(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Refresh", command=lambda: self.refresh_view(tree)).pack(side=tk.LEFT, padx=5)

        # Function to adjust column widths based on content
        def adjust_column_widths():
            for col in self.data.columns:
                # Find the maximum width needed for the column
                max_width = max(
                    tree.column(col)['width'],
                    len(str(tree.heading(col)['text'])) * 10,
                    max(len(str(row[col])) * 10 for _, row in self.data.iterrows())
                )
                tree.column(col, width=min(max_width, 300))  # Limit max width to 300 pixels

        # Adjust column widths after adding data
        adjust_column_widths()
    
    def search_entries(self, tree, search_term):
        tree.delete(*tree.get_children())
        for i, row in self.data.iterrows():
            if search_term.lower() in str(row).lower():
                tree.insert('', 'end', values=list(row))
    
    def sort_treeview(self, tree, col, reverse):
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        l.sort(key=lambda t: self.sort_key(t[0]), reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)

        # Update the heading with an arrow indicating sort direction
        for c in tree['columns']:
            tree.heading(c, text=c.split(' ')[0])  # Remove existing arrows
        new_text = f"{col} {'▼' if reverse else '▲'}"
        tree.heading(col, text=new_text)

        # Reverse sort next time
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))
        
    def sort_key(self, value):
        # Try to convert to int or float for numeric sorting
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value.lower()  # Fall back to case-insensitive string comparison

    def edit_entry(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an entry to edit.")
            return

        item = tree.item(selected_item)
        index = int(item['values'][0]) - 1  # Get the actual index from the "Index" column
        values = item['values']

        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Entry")
        edit_window.geometry("800x600")

        # Create a canvas with scrollbar
        canvas = tk.Canvas(edit_window)
        scrollbar = ttk.Scrollbar(edit_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create input fields
        entry_fields = {}
        for i, col in enumerate(self.data.columns):
            ttk.Label(scrollable_frame, text=f"{col}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            
            if col == "Application Date":
                entry_fields[col] = DateEntry(scrollable_frame, width=20, background='darkblue', foreground='white', borderwidth=2)
                entry_fields[col].set_date(datetime.strptime(values[i], "%Y-%m-%d") if values[i] else datetime.now())
            elif col in ["Interview Date", "Follow-up Date"]:
                date_frame = ttk.Frame(scrollable_frame)
                date_frame.grid(row=i, column=1, sticky=tk.W)
                entry_fields[f"{col}_check"] = tk.BooleanVar(value=not values[i])
                check = ttk.Checkbutton(date_frame, text="No date", variable=entry_fields[f"{col}_check"], 
                                        command=lambda f=col: self.toggle_date_edit(f, entry_fields))
                check.pack(side=tk.LEFT)
                entry_fields[col] = DateEntry(date_frame, width=20, background='darkblue', foreground='white', borderwidth=2)
                entry_fields[col].pack(side=tk.LEFT)
                if values[i]:
                    entry_fields[col].set_date(datetime.strptime(values[i], "%Y-%m-%d"))
                else:
                    entry_fields[col].config(state='disabled')
            elif col == "Status":
                entry_fields[col] = ttk.Combobox(scrollable_frame, values=["Applied", "Interview Scheduled", "Rejected", "Offer Received"])
                entry_fields[col].set(values[i])
            elif col == "Priority":
                entry_fields[col] = ttk.Combobox(scrollable_frame, values=["Low", "Medium", "High"])
                entry_fields[col].set(values[i])
            elif col in ["Resume Version", "Cover Letter Version"]:
                file_frame = ttk.Frame(scrollable_frame)
                file_frame.grid(row=i, column=1, sticky=tk.W)
                entry_fields[col] = ttk.Combobox(file_frame, width=30)
                entry_fields[col].pack(side=tk.LEFT)
                ttk.Button(file_frame, text="Upload", command=lambda f=col: self.upload_file_edit(f, entry_fields)).pack(side=tk.LEFT)
                self.update_file_list_edit(col, entry_fields)
                entry_fields[col].set(values[i])
            elif col in ["Notes", "Next Steps"]:
                entry_fields[col] = tk.Text(scrollable_frame, width=40, height=3)
                entry_fields[col].insert(tk.END, values[i])
            else:
                entry_fields[col] = ttk.Entry(scrollable_frame, width=40)
                entry_fields[col].insert(0, values[i])
            
            if col not in ["Interview Date", "Follow-up Date", "Resume Version", "Cover Letter Version"]:
                entry_fields[col].grid(row=i, column=1, pady=2, padx=5, sticky=tk.W)

        def save_edit():
            new_values = [values[0]]  # Keep the original index
            for col in self.data.columns[1:]:  # Skip the "Index" column
                if col in ["Interview Date", "Follow-up Date"]:
                    if entry_fields[f"{col}_check"].get():
                        new_values.append("")
                    else:
                        new_values.append(entry_fields[col].get_date().strftime("%Y-%m-%d"))
                elif isinstance(entry_fields[col], DateEntry):
                    new_values.append(entry_fields[col].get_date().strftime("%Y-%m-%d"))
                elif isinstance(entry_fields[col], tk.Text):
                    new_values.append(entry_fields[col].get("1.0", tk.END).strip())
                else:
                    new_values.append(entry_fields[col].get())

            self.data.iloc[index] = new_values
            self.save_data()
            tree.item(selected_item, values=new_values)
            edit_window.destroy()
            messagebox.showinfo("Success", "Entry updated successfully!")

        ttk.Button(scrollable_frame, text="Save", command=save_edit).grid(row=len(self.data.columns), column=1, pady=10)

    def toggle_date_edit(self, field, entry_fields):
        if entry_fields[f"{field}_check"].get():
            entry_fields[field].config(state='disabled')
        else:
            entry_fields[field].config(state='normal')

    def upload_file_edit(self, field, entry_fields):
        file_path = filedialog.askopenfilename()
        if file_path:
            if "Resume" in field:
                destination = self.resume_folder
            else:
                destination = self.cover_letter_folder
            shutil.copy(file_path, destination)
            self.update_file_list_edit(field, entry_fields)

    def update_file_list_edit(self, field, entry_fields):
        if "Resume" in field:
            folder = self.resume_folder
        else:
            folder = self.cover_letter_folder
        files = [""] + [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        entry_fields[field]['values'] = files

    def delete_entry(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an entry to delete.")
            return

        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this entry?"):
            item = tree.item(selected_item)
            try:
                index = next(i for i, v in enumerate(item['values']) if str(v).isdigit()) # Find the index column
                index_value = int(item['values'][index]) - 1  # Get the actual index from the "Index" column
                self.data = self.data[self.data['Index'] != index_value + 1].reset_index(drop=True)
                self.data['Index'] = range(1, len(self.data) + 1)  # Reindex the remaining entries
                self.save_data()
                tree.delete(selected_item)
                self.refresh_view(tree)  # Refresh the view to update all indices
                messagebox.showinfo("Success", "Entry deleted successfully!")
            except ValueError:
                messagebox.showerror("Error", "Unable to delete entry. Invalid index found.")

    def save_to_excel(self):
        default_filename = "job_application_tracker.xlsx"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_filename
        )
        if file_path:
            self.data.to_excel(file_path, index=False)
            messagebox.showinfo("Success", f"Data saved to {file_path}")

    def save_to_csv(self):
        default_filename = "job_application_tracker.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_filename
        )
        if file_path:
            self.data.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Data saved to {file_path}")
    
    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")])
        if not file_path:
            return

        if not messagebox.askyesno("Warning", "Importing a new file will replace all current entries. Are you sure you want to continue?"):
            return

        try:
            if file_path.endswith('.xlsx'):
                imported_df = pd.read_excel(file_path)
            else:
                imported_df = pd.read_csv(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")
            return

        self.map_columns(imported_df)

    def map_columns(self, imported_df):
        mapping_window = Toplevel(self.master)
        mapping_window.title("Map Columns")
        mapping_window.geometry("400x400")

        # Create a canvas with scrollbar
        canvas = Canvas(mapping_window)
        scrollbar = ttk.Scrollbar(mapping_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(scrollable_frame, text="Map your columns to the app's columns:").pack(pady=10)

        mapping = {}
        for col in self.data.columns:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(frame, text=col, width=20).pack(side="left")
            mapping[col] = StringVar(mapping_window)
            
            # Auto-map if column names match
            default_value = col if col in imported_df.columns else ""
            
            combo = ttk.Combobox(frame, textvariable=mapping[col], values=[""] + list(imported_df.columns), width=30)
            combo.pack(side="left")
            combo.set(default_value)

        def apply_mapping():
            new_data = pd.DataFrame(columns=self.data.columns)
            for app_col, import_col in mapping.items():
                if import_col.get() and app_col != "Index":
                    # Handle empty cells
                    new_data[app_col] = imported_df[import_col.get()].fillna('').astype(str).replace('nan', '')
            
            # Add Index column
            new_data['Index'] = range(1, len(new_data) + 1)
            
            # Reorder columns to ensure Index is first
            new_data = new_data[['Index'] + [col for col in new_data.columns if col != 'Index']]
            
            # Replace the current data with the new data
            self.data = new_data
            self.save_data()
            mapping_window.destroy()
            messagebox.showinfo("Success", "Data imported successfully! All previous entries have been replaced.")

        ttk.Button(scrollable_frame, text="Import", command=apply_mapping).pack(pady=10)
    
    def delete_all_entries(self, tree):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all entries? This action cannot be undone."):
            self.data = pd.DataFrame(columns=self.data.columns)
            self.save_data()
            self.refresh_view(tree)
            messagebox.showinfo("Success", "All entries have been deleted.")
    
    def refresh_view(self, tree):
        for item in tree.get_children():
            tree.delete(item)
        for i, row in self.data.iterrows():
            tree.insert('', 'end', values=list(row))

if __name__ == "__main__":
    root = tk.Tk()
    app = JobApplicationTracker(root)
    root.mainloop()

    