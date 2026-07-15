import customtkinter as ctk 
from tkinter import messagebox 
import random 
import mysql.connector 
import datetime,socket

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('INSCRIPTION')
        self._set_appearance_mode('system')
        #self.attributes('-fullscreen',True)  
        self.geometry(f"{int(self.winfo_screenwidth())}x{int(self.winfo_screenheight())}+0+0") 
        ctk.set_default_color_theme("blue")
        self.configure(fg_color='white')
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.accueil()
        self.confirmer.configure(command=self.valider)
        self.bind_all('<Control-Shift-B>',lambda e: self.quit())
        #Maintenant, on supprime les raccourcis pour pouvoir quitter sans s'inscrire 
        #self.bind('<Alt-F4>',lambda e: "break")
        self.bind('<Escape>',lambda e: 'break')
        self.bind('<Control-w>',lambda e: 'break')
        self.bind('<Control-q>',lambda e: 'break')
        self.protocol('WM_DELETE_WINDOW',lambda e: None)
        self.bind('<Button-1>',self.animation)
        self.nom.bind('<Return>',self.valider_1)
        self.prenom.bind('<Return>',self.valider_2)
    def accueil(self):
        """Cette fonction est faite pour l'accueil, donc l'inscription"""
        self.boite = ctk.CTkFrame(self,fg_color='white')
        self.label = ctk.CTkLabel(self.boite,text="Authentification CAEB",text_color='blue',fg_color='white',font=('Times',50,'bold'),width=500,wraplength=400)
        self.nom = ctk.CTkEntry(self.boite,border_color='black',fg_color='white',bg_color='white',placeholder_text='Entrez votre nom',height=30,font=('Times',25,'italic'),text_color='black')
        self.nom_error = ctk.CTkLabel(self.boite,text="",text_color='red',fg_color='white',font=('Times',20,'normal'))
        self.prenom = ctk.CTkEntry(self.boite,border_color='black',fg_color='white',bg_color='white',placeholder_text='Entrez votre prenom',corner_radius=5,height=30,font=('Times',25,'italic'),text_color='black')
        self.prenom_error = ctk.CTkLabel(self.boite,text="",text_color='red',fg_color='white',font=('Times',20,'normal'))
        self.confirmer = ctk.CTkButton(self.boite,text='Confirmer',corner_radius=10,height=28,font=('Times',30,'bold'),fg_color='blue',text_color='white')
        self.placer()
        self.nom.focus()
    def placer(self):
        """CEtte fonction pour pouvoir ajouter les éléments créer sur l'app"""
        self.label.pack(pady=(5,10))
        self.boite.pack(expand=True,ipadx=5,ipady=5)
        self.nom.pack(expand=True,fill='x',padx=10,pady=5)
        self.nom_error.pack(expand=True)
        self.prenom.pack(expand=True,fill='x',padx=10,pady=5)
        self.prenom_error.pack(expand=True)
        self.confirmer.pack(expand=True,pady=(0,5))
    def valider(self):
        """Cette fonction va nous permettre de valider ce que les gens ont tapé d'abord"""
        self.name = self.nom.get()
        self.firstname = self.prenom.get()
        self.nom_error.configure(text='',text_color='red')
        self.prenom_error.configure(text='',text_color='red')
        if len(self.name)<3:
            self.nom_error.configure(text='Veuillez entrer un nom valide',text_color='red')
        if len(self.firstname)<3:
            self.prenom_error.configure(text='Veuillez entrer un prénom valide',text_color='red')
        if len(self.name)>=3 and len(self.firstname)>=3:
            self.nom_error.configure(text='Valide',text_color='blue')
            self.prenom_error.configure(text='Valide',text_color='blue')
            self.pusher()
    def valider_1(self,e):
        """Pour la validation de la premiere frappe"""
        self.nom_error.configure(text='',text_color='red')
        self.prenom_error.configure(text='',text_color='red')
        if 0<len(self.nom.get())<3:
            self.nom_error.configure(text='Veuillez entrer un nom valide',text_color='red')
        if len(self.nom.get())==0:
            self.nom_error.configure(text='Entrée vide',text_color='red')
        if len(self.nom.get())>3:
            self.nom_error.configure(text='Valide',text_color='blue')
            self.prenom.focus()

    def valider_2(self,e):
        """POur la validation de la deuxième frappe"""
        self.nom_error.configure(text='',text_color='red')
        self.prenom_error.configure(text='',text_color='red')
        if 0<len(self.prenom.get())<3:
            self.prenom_error.configure(text='Veuillez entrer un nom valide',text_color='red')
        if len(self.prenom.get())==0:
            self.prenom_error.configure(text='Entrée vide',text_color='red')
        if len(self.prenom.get())>3:
            self.prenom_error.configure(text='Valide',text_color='blue')
            self.valider()

    def pusher(self):
        """Cette fonction pour la commande que fera le bouton confirmer """
        self.nom_pc = socket.gethostname()
        adresse_ip = socket.gethostbyname('CIA-008')
        conn = mysql.connector.connect(
        host=adresse_ip,
        user='inscription',
        password='CLUBIA',
        database='authentification')
        cursor = conn.cursor()

        try:
            sql = "INSERT INTO users (nom,prenom,date,nom_pc) VALUES (%s,%s,%s,%s)"
            valeurs = (self.name.upper(),self.firstname.capitalize(),str(datetime.datetime.now()),self.nom_pc)
            cursor.execute(sql,valeurs)
            conn.commit()
        except Exception as e:
            self.prenom_error.configure(text=f'Erreur rencontrée {e}',text_color='red')
            messagebox.showerror('Mysql',e)
        self.quit()
    def animation(self,e):
        """C'est juste une petite animation qu'on veut faire pour pouvoir faire apparaître des cercles sur l'écran"""
       


app = App()
app.mainloop()