import requests,re,sys, os, threading, time
import img2pdf  # https://github.com/josch/img2pdf
import PyPDF2  # https://github.com/mstamy2/PyPDF2

class downloader:
	def __init__(self):
		self.session = requests.Session()
		self.email = ""
		self.password = ""
		self.isbn = ""

	def login(self,email, password):
		print "Loggin in..."
		html=self.session.get("https://www.mondadorieducation.it/app/mondadorieducation/login/loginJsonp?username="+email+"&password="+password+"&format=json&jsoncallback=jsonp11").text
		if not '"result":"OK"' in html: sys.exit("Login failed, check your email/password!")
		print "Login successful."
		self.session.get("http://libropiuweb.mondadorieducation.it/mod_connect/login?urlRitorno=http%3A%2F%2Flibropiuweb.mondadorieducation.it%2F")
		return re.search('"username":"(.*?)"',html).group(1)

	def decrypt(self,data,page):
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

	def get_npages(self,username,isbn):
		print "Getting page count..."
		html=self.session.get("http://iflipit.mondadorieducation.it/desktop/index.php?accesslevel=st-pl&usr="+username+"&iss="+isbn+"&fil=iss").text
		return int(re.search('"pagesCount":(.*?),',html).group(1))

	def download(self,username,isbn,pagen):
		sys.stdout.write("\rDownloading page n. "+str(pagen)+"...")
		sys.stdout.flush()
		pageid="0"*(3-len(str(pagen)))+str(pagen)
		f=open("/tmp/"+isbn+"_"+str(pagen)+".jpg","wb")
		try:
			content=self.session.get("http://iflipit.mondadorieducation.it/desktop/index.php?usr="+username+"&iss="+isbn+"&fld=sdf&id="+pageid+"&ext=js").content
		except:
			self.download(username,isbn,pagen)
		data=self.decrypt(content,pagen)
		f.write(data)
		f.close()

	def start(self):
		username=self.login(self.email,self.password)
		npages=self.get_npages(username,self.isbn)

		print "Starting downloading "+str(npages)+" pages."
		pagen=1
		signal=1
		while signal:
			for i in range(30-threading.activeCount()):
				if pagen==npages+1:signal=0;break;
				threading.Thread(target=self.download,args=(username,self.isbn,pagen,)).start()
				pagen+=1
			time.sleep(1)

		while 1:
			if threading.activeCount()==1:
				print "\nDone, got all pages."
				break
			else:
				time.sleep(1)

		print("\nConverting images to PDF format...")
		for npage in range(1,npages+1):
			pdf_bytes=img2pdf.convert(["/tmp/"+self.isbn+"_"+str(npage)+".jpg"])
			f = open("/tmp/"+self.isbn+"_"+str(npage)+".pdf","wb")
			f.write(pdf_bytes)
			f.close()
			sys.stdout.write("\rConverting page n. "+str(npage)+"...")
			sys.stdout.flush()
	
		merger = PyPDF2.PdfFileMerger()
		print("\nMerging everything...")
		for npage in range(1,npages+1):
			merger.append(PyPDF2.PdfFileReader(open("/tmp/"+self.isbn+"_"+str(npage)+'.pdf','rb')))
		merger.write(self.isbn+".pdf")
		print("Well done! "+self.isbn+".pdf created!")	
