import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Scrollbar
from openai import OpenAI
import pandas as pd
from pprint import pprint
import fitz  #PyMuPDF
from fpdf import FPDF
from PyPDF2 import PdfFileMerger

# Initialize OpenAI client
client = OpenAI(api_key="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")

# Create a new FPDF object
pdf = FPDF()

def write_pdf(text,selectedItems):
    # Set the font and font size
    pdf.set_font('Arial', size=12)

    # Add a new page to the PDF
    for i in selectedItems:
        pdf.add_page()

    # Write the text to the PDF
    pdf.write(5, text)

def extract_questions_from_pdf(file_path):
    questions = []
    try:
        # Open the PDF file
        pdf_document = fitz.open(file_path)
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text = page.get_text("text")
            # Add page number for each question
            formatted_text = f"Page {page_num + 1}:\n{text}"
            questions.append(formatted_text)
    except Exception as e:
        messagebox.showerror("Error", f"Error reading PDF file: {e}")
        return None
    return questions

def send_question(questions):
    global ans
    try:
        # Request completion from OpenAI for each question
        for question in questions:
            completion = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                temperature=0
            )
            ans = eval(completion.choices[0].message.content)
            
    except Exception as e:
        messagebox.showerror("Error", f"Error requesting completion from OpenAI: {e}")
        return None
    return ans

def create_qdict():
    global system_prompt

    # System prompt providing instructions
    system_prompt = 'The file uploaded is a CBSE curriculum Question Paper, of which the grade is mentioned. For that grade, look up the CBSE syllabus for the current year on the official CBSE website. Once you have the syllabus, identify the chapters that correspond to the questions in the question paper. These exact chapter names must be used. Create a dictionary in the format {Question Number:[Chapter name, Possible subtopic]} where a key value pair has to be made for each question. In this dictionary, each key is a question number, and the value is a list containing the chapter name and possible subtopic related to that question. Note that the key must be an integer.'

    # Create GUI window
    window = tk.Tk()
    window.title("CBSE Curriculum Question Paper Analysis")
    window.geometry("800x600")
    window.configure(bg="#f0f0f0")
    click_label = tk.Label(window, text="Upload Question Paper and Marklist to get started!", bg="#f0f0f0", font=("Arial", 14))
    click_label.pack(pady=10)

    # Function to handle the "Next" button click event
    def next_click():
        selected_indices = listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one question, or upload a file.")
            return
        selected_questions = [listbox.get(i) for i in selected_indices]
        answers = send_question(selected_questions)
        if answers:
            #messagebox.showinfo("Answers", "\n".join(answers))
            print(answers)

        count=1       
        for value in range(2,7):
            listtemp=answers[count]
            listtemp.append(average[value])
            count+=1

        level={"CRITICAL":[],"WEAK":[],"MODERATE":[],"GOOD":[],"EXCELLENT":[]}
        for question in answers.keys():
            temp=answers[question][2]
            if temp<=30:
                level["CRITICAL"].append(answers[question][0])
            elif temp<=50:
                level["WEAK"].append(answers[question][0])
            elif temp<=70:
                level["MODERATE"].append(answers[question][0])
            elif temp>70 and temp<90:
                level["GOOD"].append(answers[question][0])
            elif temp>=90:
                level["EXCELLENT"].append(answers[question][0])

            listbox.delete(0, tk.END)
            for key in level:
                listbox.insert(tk.END, key, level[key], '\n')

        #messagebox.showinfo("Answers", "\n".join(answers))
    def create_notes():
        system_prompt2= 'Generate comprehensive study notes and practice questions for each chapter. The notes should cover key concepts, explanations, and examples in a clear and concise manner. Include practice questions with answers to reinforce understanding and application of the concepts. The notes should be structured and organized to aid in effective studying and revision.'
        selected_indices = listbox.curselection()
        selectedItems = []
        for index in selected_indices:
            selectedItems.append(str(listbox.get(index)))
        print(selectedItems)
        #gpt
        try:
            for chapter in selectedItems: # Request notes generation from OpenAI based on chapter, grade, and CBSE curriculum
                completion = client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {'role': 'system', 'content': system_prompt2},
                        {'role': 'user', 'content': chapter}
                    ],
                    temperature=0                )
                write_pdf(completion.choices[0].message.content, selectedItems)

                # Display generated notes in a dialog box popup
            '''for ch in notes:
                with open('output.txt', 'wt') as out:
                    pprint(ch, stream=out)
                print(ch)'''
                # Save the PDF
            pdf.output('output.pdf')

        except Exception as e:
            messagebox.showerror("Error", f"Error generating notes using OpenAI: {e}")

    
    # Upload button
    def upload_qp():
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            questions = extract_questions_from_pdf(file_path)
            if questions:
                listbox.delete(0, tk.END)
                for question in questions:
                    listbox.insert(tk.END, question)

    upload_qp_button = tk.Button(window, text="Upload Question Paper", command=upload_qp, bg="#007bff", fg="white", font=("Arial", 12, "bold"))
    upload_qp_button.pack(pady=10)

    def upload_excel():
        global average
        file_path = filedialog.askopenfilename(filetypes=[("EXCEL Files", "*.xlsx")])
        if file_path:
            df = pd.read_excel(file_path)
            out = df.to_numpy().tolist()
            average=out[-1]
            print(average)

    upload_excel_button = tk.Button(window, text="Upload Marklist as Excel", command=upload_excel, bg="#007bff", fg="white", font=("Arial", 12, "bold"))
    upload_excel_button.pack(pady=10)

    # Listbox to display questions
    listbox_frame = tk.Frame(window)
    listbox_frame.pack(pady=10)
    scrollbar = Scrollbar(listbox_frame, orient=tk.VERTICAL)
    listbox = Listbox(listbox_frame, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, font=("Arial", 12), bg="white", selectbackground="#007bff", width=100, height=20)
    scrollbar.config(command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Next button
    next_button = tk.Button(window, text="Chapterwise Result Analysis", command=next_click, bg="#007bff", fg="white", font=("Arial", 12, "bold"))
    next_button.pack(pady=10)

    #generate practice sheet
    create_notes_button = tk.Button(window, text="Create Practice Sheet", command=create_notes, bg="#007bff", fg="white", font=("Arial", 12, "bold"))
    create_notes_button.pack(pady=10)

    # Run the GUI main loop
    window.mainloop()

# Call the function to create the dictionary
create_qdict()
