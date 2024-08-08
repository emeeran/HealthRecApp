import tkinter as tk
from tkinter import ttk, filedialog
from tkcalendar import DateEntry
import sqlite3
import os
import shutil
import csv

class HealthRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Health Records System")

        # Database setup
        self.db_path = "health_records.db"
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

        # Record management
        self.current_patient_id = None
        self.current_record_id = None
        self.patients = []
        self.records = []
        self.view_mode = True

        # GUI setup
        self.setup_gui()
        self.load_patients()

    def setup_gui(self):
        self.setup_frames()
        self.setup_patient_list()
        self.setup_buttons()
        self.setup_input_fields()
        self.setup_record_display()
        self.setup_uploaded_documents_list()

    def setup_frames(self):
        self.left_frame = self.create_frame(self.root, 0, 0)
        self.center_frame = self.create_frame(self.root, 0, 1)
        self.right_frame = self.create_frame(self.root, 0, 2)

        for i in range(3):
            self.root.columnconfigure(i, weight=2 if i else 1)
            self.root.rowconfigure(i, weight=1)

    def create_frame(self, parent, row, col, rowspan=1):
        frame = ttk.Frame(parent, padding=(10, 10))
        frame.grid(row=row, column=col, sticky="nsew", rowspan=rowspan)
        return frame

    def setup_patient_list(self):
        ttk.Label(self.left_frame, text="Patients", font=("Helvetica", 12, "bold")).pack()

        self.patient_listbox = tk.Listbox(self.left_frame, width=30)
        self.patient_listbox.pack(expand=True, fill=tk.BOTH)
        self.patient_listbox.bind("<<ListboxSelect>>", self.on_patient_select)

    def setup_buttons(self):
        buttons = [
            ("New Patient", self.new_patient),
            ("New Record", self.new_record),
            ("View", self.toggle_view_mode),
            ("Edit", self.edit_record),
            ("Save", self.save_record),
            ("Delete Record", self.delete_record),
            ("Upload", self.upload_document),
            ("Download", self.download_document),
            ("Export to CSV", self.export_to_csv),
            ("Import from CSV", self.import_from_csv),
        ]

        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack()

        for i, (text, command) in enumerate(buttons):
            ttk.Button(button_frame, text=text, command=command, width=15).grid(row=i // 2, column=i % 2, pady=5, padx=5)

        # Frame for Close and Scroll buttons
        bottom_frame = ttk.Frame(self.left_frame)
        bottom_frame.pack(pady=5)

        # Close Button
        ttk.Button(bottom_frame, text="Close", command=self.root.quit, width=15).pack(side=tk.LEFT, padx=5)

        # Scroll Buttons Frame
        scroll_frame = ttk.Frame(bottom_frame) 
        scroll_frame.pack(side=tk.LEFT) 

        # Scroll Up Button
        up_button = ttk.Button(scroll_frame, text="\u25b2", command=self.scroll_up, width=7) 
        up_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Scroll Down Button
        down_button = ttk.Button(scroll_frame, text="\u25bc", command=self.scroll_down, width=7) 
        down_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.record_counter_label = ttk.Label(self.left_frame, text="Record: 0 of 0", font=("Helvetica", 10, "bold"))
        self.record_counter_label.pack(pady=5)

    def setup_input_fields(self):
        labels = ["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]
        self.input_boxes = {label: self.create_input_field(label) for label in labels}
        for i, label in enumerate(labels):
            ttk.Label(self.center_frame, text=f"{label}:", font=("Helvetica", 10, "bold")).grid(row=i, column=0, sticky="w", padx=5, pady=5)
            self.input_boxes[label].grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            self.input_boxes[label].config(state="disabled")

    def create_input_field(self, label):
        if label == "Date":
            return DateEntry(self.center_frame, width=17, background='darkblue', foreground='white', borderwidth=2)
        else:
            text_box = tk.Text(self.center_frame, height=1, width=50, wrap="word")
            text_box.bind("<FocusIn>", self.on_focus_in)
            text_box.bind("<FocusOut>", self.on_focus_out)
            return text_box

    def setup_record_display(self):
        ttk.Label(self.right_frame, text="Medical Record", font=("Helvetica", 14, "bold")).pack(anchor="center")
        self.record_details_text = tk.Text(self.right_frame, wrap="word", height=25, width=45)
        self.record_details_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.record_details_text.config(state="disabled")

    def setup_uploaded_documents_list(self):
        ttk.Label(self.right_frame, text="Documents List", font=("Helvetica", 12, "bold")).pack(anchor="center", pady=10)
        self.uploaded_documents_list = tk.Listbox(self.right_frame, height=5, width=30)
        self.uploaded_documents_list.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.uploaded_documents_list.bind("<<ListboxSelect>>", self.on_document_selection)

    def on_focus_in(self, event):
        event.widget.config(height=5)

    def on_focus_out(self, event):
        event.widget.config(height=1)

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    date TEXT,
                    complaint TEXT,
                    doctor TEXT,
                    investigation TEXT,
                    diagnosis TEXT,
                    medication TEXT,
                    notes TEXT,
                    follow_up TEXT,
                    document_path TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)

    def new_patient(self):
        def save_patient():
            name = patient_name_entry.get()
            if name:
                with self.conn:
                    self.conn.execute("INSERT INTO patients (name) VALUES (?)", (name,))
                self.load_patients()
                add_patient_window.destroy()

        add_patient_window = tk.Toplevel(self.root)
        add_patient_window.title("Add New Patient")

        ttk.Label(add_patient_window, text="Patient Name:").grid(row=0, column=0, padx=5, pady=5)
        patient_name_entry = ttk.Entry(add_patient_window)
        patient_name_entry.grid(row=0, column=1, padx=5, pady=5)

        save_button = ttk.Button(add_patient_window, text="Save", command=save_patient)
        save_button.grid(row=1, column=1, pady=10)

    def load_patients(self):
        self.patients = []
        with self.conn:
            cursor = self.conn.execute("SELECT id, name FROM patients")
            self.patients = cursor.fetchall()

        self.patient_listbox.delete(0, tk.END)
        for patient_id, name in self.patients:
            self.patient_listbox.insert(tk.END, name)

    def on_patient_select(self, event):
        if (selection := self.patient_listbox.curselection()):
            self.current_patient_id = self.patients[selection[0]][0]
            self.load_records()
            self.update_record_display()

    def new_record(self):
        if not self.current_patient_id:
            print("Please select a patient first.")
            return

        self.current_record_id = None
        self.clear_input_fields()
        self.record_details_text.delete(1.0, tk.END)
        self.uploaded_documents_list.delete(0, tk.END)
        self.view_mode = False
        self.update_view_mode()

    def toggle_view_mode(self):
        self.view_mode = not self.view_mode
        self.update_view_mode()

    def update_view_mode(self):
        state = "normal" if not self.view_mode else "disabled"
        for input_box in self.input_boxes.values():
            input_box.config(state=state)
        self.record_details_text.config(state="normal" if self.view_mode else "disabled")

    def edit_record(self):
        if self.view_mode and self.current_record_id:
            self.toggle_view_mode()

    def clear_input_fields(self):
        for input_box in self.input_boxes.values():
            input_box.delete(0, tk.END) if isinstance(input_box, tk.Entry) else input_box.delete(1.0, tk.END)

    def delete_record(self):
        if self.current_record_id:
            with self.conn:
                cursor = self.conn.execute("SELECT document_path FROM health_records WHERE id = ?", (self.current_record_id,))
                document_path = cursor.fetchone()[0]
                if document_path and os.path.exists(document_path):
                    os.remove(document_path)
                self.conn.execute("DELETE FROM health_records WHERE id = ?", (self.current_record_id,))
            
            # Update current_record_id after deletion
            current_index = self.get_record_index(self.current_record_id)
            if current_index is not None: 
                self.current_record_id = self.records[current_index][0] if current_index < len(self.records) else None
            else:
                self.current_record_id = None
            self.load_records()
            self.update_record_display()

    def save_record(self):
        if not self.current_patient_id:
            print("Please select a patient first.")
            return

        record_details = self.get_record_details_from_ui()
        if not any(record_details.values()):
            print("Cannot save an empty record.")
            return

        with self.conn:
            if self.current_record_id:
                # Update existing record
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
                self.conn.execute(query, (*record_details.values(), self.current_record_id))
            else:
                # Insert new record
                query = """
                    INSERT INTO health_records (patient_id, date, complaint, doctor, investigation, diagnosis, medication, notes, follow_up)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor = self.conn.execute(query, (self.current_patient_id, *record_details.values()))
                self.current_record_id = cursor.lastrowid

        self.load_records()
        self.update_record_display()
        self.toggle_view_mode()

    def upload_document(self):
        if self.current_record_id:
            file_paths = filedialog.askopenfilenames()
            for file_path in file_paths:
                if file_path:
                    if not os.path.exists('uploaded_docs'):
                        os.makedirs('uploaded_docs')
                    destination_path = os.path.join('uploaded_docs', os.path.basename(file_path))
                    shutil.copyfile(file_path, destination_path)
                    with self.conn:
                        self.conn.execute("UPDATE health_records SET document_path = ? WHERE id = ?", (destination_path, self.current_record_id))
            self.update_record_display()
        else:
            print("No record selected to upload documents.")

    def download_document(self):
        if (selected_index := self.uploaded_documents_list.curselection()):
            document_path = self.uploaded_documents_list.get(selected_index[0])
            # Extract the actual file path from the numbered list
            document_path = document_path.split(". ", 1)[1] 
            save_path = filedialog.asksaveasfilename(defaultextension=".txt")
            if save_path:
                shutil.copy(document_path, save_path)

    def scroll_down(self):
        if self.records: 
            current_index = self.get_record_index(self.current_record_id)
            next_index = (current_index + 1) % len(self.records)
            self.current_record_id = self.records[next_index][0]
            self.update_record_display()

    def scroll_up(self):
        if self.records:
            current_index = self.get_record_index(self.current_record_id)
            previous_index = (current_index - 1) % len(self.records) 
            self.current_record_id = self.records[previous_index][0]
            self.update_record_display()

    def get_record_index(self, record_id):
        if record_id is None:
            return 0 if self.records else None
        try:
            return [record[0] for record in self.records].index(record_id)
        except ValueError:
            return 0 if self.records else None 

    def load_records(self):
        self.records = []
        if self.current_patient_id:
            with self.conn:
                cursor = self.conn.execute("SELECT id, date FROM health_records WHERE patient_id = ?", (self.current_patient_id,))
                self.records = cursor.fetchall()

        if self.records:
            self.current_record_id = self.records[0][0]
        else:
            self.current_record_id = None
        self.update_record_display()

    def update_record_display(self):
        if self.current_record_id:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM health_records WHERE id = ?", (self.current_record_id,))
                record = cursor.fetchone()
            if record:
                self.clear_input_fields()
                for i, label in enumerate(["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]):
                    value = record[i + 2]  # Offset by 2 to account for id and patient_id
                    if label == "Date":
                        self.input_boxes[label].set_date(value)
                    else:
                        self.input_boxes[label].insert(1.0, value)

                self.record_details_text.config(state="normal")
                self.record_details_text.delete(1.0, tk.END)
                labels = ["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]
                for label, value in zip(labels, record[2:]):  # Display from "Date" onwards
                    self.record_details_text.insert(tk.END, f"{label}: {value}\n\n")
                self.record_details_text.config(state="disabled")

                # Update uploaded documents list
                self.uploaded_documents_list.delete(0, tk.END)
                if document_path := record[10]:  # Index 10 for document_path
                    file_name = os.path.basename(document_path)  # Get file name
                    self.uploaded_documents_list.insert(tk.END, f"{len(self.uploaded_documents_list.get(0, tk.END)) + 1}. {file_name}") 
        else:
            self.clear_input_fields()
            self.record_details_text.delete(1.0, tk.END)
            self.uploaded_documents_list.delete(0, tk.END)

        # Update record counter
        self.record_counter_label.config(text=f"Record: {self.get_record_index(self.current_record_id) + 1 if self.current_record_id else 0} of {len(self.records)}")

    def get_record_details_from_ui(self):
        return {label: input_box.get("1.0", tk.END).strip() if isinstance(input_box, tk.Text) else input_box.get().strip() for label, input_box in self.input_boxes.items()}

    def on_document_selection(self, event):
        if (selection := self.uploaded_documents_list.curselection()):
            selected_item = self.uploaded_documents_list.get(selection[0])
            # Extract the actual file path from the numbered list
            document_path = selected_item.split(". ", 1)[1] 
            try:
                with open(document_path, 'r') as file:
                    content = file.read()
                self.record_details_text.config(state="normal")
                self.record_details_text.delete(1.0, tk.END)
                self.record_details_text.insert(tk.END, content)
                self.record_details_text.config(state="disabled")
            except FileNotFoundError:
                print(f"File not found: {document_path}")

    def export_to_csv(self):
        if not self.current_patient_id:
            print("Please select a patient first.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if save_path:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM health_records WHERE patient_id = ?", (self.current_patient_id,))
                rows = cursor.fetchall()
            with open(save_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Patient ID', 'Date', 'Complaint', 'Doctor', 'Investigation', 'Diagnosis', 'Medication', 'Notes', 'Follow-up', 'Document Path'])
                writer.writerows(rows)
            print(f"Records exported to {save_path}")

    def import_from_csv(self):
        if not self.current_patient_id:
            print("Please select a patient first.")
            return

        file_path = filedialog.askopenfilename(
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if file_path:
            try:
                with open(file_path, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader)  # Skip the header row

                    for row in reader:
                        if len(row) == 11:
                            with self.conn:
                                self.conn.execute(
                                    """
                                    INSERT INTO health_records (patient_id, date, complaint, doctor, investigation, diagnosis, medication, notes, follow_up, document_path) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (self.current_patient_id, *row[2:]),
                                )
                        else:
                            print(f"Skipping row due to incorrect column count: {row}")

                self.load_records()
                self.update_record_display()
                print(f"Records imported from {file_path}")

            except FileNotFoundError:
                print(f"File not found: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthRecordApp(root)
    root.resizable(True, True)
    root.mainloop()