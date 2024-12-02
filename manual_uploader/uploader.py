import os
import fitz
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database_manager import DatabaseManager
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

try:
    db_manager = DatabaseManager()
except ValueError:
    raise ValueError("Construction of the db_manager failed.")
try:
    db_manager.connect()
except ConnectionError:
    raise ConnectionError("Cannot connect to the database")

class PDFUploaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Uploader")
        self.root.geometry("600x500")
        
        # Add a label for the product name entry
        self.product_label = tk.Label(root, text="Enter Product Name:")
        self.product_label.pack(pady=5)
        
        # Create a StringVar to track the entry content
        self.product_name_var = tk.StringVar()
        self.product_name_entry = tk.Entry(root, width=50, textvariable=self.product_name_var)
        self.product_name_entry.pack(pady=5)
        
        self.load_pdf_button = tk.Button(root, text="Load PDF", command=self.load_pdf)
        self.load_pdf_button.pack(pady=10)
        
        self.load_txt_button = tk.Button(root, text="Load TXT", command=self.load_txt)
        self.load_txt_button.pack(pady=10)
        
        self.text_preview = scrolledtext.ScrolledText(root, width=70, height=20)
        self.text_preview.pack(pady=10)
        
        self.upload_button = tk.Button(root, text="Upload to Database", command=self.upload_to_db)
        self.upload_button.pack(pady=10)
        
        self.file_content = ""
        self.filename = ""

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.filename = file_path.split("/")[-1]
            try:
                with fitz.open(file_path) as pdf:
                    text = "\n".join([page.get_text() for page in pdf])
                    self.file_content = text
                    self.text_preview.delete(1.0, tk.END)
                    self.text_preview.insert(tk.END, text)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load PDF: {str(e)}")

    def load_txt(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.filename = file_path.split("/")[-1]
            try:
                with open(file_path, 'r', encoding='utf-8') as txt_file:
                    text = txt_file.read()
                    self.file_content = text
                    self.text_preview.delete(1.0, tk.END)
                    self.text_preview.insert(tk.END, text)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load TXT file: {str(e)}")

    def upload_to_db(self):
        product_name = self.product_name_var.get().strip()
        if not product_name:
            messagebox.showerror("Error", "Please enter a product name")
            return
            
        print(f"Product Name: {product_name}")
        print(f"File Content Length: {len(self.file_content)}")
        
        try:
            db_manager.add_manual(product=product_name, manual=self.file_content)
            messagebox.showinfo("Success", "Successfully uploaded to database")
            # Clear the fields after successful upload
            self.product_name_var.set("")
            self.text_preview.delete(1.0, tk.END)
            self.file_content = ""
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload to database: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFUploaderApp(root)
    root.mainloop()



