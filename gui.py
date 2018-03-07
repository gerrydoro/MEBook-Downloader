#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Adattamento PARZIALE in Python3 a cura di gerrydoro

# Sistemate le dipendenze
from PIL import Image
import PIL
import tkinter
# Tkinter -> tkinter
import tkinter.messagebox
# tkMessageBox -> tkinter.messagebox
import requests
import re
import threading
import io
import PyPDF2

def start():
	logbox.delete(0, tkinter.END)
	isbn_entry.configure(state='disabled')
	start_button.configure(state='disabled')
	threading.Thread(target=engine).start()

def engine():
	isbn = isbn_value.get()
	if len(isbn)!=12:

		tkinter.messagebox.showerror("Errore", "La lunghezza del codice ISBN deve essere pari a 12!", icon='error')
        # tkmessagebox -> tkinter.messagebox

		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
	result = tkinter.messagebox.askquestion("Conferma", "Sicuro di voler scaricare questo libro?\n\nISBN: "+isbn, icon='question')
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
			content=session.get("http://iflipit.mondadorieducation.it/desktop/index.php?usr="+username+"&iss="+isbn+"&fld=sdf&id="+pageid+"&ext=js", verify='getTestTrustPath.pem').content
            # Aggiunta verifica della catena di certificati SSL dumpati su "getTestTrustPath.pem", la mancaza di questa verifica restituiva un [SSL: CERTIFICATE_VERIFY_FAILED]
		except:
			download(username,isbn,pagen)
			return
		data=decrypt(content,pagen)
		pdf = io.BytesIO()
		PIL.Image.Image.save(PIL.Image.open(io.BytesIO(data)), pdf, "PDF", resoultion=100.0)
		pdf_data[pagen] = pdf.getvalue()
		
	logbox.insert(tkinter.END, "Inizializzazione")
	session = requests.Session()

	logbox.insert(tkinter.END, "Login")
	email = "mail@domain.com"
	password = "password"
	html=session.get("https://www.mondadorieducation.it/app/mondadorieducation/login/loginJsonp?username="+email+"&password="+password+"&format=json&jsoncallback=jsonp11", verify='getTestTrustPath.pem').text
	
	if not '"result":"OK"' in html:
		logbox.insert(tkinter.END, "Login fallito")
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
		return

	logbox.insert(tkinter.END, "Recupero informazioni")
	session.get("http://libropiuweb.mondadorieducation.it/mod_connect/login?urlRitorno=http%3A%2F%2Flibropiuweb.mondadorieducation.it%2F", verify='getTestTrustPath.pem')
	username = re.search('"username":"(.*?)"',html).group(1)
	html=session.get("http://iflipit.mondadorieducation.it/desktop/index.php?accesslevel=st-pl&usr="+username+"&iss="+isbn+"&fil=iss", verify='getTestTrustPath.pem').text
	try:
		npages = int(re.search('"pagesCount":(.*?),',html).group(1))
	except:
		tkinter.messagebox.showerror("Errore", "ISBN non valido o non disponibile", icon='error')
		logbox.insert(tkinter.END, "ISBN non valido o non disponibile")
		isbn_entry.configure(state='normal')
		start_button.configure(state='normal')
		return

        '''
        Qui il programma si ferma, probabilmente la variabile "html" non ha il contenuto aspettato
    
        Il contenuto della variabile "html" in questo momento è

        <!DOCTYPE html>
        <html class="no-js" lang="">
          <head>
            <title>HUB Scuola</title>

            <!-- font -->

            <meta http-equiv="x-ua-compatible" content="IE=Edge"/>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no"/>
            <meta name="google-site-verification" content="qcM2CnSFyttSNbZq5u8_lmRXdGm2AEeqFW3FNqZAYjw"/>

            <!-- meta http-equiv="Cache-control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="cache-control" content="max-age=0" />
            <meta http-equiv="expires" content="0" />
            <meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
            <meta http-equiv="Pragma" content="no-cache" -->

            <!-- <link rel="shortcut icon" type="image/ico" href="/favicon.ico" /> -->
            <link rel="icon" type="image/png" href="/app/images/xfavicon.png.pagespeed.ic.oz5sUKqxWf.png" sizes="16x16">
            <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,400,600,700&amp;subset=cyrillic-ext" rel="stylesheet">
            <!--<script src="js/vendor/modernizr-custom.js"></script>-->
            <script type='text/javascript' src='https://digital.mondadori.it/new-privacy-2014/newprivacypolicy.js'></script>
          <link href="/A.style.236b3a91a77ddf0e7654.css.pagespeed.cf.6C7ZnRJYwP.css" rel="stylesheet"></head>

          <body>
            <div id="app"></div>
          <script type="text/javascript" src="/bundle.236b3a91a77ddf0e7654.js.pagespeed.jm.Fvce8iICKz.js"></script></body>
        </html>

        '''

	logbox.insert(tkinter.END, "Inizio scaricamento delle pagine")

	pdf_data = {}

	pagen=1
	signal = 1
	while signal:
		for i in range(10-threading.activeCount()):
			if pagen<npages+1:
				if pagen!=1:logbox.delete(tkinter.END)
				logbox.insert(tkinter.END, "Stato download: "+str(pagen)+"/"+str(npages)+" ("+str(((pagen*100)/npages))+"%)")
				threading.Thread(target=download, args=(username, isbn, pagen,)).start()
				pagen+=1
			else:
				signal = 0
				break

	while 1:
		if threading.activeCount()==2:
			break

	logbox.insert(tkinter.END, "Unione PDF")
	merger = PyPDF2.PdfFileMerger()
	for i in range(1,npages+1):
		merger.append(PyPDF2.PdfFileReader(io.BytesIO(pdf_data[i])))
	merger.write(isbn+".pdf")
	logbox.insert(tkinter.END, "Libro scaricato con successo!")
	isbn_entry.configure(state='normal')
	start_button.configure(state='normal')

window = tkinter.Tk()
window.geometry("300x300")
window.resizable(width=False, height=False)
window.title("ME•book Downloader v.0.1")


tkinter.Label(text="ISBN libro:", font = "Verdana 12 bold").pack(padx=10, pady=10, anchor=tkinter.W)
isbn_value = tkinter.StringVar()
isbn_entry = tkinter.Entry(window, textvariable = isbn_value)
isbn_entry.pack(padx=10, anchor=tkinter.W)
tkinter.Label(text="Esempio: 978880022602").pack(padx=10, anchor=tkinter.W)
start_button = tkinter.Button(window, text="Start", command=start)
start_button.pack(padx=10, anchor=tkinter.E)
tkinter.Frame(width=300, bg="black").pack(pady=20, anchor=tkinter.W)

logbox = tkinter.Listbox(window, bd=0)
logbox.pack(padx=10, fill=tkinter.X)

window.mainloop()