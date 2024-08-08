import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import DateEntry
import sqlite3
import os
import shutil

class HealthRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Meeran's Health Records")
        self.conn = sqlite3.connect("health_records.db")
        self.create_table()

        self.current_record_index = 0
        self.records = []
        self.view_mode = True

        # Patient details
        self.patient_name = tk.StringVar()
        self.patient_age = tk.StringVar()
        self.patient_sex = tk.StringVar()
        self.existing_disease = tk.StringVar()
        self.allergy = tk.StringVar()

        # Get patient details on the first run
        self.get_patient_details()

        # Frames setup
        self.setup_frames()

        # Initialize the uploaded document list 
        self.setup_uploaded_documents_list()

        # Load records
        self.load_records()

        # Update record counter initially
        self.update_record_count()

        # Update medical history after widgets are initialized
        self.update_medical_history()

    def setup_frames(self):
        # Create frames
        self.left_frame = ttk.Frame(self.root, padding=(10, 10))
        self.left_frame.grid(row=0, column=0, sticky="ns", rowspan=4) 
        self.center_frame = ttk.Frame(self.root, padding=(10, 10))
        self.center_frame.grid(row=0, column=1, sticky="nsew", rowspan=4)
        self.right_frame = ttk.Frame(self.root, padding=(10, 10))
        self.right_frame.grid(row=0, column=2, sticky="nsew", rowspan=4)

        # Set column and row weights to make them resizable
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.columnconfigure(2, weight=2)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=1)
        self.root.rowconfigure(3, weight=1)

        # Setup left frame buttons
        self.setup_buttons()

        # Setup center frame input fields
        self.setup_input_fields()

        # Setup right frame text display
        self.setup_record_display()

        # Setup medical history display
        self.setup_medical_history()

    def setup_buttons(self):
        # Buttons setup
        buttons = [
            ("New", self.new_record),
            ("View", self.toggle_view_mode),
            ("Edit", self.edit_record),
            ("Save", self.save_record),
            ("Delete", self.delete_record),
            ("Upload", self.upload_document),
            ("Download", self.download_document),
            ("Close", self.root.quit),
        ]
        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.left_frame, text=text, command=command).grid(row=i, column=0, sticky="ew", pady=5)

        self.scroll_buttons_frame = ttk.Frame(self.left_frame)
        self.scroll_buttons_frame.grid(row=len(buttons), column=0, sticky="ew", pady=5)
        ttk.Button(self.scroll_buttons_frame, text="\u25b2", command=self.scroll_up).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(self.scroll_buttons_frame, text="\u25bc", command=self.scroll_down).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.record_counter_label = ttk.Label(self.left_frame, text="Record: 001 of 001", font=("Helvetica", 10, "bold"))
        self.record_counter_label.grid(row=len(buttons) + 1, column=0, sticky="ew", pady=5)

    def setup_input_fields(self):
        # Create input fields
        labels = [
            "Date", "Complaint", "Doctor", "Investigation",
            "Diagnosis", "Medication", "Notes", "Follow-up"
        ]
        self.input_boxes = {}
        for i, label_text in enumerate(labels):
            ttk.Label(self.center_frame, text=f"{label_text}:", font=("Helvetica", 10, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            if label_text == "Date":
                self.input_boxes[label_text] = DateEntry(self.center_frame, width=17, background='darkblue', foreground='white', borderwidth=2)
            else:
                self.input_boxes[label_text] = tk.Text(self.center_frame, height=1, width=50)
                self.input_boxes[label_text].bind("<FocusIn>", self.on_focus_in)
                self.input_boxes[label_text].bind("<FocusOut>", self.on_focus_out)
            self.input_boxes[label_text].grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            self.input_boxes[label_text].config(state="disabled")

    def setup_record_display(self):
        # Record display setup
        ttk.Label(self.right_frame, text="Medical Record", font=("Helvetica", 14, "bold")).pack(anchor="center")
        self.record_details_text = tk.Text(self.right_frame, wrap="word", height=25, width=45)
        self.record_details_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.record_details_text.config(state="disabled")

    def setup_uploaded_documents_list(self):
        # Setup the listbox to display uploaded documents
        ttk.Label(self.right_frame, text="Uploaded Documents", font=("Helvetica", 12, "bold")).pack(anchor="center", pady=10)
        self.uploaded_documents_list = tk.Listbox(self.right_frame, height=5, width=30)
        self.uploaded_documents_list.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.uploaded_documents_list.bind("<<ListboxSelect>>", self.on_record_selection)

    def setup_medical_history(self):
        # Medical history display setup
        self.history_frame = ttk.LabelFrame(self.center_frame, text="Brief Medical History", padding=(5, 5) )
        self.history_frame.grid(row=15, column=0, columnspan=2, sticky="ew", padx=5, pady=10)  # Moved to row 9

        self.medical_history_text = tk.Text(self.history_frame, wrap="word", height=5, width=50)
        self.medical_history_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.medical_history_text.config(state="disabled")

    def on_focus_in(self, event):
        widget = event.widget
        widget.config(height=5)

    def on_focus_out(self, event):
        widget = event.widget
        widget.config(height=1)

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    complaint TEXT,
                    doctor TEXT,
                    investigation TEXT,
                    diagnosis TEXT,
                    medication TEXT,
                    notes TEXT,
                    follow_up TEXT,
                    document_path TEXT
                )
            """)
            # Create table for patient details if it doesn't exist
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS patient_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    age INTEGER,
                    sex TEXT,
                    existing_disease TEXT,
                    allergy TEXT
                )
            """)

    def new_record(self):
        for input_box in self.input_boxes.values():
            input_box.delete(0, tk.END) if isinstance(input_box, tk.Entry) else input_box.delete(1.0, tk.END)
        self.record_details_text.delete(1.0, tk.END)
        self.view_mode = False
        self.update_view_mode()
        self.current_record_index = len(self.records)  

    def toggle_view_mode(self):
        self.view_mode = not self.view_mode
        self.update_view_mode()
        self.update_display()

    def update_view_mode(self):
        if self.view_mode:
            for input_box in self.input_boxes.values():
                input_box.config(state="disabled")
            self.record_details_text.config(state="normal")
        else:
            for input_box in self.input_boxes.values():
                input_box.config(state="normal")
            self.record_details_text.config(state="disabled")

    def edit_record(self):
        if self.view_mode:
            self.toggle_view_mode()

    def clear_record_details(self):
        self.record_details_text.delete(1.0, tk.END)

    def update_display(self):
        self.load_record_details()
        self.load_uploaded_documents()  

    def delete_record(self):
        if self.records:  
            # Get the record ID correctly
            record_id = self.records[self.current_record_index][0]

            # Delete associated documents
            with self.conn:
                cursor = self.conn.execute("SELECT document_path FROM health_records WHERE id = ?", (record_id,))
                document_path = cursor.fetchone()[0]
                if document_path and os.path.exists(document_path):
                    os.remove(document_path)

            # Delete the record from the database
            with self.conn:
                self.conn.execute("DELETE FROM health_records WHERE id = ?", (record_id,))
                self.conn.commit()

            # Update the listbox and records
            self.uploaded_documents_list.delete(0, tk.END)
            self.load_records()
            self.update_record_count()

            # Adjust the current record index if necessary
            if self.current_record_index >= len(self.records):
                self.current_record_index = len(self.records) - 1

            # Update the display to reflect changes
            self.update_display()

    def save_record(self):
        record_details = self.get_record_details_from_ui()
        if not any(record_details.values()):
            print("Cannot save an empty record.")
            return

        if not self.view_mode:
            if self.current_record_index >= len(self.records):
                # If it's a new record
                with self.conn:
                    query = """
                        INSERT INTO health_records (date, complaint, doctor, investigation, diagnosis, medication, notes, follow_up)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    self.conn.execute(query, tuple(record_details.values()))
                    self.conn.commit()
                self.load_records()  # Refresh records
                self.current_record_index = len(self.records) - 1  # Go to the new record
            else:
                # If it's an existing record
                record_id = self.records[self.current_record_index][0]
                with self.conn:
                    query = """
                        UPDATE health_records SET
                        date = ?,
                        complaint = ?,
                        doctor = ?,
                        investigation = ?,
                        diagnosis = ?,
                        medication = ?,
                        notes = ?,
                        follow_up = ?
                        WHERE id = ?
                    """
                    self.conn.execute(query, (*record_details.values(), record_id))
                    self.conn.commit()

        self.toggle_view_mode()
        self.load_records()
        self.update_record_count()
        self.update_display()

    def upload_document(self):
        file_paths = filedialog.askopenfilenames()
        for file_path in file_paths:
            if file_path:
                if not os.path.exists('uploaded_docs'):
                    os.makedirs('uploaded_docs')
                destination_path = os.path.join('uploaded_docs', os.path.basename(file_path))
                shutil.copyfile(file_path, destination_path)
                # Associate the uploaded document with the current record
                if not self.view_mode:  # Only allow uploads when in edit mode
                    record_id = self.records[self.current_record_index][0]
                    with self.conn:
                        self.conn.execute("UPDATE health_records SET document_path = ? WHERE id = ?", (destination_path, record_id))
                        self.conn.commit()
                # Update the document list for the current record
                self.load_uploaded_documents()
                self.update_display()

    def download_document(self):
        if (selected_index := self.uploaded_documents_list.curselection()):
            record_id = int(self.uploaded_documents_list.get(selected_index[0]).split(":")[0])
            with self.conn:
                cursor = self.conn.execute("SELECT document_path FROM health_records WHERE id = ?", (record_id,))
                document_path = cursor.fetchone()[0]
            if document_path:
                save_path = filedialog.asksaveasfilename(defaultextension=".txt")
                if save_path:
                    shutil.copy(document_path, save_path)

    def scroll_down(self):
        if self.current_record_index < len(self.records) - 1:
            self.current_record_index += 1
        self.update_display()
        self.update_record_count()

    def scroll_up(self):
        if self.current_record_index > 0:
            self.current_record_index -= 1
        self.update_display()
        self.update_record_count()

    def load_records(self):
        self.records = []
        with self.conn:
            cursor = self.conn.execute("SELECT id, date FROM health_records")
            for row in cursor.fetchall():
                self.records.append(row)
        self.update_record_count()
        self.current_record_index = len(self.records) - 1 if self.records else 0
        self.load_record_details()

    def load_uploaded_documents(self):
        self.uploaded_documents_list.delete(0, tk.END)
        # Only display documents associated with the current record
        if self.current_record_index >= 0 and self.current_record_index < len(self.records):
            record_id = self.records[self.current_record_index][0]
            with self.conn:
                cursor = self.conn.execute("SELECT document_path FROM health_records WHERE id = ?", (record_id,))
                if (record := cursor.fetchone()):
                    document_path = record[0]
                    if document_path:
                        # Display only the filename
                        filename = os.path.basename(document_path)
                        self.uploaded_documents_list.insert(tk.END, filename)

    def load_record_details(self):
        self.record_details_text.delete(1.0, tk.END)
        if self.view_mode and self.current_record_index >= 0 and self.current_record_index < len(self.records):
            record_id = self.records[self.current_record_index][0]
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM health_records WHERE id = ?", (record_id,))
                if (record := cursor.fetchone()):
                    labels = ["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]
                    for label, value in zip(labels, record[1:]):
                        self.record_details_text.insert(tk.END, f"{label}: {value}\n\n")
                    # Load and display uploaded documents
                    self.load_uploaded_documents()

    def get_record_details_from_ui(self):
        return {label: input_box.get("1.0", tk.END).strip() if isinstance(input_box, tk.Text) else input_box.get().strip() for label, input_box in self.input_boxes.items()}

    def on_record_selection(self, event):
        if (selected_index := self.uploaded_documents_list.curselection()):
            self.current_record_index = selected_index[0]
            self.update_display()

    def update_record_count(self):
        record_count = len(self.records)
        current_record_number = self.current_record_index + 1
        self.record_counter_label.config(text=f"Record: {current_record_number:03} of {record_count:03}")

    def get_patient_details(self):
        with self.conn:
            cursor = self.conn.execute("SELECT * FROM patient_details")
            patient_data = cursor.fetchone()

        if patient_data is None:
            # Prompt for details using a form
            self.patient_details_form()
        else:
            # Load existing details
            self.patient_name.set(patient_data[1])
            self.patient_age.set(patient_data[2])
            self.patient_sex.set(patient_data[3])
            self.existing_disease.set(patient_data[4])
            self.allergy.set(patient_data[5])

    def patient_details_form(self):
        form_window = tk.Toplevel(self.root)
        form_window.title("Enter Patient Details")

        labels = ["Name:", "Age:", "Sex:", "Existing Diseases:", "Allergies:"]
        entries = []

        for i, label in enumerate(labels):
            ttk.Label(form_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_window)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            entries.append(entry)

        def save_details():
            self.patient_name.set(entries[0].get())
            self.patient_age.set(entries[1].get())
            self.patient_sex.set(entries[2].get())
            self.existing_disease.set(entries[3].get())
            self.allergy.set(entries[4].get())

            # Save details to the database
            with self.conn:
                self.conn.execute(
                    """INSERT INTO patient_details (name, age, sex, existing_disease, allergy) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (self.patient_name.get(), self.patient_age.get(), self.patient_sex.get(),
                     self.existing_disease.get(), self.allergy.get()),
                )
            form_window.destroy()

        save_button = ttk.Button(form_window, text="Save", command=save_details)
        save_button.grid(row=len(labels), column=0, columnspan=2, pady=10)

        form_window.wait_window() # Wait for the form to be closed

    def update_medical_history(self):
        self.medical_history_text.config(state="normal")
        self.medical_history_text.delete(1.0, tk.END)
        self.medical_history_text.insert(tk.END, f"Name: {self.patient_name.get()}\n")
        self.medical_history_text.insert(tk.END, f"Age: {self.patient_age.get()}\n")
        self.medical_history_text.insert(tk.END, f"Sex: {self.patient_sex.get()}\n")
        self.medical_history_text.insert(tk.END, f"Existing Diseases: {self.existing_disease.get()}\n")
        self.medical_history_text.insert(tk.END, f"Allergies: {self.allergy.get()}")
        self.medical_history_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = HealthRecordApp(root)
    root.resizable(True, True) 
    root.mainloop()