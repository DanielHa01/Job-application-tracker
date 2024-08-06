import sys
import os
import pandas as pd
from datetime import datetime
import pickle
import logging
import shutil
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QComboBox, QDateEdit, QTextEdit, QFileDialog, QMessageBox, 
                             QScrollArea, QCheckBox, QHeaderView, QGridLayout, QDialog, 
                             QTabWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QDate, QSortFilterProxyModel, QSize
from PyQt6.QtGui import QStandardItemModel, QStandardItem
import textwrap

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class JobApplicationTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Job Application Tracker")
        self.setGeometry(100, 100, 800, 1000)

        self.app_data_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.app_data_dir, "job_applications.pkl")
        self.resume_folder = os.path.join(self.app_data_dir, "resume")
        self.cover_letter_folder = os.path.join(self.app_data_dir, "cover_letter")

        os.makedirs(self.resume_folder, exist_ok=True)
        os.makedirs(self.cover_letter_folder, exist_ok=True)

        self.required_fields = ["Company Name", "Job Title", "Status", "Company Website", "Location", "Application Method", "Resume Version", "Term"]

        self.total_apps_label = None

        self.load_data()

        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.init_ui()

    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    self.data = pickle.load(f)
                logging.info(f"Data loaded successfully from {self.data_file}")
                # Convert date columns to datetime
                date_columns = ['Application Date', 'Interview Date', 'Follow-up Date']
                for col in date_columns:
                    self.data[col] = self.data[col].apply(lambda x: pd.to_datetime(x, format='%Y-%m-%d') if x and pd.notna(x) else '')
                logging.info(f"Data loaded successfully from {self.data_file}")
            else:
                self.data = pd.DataFrame(columns=[
                    "Index", "Company Name", "Job Title", "Position", "Industry", "Term",
                    "Application Date", "Status", "Job URL", "Company Website", "Location", 
                    "Salary Range", "Contact Person", "Contact Email/Phone", "Application Method",
                    "Resume Version", "Cover Letter Version", "Interview Date", "Follow-up Date", 
                    "Notes", "Next Steps", "Priority"
                ])
                logging.info("New data file created")
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}\nCreating new data file.")
            self.data = pd.DataFrame(columns=[
                "Index", "Company Name", "Job Title", "Position", "Industry", "Term",
                "Application Date", "Status", "Job URL", "Company Website", "Location", 
                "Salary Range", "Contact Person", "Contact Email/Phone", "Application Method",
                "Resume Version", "Cover Letter Version", "Interview Date", "Follow-up Date", 
                "Notes", "Next Steps", "Priority"
            ])

    def save_data(self):
        try:
            with open(self.data_file, 'wb') as f:
                pickle.dump(self.data, f)
            logging.info(f"Data saved successfully to {self.data_file}")
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")
    
    def populate_file_list(self, folder):
        return [""] + [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

    def init_ui(self):
        # Input fields
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        scroll_layout.setColumnStretch(1, 1)  # Make the second column (with input widgets) stretchable

        self.fields = {}
        row = 0
        for field in self.data.columns:
            if field != "Index" and not field.endswith("_check"):
                if field in self.required_fields:
                    label = QLabel(f"{field}")
                    asterisk = QLabel("*")
                    asterisk.setStyleSheet("color: red")
                    label_layout = QHBoxLayout()
                    label_layout.addWidget(label)
                    label_layout.addWidget(asterisk)
                    label_layout.addStretch()
                    scroll_layout.addLayout(label_layout, row, 0)
                else:
                    label = QLabel(f"{field}:")
                    scroll_layout.addWidget(label, row, 0)

                if field in ["Application Date", "Interview Date", "Follow-up Date"]:
                    date_layout = QHBoxLayout()
                    self.fields[field] = QDateEdit()
                    self.fields[field].setCalendarPopup(True)
                    self.fields[field].setDate(QDate.currentDate())
                    date_layout.addWidget(self.fields[field])
                    
                    if field in ["Interview Date", "Follow-up Date"]:
                        check_box = QCheckBox("No date")
                        check_box.stateChanged.connect(lambda state, f=field: self.toggle_date(f, state))
                        date_layout.addWidget(check_box)
                        self.fields[f"{field}_check"] = check_box
                    
                    scroll_layout.addLayout(date_layout, row, 1)
                elif field == "Status":
                    self.fields[field] = QComboBox()
                    self.fields[field].addItems(["Applied", "Interview Scheduled", "Rejected", "Offer Received"])
                    scroll_layout.addWidget(self.fields[field], row, 1)
                elif field == "Priority":
                    self.fields[field] = QComboBox()
                    self.fields[field].addItems(["", "Low", "Medium", "High"])
                    scroll_layout.addWidget(self.fields[field], row, 1)
                elif field == "Application Method":
                    self.fields[field] = QComboBox()
                    self.fields[field].addItems(["Company's Website", "LinkedIn", "Indeed", "Glassdoor", "Referral", "Email", "Other"])
                    scroll_layout.addWidget(self.fields[field], row, 1)
                elif field in ["Resume Version", "Cover Letter Version"]:
                    field_layout = QHBoxLayout()
                    self.fields[field] = QComboBox()
                    if field == "Resume Version":
                        self.fields[field].addItems(self.populate_file_list(self.resume_folder))
                        upload_button = QPushButton("Upload Resume")
                        upload_button.clicked.connect(lambda: self.upload_file("resume"))
                    else:
                        self.fields[field].addItems(self.populate_file_list(self.cover_letter_folder))
                        upload_button = QPushButton("Upload Cover Letter")
                        upload_button.clicked.connect(lambda: self.upload_file("cover_letter"))
                    field_layout.addWidget(self.fields[field])
                    field_layout.addWidget(upload_button)
                    scroll_layout.addLayout(field_layout, row, 1)
                elif field in ["Notes", "Next Steps"]:
                    self.fields[field] = QTextEdit()
                    self.fields[field].setMinimumHeight(60)  # Set a minimum height for text fields
                    scroll_layout.addWidget(self.fields[field], row, 1)
                else:
                    self.fields[field] = QLineEdit()
                    scroll_layout.addWidget(self.fields[field], row, 1)

                row += 1
                
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Entry")
        add_button.clicked.connect(self.add_entry)
        button_layout.addWidget(add_button)

        view_button = QPushButton("View Entries")
        view_button.clicked.connect(self.view_entries)
        button_layout.addWidget(view_button)

        save_as_button = QPushButton("Save As")
        save_as_button.clicked.connect(self.save_as)
        button_layout.addWidget(save_as_button)

        import_button = QPushButton("Import File")
        import_button.clicked.connect(self.import_file)
        button_layout.addWidget(import_button)

        self.main_layout.addLayout(button_layout)

        self.init_dashboard()

        # Add total applications count
        self.total_apps_label = QLabel(f"Total Applications: {len(self.data)}")
        self.main_layout.addWidget(self.total_apps_label)

    def upload_file(self, file_type, combo_box=None):
        file_path, _ = QFileDialog.getOpenFileName(self, f"Upload {file_type.replace('_', ' ').title()}", "", "All Files (*)")
        if file_path:
            file_name = os.path.basename(file_path)
            file_name_parts = file_name.split('.')
            if len(file_name_parts) <= 1:
                QMessageBox.critical(self, "Error", "Invalid file")
                return
            file_name = ""
            for i in range(len(file_name_parts) - 1):
                file_name += file_name_parts[i]
                if i < len(file_name_parts) - 2:
                    file_name += "."
            file_name += datetime.now().strftime("_%m_%d_%Y") + "." + file_name_parts[-1]
            if file_type == "resume":
                dest_folder = self.resume_folder
                if not combo_box:
                    combo_box = self.fields["Resume Version"]
            else:
                dest_folder = self.cover_letter_folder
                if not combo_box:
                    combo_box = self.fields["Cover Letter Version"]
            
            dest_path = os.path.join(dest_folder, file_name)
            shutil.copy2(file_path, dest_path)
            
            combo_box.addItem(file_name)
            combo_box.setCurrentText(file_name)
            QMessageBox.information(self, "Success", f"{file_type.replace('_', ' ').title()} uploaded successfully!")

    def toggle_date(self, field, state):
        if state == Qt.CheckState.Checked.value:
            self.fields[field].setEnabled(False)
        else:
            self.fields[field].setEnabled(True)

    def update_total_apps_count(self):
        if self.total_apps_label:
            self.total_apps_label.setText(f"Total Applications: {len(self.data)}")

    def add_entry(self):
        new_entry = {}
        missing_fields = []

        for field in self.data.columns:
            if field != "Index":
                if field in self.required_fields:
                    if isinstance(self.fields[field], QComboBox):
                        if not self.fields[field].currentText():
                            missing_fields.append(field)
                    elif isinstance(self.fields[field], QLineEdit) and not self.fields[field].text():
                        missing_fields.append(field)
                
                if field in ["Application Date", "Interview Date", "Follow-up Date"]:
                    if field in ["Interview Date", "Follow-up Date"] and self.fields[f"{field}_check"].isChecked():
                        new_entry[field] = ""
                    else:
                        new_entry[field] = self.fields[field].date().toString("yyyy-MM-dd")
                elif isinstance(self.fields[field], QDateEdit):
                    new_entry[field] = self.fields[field].date().toString("yyyy-MM-dd")
                elif isinstance(self.fields[field], QTextEdit):
                    new_entry[field] = self.fields[field].toPlainText()
                elif isinstance(self.fields[field], QComboBox):
                    new_entry[field] = self.fields[field].currentText()
                else:
                    new_entry[field] = self.fields[field].text()

        if missing_fields:
            QMessageBox.warning(self, "Missing Fields", f"Please fill in the following required fields: {', '.join(missing_fields)}")
            return

        new_entry["Index"] = len(self.data) + 1
        self.data = self.data._append(new_entry, ignore_index=True)
        self.save_data()
        self.update_dashboard()
        self.update_total_apps_count()
        QMessageBox.information(self, "Success", "Entry added successfully!")
        self.clear_fields()

    def clear_fields(self):
        for field, widget in self.fields.items():
            if field.endswith("_check"):
                widget.setChecked(False)
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            elif isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            else:
                widget.clear()

    def view_entries(self):
        self.view_window = QWidget()
        self.view_window.setWindowTitle("View Entries")
        self.view_window.setGeometry(200, 200, 1000, 600)
        layout = QVBoxLayout(self.view_window)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        
        # Filter out the columns we don't want to display
        display_columns = [col for col in self.data.columns if not col.endswith('_check') and col != "Index"]
        
        self.table.setColumnCount(len(display_columns))
        self.table.setHorizontalHeaderLabels(display_columns)
        self.table.setRowCount(len(self.data))

        # Set column widths
        header = self.table.horizontalHeader()
        for i in range(len(display_columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Enable sorting
        self.table.setSortingEnabled(True)

        self.refresh_table(self.table, display_columns)

        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_entry)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_entry)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        self.view_window.show()


    def filter_table(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def edit_entry(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an entry to edit.")
            return

        row = selected_items[0].row()
        edit_window = QWidget()
        edit_window.setWindowTitle("Edit Entry")
        edit_window.setGeometry(300, 300, 600, 800)
        layout = QVBoxLayout(edit_window)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QGridLayout(scroll_widget)
        scroll_layout.setColumnStretch(1, 1)

        edit_fields = {}
        grid_row = 0
        for col in self.data.columns:
            if col != "Index" and not col.endswith("_check"):
                field_layout = QHBoxLayout()
                
                if col in self.required_fields:
                    label = QLabel(f"{col}")
                    asterisk = QLabel("*")
                    asterisk.setStyleSheet("color: red")
                    label_layout = QHBoxLayout()
                    label_layout.addWidget(label)
                    label_layout.addWidget(asterisk)
                    label_layout.addStretch()
                    scroll_layout.addLayout(label_layout, grid_row, 0)
                else:
                    label = QLabel(f"{col}:")
                    scroll_layout.addWidget(label, grid_row, 0)

                if col in ["Application Date", "Interview Date", "Follow-up Date"]:
                    date_layout = QHBoxLayout()
                    edit_fields[col] = QDateEdit()
                    edit_fields[col].setCalendarPopup(True)
                    date_value = self.data.iloc[row][col]
                    if pd.notna(date_value):
                        edit_fields[col].setDate(QDate.fromString(str(date_value)[:10], "yyyy-MM-dd"))
                    date_layout.addWidget(edit_fields[col])
                    
                    if col in ["Interview Date", "Follow-up Date"]:
                        check_box = QCheckBox("No date")
                        check_box.stateChanged.connect(lambda state, f=col: self.toggle_date_edit(f, state, edit_fields))
                        check_box.setChecked(pd.isna(date_value))
                        date_layout.addWidget(check_box)
                        edit_fields[f"{col}_check"] = check_box  # Store the checkbox in edit_fields
                    
                    scroll_layout.addLayout(date_layout, grid_row, 1)
                elif col == "Status":
                    edit_fields[col] = QComboBox()
                    edit_fields[col].addItems(["Applied", "Interview Scheduled", "Rejected", "Offer Received"])
                    edit_fields[col].setCurrentText(str(self.data.iloc[row][col]))
                    scroll_layout.addWidget(edit_fields[col], grid_row, 1)
                elif col == "Priority":
                    edit_fields[col] = QComboBox()
                    edit_fields[col].addItems(["", "Low", "Medium", "High"])
                    edit_fields[col].setCurrentText(str(self.data.iloc[row][col]))
                    scroll_layout.addWidget(edit_fields[col], grid_row, 1)
                elif col == "Application Method":
                    edit_fields[col] = QComboBox()
                    edit_fields[col].addItems(["Company's Website", "LinkedIn", "Indeed", "Glassdoor", "Referral", "Email", "Other"])
                    edit_fields[col].setCurrentText(str(self.data.iloc[row][col]))
                    scroll_layout.addWidget(edit_fields[col], grid_row, 1)
                elif col in ["Resume Version", "Cover Letter Version"]:
                    edit_fields[col] = QComboBox()
                    if col == "Resume Version":
                        edit_fields[col].addItems(self.populate_file_list(self.resume_folder))
                        upload_button = QPushButton("Upload Resume")
                        upload_button.clicked.connect(lambda: self.upload_file("resume", edit_fields[col]))
                    else:
                        edit_fields[col].addItems(self.populate_file_list(self.cover_letter_folder))
                        upload_button = QPushButton("Upload Cover Letter")
                        upload_button.clicked.connect(lambda: self.upload_file("cover_letter", edit_fields[col]))
                    edit_fields[col].setCurrentText(str(self.data.iloc[row][col]))
                    field_layout.addWidget(edit_fields[col])
                    field_layout.addWidget(upload_button)
                    scroll_layout.addLayout(field_layout, grid_row, 1)
                elif col in ["Notes", "Next Steps"]:
                    edit_fields[col] = QTextEdit()
                    edit_fields[col].setText(str(self.data.iloc[row][col]))
                    scroll_layout.addWidget(edit_fields[col], grid_row, 1)
                else:
                    edit_fields[col] = QLineEdit()
                    edit_fields[col].setText(str(self.data.iloc[row][col]))
                    scroll_layout.addWidget(edit_fields[col], grid_row, 1)

                grid_row += 1

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_edit(row, edit_fields, edit_window))
        layout.addWidget(save_button)

        edit_window.show()

    def toggle_date_edit(self, field, state, edit_fields):
        if state == Qt.CheckState.Checked.value:
            edit_fields[field].setEnabled(False)
        else:
            edit_fields[field].setEnabled(True)

    def save_edit(self, row, edit_fields, edit_window):
        missing_fields = []
        updated_data = {}

        for col, widget in edit_fields.items():
            if col.endswith("_check"):
                continue  # Skip the check boxes, we'll handle them with their corresponding date fields

            if col in self.required_fields:
                if isinstance(widget, QComboBox) and not widget.currentText():
                    missing_fields.append(col)
                elif isinstance(widget, QLineEdit) and not widget.text():
                    missing_fields.append(col)
                elif isinstance(widget, QTextEdit) and not widget.toPlainText():
                    missing_fields.append(col)

            if col in ["Interview Date", "Follow-up Date"]:
                if f"{col}_check" in edit_fields and edit_fields[f"{col}_check"].isChecked():
                    updated_data[col] = ""  # Use None for empty dates
                else:
                    updated_data[col] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QDateEdit):
                updated_data[col] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QTextEdit):
                updated_data[col] = widget.toPlainText()
            elif isinstance(widget, QComboBox):
                updated_data[col] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                updated_data[col] = widget.text()

        if missing_fields:
            QMessageBox.warning(self, "Missing Fields", f"Please fill in the following required fields: {', '.join(missing_fields)}")
            return

        updated_data["Index"] = row + 1
        self.data.iloc[row] = updated_data

        self.save_data()
        self.refresh_table(self.table, display_columns=[col for col in self.data.columns if not col.endswith('_check') and col != "Index"])
        self.update_dashboard()
        edit_window.close()
        QMessageBox.information(self, "Success", "Entry updated successfully!")

    def delete_entry(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an entry to delete.")
            return

        row = selected_items[0].row()
        if QMessageBox.question(self, "Confirm Deletion", "Are you sure you want to delete this entry?") == QMessageBox.StandardButton.Yes:
            self.data = self.data.drop(self.data.index[row]).reset_index(drop=True)
            self.data['Index'] = range(1, len(self.data) + 1)
            self.save_data()
            self.refresh_table(self.table)
            self.update_dashboard()
            self.update_total_apps_count()
            QMessageBox.information(self, "Success", "Entry deleted successfully!")

    def refresh_table(self, table, display_columns):
        table.setRowCount(len(self.data))

        for i, (_, row) in enumerate(self.data.iterrows()):
            for j, col in enumerate(display_columns):
                if col != "Index":
                    item = QTableWidgetItem(str(row[col]))
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make item read-only
                    table.setItem(i, j, item)

    def save_as(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self, "Save File", "job_application_tracker",
            "Excel Files (*.xlsx);;CSV Files (*.csv)", options=options)
        
        if file_name:
            if selected_filter == "Excel Files (*.xlsx)":
                if not file_name.endswith('.xlsx'):
                    file_name += '.xlsx'
                self.data.to_excel(file_name, index=False)
            elif selected_filter == "CSV Files (*.csv)":
                if not file_name.endswith('.csv'):
                    file_name += '.csv'
                self.data.to_csv(file_name, index=False)
            
            QMessageBox.information(self, "Success", f"Data saved to {file_name}")

    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel files (*.xlsx);;CSV files (*.csv)")
        if not file_path:
            return

        try:
            if file_path.endswith('.xlsx'):
                imported_df = pd.read_excel(file_path)
            else:
                imported_df = pd.read_csv(file_path)
            
            # Create a mapping dialog
            mapping_dialog = QDialog(self)
            mapping_dialog.setWindowTitle("Column Mapping")
            layout = QVBoxLayout(mapping_dialog)

            mapping = {}
            for col in self.data.columns:
                if col != "Index" and not col.endswith("_check"):
                    row_layout = QHBoxLayout()
                    row_layout.addWidget(QLabel(f"Map '{col}' to:"))
                    combo = QComboBox()
                    combo.addItem("-- Skip --")
                    combo.addItems(imported_df.columns)
                    if col in imported_df.columns:
                        combo.setCurrentText(col)
                    row_layout.addWidget(combo)
                    layout.addLayout(row_layout)
                    mapping[col] = combo

            confirm_button = QPushButton("Confirm Mapping")
            confirm_button.clicked.connect(mapping_dialog.accept)
            layout.addWidget(confirm_button)

            result = mapping_dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                new_data = pd.DataFrame()
                for col, combo in mapping.items():
                    mapped_col = combo.currentText()
                    if mapped_col != "-- Skip --":
                        new_data[col] = imported_df[mapped_col]
                    else:
                        new_data[col] = ""

                # Handle null values
                new_data = new_data.replace({np.nan: '', 'nan': '', 'NaN': ''})

                # Ensure 'Index' column is present and correct
                new_data['Index'] = range(1, len(new_data) + 1)

                # Reorder columns to ensure Index is first
                new_data = new_data[['Index'] + [col for col in new_data.columns if col != 'Index']]

                if QMessageBox.question(self, "Confirm Import", "This will replace your current data. Are you sure?") == QMessageBox.StandardButton.Yes:
                    self.data = new_data
                    self.save_data()
                    QMessageBox.information(self, "Success", "Data imported successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import file: {str(e)}")
    
    def init_dashboard(self):
        # Close all existing figures
        plt.close('all')

        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Create plots
        self.status_pie_fig, status_pie_canvas = self.create_status_pie()
        self.company_bar_fig, company_bar_canvas = self.create_company_bar()
        self.timeline_line_fig, timeline_line_canvas = self.create_timeline_line()
        self.job_title_bar_fig, job_title_bar_canvas = self.create_job_title_bar()
        self.term_bar_fig, term_bar_canvas = self.create_term_bar()
        self.application_method_bar_fig, application_method_bar_canvas = self.create_application_method_bar()
        self.resume_cover_letter_bar_fig, resume_cover_letter_bar_canvas = self.create_resume_cover_letter_bar()
        self.status_stacked_area_fig, status_stacked_area_canvas = self.create_status_stacked_area()
        self.industry_pie_fig, industry_pie_canvas = self.create_industry_pie()

        # Create scalable graph widgets
        status_pie_widget = ScalableGraphWidget(self.status_pie_fig, status_pie_canvas, 'Applications by Status', fixed_height=500, legend=True)
        company_bar_widget = ScalableGraphWidget(self.company_bar_fig, company_bar_canvas, 'Top Companies by Applications', fixed_height=1000)
        timeline_line_widget = ScalableGraphWidget(self.timeline_line_fig, timeline_line_canvas, 'Applications Over Time', fixed_height=800)
        job_title_bar_widget = ScalableGraphWidget(self.job_title_bar_fig, job_title_bar_canvas, 'Top 10 Job Postitions', fixed_height=1000)
        term_bar_widget = ScalableGraphWidget(self.term_bar_fig, term_bar_canvas, 'Applications by Term', fixed_height=800)
        application_method_bar_widget = ScalableGraphWidget(self.application_method_bar_fig, application_method_bar_canvas, 'Applications by Method', fixed_height=1000)
        resume_cover_letter_bar_widget = ScalableGraphWidget(self.resume_cover_letter_bar_fig, resume_cover_letter_bar_canvas, 'Applications by Resume and Cover Letter Version', fixed_height=1200)
        status_stacked_area_widget = ScalableGraphWidget(self.status_stacked_area_fig, status_stacked_area_canvas, 'Application Statuses Over Time', fixed_height=600)
        industry_pie_widget = ScalableGraphWidget(self.industry_pie_fig, industry_pie_canvas, 'Applications by Industry', fixed_height=500, legend=True)

        # Add scalable graph widgets to the scroll layout
        scroll_layout.addWidget(status_pie_widget)
        scroll_layout.addWidget(company_bar_widget)
        scroll_layout.addWidget(timeline_line_widget)
        scroll_layout.addWidget(job_title_bar_widget)
        scroll_layout.addWidget(term_bar_widget)
        scroll_layout.addWidget(application_method_bar_widget)
        scroll_layout.addWidget(resume_cover_letter_bar_widget)
        scroll_layout.addWidget(status_stacked_area_widget)
        scroll_layout.addWidget(industry_pie_widget)

        # Set the scroll content and add to main layout
        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        dashboard_layout.addWidget(scroll_area)

        # Create a tab for the dashboard
        if not hasattr(self, 'tab_widget'):
            self.tab_widget = QTabWidget()
            self.tab_widget.addTab(self.central_widget, "Job Tracker")
        
        # Check if the dashboard tab already exists, if so, remove it
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(1)
        
        # Add the new dashboard tab
        self.tab_widget.addTab(dashboard_widget, "Dashboard")

        # Set the tab widget as the central widget if it's not already
        if self.centralWidget() != self.tab_widget:
            self.setCentralWidget(self.tab_widget)
    
    def create_status_pie(self):
        status_counts = self.data['Status'].value_counts()
        status_counts = self.group_small_values(status_counts, threshold=5)
        
        fig, ax = plt.subplots(figsize=(10, 7))
        colors = plt.cm.Set3(np.linspace(0, 1, len(status_counts)))
        wedges, texts, autotexts = ax.pie(status_counts.values, colors=colors, autopct=lambda pct: f"{pct:.1f}%\n({int(pct/100.*sum(status_counts))})", pctdistance=0.75)
        
        ax.set_title('Applications by Status')
        
        # Add legend
        ax.legend(wedges, status_counts.index,
                title="Statuses",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.setp(autotexts, size=8, weight="bold")
        ax.set_aspect("equal")
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_timeline_line(self):
        self.data['Application Date'] = pd.to_datetime(self.data['Application Date'], format="%Y-%m-%d", errors='coerce')
        date_counts = self.data['Application Date'].value_counts().sort_index()
        
        fig, ax = plt.subplots(figsize=(12, 9))  # 4:3 aspect ratio
        ax.plot(date_counts.index, date_counts.values)
        ax.set_title('Applications Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Applications')
        
        # Set x-axis ticks to be 10 days apart
        start_date = date_counts.index.min()
        end_date = date_counts.index.max()
        date_range = pd.date_range(start=start_date, end=end_date, freq='5D')
        ax.set_xticks(date_range)
        ax.set_xticklabels(date_range.strftime('%Y-%m-%d'), rotation=45, ha='right')
        
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas
    
    def create_job_title_bar(self):
        job_title_counts = self.data['Position'].value_counts().head(10)
        
        fig, ax = plt.subplots(figsize=(12, 9))
        bars = ax.bar(range(len(job_title_counts)), job_title_counts.values)
        ax.set_title('Top 10 Job Positions')
        ax.set_ylabel('Number of Applications')
        
        # Wrap x-axis labels
        wrapped_labels = [textwrap.fill(label, width=20) for label in job_title_counts.index]
        ax.set_xticks(range(len(job_title_counts)))
        ax.set_xticklabels(wrapped_labels, rotation=45, ha='right')

        # Add value labels on the bars
        for i, v in enumerate(job_title_counts.values):
            ax.text(i, v, str(v), ha='center', va='bottom')
        
        # Adjust layout to prevent cutoff
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_company_bar(self):
        company_counts = self.data['Company Name'].value_counts().head(10)
        
        fig, ax = plt.subplots(figsize=(12, 9))
        bars = ax.bar(range(len(company_counts)), company_counts.values)
        ax.set_title('Top 10 Companies by Applications')
        ax.set_ylabel('Number of Applications')
        
        # Wrap x-axis labels
        wrapped_labels = [textwrap.fill(label, width=20) for label in company_counts.index]
        ax.set_xticks(range(len(company_counts)))
        ax.set_xticklabels(wrapped_labels, rotation=45, ha='right')
        
        # Add value labels on the bars
        for i, v in enumerate(company_counts.values):
            ax.text(i, v, str(v), ha='center', va='bottom')
        
        # Adjust layout to prevent cutoff
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_term_bar(self):
        term_counts = self.data['Term'].value_counts()
        
        fig, ax = plt.subplots(figsize=(10, 7))
        bars = ax.bar(range(len(term_counts)), term_counts.values)
        ax.set_title('Applications by Term')
        ax.set_ylabel('Number of Applications')
        
        # Wrap x-axis labels
        wrapped_labels = [textwrap.fill(label, width=15) for label in term_counts.index]
        ax.set_xticks(range(len(term_counts)))
        ax.set_xticklabels(wrapped_labels, rotation=45, ha='right')
        
        # Add value labels on the bars
        for i, v in enumerate(term_counts.values):
            ax.text(i, v, str(v), ha='center', va='bottom')

        # Adjust layout to prevent cutoff
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_application_method_bar(self):
        method_counts = self.data['Application Method'].value_counts()
        
        fig, ax = plt.subplots(figsize=(12, 9))
        bars = ax.bar(range(len(method_counts)), method_counts.values)
        ax.set_title('Applications by Method')
        ax.set_ylabel('Number of Applications')
        
        # Wrap x-axis labels
        wrapped_labels = [textwrap.fill(label, width=15) for label in method_counts.index]
        ax.set_xticks(range(len(method_counts)))
        ax.set_xticklabels(wrapped_labels, rotation=45, ha='right')
        
        # Add value labels on the bars
        for i, v in enumerate(method_counts.values):
            ax.text(i, v, str(v), ha='center', va='bottom')

        # Adjust layout to prevent cutoff
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_resume_cover_letter_bar(self):
        resume_counts = self.data['Resume Version'].value_counts()
        cover_letter_counts = self.data['Cover Letter Version'].value_counts()

        # Preprocess labels
        resume_labels = [self.preprocess_label(label) if self.preprocess_label(label) != "" else "None" for label in resume_counts.index]
        cover_letter_labels = [self.preprocess_label(label) if self.preprocess_label(label) != "" else "None" for label in cover_letter_counts.index]
        
        # Calculate the number of bars
        n_resume = len(resume_counts)
        n_cover = len(cover_letter_counts)
        
        # Adjust figure size based on number of bars
        fig_height = max(8, (n_resume + n_cover) * 0.5)  # 0.5 inch per bar, minimum 8 inches
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, fig_height))
        
        # Resume Version chart
        bars1 = ax1.bar(range(len(resume_labels)), resume_counts.values)
        ax1.set_title('Applications by Resume Version')
        ax1.set_ylabel('Number of Applications')
        ax1.set_xlabel('Resume Version')
        
        # Cover Letter Version chart
        bars2 = ax2.bar(range(len(cover_letter_labels)), cover_letter_counts.values)
        ax2.set_title('Applications by Cover Letter Version')
        ax2.set_ylabel('Number of Applications')
        ax2.set_xlabel('Cover Letter Version')
        
        # Add value labels on the bars and set x-axis labels
        for ax, labels in zip([ax1, ax2], [resume_labels, cover_letter_labels]):
            for i, v in enumerate(ax.containers[0]):
                ax.text(i, v.get_height(), str(v.get_height()), ha='center', va='bottom')
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
        
        # Adjust layout to prevent cutoff
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def create_status_stacked_area(self):
        self.data['Application Date'] = pd.to_datetime(self.data['Application Date'])
        status_over_time = self.data.pivot_table(
            index='Application Date', 
            columns='Status', 
            values='Index', 
            aggfunc='count'
        ).fillna(0).cumsum()
        
        fig, ax = plt.subplots(figsize=(12, 9))
        ax.stackplot(status_over_time.index, status_over_time.T, labels=status_over_time.columns)
        ax.set_title('Application Statuses Over Time')
        ax.set_xlabel('Date')
        ax.set_ylabel('Number of Applications')
        
        # Set x-axis ticks to be 10 days apart
        start_date = status_over_time.index.min()
        end_date = status_over_time.index.max()
        date_range = pd.date_range(start=start_date, end=end_date, freq='10D')
        ax.set_xticks(date_range)
        ax.set_xticklabels(date_range.strftime('%Y-%m-%d'), rotation=45, ha='right')
        
        # Wrap legend labels
        handles, labels = ax.get_legend_handles_labels()
        wrapped_labels = [textwrap.fill(label, width=15) for label in labels]
        ax.legend(handles, wrapped_labels, loc='upper left')
        
        plt.tight_layout()
        
        canvas = FigureCanvas(fig)
        return fig, canvas
    
    def create_industry_pie(self):
        industry_counts = self.data['Industry'].value_counts()
        industry_counts = self.group_small_values(industry_counts, threshold=3)
        
        fig, ax = plt.subplots(figsize=(10, 7))
        colors = plt.cm.Set3(np.linspace(0, 1, len(industry_counts)))
        wedges, texts, autotexts = ax.pie(industry_counts.values, colors=colors, autopct=lambda pct: f"{pct:.1f}%\n({int(pct/100.*sum(industry_counts))})", pctdistance=0.75)
        
        ax.set_title('Applications by Industry')
        
        # Add legend
        ax.legend(wedges, industry_counts.index,
                title="Industries",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1))
        
        plt.setp(autotexts, size=8, weight="bold")
        ax.set_aspect("equal")
        
        canvas = FigureCanvas(fig)
        return fig, canvas

    def update_dashboard(self):
        # Close all existing figures
        plt.close('all')

        # Get the dashboard widget and its layout
        dashboard_widget = self.tab_widget.widget(1)
        dashboard_layout = dashboard_widget.layout()

        # Get the scroll area and its content widget
        scroll_area = dashboard_layout.itemAt(0).widget()
        scroll_content = scroll_area.widget()
        scroll_layout = scroll_content.layout()

        # Remove old widgets from the scroll layout
        for i in reversed(range(scroll_layout.count())): 
            widget = scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Recreate plots with updated data
        self.status_pie_fig, status_pie_canvas = self.create_status_pie()
        self.company_bar_fig, company_bar_canvas = self.create_company_bar()
        self.timeline_line_fig, timeline_line_canvas = self.create_timeline_line()
        self.job_title_bar_fig, job_title_bar_canvas = self.create_job_title_bar()
        self.term_bar_fig, term_bar_canvas = self.create_term_bar()
        self.application_method_bar_fig, application_method_bar_canvas = self.create_application_method_bar()
        self.resume_cover_letter_bar_fig, resume_cover_letter_bar_canvas = self.create_resume_cover_letter_bar()
        self.status_stacked_area_fig, status_stacked_area_canvas = self.create_status_stacked_area()
        self.industry_pie_fig, industry_pie_canvas = self.create_industry_pie()

        # Create new scalable graph widgets
        status_pie_widget = ScalableGraphWidget(self.status_pie_fig, status_pie_canvas, 'Applications by Status', fixed_height=500, legend=True)
        company_bar_widget = ScalableGraphWidget(self.company_bar_fig, company_bar_canvas, 'Top Companies by Applications', fixed_height=1000)
        timeline_line_widget = ScalableGraphWidget(self.timeline_line_fig, timeline_line_canvas, 'Applications Over Time', fixed_height=800)
        job_title_bar_widget = ScalableGraphWidget(self.job_title_bar_fig, job_title_bar_canvas, 'Top 10 Job Postitions', fixed_height=1000)
        term_bar_widget = ScalableGraphWidget(self.term_bar_fig, term_bar_canvas, 'Applications by Term', fixed_height=800)
        application_method_bar_widget = ScalableGraphWidget(self.application_method_bar_fig, application_method_bar_canvas, 'Applications by Method', fixed_height=1000)
        resume_cover_letter_bar_widget = ScalableGraphWidget(self.resume_cover_letter_bar_fig, resume_cover_letter_bar_canvas, 'Applications by Resume and Cover Letter Version', fixed_height=1200)
        status_stacked_area_widget = ScalableGraphWidget(self.status_stacked_area_fig, status_stacked_area_canvas, 'Application Statuses Over Time', fixed_height=600)
        industry_pie_widget = ScalableGraphWidget(self.industry_pie_fig, industry_pie_canvas, 'Applications by Industry', fixed_height=500, legend=True)

        # Add new scalable graph widgets to the scroll layout
        scroll_layout.addWidget(status_pie_widget)
        scroll_layout.addWidget(company_bar_widget)
        scroll_layout.addWidget(timeline_line_widget)
        scroll_layout.addWidget(job_title_bar_widget)
        scroll_layout.addWidget(term_bar_widget)
        scroll_layout.addWidget(application_method_bar_widget)
        scroll_layout.addWidget(resume_cover_letter_bar_widget)
        scroll_layout.addWidget(status_stacked_area_widget)
        scroll_layout.addWidget(industry_pie_widget)

        # Update the scroll area
        scroll_area.setWidget(scroll_content)
    
    def preprocess_label(self, label):
        parts = label.split('.')
        if len(parts) > 1:
            # If it's a filename with extension, get rid of the extension
            label = parts[0]
        # Split the file name to keep the date only
        parts = label.split('_')
        return '/'.join(parts[-3:])
    
    def group_small_values(self, data, threshold=3):
        mask = data >= threshold
        main_data = data[mask]
        other_data = data[~mask]
        
        if other_data.sum() > 0:
            return pd.concat([main_data, pd.Series({'Other': other_data.sum()})])
        else:
            return main_data
        
class ScalableGraphWidget(QWidget):
    def __init__(self, fig, canvas, title, fixed_height=400, legend=False):
        super().__init__()
        self.fig = fig
        self.canvas = canvas
        self.title = title
        self.fixed_height = fixed_height
        self.legend = legend
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel(title))
        self.layout.addWidget(self.canvas)
        
        # Set fixed height for the canvas
        self.canvas.setFixedHeight(self.fixed_height)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = event.size().width() - 20  # Subtract 20 for layout margins
        self.canvas.setFixedWidth(width)
        
        # Calculate the new figure size while maintaining the aspect ratio
        current_width, current_height = self.fig.get_size_inches()
        aspect_ratio = current_width / current_height
        new_width = width / self.fig.dpi
        new_height = self.fixed_height / self.fig.dpi
        
        self.fig.set_size_inches(new_width, new_height)
        if self.legend:
            self.fig.subplots_adjust(right=0.7)
        self.canvas.draw()

    def sizeHint(self):
        return QSize(500, self.fixed_height + 50)  # Add 30 for the title label
    
    def closeEvent(self, event):
        plt.close(self.fig)
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tracker = JobApplicationTracker()
    tracker.show()
    sys.exit(app.exec())