#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PIL import Image
import PIL
import Tkinter
import tkMessageBox
import requests
import re
import threading
import io
import PyPDF2

def start():
	logbox.delete(0, Tkinter.END)
	isbn_entry.configure(state='disabled')
	start_button.configure(state='disabled')
	threading.Thread(target=engine).start()

def engine():
	isbn = isbn_value.get()
	if len(isbn)!=12:
		tkMessageBox.showerror("Errore", "La lunghezza del codice ISBN deve essere pari a 12!", icon='error')
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
	result = tkMessageBox.askquestion("Conferma", "Sicuro di voler scaricare questo libro?\n\nISBN: "+isbn, icon='question')
	if result != 'yes':
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')

	def decrypt(data, page):
		data=data.replace('viewer._imgl('+str(page)+',"','').replace('");\nviewer._imgl('+str(page)+');','')
		data=data.decode('string_escape')
		m="fb69218f41737d7da84b1e39a949dbc2"
		arr=list(data)
		for j in range(3):
			for i in range(95,-1,-1):
				newpos=ord(m[i % 32]) % 96
				f=arr[i]
				s=arr[newpos]
				arr[i]=s
				arr[newpos] = f
		data=''.join(arr)
		return data

	def download(username, isbn, pagen):
		pageid="0"*(3-len(str(pagen)))+str(pagen)
		try:
			content=session.get("http://iflipit.mondadorieducation.it/desktop/index.php?usr="+username+"&iss="+isbn+"&fld=sdf&id="+pageid+"&ext=js").content
		except:
			download(username,isbn,pagen)
			return
		data=decrypt(content,pagen)
		pdf = io.BytesIO()
		PIL.Image.Image.save(PIL.Image.open(io.BytesIO(data)), pdf, "PDF", resoultion=100.0)
		pdf_data[pagen] = pdf.getvalue()
		
	logbox.insert(Tkinter.END, "Inizializzazione")
	session = requests.Session()

	logbox.insert(Tkinter.END, "Login")
	email = "IxPRCeyG@trashcanmail.com"
	password = "q1w2e3r4"
	html=session.get("https://www.mondadorieducation.it/app/mondadorieducation/login/loginJsonp?username="+email+"&password="+password+"&format=json&jsoncallback=jsonp11").text
	
	if not '"result":"OK"' in html:
		logbox.insert(Tkinter.END, "Login fallito")
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
		return

	logbox.insert(Tkinter.END, "Recupero informazioni")
	session.get("http://libropiuweb.mondadorieducation.it/mod_connect/login?urlRitorno=http%3A%2F%2Flibropiuweb.mondadorieducation.it%2F")
	username = re.search('"username":"(.*?)"',html).group(1)
	html=session.get("http://iflipit.mondadorieducation.it/desktop/index.php?accesslevel=st-pl&usr="+username+"&iss="+isbn+"&fil=iss").text
	try:
		npages = int(re.search('"pagesCount":(.*?),',html).group(1))
	except:
		tkMessageBox.showerror("Errore", "ISBN non valido o non disponibile", icon='error')
		logbox.insert(Tkinter.END, "ISBN non valido o non disponibile")
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
		return

	logbox.insert(Tkinter.END, "Inizio scaricamento delle pagine")

	pdf_data = {}

	pagen=1
	signal = 1
	while signal:
		for i in range(10-threading.activeCount()):
			if pagen<npages+1:
				if pagen!=1:logbox.delete(Tkinter.END)
				logbox.insert(Tkinter.END, "Stato download: "+str(pagen)+"/"+str(npages)+" ("+str(((pagen*100)/npages))+"%)")
				threading.Thread(target=download, args=(username, isbn, pagen,)).start()
				pagen+=1
			else:
				signal = 0
				break

	while 1:
		if threading.activeCount()==2:
			break

	logbox.insert(Tkinter.END, "Unione PDF")
	merger = PyPDF2.PdfFileMerger()
	for i in range(1,npages+1):
		merger.append(PyPDF2.PdfFileReader(io.BytesIO(pdf_data[i])))
	merger.write(isbn+".pdf")
	logbox.insert(Tkinter.END, "Libro scaricato con successo!")
	isbn_entry.configure(state='normal')
	start_button.configure(state='normal')

window = Tkinter.Tk()
window.geometry("300x300")
window.resizable(width=False, height=False)
window.title("ME•book Downloader v.0.1")


Tkinter.Label(text="ISBN libro:", font = "Verdana 12 bold").pack(padx=10, pady=10, anchor=Tkinter.W)
isbn_value = Tkinter.StringVar()
isbn_entry = Tkinter.Entry(window, textvariable = isbn_value)
isbn_entry.pack(padx=10, anchor=Tkinter.W)
Tkinter.Label(text="Esempio: 978880022602").pack(padx=10, anchor=Tkinter.W)
start_button = Tkinter.Button(window, text="Start", command=start)
start_button.pack(padx=10, anchor=Tkinter.E)
Tkinter.Frame(width=300, bg="black").pack(pady=20, anchor=Tkinter.W)

logbox = Tkinter.Listbox(window, bd=0)
logbox.pack(padx=10, fill=Tkinter.X)

window.mainloop()