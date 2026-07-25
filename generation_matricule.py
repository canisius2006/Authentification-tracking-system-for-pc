from datetime import datetime 
import random 

def create_matricule():
    a = f'{int(str(datetime.now().year)[2:]):02d}'
    b = f'{datetime.now().month:02d}' 
    c = f'{random.randint(1,999):03d}'
    d = f'{(97 - ((int(a+b+c))%97)):02d}'
    e = str(a)+b+'U'+c+str(d)
    return e
print(create_matricule())