import fitz  

# Path to PDF and output text file
pdf_path = "airpods2.pdf"
txt_output_path = "airpods2.txt"

# Open the PDF file
with fitz.open(pdf_path) as pdf:
    # Open the output text file in write mode
    with open(txt_output_path, "w", encoding="utf-8") as txt_file:
        # Loop through each page and extract text
        for page_num in range(pdf.page_count):
            page = pdf[page_num]
            text = page.get_text()
            txt_file.write(text)
            txt_file.write("\n")  # Separate pages with a newline

print(f"Text extracted and saved to {txt_output_path}")