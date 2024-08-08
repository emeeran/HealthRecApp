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
        self.root.title("Meeran's Health Records")

        # Database setup
        self.db_path = "health_records.db"
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

        # Record management
        self.current_record_id = None
        self.records = []
        self.view_mode = True

        # Patient details
        self.patient_details = {}
        self.get_patient_details()

        # GUI setup
        self.setup_gui()
        self.load_records()
        self.update_record_display()
        self.update_medical_history()

    def setup_gui(self):
        self.setup_frames()
        self.setup_buttons()
        self.setup_input_fields()
        self.setup_record_display()
        self.setup_uploaded_documents_list()
        self.setup_medical_history()

    def setup_frames(self):
        self.left_frame, self.center_frame, self.right_frame = [
            self.create_frame(self.root, row, col, rowspan=4)
            for row, col in [(0, 0), (0, 1), (0, 2)]
        ]
        for i in range(3):
            self.root.columnconfigure(i, weight=2 if i else 1)
            self.root.rowconfigure(i, weight=1)

    def create_frame(self, parent, row, col, rowspan=1):
        frame = ttk.Frame(parent, padding=(10, 10))
        frame.grid(row=row, column=col, sticky="nsew", rowspan=rowspan)
        return frame

    def setup_buttons(self):
        buttons = [
            ("New", self.new_record),
            ("View", self.toggle_view_mode),
            ("Edit", self.edit_record),
            ("Save", self.save_record),
            ("Delete", self.delete_record),
            ("Upload", self.upload_document),
            ("Download", self.download_document),
            ("Export to CSV", self.export_to_csv),
            ("Close", self.root.quit),
        ]
        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.left_frame, text=text, command=command).grid(row=i, column=0, sticky="ew", pady=5)

        self.create_scroll_buttons(len(buttons))
        self.record_counter_label = ttk.Label(self.left_frame, text="Record: 0 of 0", font=("Helvetica", 10, "bold"))
        self.record_counter_label.grid(row=len(buttons) + 1, column=0, sticky="ew", pady=5)

    def create_scroll_buttons(self, row):
        self.scroll_buttons_frame = ttk.Frame(self.left_frame)
        self.scroll_buttons_frame.grid(row=row, column=0, sticky="ew", pady=5)
        for text, command in [("\u25b2", self.scroll_up), ("\u25bc", self.scroll_down)]:
            ttk.Button(self.scroll_buttons_frame, text=text, command=command).pack(side=tk.LEFT, fill=tk.X, expand=True)

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
        ttk.Label(self.right_frame, text="Uploaded Documents", font=("Helvetica", 12, "bold")).pack(anchor="center", pady=10)
        self.uploaded_documents_list = tk.Listbox(self.right_frame, height=5, width=30)
        self.uploaded_documents_list.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.uploaded_documents_list.bind("<<ListboxSelect>>", self.on_document_selection)

    def setup_medical_history(self):
        self.history_frame = ttk.LabelFrame(self.center_frame, text="Brief Medical History", padding=(5, 5))
        self.history_frame.grid(row=15, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        self.medical_history_text = tk.Text(self.history_frame, wrap="word", height=5, width=50)
        self.medical_history_text.pack(expand=True, fill="both", padx=5, pady=5)
        self.medical_history_text.config(state="disabled")

    def on_focus_in(self, event):
        event.widget.config(height=5)

    def on_focus_out(self, event):
        event.widget.config(height=1)

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
            self.load_records()
            self.update_record_display()

    def save_record(self):
        record_details = self.get_record_details_from_ui()
        if not any(record_details.values()):
            print("Cannot save an empty record.")
            return

        with self.conn:  # Move with statement here
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
                    INSERT INTO health_records (date, complaint, doctor, investigation, diagnosis, medication, notes, follow_up)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor = self.conn.execute(query, tuple(record_details.values()))
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
            save_path = filedialog.asksaveasfilename(defaultextension=".txt")
            if save_path:
                shutil.copy(document_path, save_path)

    def scroll_down(self):
        if self.current_record_id:
            current_index = [record[0] for record in self.records].index(self.current_record_id)
            if current_index < len(self.records) - 1:
                self.current_record_id = self.records[current_index + 1][0]
                self.update_record_display()

    def scroll_up(self):
        if self.current_record_id:
            current_index = [record[0] for record in self.records].index(self.current_record_id)
            if current_index > 0:
                self.current_record_id = self.records[current_index - 1][0]
                self.update_record_display()

    def load_records(self):
        self.records = []
        with self.conn:
            cursor = self.conn.execute("SELECT id, date FROM health_records")
            self.records = cursor.fetchall()
        if self.records and not self.current_record_id:
            self.current_record_id = self.records[0][0]

    def update_record_display(self):
        self.record_counter_label.config(text=f"Record: {len(self.records)}")
        if self.current_record_id:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM health_records WHERE id = ?", (self.current_record_id,))
                record = cursor.fetchone()
            if record:
                self.clear_input_fields()
                for i, label in enumerate(["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]):
                    value = record[i + 1] 
                    if label == "Date":
                        self.input_boxes[label].set_date(value)
                    else:
                        self.input_boxes[label].insert(1.0, value)

                self.record_details_text.config(state="normal")
                self.record_details_text.delete(1.0, tk.END)
                labels = ["Date", "Complaint", "Doctor", "Investigation", "Diagnosis", "Medication", "Notes", "Follow-up"]
                for label, value in zip(labels, record[1:]):
                    self.record_details_text.insert(tk.END, f"{label}: {value}\n\n")
                self.record_details_text.config(state="disabled")

                # Update uploaded documents list
                self.uploaded_documents_list.delete(0, tk.END)
                if document_path := record[9]:
                    self.uploaded_documents_list.insert(tk.END, document_path)
        else:
            self.clear_input_fields()
            self.record_details_text.delete(1.0, tk.END)
            self.uploaded_documents_list.delete(0, tk.END)

    def get_record_details_from_ui(self):
        return {label: input_box.get("1.0", tk.END).strip() if isinstance(input_box, tk.Text) else input_box.get().strip() for label, input_box in self.input_boxes.items()}

    def on_document_selection(self, event):
        if (selection := self.uploaded_documents_list.curselection()):
            document_path = self.uploaded_documents_list.get(selection[0])
            try:
                with open(document_path, 'r') as file:
                    content = file.read()
                self.record_details_text.config(state="normal")
                self.record_details_text.delete(1.0, tk.END)
                self.record_details_text.insert(tk.END, content)
                self.record_details_text.config(state="disabled")
            except FileNotFoundError:
                print(f"File not found: {document_path}")

    def get_patient_details(self):
        with self.conn:
            cursor = self.conn.execute("SELECT * FROM patient_details")
            patient_data = cursor.fetchone()
        if patient_data:
            self.patient_details = {
                "Name": patient_data[1],
                "Age": patient_data[2],
                "Sex": patient_data[3],
                "Existing Diseases": patient_data[4],
                "Allergies": patient_data[5]
            }
        else:
            self.patient_details_form()

    def patient_details_form(self):
        self.form_window = tk.Toplevel(self.root)
        self.form_window.title("Enter Patient Details")

        labels = ["Name:", "Age:", "Sex:", "Existing Diseases:", "Allergies:"]
        self.entries = [ttk.Entry(self.form_window) for _ in labels]

        for i, (label, entry) in enumerate(zip(labels, self.entries)):
            ttk.Label(self.form_window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")

        self.save_button = ttk.Button(self.form_window, text="Save", command=self.save_patient_details)
        self.save_button.grid(row=len(labels), column=0, columnspan=2, pady=10)

        self.form_window.wait_window()

    def save_patient_details(self):
        self.patient_details = {
            "Name": self.entries[0].get(),
            "Age": self.entries[1].get(),
            "Sex": self.entries[2].get(),
            "Existing Diseases": self.entries[3].get(),
            "Allergies": self.entries[4].get()
        }
        with self.conn:
            self.conn.execute(
                "INSERT INTO patient_details (name, age, sex, existing_disease, allergy) VALUES (?, ?, ?, ?, ?)",
                tuple(self.patient_details.values())
            )
        self.form_window.destroy()
        self.update_medical_history()

    def update_medical_history(self):
        self.medical_history_text.config(state="normal")
        self.medical_history_text.delete(1.0, tk.END)
        for key, value in self.patient_details.items():
            self.medical_history_text.insert(tk.END, f"{key}: {value}\n")
        self.medical_history_text.config(state="disabled")

    def export_to_csv(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if save_path:
            with self.conn:
                cursor = self.conn.execute("SELECT * FROM health_records")
                rows = cursor.fetchall()
            with open(save_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'Date', 'Complaint', 'Doctor', 'Investigation', 'Diagnosis', 'Medication', 'Notes', 'Follow-up', 'Document Path'])
                writer.writerows(rows)
            print(f"Records exported to {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HealthRecordApp(root)
    root.resizable(True, True)
    root.mainloop()